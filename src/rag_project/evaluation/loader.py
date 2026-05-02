"""Evaluation dataset loading utilities."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from rag_project.evaluation.runner import EvaluationQuery


def load_evaluation_queries(path: str | Path) -> list[EvaluationQuery]:
    """Load JSONL evaluation queries from disk."""
    query_path = Path(path)
    if not query_path.exists():
        raise FileNotFoundError(f"Evaluation query file not found: {query_path}")

    queries: list[EvaluationQuery] = []
    for line_number, line in enumerate(
        query_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
            queries.append(EvaluationQuery(**payload))
        except (json.JSONDecodeError, ValidationError, TypeError) as exc:
            raise ValueError(
                f"Invalid evaluation query at {query_path}:{line_number}"
            ) from exc

    return queries
