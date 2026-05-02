"""Optional SiliconFlow reranker with mock fallback."""

from __future__ import annotations

from typing import Any, Callable

from rag_project.http_client import post_json as default_post_json
from rag_project.retrieval.reranker import MockRerankerClient, RerankerClient
from rag_project.schemas import Chunk, RerankResult

PostJson = Callable[..., dict[str, Any]]


class SiliconFlowRerankerClient:
    """SiliconFlow rerank API client."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = "https://api.siliconflow.cn/v1",
        timeout: float = 30.0,
        fallback_client: RerankerClient | None = None,
        post_json: PostJson = default_post_json,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.fallback_client = fallback_client or MockRerankerClient()
        self.post_json = post_json

    def rerank(self, query: str, candidates: list[Chunk]) -> list[RerankResult]:
        """Rerank candidates, falling back to the mock reranker on failure."""
        if not candidates:
            return []

        try:
            data = self.post_json(
                f"{self.base_url}/rerank",
                headers=self._headers(),
                json={
                    "model": self.model,
                    "query": query,
                    "documents": [candidate.text for candidate in candidates],
                },
                timeout=self.timeout,
            )
            results = self._parse_results(data, candidates)
            if not results:
                raise ValueError("SiliconFlow response did not include rerank results")
            return results
        except Exception:
            return self.fallback_client.rerank(query, candidates)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _parse_results(
        data: dict[str, Any], candidates: list[Chunk]
    ) -> list[RerankResult]:
        raw_results = data.get("results")
        if not isinstance(raw_results, list):
            return []

        output: list[tuple[float, int, str]] = []
        for item in raw_results:
            if not isinstance(item, dict):
                continue
            index = item.get("index")
            if not isinstance(index, int) or index < 0 or index >= len(candidates):
                continue
            score = item.get("relevance_score", item.get("score", 0.0))
            try:
                output.append((float(score), index, candidates[index].chunk_id))
            except (TypeError, ValueError):
                continue

        output.sort(key=lambda row: (-row[0], row[1], row[2]))
        return [
            RerankResult(chunk_id=chunk_id, score=score, rank=rank)
            for rank, (score, _, chunk_id) in enumerate(output, start=1)
        ]
