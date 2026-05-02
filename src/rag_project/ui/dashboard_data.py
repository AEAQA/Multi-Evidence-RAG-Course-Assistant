"""Data helpers for the Streamlit MVP dashboard."""

from __future__ import annotations

import csv
from pathlib import Path

from pydantic import BaseModel

from rag_project.app_services.query_service import QueryService, WorkbenchState
from rag_project.config import AppConfig, load_config
from rag_project.evaluation.loader import load_evaluation_queries
from rag_project.evaluation.runner import (
    evaluate_retrieval_methods,
    write_evaluation_reports,
)
from rag_project.evaluation.sample_corpus import build_sample_evaluation_chunks

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_QUERY_PATH = ROOT / "data" / "eval" / "queries.jsonl"
DEFAULT_REPORT_DIR = ROOT / "reports" / "evaluation"

DashboardState = WorkbenchState


class EvaluationReportData(BaseModel):
    """Evaluation report tables and Markdown for display."""

    metrics: list[dict[str, str]]
    latency: list[dict[str, str]]
    error_cases_markdown: str


def build_sample_dashboard_state(
    query: str,
    top_k: int = 5,
    *,
    config: AppConfig | None = None,
) -> DashboardState:
    """Run local retrieval and mock answer generation over the sample corpus."""
    runtime_config = config or load_config()
    return QueryService(config=runtime_config).run(query, top_k=top_k)


def load_or_create_evaluation_reports(
    *,
    report_dir: str | Path = DEFAULT_REPORT_DIR,
    query_path: str | Path = DEFAULT_QUERY_PATH,
) -> EvaluationReportData:
    """Read existing reports or create them from local sample data."""
    report_path = Path(report_dir)
    metrics_path = report_path / "retrieval_metrics.csv"
    latency_path = report_path / "latency_metrics.csv"
    error_cases_path = report_path / "error_cases.md"

    if not (
        metrics_path.exists() and latency_path.exists() and error_cases_path.exists()
    ):
        queries = load_evaluation_queries(query_path)
        chunks = build_sample_evaluation_chunks()
        result = evaluate_retrieval_methods(chunks, queries, top_k=5)
        write_evaluation_reports(result, report_path)

    return EvaluationReportData(
        metrics=_read_csv_rows(metrics_path),
        latency=_read_csv_rows(latency_path),
        error_cases_markdown=error_cases_path.read_text(encoding="utf-8"),
    )


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))
