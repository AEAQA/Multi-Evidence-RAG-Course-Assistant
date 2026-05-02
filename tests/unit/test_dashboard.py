from pathlib import Path

import app.streamlit_app as streamlit_app
from rag_project.config import AppConfig
from rag_project.schemas import Chunk, ChunkMetadata, RetrievalResult
from rag_project.ui.dashboard_data import (
    build_sample_dashboard_state,
    load_or_create_evaluation_reports,
)


def test_streamlit_app_module_imports() -> None:
    assert callable(streamlit_app.main)


def test_workbench_query_requires_explicit_run_button() -> None:
    assert streamlit_app._should_run_query(False, "What is overfitting?") is False
    assert streamlit_app._should_run_query(True, "What is overfitting?") is True
    assert streamlit_app._should_run_query(True, "   ") is False


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
    assert state.diagnostics
    assert state.timing_ms["total"] >= 0


def test_dashboard_state_does_not_require_api_keys(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SILICONFLOW_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    state = build_sample_dashboard_state(
        "What does reranking do?",
        top_k=2,
        config=AppConfig(),
    )

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


def test_results_to_frame_handles_image_metadata_without_pandas() -> None:
    chunk = Chunk(
        chunk_id="doc001_page002_image_0001",
        doc_id="doc001",
        source_file="lecture.pdf",
        page=2,
        type="image",
        text="A diagram of hybrid retrieval.",
        metadata=ChunkMetadata(
            image_path="data/processed/images/doc001_p002_img001.png",
            bbox=[72.0, 110.0, 172.0, 210.0],
            caption="A diagram of hybrid retrieval.",
            nearby_text="The figure below shows the retrieval pipeline.",
        ),
    )
    result = RetrievalResult(
        chunk_id=chunk.chunk_id,
        score=1.0,
        rank=1,
        method="reranked",
        chunk=chunk,
    )

    rows = streamlit_app._results_to_frame([result])

    assert isinstance(rows, list)
    assert rows[0]["type"] == "image"
    assert rows[0]["image_path"] == "data/processed/images/doc001_p002_img001.png"
    assert rows[0]["caption"] == "A diagram of hybrid retrieval."


def test_diagnostics_to_rows_are_plain_dicts() -> None:
    state = build_sample_dashboard_state(
        "What is overfitting?",
        top_k=2,
        config=AppConfig(),
    )

    rows = streamlit_app._diagnostics_to_rows(state.diagnostics)

    assert isinstance(rows, list)
    assert rows[0]["method"]
    assert rows[0]["confidence"]
    assert rows[0]["recommendation"]
