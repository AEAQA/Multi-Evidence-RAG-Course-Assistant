"""Milestone 2 retrieval baseline pipeline."""

from __future__ import annotations

from time import perf_counter

from rag_project.retrieval.bm25_retriever import BM25Retriever
from rag_project.retrieval.dense_retriever import FakeDenseRetriever
from rag_project.retrieval.fusion import reciprocal_rank_fusion
from rag_project.retrieval.reranker import RerankerClient, MockRerankerClient
from rag_project.schemas import Chunk, RetrievalPipelineOutput, RetrievalResult


class RetrievalPipeline:
    """Compare BM25, fake dense, fusion, and reranked retrieval."""

    def __init__(
        self,
        chunks: list[Chunk],
        *,
        reranker: RerankerClient | None = None,
        dense_dimensions: int = 128,
    ) -> None:
        self.chunks = list(chunks)
        self.bm25 = BM25Retriever(self.chunks)
        self.dense = FakeDenseRetriever(self.chunks, dimensions=dense_dimensions)
        self.reranker = reranker or MockRerankerClient()

    def search(self, query: str, top_k: int = 5) -> RetrievalPipelineOutput:
        """Run all M2 retrieval baselines for one query."""
        output, _ = self.search_with_timing(query, top_k=top_k)
        return output

    def search_with_timing(
        self, query: str, top_k: int = 5
    ) -> tuple[RetrievalPipelineOutput, dict[str, float]]:
        """Run all retrieval baselines and return phase timings."""
        candidate_k = max(top_k, top_k * 2)
        started = perf_counter()

        bm25_started = perf_counter()
        bm25_results = self.bm25.search(query, top_k=candidate_k)
        bm25_finished = perf_counter()

        dense_started = perf_counter()
        dense_results = self.dense.search(query, top_k=candidate_k)
        dense_finished = perf_counter()

        fusion_started = perf_counter()
        fusion_results = reciprocal_rank_fusion(
            [bm25_results, dense_results], top_k=candidate_k
        )
        fusion_finished = perf_counter()

        reranker_started = perf_counter()
        reranked_results = self._rerank(query, fusion_results, top_k=top_k)
        reranker_finished = perf_counter()

        output = RetrievalPipelineOutput(
            bm25_results=bm25_results[:top_k],
            dense_results=dense_results[:top_k],
            fusion_results=fusion_results[:top_k],
            reranked_results=reranked_results,
        )
        return output, {
            "bm25": _elapsed_ms(bm25_started, bm25_finished),
            "dense": _elapsed_ms(dense_started, dense_finished),
            "fusion": _elapsed_ms(fusion_started, fusion_finished),
            "reranker": _elapsed_ms(reranker_started, reranker_finished),
            "retrieval": _elapsed_ms(started, reranker_finished),
        }

    def _rerank(
        self, query: str, candidates: list[RetrievalResult], *, top_k: int
    ) -> list[RetrievalResult]:
        if top_k <= 0 or not candidates:
            return []

        chunks_by_id = {result.chunk_id: result.chunk for result in candidates}
        reranked = self.reranker.rerank(
            query, [result.chunk for result in candidates]
        )

        results: list[RetrievalResult] = []
        for rank, result in enumerate(reranked[:top_k], start=1):
            chunk = chunks_by_id[result.chunk_id]
            results.append(
                RetrievalResult(
                    chunk_id=result.chunk_id,
                    score=result.score,
                    rank=rank,
                    method="reranked",
                    chunk=chunk,
                )
            )
        return results


def _elapsed_ms(start: float, end: float) -> float:
    return round((end - start) * 1000, 3)
