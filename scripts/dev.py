"""
Cross-platform developer command wrapper.

Usage:
python scripts/dev.py info
python scripts/dev.py test
python scripts/dev.py run
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


def cmd_test(_: argparse.Namespace) -> int:
    """Run test suite."""
    basetemp = ROOT / "pytest_runs" / uuid.uuid4().hex
    basetemp.parent.mkdir(exist_ok=True)
    return run_command(
        [sys.executable, "-m", "pytest", "--basetemp", str(basetemp)]
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
    test_parser.set_defaults(func=cmd_test)

    run_parser = subparsers.add_parser("run", help="Run Streamlit app.")
    run_parser.set_defaults(func=cmd_run)

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
