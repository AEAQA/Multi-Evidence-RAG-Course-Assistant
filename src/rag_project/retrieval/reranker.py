"""Reranker interface and deterministic mock implementation."""

from __future__ import annotations

from typing import Protocol

from rag_project.schemas import Chunk, RerankResult


class RerankerClient(Protocol):
    """Interface for reranking retrieved candidates."""

    def rerank(self, query: str, candidates: list[Chunk]) -> list[RerankResult]:
        """Return reranked candidates."""


class MockRerankerClient:
    """Offline lexical-overlap reranker."""

    def rerank(self, query: str, candidates: list[Chunk]) -> list[RerankResult]:
        query_terms = set(query.lower().split())

        scored = []
        for index, chunk in enumerate(candidates):
            text_terms = chunk.text.lower().split()
            score = sum(1 for term in text_terms if term in query_terms)
            scored.append((float(score), index, chunk))

        scored.sort(key=lambda item: (-item[0], item[1], item[2].chunk_id))
        return [
            RerankResult(chunk_id=chunk.chunk_id, score=score, rank=rank)
            for rank, (score, _, chunk) in enumerate(scored, start=1)
        ]
