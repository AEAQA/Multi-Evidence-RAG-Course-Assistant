"""LLM client interface and deterministic mock implementation."""

from __future__ import annotations

from typing import Protocol

from rag_project.schemas import AnswerResponse, Chunk, Citation


class LLMClient(Protocol):
    """Interface for grounded answer generation."""

    def generate_answer(
        self, question: str, evidence_chunks: list[Chunk]
    ) -> AnswerResponse:
        """Generate an answer using only provided evidence."""


class MockLLMClient:
    """Offline mock LLM for tests and local mode."""

    def generate_answer(
        self, question: str, evidence_chunks: list[Chunk]
    ) -> AnswerResponse:
        if not evidence_chunks:
            return AnswerResponse(
                answer="The provided materials do not contain enough evidence to answer this question.",
                citations=[],
                insufficient_evidence=True,
            )

        top_chunks = evidence_chunks[:5]
        evidence_text = " ".join(chunk.text for chunk in top_chunks)
        answer = (
            f"Based on the retrieved evidence, {evidence_text[:240].strip()}"
        )
        citations = [
            Citation(
                chunk_id=chunk.chunk_id,
                source_file=chunk.source_file,
                page=chunk.page,
            )
            for chunk in top_chunks
        ]
        return AnswerResponse(
            answer=answer,
            citations=citations,
            insufficient_evidence=False,
        )
