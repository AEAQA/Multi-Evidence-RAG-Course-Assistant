"""BM25 lexical retrieval baseline."""

from __future__ import annotations

import math
from collections import Counter

from rag_project.retrieval.tokenization import tokenize
from rag_project.schemas import Chunk, RetrievalResult


class BM25Retriever:
    """CPU-friendly BM25 retriever over in-memory chunks."""

    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = list(chunks)
        self._tokenized_corpus = [tokenize(chunk.text) for chunk in self.chunks]
        self._term_counts = [Counter(tokens) for tokens in self._tokenized_corpus]
        self._doc_lengths = [len(tokens) for tokens in self._tokenized_corpus]
        self._avg_doc_length = (
            sum(self._doc_lengths) / len(self._doc_lengths)
            if self._doc_lengths
            else 0.0
        )
        self._doc_freqs = self._build_doc_freqs()

    def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        """Return top-k BM25 results with stable tie-breaking."""
        if top_k <= 0 or not self.chunks:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores = [self._score(query_tokens, index) for index in range(len(self.chunks))]
        ranked = sorted(
            enumerate(scores),
            key=lambda item: (-float(item[1]), item[0], self.chunks[item[0]].chunk_id),
        )

        results: list[RetrievalResult] = []
        for rank, (index, score) in enumerate(ranked[:top_k], start=1):
            chunk = self.chunks[index]
            results.append(
                RetrievalResult(
                    chunk_id=chunk.chunk_id,
                    score=float(score),
                    rank=rank,
                    method="bm25",
                    chunk=chunk,
                )
            )
        return results

    def _build_doc_freqs(self) -> dict[str, int]:
        doc_freqs: dict[str, int] = {}
        for tokens in self._tokenized_corpus:
            for token in set(tokens):
                doc_freqs[token] = doc_freqs.get(token, 0) + 1
        return doc_freqs

    def _score(self, query_tokens: list[str], doc_index: int) -> float:
        k1 = 1.5
        b = 0.75
        score = 0.0
        total_docs = len(self.chunks)
        doc_length = self._doc_lengths[doc_index]
        term_counts = self._term_counts[doc_index]

        for token in query_tokens:
            term_frequency = term_counts.get(token, 0)
            if term_frequency == 0:
                continue
            doc_frequency = self._doc_freqs.get(token, 0)
            idf = math.log(1.0 + (total_docs - doc_frequency + 0.5) / (doc_frequency + 0.5))
            denominator = term_frequency + k1 * (
                1.0 - b + b * doc_length / max(self._avg_doc_length, 1.0)
            )
            score += idf * (term_frequency * (k1 + 1.0)) / denominator

        return score
