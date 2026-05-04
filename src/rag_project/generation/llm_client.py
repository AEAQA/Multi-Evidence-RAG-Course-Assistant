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
                generation_mode="mock",
            )

        top_chunks = evidence_chunks[:5]
        if question.startswith("Answer the original multi-intent question by sub-question."):
            answer = _build_mock_multi_intent_answer(question, top_chunks)
        else:
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
            generation_mode="mock",
        )


def _build_mock_grounded_answer(chunks: list[Chunk]) -> str:
    readable = [c for c in chunks if _first_sentence(c.text) != "the selected evidence is relevant"]
    if not readable:
        return "The provided materials do not contain enough evidence to answer this question."

    if len(readable) == 1:
        topic = _extract_topic(readable[0].text)
        return (
            f"Based on the retrieved material, {_first_sentence(readable[0].text)} [E1]. "
            f"According to this evidence from {readable[0].source_file} (page {readable[0].page}), "
            f"the topic of {topic} is addressed directly in the course content."
        )

    topic0 = _extract_topic(readable[0].text)
    topic1 = _extract_topic(readable[1].text)
    return (
        f"Based on the retrieved course materials, here is a summary of what the evidence shows. "
        f"One source explains that {_first_sentence(readable[0].text)} [E1]. "
        f"Another piece of evidence adds that {_first_sentence(readable[1].text)} [E2]. "
        f"Together, these materials suggest that both {topic0} and {topic1} "
        f"are relevant to understanding the concepts covered in the course content."
    )


def _build_mock_multi_intent_answer(question: str, chunks: list[Chunk]) -> str:
    sections: list[str] = []
    chunk_by_marker = {
        f"E{index}": chunk for index, chunk in enumerate(chunks, start=1)
    }
    for line in question.splitlines():
        match = re.match(
            r"^(Q\d+)\.\s+(.+?)\s+\|\s+support=([^|]+)\|\s+evidence=(.+)$",
            line.strip(),
        )
        if not match:
            continue
        qid, sub_question, support_label, evidence_text = match.groups()
        marker_match = re.search(r"\bE\d+\b", evidence_text)
        if "insufficient" in support_label.lower() or not marker_match:
            sections.append(
                f"{qid}. {sub_question}\n"
                "The retrieved materials do not contain enough evidence for this part."
            )
            continue
        marker = marker_match.group(0)
        chunk = chunk_by_marker.get(marker)
        if chunk is None:
            sections.append(
                f"{qid}. {sub_question}\n"
                "The retrieved materials do not contain enough evidence for this part."
            )
            continue
        sections.append(
            f"{qid}. {sub_question}\n"
            f"The evidence indicates that {_first_sentence(chunk.text)} [{marker}]."
        )
    if sections:
        return "\n\n".join(sections)
    return _build_mock_grounded_answer(chunks)


def _extract_topic(text: str) -> str:
    cleaned = re.sub(r"\|{2,}", " ", str(text or ""))
    cleaned = re.sub(r"[│┃┆┇]{2,}", " ", cleaned)
    cleaned = " ".join(cleaned.split())
    words = cleaned.split()
    if not words:
        return "the course concept"
    key = [w for w in words[:8] if len(w) > 2 and w.lower() not in {"the", "and", "for", "that", "this", "with", "from"}]
    if not key:
        key = words[:4]
    topic = " ".join(key[:4])
    return topic if len(topic) < 60 else topic[:57] + "..."


def _first_sentence(text: str, *, max_chars: int = 180) -> str:
    normalized = " ".join(str(text or "").split())
    cleaned = _clean_for_sentence(normalized)
    if not cleaned:
        return "the selected evidence is relevant"
    match = re.search(r"(.+?[.!?])(?:\s|$)", cleaned)
    sentence = match.group(1) if match else cleaned
    sentence = sentence.strip().rstrip(".!?;:")
    if len(sentence) > max_chars:
        sentence = sentence[: max_chars - 1].rstrip() + "..."
    return sentence


def _clean_for_sentence(text: str) -> str:
    text = re.sub(r"\|{2,}", " ", text)
    text = re.sub(r"[│┃┆┇┊┋╎╏╌╍]{2,}", " ", text)
    text = re.sub(r"([a-f0-9]{32,})", "", text)
    text = re.sub(r"\bpage_\d+_(text|image|table)_\d+\b", "", text)
    text = " ".join(text.split())
    return text.strip()
