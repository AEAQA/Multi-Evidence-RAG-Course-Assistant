"""Milestone 2 retrieval baseline pipeline."""

from __future__ import annotations

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
        candidate_k = max(top_k, top_k * 2)
        bm25_results = self.bm25.search(query, top_k=candidate_k)
        dense_results = self.dense.search(query, top_k=candidate_k)
        fusion_results = reciprocal_rank_fusion(
            [bm25_results, dense_results], top_k=candidate_k
        )

        reranked_results = self._rerank(query, fusion_results, top_k=top_k)

        return RetrievalPipelineOutput(
            bm25_results=bm25_results[:top_k],
            dense_results=dense_results[:top_k],
            fusion_results=fusion_results[:top_k],
            reranked_results=reranked_results,
        )

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
