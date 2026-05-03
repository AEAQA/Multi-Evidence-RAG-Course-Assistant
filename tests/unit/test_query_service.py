from rag_project.app_services.query_service import (
    QueryService,
    build_corpus_signature,
    build_retrieval_pipeline,
)
from rag_project.config import AppConfig
from rag_project.schemas import Chunk, ChunkMetadata
import re


def test_query_service_returns_workbench_state() -> None:
    state = QueryService(config=AppConfig()).run(
        "What is overfitting?",
        top_k=3,
    )

    assert state.query == "What is overfitting?"
    assert state.answer.answer
    assert state.answer.citations
    assert state.answer.evidence_chunks
    assert state.retrieval.bm25_results
    assert state.retrieval.dense_results
    assert state.retrieval.fusion_results
    assert state.retrieval.reranked_results
    assert state.timing_ms["total"] >= 0
    assert {
        "bm25",
        "dense",
        "fusion",
        "reranker",
        "retrieval",
        "retrieval_total",
        "pipeline_build",
        "generation",
        "total",
    } <= set(state.timing_ms)
    assert {item.method for item in state.diagnostics} == {
        "bm25",
        "dense",
        "fusion",
        "reranked",
    }
    assert [item.evidence_id for item in state.final_evidence[:3]] == ["E1", "E2", "E3"]
    assert all(citation.evidence_id for citation in state.answer.citations)
    assert "[E1]" in state.answer.answer
    assert "References:" not in state.answer.answer
    markers = set(re.findall(r"\[(E\d+)\]", state.answer.answer))
    citation_ids = {citation.evidence_id for citation in state.answer.citations}
    evidence_ids = {item.evidence_id for item in state.final_evidence}
    assert markers <= citation_ids
    assert markers <= evidence_ids
    assert [stage.stage for stage in state.retrieval_trace] == [
        "BM25",
        "Dense",
        "Fusion",
        "Reranker",
        "Final Evidence",
    ]
    assert state.scope["chunk_count"] > 0


def test_query_service_no_key_api_mode_falls_back_to_mock() -> None:
    config = AppConfig(
        app_mode="api",
        llm_provider="siliconflow",
        llm_model="deepseek-ai/DeepSeek-V3",
        reranker_provider="siliconflow",
        reranker_model="BAAI/bge-reranker-v2-m3",
        siliconflow_api_key="",
    )

    state = QueryService(config=config).run("What does reranking do?", top_k=2)

    assert state.answer.answer
    assert state.provider_status.by_component["llm"].state == "missing-key"
    assert state.provider_status.by_component["reranker"].state == "missing-key"


def test_query_service_diagnostics_are_stable() -> None:
    state = QueryService(config=AppConfig()).run("overfitting validation", top_k=2)
    reranked = next(item for item in state.diagnostics if item.method == "reranked")

    assert reranked.result_count == 2
    assert reranked.confidence_label in {"high", "medium", "low", "none"}
    assert reranked.recommendation


def test_query_service_empty_corpus_returns_insufficient_evidence() -> None:
    state = QueryService(config=AppConfig(), chunks=[]).run(
        "Can the system answer without documents?",
        top_k=3,
    )

    assert state.answer.insufficient_evidence is True
    assert not state.answer.evidence_chunks
    assert all(item.confidence_label == "none" for item in state.diagnostics)


def test_query_service_uses_selected_uploaded_chunks() -> None:
    chunk = Chunk(
        chunk_id="uploaded_doc_page001_text_0001",
        doc_id="uploaded_doc",
        source_file="custom_notes.txt",
        page=1,
        type="text",
        text="The custom notes say alpha calibration is checked with held-out validation data.",
        metadata=ChunkMetadata(),
    )

    state = QueryService(config=AppConfig(), chunks=[chunk]).run(
        "What do the custom notes say about alpha calibration?",
        top_k=1,
    )

    assert state.answer.citations[0].source_file == "custom_notes.txt"
    assert state.answer.evidence_chunks[0].chunk_id == chunk.chunk_id


def test_query_service_exposes_scored_final_evidence_results() -> None:
    chunk = Chunk(
        chunk_id="uploaded_doc_page001_text_0001",
        doc_id="uploaded_doc",
        source_file="custom_notes.txt",
        page=1,
        type="text",
        text="The custom notes say reranking selects final evidence chunks.",
        metadata=ChunkMetadata(),
    )

    state = QueryService(config=AppConfig(), chunks=[chunk]).run(
        "What selects final evidence chunks?",
        top_k=1,
    )

    assert state.final_evidence_results
    result = state.final_evidence_results[0]
    assert result.chunk_id == chunk.chunk_id
    assert result.method == "reranked"
    assert result.score >= 0
    assert state.final_evidence[0].evidence_id == "E1"
    assert state.final_evidence[0].chunk_id == chunk.chunk_id
    assert state.answer.citations[0].evidence_id == "E1"
    assert "[E1]" in state.answer.answer
    assert "References:" not in state.answer.answer


def test_query_service_accepts_prebuilt_retrieval_pipeline() -> None:
    chunk = Chunk(
        chunk_id="uploaded_doc_page001_text_0001",
        doc_id="uploaded_doc",
        source_file="custom_notes.txt",
        page=1,
        type="text",
        text="Cached indexes should answer questions about validation data.",
        metadata=ChunkMetadata(),
    )
    pipeline = build_retrieval_pipeline([chunk])

    state = QueryService(
        config=AppConfig(),
        chunks=[chunk],
        retrieval_pipeline=pipeline,
    ).run("What should cached indexes answer about?", top_k=1)

    assert state.answer.citations[0].source_file == "custom_notes.txt"
    assert state.timing_ms["pipeline_build"] >= 0
    assert state.timing_ms["bm25"] >= 0


def test_build_corpus_signature_is_stable_for_same_chunks() -> None:
    chunk = Chunk(
        chunk_id="doc_page001_text_0001",
        doc_id="doc",
        source_file="notes.txt",
        page=1,
        type="text",
        text="Stable signatures let Streamlit reuse cached retrieval pipelines.",
        metadata=ChunkMetadata(),
    )

    assert build_corpus_signature([chunk]) == build_corpus_signature([chunk])
