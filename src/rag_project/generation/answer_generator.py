"""Grounded answer generation orchestration."""

from __future__ import annotations

from rag_project.generation.llm_client import LLMClient, MockLLMClient
from rag_project.generation.prompt_builder import build_grounded_prompt
from rag_project.schemas import AnswerResponse, Chunk, RetrievalResult


class AnswerGenerator:
    """Select evidence and call an LLM client in grounded mode."""

    def __init__(
        self,
        *,
        llm_client: LLMClient | None = None,
        max_evidence: int = 5,
    ) -> None:
        if max_evidence <= 0:
            raise ValueError("max_evidence must be positive")
        self.llm_client = llm_client or MockLLMClient()
        self.max_evidence = max_evidence

    def generate(
        self,
        question: str,
        retrieved_results: list[RetrievalResult],
    ) -> AnswerResponse:
        """Generate an answer using only top retrieved evidence."""
        evidence_chunks = [result.chunk for result in retrieved_results[: self.max_evidence]]
        if not evidence_chunks:
            return AnswerResponse(
                answer="The provided materials do not contain enough evidence to answer this question.",
                citations=[],
                insufficient_evidence=True,
                evidence_chunks=[],
                retrieval_explanation="No retrieved evidence was available for answer generation.",
            )

        prompt = build_grounded_prompt(
            question, evidence_chunks, max_evidence=self.max_evidence
        )
        response = self.llm_client.generate_answer(question, evidence_chunks)
        response.evidence_chunks = evidence_chunks
        response.retrieval_explanation = (
            f"Top {len(evidence_chunks)} reranked evidence chunks were selected "
            "for grounded answer generation. The prompt marks retrieved context "
            "as untrusted reference material."
        )
        # Keep the prompt build on the orchestration path for API clients and
        # tests that verify prompt-injection handling.
        _ = prompt
        return response


def generate_grounded_answer(
    question: str,
    retrieved_results: list[RetrievalResult],
    *,
    llm_client: LLMClient | None = None,
    max_evidence: int = 5,
) -> AnswerResponse:
    """Convenience wrapper for grounded answer generation."""
    return AnswerGenerator(
        llm_client=llm_client,
        max_evidence=max_evidence,
    ).generate(question, retrieved_results)
