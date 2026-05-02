"""Corpus helpers for the Streamlit Evidence Workbench."""

from __future__ import annotations

from collections import Counter

from pydantic import BaseModel, Field

from rag_project.evaluation.sample_corpus import build_sample_evaluation_chunks
from rag_project.schemas import Chunk

SAMPLE_QUESTIONS: list[str] = [
    "What is overfitting and why does validation data matter?",
    "How does reranking improve retrieval quality?",
    "When should we prefer hybrid retrieval over BM25 alone?",
    "What does NDCG measure in retrieval evaluation?",
]


class CorpusSummary(BaseModel):
    """Lightweight corpus summary for the workbench sidebar."""

    corpus_name: str
    chunk_count: int
    type_counts: dict[str, int] = Field(default_factory=dict)
    source_files: list[str] = Field(default_factory=list)
    sample_questions: list[str] = Field(default_factory=list)


def load_sample_corpus() -> list[Chunk]:
    """Load the public synthetic sample corpus."""
    return build_sample_evaluation_chunks()


def build_sample_corpus_summary(chunks: list[Chunk] | None = None) -> CorpusSummary:
    """Summarize the sample corpus without requiring Pandas."""
    corpus_chunks = chunks if chunks is not None else load_sample_corpus()
    type_counts = Counter(chunk.type for chunk in corpus_chunks)
    source_files = sorted({chunk.source_file for chunk in corpus_chunks})
    return CorpusSummary(
        corpus_name="Synthetic course study corpus",
        chunk_count=len(corpus_chunks),
        type_counts=dict(sorted(type_counts.items())),
        source_files=source_files,
        sample_questions=SAMPLE_QUESTIONS,
    )
