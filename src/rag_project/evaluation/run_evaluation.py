"""Run local/offline retrieval evaluation."""

from __future__ import annotations

from pathlib import Path

from rag_project.evaluation.loader import load_evaluation_queries
from rag_project.evaluation.runner import (
    evaluate_retrieval_methods,
    write_evaluation_reports,
)
from rag_project.evaluation.sample_corpus import build_sample_evaluation_chunks

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_QUERY_PATH = ROOT / "data" / "eval" / "queries.jsonl"
DEFAULT_REPORT_DIR = ROOT / "reports" / "evaluation"


def main() -> int:
    queries = load_evaluation_queries(DEFAULT_QUERY_PATH)
    chunks = build_sample_evaluation_chunks()
    result = evaluate_retrieval_methods(chunks, queries, top_k=5)
    written_paths = write_evaluation_reports(result, DEFAULT_REPORT_DIR)

    print("Evaluation completed.")
    for method, metrics in sorted(result.summary_by_method.items()):
        metrics_text = ", ".join(
            f"{metric}={value:.3f}" for metric, value in sorted(metrics.items())
        )
        print(f"{method}: {metrics_text}")

    print("Wrote reports:")
    for path in written_paths:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
