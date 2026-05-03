"""LLM client interface and deterministic mock implementation."""

from __future__ import annotations

import re
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
                evidence_chunks=[],
                retrieval_explanation="No evidence chunks were provided to the mock LLM.",
            )

        top_chunks = evidence_chunks[:5]
        answer = _build_mock_grounded_answer(top_chunks)
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
            evidence_chunks=top_chunks,
            retrieval_explanation=(
                f"Mock LLM used {len(top_chunks)} evidence chunks and ignored any "
                "instructions embedded inside retrieved context."
            ),
        )


def _build_mock_grounded_answer(chunks: list[Chunk]) -> str:
    claims: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        claim = _first_sentence(chunk.text)
        marker = f"[E{index}]"
        if index == 1:
            claims.append(f"The materials indicate that {claim} {marker}.")
        else:
            claims.append(f"They also state that {claim} {marker}.")
    return " ".join(claims)


def _first_sentence(text: str, *, max_chars: int = 180) -> str:
    normalized = " ".join(str(text or "").split())
    if not normalized:
        return "the selected evidence is relevant"
    match = re.search(r"(.+?[.!?])(?:\s|$)", normalized)
    sentence = match.group(1) if match else normalized
    sentence = sentence.strip().rstrip(".!?;:")
    if len(sentence) > max_chars:
        sentence = sentence[: max_chars - 1].rstrip() + "..."
    return sentence
