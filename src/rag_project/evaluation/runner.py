"""Retrieval evaluation runner and report writers."""

from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import Callable

from pydantic import BaseModel, Field

from rag_project.evaluation.metrics import evaluate_retrieval_run, mean_metrics
from rag_project.retrieval.bm25_retriever import BM25Retriever
from rag_project.retrieval.dense_retriever import FakeDenseRetriever
from rag_project.retrieval.fusion import reciprocal_rank_fusion
from rag_project.retrieval.reranker import MockRerankerClient
from rag_project.schemas import Chunk, RetrievalResult


class EvaluationQuery(BaseModel):
    query_id: str
    query: str
    relevant_chunk_ids: list[str] = Field(min_length=1)


class EvaluationResult(BaseModel):
    metric_rows: list[dict[str, float | str]]
    latency_rows: list[dict[str, float | str]]
    summary_by_method: dict[str, dict[str, float]]
    error_cases_markdown: str


def evaluate_retrieval_methods(
    chunks: list[Chunk],
    queries: list[EvaluationQuery],
    *,
    top_k: int = 5,
) -> EvaluationResult:
    """Evaluate BM25, dense, fusion, and reranked retrieval."""
    bm25 = BM25Retriever(chunks)
    dense = FakeDenseRetriever(chunks)
    reranker = MockRerankerClient()

    metric_rows: list[dict[str, float | str]] = []
    latency_rows: list[dict[str, float | str]] = []
    per_query_results: list[tuple[EvaluationQuery, str, list[str], dict[str, float]]] = []

    for query in queries:
        bm25_results, bm25_latency = _timed(lambda: bm25.search(query.query, top_k=top_k))
        dense_results, dense_latency = _timed(
            lambda: dense.search(query.query, top_k=top_k)
        )
        fusion_results, fusion_latency = _timed(
            lambda: reciprocal_rank_fusion(
                [bm25_results, dense_results],
                top_k=top_k,
            )
        )
        reranked_results, reranked_latency = _timed(
            lambda: _rerank(query.query, fusion_results, reranker, top_k=top_k)
        )

        method_outputs = {
            "bm25": (bm25_results, bm25_latency),
            "dense": (dense_results, dense_latency),
            "fusion": (fusion_results, bm25_latency + dense_latency + fusion_latency),
            "reranked": (
                reranked_results,
                bm25_latency + dense_latency + fusion_latency + reranked_latency,
            ),
        }

        for method, (results, latency_ms) in method_outputs.items():
            retrieved_ids = [result.chunk_id for result in results]
            metrics = evaluate_retrieval_run(
                retrieved_chunk_ids=retrieved_ids,
                relevant_chunk_ids=query.relevant_chunk_ids,
            )
            metric_rows.append(
                {
                    "query_id": query.query_id,
                    "method": method,
                    **metrics,
                }
            )
            latency_rows.append(
                {
                    "query_id": query.query_id,
                    "method": method,
                    "latency_ms": latency_ms,
                }
            )
            per_query_results.append((query, method, retrieved_ids, metrics))

    summary_by_method = _summarize_by_method(metric_rows)
    error_cases_markdown = _build_error_cases_markdown(per_query_results)
    return EvaluationResult(
        metric_rows=metric_rows,
        latency_rows=latency_rows,
        summary_by_method=summary_by_method,
        error_cases_markdown=error_cases_markdown,
    )


def write_evaluation_reports(
    result: EvaluationResult,
    output_dir: str | Path,
) -> list[Path]:
    """Write required M4 report artifacts."""
    report_dir = Path(output_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = report_dir / "retrieval_metrics.csv"
    latency_path = report_dir / "latency_metrics.csv"
    error_cases_path = report_dir / "error_cases.md"

    _write_csv(metrics_path, result.metric_rows)
    _write_csv(latency_path, result.latency_rows)
    error_cases_path.write_text(result.error_cases_markdown, encoding="utf-8")

    return [metrics_path, latency_path, error_cases_path]


def _timed(
    callback: Callable[[], list[RetrievalResult]]
) -> tuple[list[RetrievalResult], float]:
    start = time.perf_counter()
    results = callback()
    latency_ms = (time.perf_counter() - start) * 1000.0
    return results, latency_ms


def _rerank(
    query: str,
    fusion_results: list[RetrievalResult],
    reranker: MockRerankerClient,
    *,
    top_k: int,
) -> list[RetrievalResult]:
    chunks_by_id = {result.chunk_id: result.chunk for result in fusion_results}
    reranked = reranker.rerank(query, [result.chunk for result in fusion_results])

    output: list[RetrievalResult] = []
    for rank, result in enumerate(reranked[:top_k], start=1):
        chunk = chunks_by_id[result.chunk_id]
        output.append(
            RetrievalResult(
                chunk_id=result.chunk_id,
                score=result.score,
                rank=rank,
                method="reranked",
                chunk=chunk,
            )
        )
    return output


def _summarize_by_method(
    metric_rows: list[dict[str, float | str]]
) -> dict[str, dict[str, float]]:
    methods = sorted({str(row["method"]) for row in metric_rows})
    summary: dict[str, dict[str, float]] = {}
    for method in methods:
        rows = [
            {
                key: float(value)
                for key, value in row.items()
                if key not in {"query_id", "method"}
            }
            for row in metric_rows
            if row["method"] == method
        ]
        summary[method] = mean_metrics(rows)
    return summary


def _build_error_cases_markdown(
    rows: list[tuple[EvaluationQuery, str, list[str], dict[str, float]]]
) -> str:
    successes = [row for row in rows if row[3].get("recall@5", 0.0) >= 1.0][:3]
    weak_cases = [row for row in rows if row[3].get("recall@5", 0.0) < 1.0][:3]

    lines = ["# Retrieval Error Cases", ""]
    lines.extend(_format_cases("Successful Cases", successes))
    lines.extend(_format_cases("Weak Or Failed Cases", weak_cases))
    if not weak_cases:
        lines.extend(
            [
                "## Weak Or Failed Cases",
                "",
                "No weak cases were found in this evaluation run.",
                "",
            ]
        )
    return "\n".join(lines)


def _format_cases(
    title: str,
    rows: list[tuple[EvaluationQuery, str, list[str], dict[str, float]]],
) -> list[str]:
    lines = [f"## {title}", ""]
    if not rows:
        lines.extend(["No cases available.", ""])
        return lines

    for query, method, retrieved_ids, metrics in rows:
        lines.extend(
            [
                f"### {query.query_id} - {method}",
                "",
                f"- Query: {query.query}",
                f"- Expected evidence: {', '.join(query.relevant_chunk_ids)}",
                f"- Retrieved evidence: {', '.join(retrieved_ids) if retrieved_ids else '<none>'}",
                f"- Recall@5: {metrics.get('recall@5', 0.0):.3f}",
                "",
            ]
        )
    return lines


def _write_csv(path: Path, rows: list[dict[str, float | str]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
