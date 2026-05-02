from pathlib import Path

import pytest

from rag_project.evaluation.loader import load_evaluation_queries
from rag_project.evaluation.runner import (
    EvaluationQuery,
    evaluate_retrieval_methods,
    write_evaluation_reports,
)
from rag_project.schemas import Chunk, ChunkMetadata


def _chunk(chunk_id: str, text: str) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        doc_id="eval",
        source_file="sample_eval.txt",
        page=1,
        type="text",
        text=text,
        metadata=ChunkMetadata(),
    )


def _chunks() -> list[Chunk]:
    return [
        _chunk("eval_page001_text_0001", "overfitting validation generalization"),
        _chunk("eval_page001_text_0002", "dense retrieval embeddings semantic search"),
        _chunk("eval_page001_text_0003", "office hours grading logistics"),
    ]


def test_load_evaluation_queries_from_jsonl(tmp_path: Path) -> None:
    query_path = tmp_path / "queries.jsonl"
    query_path.write_text(
        '{"query_id":"q001","query":"What is overfitting?",'
        '"relevant_chunk_ids":["eval_page001_text_0001"]}\n',
        encoding="utf-8",
    )

    queries = load_evaluation_queries(query_path)

    assert queries == [
        EvaluationQuery(
            query_id="q001",
            query="What is overfitting?",
            relevant_chunk_ids=["eval_page001_text_0001"],
        )
    ]


def test_load_evaluation_queries_rejects_invalid_jsonl(tmp_path: Path) -> None:
    query_path = tmp_path / "queries.jsonl"
    query_path.write_text('{"query_id":"q001"}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid evaluation query"):
        load_evaluation_queries(query_path)


def test_evaluate_retrieval_methods_returns_metrics_and_latency_rows() -> None:
    queries = [
        EvaluationQuery(
            query_id="q001",
            query="overfitting validation",
            relevant_chunk_ids=["eval_page001_text_0001"],
        )
    ]

    result = evaluate_retrieval_methods(_chunks(), queries, top_k=5)

    assert {row["method"] for row in result.metric_rows} == {
        "bm25",
        "dense",
        "fusion",
        "reranked",
    }
    assert {row["method"] for row in result.latency_rows} == {
        "bm25",
        "dense",
        "fusion",
        "reranked",
    }
    assert all(row["latency_ms"] >= 0.0 for row in result.latency_rows)
    assert result.summary_by_method["bm25"]["recall@5"] == 1.0


def test_write_evaluation_reports_creates_required_files(tmp_path: Path) -> None:
    queries = [
        EvaluationQuery(
            query_id="q001",
            query="overfitting validation",
            relevant_chunk_ids=["eval_page001_text_0001"],
        )
    ]
    result = evaluate_retrieval_methods(_chunks(), queries, top_k=5)

    written = write_evaluation_reports(result, tmp_path)

    assert (tmp_path / "retrieval_metrics.csv").exists()
    assert (tmp_path / "latency_metrics.csv").exists()
    assert (tmp_path / "error_cases.md").exists()
    assert set(written) == {
        tmp_path / "retrieval_metrics.csv",
        tmp_path / "latency_metrics.csv",
        tmp_path / "error_cases.md",
    }
