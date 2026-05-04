"""Optional SiliconFlow LLM client with mock fallback."""

from __future__ import annotations

from typing import Any, Callable

from rag_project.generation.llm_client import LLMClient, MockLLMClient
from rag_project.generation.prompt_builder import build_grounded_prompt
from rag_project.http_client import post_json as default_post_json
from rag_project.schemas import AnswerResponse, Chunk, Citation

PostJson = Callable[..., dict[str, Any]]


class SiliconFlowLLMClient:
    """SiliconFlow chat-completions client for grounded answer generation."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = "https://api.siliconflow.cn/v1",
        timeout: float = 30.0,
        fallback_client: LLMClient | None = None,
        post_json: PostJson = default_post_json,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.fallback_client = fallback_client or MockLLMClient()
        self.post_json = post_json

    def generate_answer(
        self, question: str, evidence_chunks: list[Chunk]
    ) -> AnswerResponse:
        """Generate a grounded answer, falling back to mock on API failure."""
        if not evidence_chunks:
            return self.fallback_client.generate_answer(question, evidence_chunks)

        try:
            prompt = build_grounded_prompt(question, evidence_chunks, max_evidence=5)
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a precise academic assistant that ONLY uses provided "
                            "evidence to answer questions. You MUST:\n"
                            "1. Read and understand the provided evidence chunks.\n"
                            "2. Synthesize a natural-language answer in 2-4 paragraphs.\n"
                            "3. Never copy-paste or concatenate evidence text verbatim.\n"
                            "4. Paraphrase, summarize, and relate concepts across chunks.\n"
                            "5. Place citation markers [E1] [E2] [E3] inline after each supported claim.\n"
                            "6. Do not use a separate References section at the end.\n"
                            "7. If the evidence does not support the question, state so clearly.\n"
                            "8. Never repeat chunk IDs, source file paths, hashes, internal "
                            "identifiers, table delimiters, box-drawing characters, or OCR noise.\n"
                            "9. Write as if explaining to a student: be clear, educational, "
                            "and grounded in the retrieved material."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0,
            }
            data = self.post_json(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
                timeout=self.timeout,
            )
            answer = self._extract_answer(data)
            if not answer:
                raise ValueError("SiliconFlow response did not include answer text")
            top_chunks = evidence_chunks[:5]
            return AnswerResponse(
                answer=answer,
                citations=[
                    Citation(
                        chunk_id=chunk.chunk_id,
                        source_file=chunk.source_file,
                        page=chunk.page,
                    )
                    for chunk in top_chunks
                ],
                insufficient_evidence=False,
                evidence_chunks=top_chunks,
                retrieval_explanation=(
                    f"SiliconFlow LLM model {self.model} generated an answer "
                    "from selected evidence chunks."
                ),
            )
        except Exception:
            response = self.fallback_client.generate_answer(question, evidence_chunks)
            response.retrieval_explanation = (
                response.retrieval_explanation
                + " SiliconFlow LLM fallback was used after API failure."
            ).strip()
            return response

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _extract_answer(data: dict[str, Any]) -> str:
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            return ""
        first = choices[0]
        if not isinstance(first, dict):
            return ""
        message = first.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
                return content.strip()
        text = first.get("text")
        return text.strip() if isinstance(text, str) else ""
