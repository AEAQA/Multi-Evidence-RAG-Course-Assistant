from rag_project.app_services.query_service import (
    QueryService,
    build_corpus_signature,
    build_retrieval_pipeline,
)
from rag_project.config import AppConfig
from rag_project.schemas import Chunk, ChunkMetadata, RetrievalPipelineOutput, RetrievalResult
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


def test_query_service_final_evidence_preview_uses_sentence_boundary() -> None:
    long_text = (
        "This first sentence gives a readable grounded explanation about reranking and final evidence. "
        "This second sentence adds enough context for the evidence card without cutting words apart. "
        + "extra context " * 80
    )
    chunk = Chunk(
        chunk_id="uploaded_doc_page001_text_0001",
        doc_id="uploaded_doc",
        source_file="custom_notes.txt",
        page=1,
        type="text",
        text=long_text,
        metadata=ChunkMetadata(),
    )

    state = QueryService(config=AppConfig(), chunks=[chunk]).run(
        "What does the readable explanation say about reranking?",
        top_k=1,
    )

    preview = state.final_evidence[0].preview
    assert preview.endswith("...")
    assert len(preview) <= 523
    assert not preview.endswith("context ...")


def test_invalid_table_chunks_do_not_become_cited_evidence() -> None:
    table = Chunk(
        chunk_id="doc_page001_table_0001",
        doc_id="doc",
        source_file="tables.pdf",
        page=1,
        type="table",
        text="Table extracted from PDF.",
        metadata=ChunkMetadata(caption="Table extracted from PDF."),
    )
    pipeline = _StaticPipeline([_result(table, score=0.99)])

    state = QueryService(
        config=AppConfig(),
        chunks=[table],
        retrieval_pipeline=pipeline,
    ).run("What does this table say?", top_k=1)

    assert state.retrieval.reranked_results[0].chunk_id == table.chunk_id
    assert state.answer.insufficient_evidence is True
    assert state.final_evidence == []
    assert state.answer.citations == []


def test_valid_table_chunks_are_allowed_for_table_intent_queries() -> None:
    text = Chunk(
        chunk_id="doc_page001_text_0001",
        doc_id="doc",
        source_file="tables.pdf",
        page=1,
        type="text",
        text="The notes explain model evaluation in prose.",
        metadata=ChunkMetadata(),
    )
    table = Chunk(
        chunk_id="doc_page001_table_0001",
        doc_id="doc",
        source_file="tables.pdf",
        page=1,
        type="table",
        text="Method Accuracy Recall Precision BM25 0.80 0.76 0.84 Dense 0.71 0.69 0.73 Fusion 0.86 0.82 0.88",
        metadata=ChunkMetadata(
            table_summary="Method Accuracy Recall Precision BM25 0.80 0.76 0.84 Dense 0.71 0.69 0.73 Fusion 0.86 0.82 0.88",
            table_html="<table><tr><td>Method</td><td>Accuracy</td></tr><tr><td>BM25</td><td>0.80</td></tr></table>",
        ),
    )
    pipeline = _StaticPipeline([
        _result(text, score=0.95),
        _result(table, score=0.90),
    ])

    state = QueryService(
        config=AppConfig(),
        chunks=[text, table],
        retrieval_pipeline=pipeline,
    ).run("Compare the numerical data in the table columns.", top_k=2)

    assert state.answer.insufficient_evidence is False
    assert state.final_evidence[0].chunk_id == table.chunk_id
    assert state.final_evidence[0].table_summary
    assert state.answer.citations[0].evidence_id == "E1"


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


class _StaticPipeline:
    def __init__(self, reranked_results: list[RetrievalResult]) -> None:
        self.reranked_results = reranked_results

    def search_with_timing(
        self,
        query: str,
        *,
        top_k: int,
    ) -> tuple[RetrievalPipelineOutput, dict[str, float]]:
        output = RetrievalPipelineOutput(
            bm25_results=self.reranked_results[:top_k],
            dense_results=self.reranked_results[:top_k],
            fusion_results=self.reranked_results[:top_k],
            reranked_results=self.reranked_results[:top_k],
        )
        return output, {
            "bm25": 0.0,
            "dense": 0.0,
            "fusion": 0.0,
            "reranker": 0.0,
            "retrieval": 0.0,
        }


def _result(chunk: Chunk, *, score: float) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=chunk.chunk_id,
        score=score,
        rank=1,
        method="reranked",
        chunk=chunk,
    )
