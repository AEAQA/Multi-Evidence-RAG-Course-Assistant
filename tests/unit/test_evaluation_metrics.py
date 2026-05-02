from rag_project.evaluation.metrics import (
    evaluate_retrieval_run,
    mean_metrics,
    mrr_at_k,
    ndcg_at_k,
    recall_at_k,
)


def test_recall_at_k_detects_any_relevant_hit() -> None:
    retrieved = ["c1", "c2", "c3"]
    relevant = ["c3", "c9"]

    assert recall_at_k(retrieved, relevant, k=2) == 0.0
    assert recall_at_k(retrieved, relevant, k=3) == 1.0


def test_mrr_at_k_returns_reciprocal_first_relevant_rank() -> None:
    retrieved = ["c1", "c2", "c3"]
    relevant = ["c2", "c3"]

    assert mrr_at_k(retrieved, relevant, k=3) == 0.5
    assert mrr_at_k(retrieved, relevant, k=1) == 0.0


def test_ndcg_at_k_handles_multiple_relevant_items() -> None:
    retrieved = ["c1", "c2", "c3"]
    relevant = ["c2", "c3"]

    score = ndcg_at_k(retrieved, relevant, k=3)

    assert round(score, 4) == 0.6934


def test_metrics_return_zero_for_empty_relevant_set() -> None:
    retrieved = ["c1", "c2"]

    assert recall_at_k(retrieved, [], k=5) == 0.0
    assert mrr_at_k(retrieved, [], k=5) == 0.0
    assert ndcg_at_k(retrieved, [], k=5) == 0.0


def test_evaluate_retrieval_run_returns_required_m4_metrics() -> None:
    metrics = evaluate_retrieval_run(
        retrieved_chunk_ids=["c1", "c2", "c3"],
        relevant_chunk_ids=["c3"],
    )

    assert metrics == {
        "recall@1": 0.0,
        "recall@3": 1.0,
        "recall@5": 1.0,
        "mrr@5": 1 / 3,
        "ndcg@5": 0.5,
    }


def test_mean_metrics_averages_multiple_runs() -> None:
    averaged = mean_metrics(
        [
            {"recall@1": 1.0, "mrr@5": 0.5},
            {"recall@1": 0.0, "mrr@5": 1.0},
        ]
    )

    assert averaged == {"recall@1": 0.5, "mrr@5": 0.75}
