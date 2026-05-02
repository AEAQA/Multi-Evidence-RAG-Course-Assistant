"""Evaluation package."""

from rag_project.evaluation.metrics import (
    evaluate_retrieval_run,
    mean_metrics,
    mrr_at_k,
    ndcg_at_k,
    recall_at_k,
)
from rag_project.evaluation.loader import load_evaluation_queries
from rag_project.evaluation.runner import (
    EvaluationQuery,
    EvaluationResult,
    evaluate_retrieval_methods,
    write_evaluation_reports,
)

__all__ = [
    "EvaluationQuery",
    "EvaluationResult",
    "evaluate_retrieval_run",
    "evaluate_retrieval_methods",
    "load_evaluation_queries",
    "mean_metrics",
    "mrr_at_k",
    "ndcg_at_k",
    "recall_at_k",
    "write_evaluation_reports",
]
