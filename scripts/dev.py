"""
Cross-platform developer command wrapper.

Usage:
python scripts/dev.py info
python scripts/dev.py test
python scripts/dev.py run
python scripts/dev.py api
python scripts/dev.py ui
python scripts/dev.py ui-test
python scripts/dev.py eval
python scripts/dev.py api-smoke
python scripts/dev.py clean

This script is intended for both human developers and coding agents.
It avoids relying on platform-specific shell commands such as make/source.
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_command(command: list[str], cwd: Path | None = None) -> int:
    """Run a command and stream output to the current terminal."""
    cwd = cwd or ROOT
    env = os.environ.copy()
    src_path = str(ROOT / "src")
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        src_path
        if not existing_pythonpath
        else os.pathsep.join([src_path, existing_pythonpath])
    )
    if platform.system() == "Windows":
        node_dir = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "nodejs"
        if node_dir.exists():
            env["PATH"] = os.pathsep.join([str(node_dir), env.get("PATH", "")])
    print(f"\n[dev.py] Running: {' '.join(command)}")
    print(f"[dev.py] Working directory: {cwd}\n")
    try:
        completed = subprocess.run(command, cwd=str(cwd), env=env, check=False)
        return int(completed.returncode)
    except FileNotFoundError as exc:
        print(f"[dev.py] Command not found: {command[0]}")
        print(f"[dev.py] Error: {exc}")
        return 127


def cmd_info(_: argparse.Namespace) -> int:
    """Print environment and project information."""
    print("[dev.py] Project root:", ROOT)
    print("[dev.py] OS:", platform.system())
    print("[dev.py] OS version:", platform.platform())
    print("[dev.py] Python executable:", sys.executable)
    print("[dev.py] Python version:", sys.version.replace("\n", " "))
    print("[dev.py] Current working directory:", Path.cwd())

    conda_prefix = os.environ.get("CONDA_PREFIX")
    conda_default_env = os.environ.get("CONDA_DEFAULT_ENV")
    print("[dev.py] CONDA_PREFIX:", conda_prefix or "<not set>")
    print("[dev.py] CONDA_DEFAULT_ENV:", conda_default_env or "<not set>")

    return 0


def cmd_test(args: argparse.Namespace) -> int:
    """Run test suite."""
    basetemp = ROOT / "pytest_runs" / uuid.uuid4().hex
    cache_dir = ROOT / "pytest_runs" / f"cache_{uuid.uuid4().hex}"
    basetemp.parent.mkdir(exist_ok=True)
    pytest_args = list(args.pytest_args or [])
    if pytest_args and pytest_args[0] == "--":
        pytest_args = pytest_args[1:]
    return run_command(
        [
            sys.executable,
            "-m",
            "pytest",
            "--basetemp",
            str(basetemp),
            "-o",
            f"cache_dir={cache_dir}",
            *pytest_args,
        ]
    )


def cmd_run(_: argparse.Namespace) -> int:
    """Run Streamlit app."""
    app_path = ROOT / "app" / "streamlit_app.py"
    if not app_path.exists():
        print(f"[dev.py] Streamlit app not found: {app_path}")
        print("[dev.py] Create app/streamlit_app.py first.")
        return 1

    return run_command(
        [sys.executable, "-m", "streamlit", "run", str(app_path)]
    )


def cmd_api(_: argparse.Namespace) -> int:
    """Run FastAPI adapter for the React product UI."""
    return run_command(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "rag_project.api.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--reload",
        ]
    )


def _npm_command() -> str:
    npm_name = "npm.cmd" if platform.system() == "Windows" else "npm"
    resolved = shutil.which(npm_name)
    if resolved:
        return resolved
    if platform.system() == "Windows":
        candidates = [
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "nodejs" / "npm.cmd",
            Path(os.environ.get("APPDATA", "")) / "npm" / "npm.cmd",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "nodejs" / "npm.cmd",
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
    return npm_name


def cmd_ui(_: argparse.Namespace) -> int:
    """Run the React product UI dev server."""
    frontend_dir = ROOT / "frontend"
    if not frontend_dir.exists():
        print(f"[dev.py] Frontend directory not found: {frontend_dir}")
        return 1
    return run_command([_npm_command(), "run", "dev"], cwd=frontend_dir)


def cmd_ui_test(_: argparse.Namespace) -> int:
    """Run React product UI tests."""
    frontend_dir = ROOT / "frontend"
    if not frontend_dir.exists():
        print(f"[dev.py] Frontend directory not found: {frontend_dir}")
        return 1
    return run_command([_npm_command(), "run", "test"], cwd=frontend_dir)


def cmd_eval(_: argparse.Namespace) -> int:
    """Run retrieval evaluation pipeline."""
    module = "rag_project.evaluation.run_evaluation"
    return run_command([sys.executable, "-m", module])


def cmd_api_smoke(_: argparse.Namespace) -> int:
    """Run optional API-enhanced smoke check."""
    module = "rag_project.api_smoke"
    return run_command([sys.executable, "-m", module])


def cmd_clean(_: argparse.Namespace) -> int:
    """Remove common local cache/output directories."""
    targets = [
        ROOT / ".pytest_cache",
        ROOT / ".pytest_tmp",
        ROOT / ".mypy_cache",
        ROOT / ".ruff_cache",
        ROOT / "pytest_tmp",
        ROOT / "pytest_run_tmp",
        ROOT / "pytest_runs",
        ROOT / "reports" / "evaluation",
        ROOT / "reports" / "figures",
    ]

    targets.extend(ROOT.glob("pytest-cache-files-*"))

    for target in targets:
        if target.exists():
            print(f"[dev.py] Removing: {target}")
            try:
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            except OSError as exc:
                print(f"[dev.py] Warning: could not remove {target}: {exc}")

    for pycache in ROOT.rglob("__pycache__"):
        print(f"[dev.py] Removing: {pycache}")
        try:
            shutil.rmtree(pycache)
        except OSError as exc:
            print(f"[dev.py] Warning: could not remove {pycache}: {exc}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cross-platform project command runner."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    info_parser = subparsers.add_parser("info", help="Show environment info.")
    info_parser.set_defaults(func=cmd_info)

    test_parser = subparsers.add_parser("test", help="Run tests.")
    test_parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Optional arguments passed through to pytest after --.",
    )
    test_parser.set_defaults(func=cmd_test)

    run_parser = subparsers.add_parser("run", help="Run Streamlit app.")
    run_parser.set_defaults(func=cmd_run)

    api_parser = subparsers.add_parser("api", help="Run FastAPI adapter.")
    api_parser.set_defaults(func=cmd_api)

    ui_parser = subparsers.add_parser("ui", help="Run React product UI.")
    ui_parser.set_defaults(func=cmd_ui)

    ui_test_parser = subparsers.add_parser("ui-test", help="Run React product UI tests.")
    ui_test_parser.set_defaults(func=cmd_ui_test)

    eval_parser = subparsers.add_parser("eval", help="Run evaluation.")
    eval_parser.set_defaults(func=cmd_eval)

    api_smoke_parser = subparsers.add_parser(
        "api-smoke", help="Run optional API smoke check."
    )
    api_smoke_parser.set_defaults(func=cmd_api_smoke)

    clean_parser = subparsers.add_parser("clean", help="Clean local caches and reports.")
    clean_parser.set_defaults(func=cmd_clean)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
