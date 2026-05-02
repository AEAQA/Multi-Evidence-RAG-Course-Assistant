from pathlib import Path

import app.streamlit_app as streamlit_app
from rag_project.ui.dashboard_data import (
    build_sample_dashboard_state,
    load_or_create_evaluation_reports,
)


def test_streamlit_app_module_imports() -> None:
    assert callable(streamlit_app.main)


def test_build_sample_dashboard_state_returns_retrieval_and_answer() -> None:
    state = build_sample_dashboard_state("What is overfitting?", top_k=3)

    assert state.query == "What is overfitting?"
    assert state.retrieval.bm25_results
    assert state.retrieval.dense_results
    assert state.retrieval.fusion_results
    assert state.retrieval.reranked_results
    assert state.answer.answer
    assert state.answer.citations
    assert state.answer.evidence_chunks


def test_dashboard_state_does_not_require_api_keys(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SILICONFLOW_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    state = build_sample_dashboard_state("What does reranking do?", top_k=2)

    assert state.answer.insufficient_evidence is False
    assert state.answer.citations


def test_load_or_create_evaluation_reports_creates_missing_reports(tmp_path: Path) -> None:
    reports = load_or_create_evaluation_reports(report_dir=tmp_path)

    assert reports.metrics
    assert reports.latency
    assert "Retrieval Error Cases" in reports.error_cases_markdown
    assert (tmp_path / "retrieval_metrics.csv").exists()
    assert (tmp_path / "latency_metrics.csv").exists()
    assert (tmp_path / "error_cases.md").exists()
