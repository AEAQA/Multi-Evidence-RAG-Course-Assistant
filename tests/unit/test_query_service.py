from rag_project.app_services.query_service import QueryService
from rag_project.config import AppConfig
from rag_project.schemas import Chunk, ChunkMetadata


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
    assert {item.method for item in state.diagnostics} == {
        "bm25",
        "dense",
        "fusion",
        "reranked",
    }


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
