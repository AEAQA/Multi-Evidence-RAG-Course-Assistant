"""Retrieval evaluation metrics for Milestone 4."""

from __future__ import annotations

import math
from collections.abc import Iterable


def recall_at_k(
    retrieved_chunk_ids: list[str],
    relevant_chunk_ids: Iterable[str],
    *,
    k: int,
) -> float:
    """Return 1.0 when any relevant chunk appears in top-k, else 0.0."""
    if k <= 0:
        return 0.0
    relevant = set(relevant_chunk_ids)
    if not relevant:
        return 0.0
    return 1.0 if relevant.intersection(retrieved_chunk_ids[:k]) else 0.0


def mrr_at_k(
    retrieved_chunk_ids: list[str],
    relevant_chunk_ids: Iterable[str],
    *,
    k: int,
) -> float:
    """Return reciprocal rank of the first relevant hit in top-k."""
    if k <= 0:
        return 0.0
    relevant = set(relevant_chunk_ids)
    if not relevant:
        return 0.0

    for index, chunk_id in enumerate(retrieved_chunk_ids[:k], start=1):
        if chunk_id in relevant:
            return 1.0 / index
    return 0.0


def ndcg_at_k(
    retrieved_chunk_ids: list[str],
    relevant_chunk_ids: Iterable[str],
    *,
    k: int,
) -> float:
    """Return binary-relevance NDCG@k."""
    if k <= 0:
        return 0.0
    relevant = set(relevant_chunk_ids)
    if not relevant:
        return 0.0

    dcg = 0.0
    for index, chunk_id in enumerate(retrieved_chunk_ids[:k], start=1):
        if chunk_id in relevant:
            dcg += 1.0 / math.log2(index + 1)

    ideal_hits = min(len(relevant), k)
    ideal_dcg = sum(1.0 / math.log2(index + 1) for index in range(1, ideal_hits + 1))
    if ideal_dcg == 0.0:
        return 0.0
    return dcg / ideal_dcg


def evaluate_retrieval_run(
    *,
    retrieved_chunk_ids: list[str],
    relevant_chunk_ids: list[str],
) -> dict[str, float]:
    """Calculate the required M4 retrieval metrics for one query."""
    return {
        "recall@1": recall_at_k(retrieved_chunk_ids, relevant_chunk_ids, k=1),
        "recall@3": recall_at_k(retrieved_chunk_ids, relevant_chunk_ids, k=3),
        "recall@5": recall_at_k(retrieved_chunk_ids, relevant_chunk_ids, k=5),
        "mrr@5": mrr_at_k(retrieved_chunk_ids, relevant_chunk_ids, k=5),
        "ndcg@5": ndcg_at_k(retrieved_chunk_ids, relevant_chunk_ids, k=5),
    }


def mean_metrics(metric_rows: list[dict[str, float]]) -> dict[str, float]:
    """Average metric dictionaries by key."""
    if not metric_rows:
        return {}

    keys = sorted({key for row in metric_rows for key in row})
    return {
        key: sum(row.get(key, 0.0) for row in metric_rows) / len(metric_rows)
        for key in keys
    }
