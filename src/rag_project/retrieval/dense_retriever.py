"""Deterministic fake dense retrieval baseline."""

from __future__ import annotations

import hashlib
import math

from rag_project.retrieval.tokenization import tokenize
from rag_project.schemas import Chunk, RetrievalResult


class FakeDenseRetriever:
    """Offline dense-like retriever using stable hashing vectors."""

    def __init__(self, chunks: list[Chunk], dimensions: int = 128) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self.chunks = list(chunks)
        self.dimensions = dimensions
        self._vectors = [self._embed(chunk.text) for chunk in self.chunks]

    def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        """Return top-k fake dense results using cosine similarity."""
        if top_k <= 0 or not self.chunks:
            return []

        query_vector = self._embed(query)
        if not any(query_vector):
            return []

        scored = [
            (self._cosine(query_vector, vector), index)
            for index, vector in enumerate(self._vectors)
        ]
        scored.sort(key=lambda item: (-item[0], item[1], self.chunks[item[1]].chunk_id))

        results: list[RetrievalResult] = []
        for rank, (score, index) in enumerate(scored[:top_k], start=1):
            chunk = self.chunks[index]
            results.append(
                RetrievalResult(
                    chunk_id=chunk.chunk_id,
                    score=float(score),
                    rank=rank,
                    method="dense",
                    chunk=chunk,
                )
            )
        return results

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in tokenize(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        return vector

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        numerator = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))
        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0
        return numerator / (left_norm * right_norm)
