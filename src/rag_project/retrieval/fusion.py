"""Hybrid retrieval fusion utilities."""

from __future__ import annotations

from rag_project.schemas import RetrievalResult


def reciprocal_rank_fusion(
    result_lists: list[list[RetrievalResult]],
    *,
    top_k: int = 5,
    k: int = 60,
) -> list[RetrievalResult]:
    """Fuse ranked retrieval lists by reciprocal rank fusion."""
    if top_k <= 0:
        return []

    scores: dict[str, float] = {}
    chunks: dict[str, RetrievalResult] = {}
    best_rank: dict[str, int] = {}

    for results in result_lists:
        for result in results:
            scores[result.chunk_id] = scores.get(result.chunk_id, 0.0) + (
                1.0 / (k + result.rank)
            )
            chunks.setdefault(result.chunk_id, result)
            best_rank[result.chunk_id] = min(
                best_rank.get(result.chunk_id, result.rank), result.rank
            )

    ranked_ids = sorted(
        scores,
        key=lambda chunk_id: (-scores[chunk_id], best_rank[chunk_id], chunk_id),
    )

    fused: list[RetrievalResult] = []
    for rank, chunk_id in enumerate(ranked_ids[:top_k], start=1):
        source_result = chunks[chunk_id]
        fused.append(
            RetrievalResult(
                chunk_id=chunk_id,
                score=scores[chunk_id],
                rank=rank,
                method="fusion",
                chunk=source_result.chunk,
            )
        )
    return fused
