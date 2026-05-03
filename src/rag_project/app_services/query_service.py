"""Query orchestration service for the Streamlit Evidence Workbench."""

from __future__ import annotations

import hashlib
import json
import re
from time import perf_counter

from pydantic import BaseModel, Field

from rag_project.app_services.corpus_service import (
    CorpusBundle,
    CorpusSummary,
    load_sample_corpus,
)
from rag_project.app_services.provider_status import ProviderStatus, build_provider_status
from rag_project.config import AppConfig, load_config
from rag_project.generation.answer_generator import AnswerGenerator
from rag_project.providers import create_llm_client, create_reranker_client
from rag_project.retrieval.reranker import RerankerClient
from rag_project.retrieval.pipeline import RetrievalPipeline
from rag_project.schemas import (
    AnswerResponse,
    Chunk,
    Citation,
    EvidenceReference,
    RetrievalPipelineOutput,
    RetrievalResult,
    RetrievalTraceStage,
)


class MethodDiagnostic(BaseModel):
    """Human-facing diagnostic for one retrieval method."""

    method: str
    result_count: int
    top_score: float
    confidence: float
    confidence_label: str
    recommendation: str


class WorkbenchState(BaseModel):
    """Complete UI state for one workbench query."""

    query: str
    retrieval: RetrievalPipelineOutput
    answer: AnswerResponse
    provider_status: ProviderStatus
    timing_ms: dict[str, float] = Field(default_factory=dict)
    diagnostics: list[MethodDiagnostic] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    corpus_summary: CorpusSummary | None = None
    corpus_warnings: list[str] = Field(default_factory=list)
    final_evidence_results: list[RetrievalResult] = Field(default_factory=list)
    final_evidence: list[EvidenceReference] = Field(default_factory=list)
    retrieval_trace: list[RetrievalTraceStage] = Field(default_factory=list)
    scope: dict[str, object] = Field(default_factory=dict)


class QueryService:
    """Run retrieval, answer generation, diagnostics, and timing."""

    def __init__(
        self,
        *,
        config: AppConfig | None = None,
        chunks: list[Chunk] | None = None,
        retrieval_pipeline: RetrievalPipeline | None = None,
    ) -> None:
        self.config = config or load_config()
        self.chunks = load_sample_corpus() if chunks is None else list(chunks)
        self.retrieval_pipeline = retrieval_pipeline

    def run(self, query: str, *, top_k: int = 5) -> WorkbenchState:
        """Run the full workbench query path with provider fallback clients."""
        return _run_query(
            query=query,
            chunks=self.chunks,
            config=self.config,
            top_k=top_k,
            retrieval_pipeline=self.retrieval_pipeline,
        )


def run_query(
    query: str,
    corpus_bundle: CorpusBundle,
    *,
    config: AppConfig | None = None,
    top_k: int = 5,
    retrieval_pipeline: RetrievalPipeline | None = None,
) -> WorkbenchState:
    """Run a query against an explicit corpus bundle."""
    runtime_config = config or load_config()
    return _run_query(
        query=query,
        chunks=corpus_bundle.chunks,
        config=runtime_config,
        top_k=top_k,
        corpus_summary=corpus_bundle.summary,
        corpus_warnings=corpus_bundle.warnings,
        retrieval_pipeline=retrieval_pipeline,
    )


def _run_query(
    *,
    query: str,
    chunks: list[Chunk],
    config: AppConfig,
    top_k: int,
    corpus_summary: CorpusSummary | None = None,
    corpus_warnings: list[str] | None = None,
    retrieval_pipeline: RetrievalPipeline | None = None,
) -> WorkbenchState:
    normalized_query = query.strip()
    bounded_top_k = max(1, min(top_k, 10))
    provider_status = build_provider_status(config)

    started = perf_counter()
    pipeline_started = perf_counter()
    pipeline = retrieval_pipeline or build_retrieval_pipeline(
        chunks,
        reranker=create_reranker_client(config),
    )
    pipeline_finished = perf_counter()

    retrieval, retrieval_timings = pipeline.search_with_timing(
        normalized_query, top_k=bounded_top_k
    )
    retrieval_finished = perf_counter()

    generation_started = perf_counter()
    answer = AnswerGenerator(
        llm_client=create_llm_client(config),
        max_evidence=bounded_top_k,
    ).generate(normalized_query, retrieval.reranked_results)
    finished = perf_counter()

    timing_ms = {
        **retrieval_timings,
        "pipeline_build": _elapsed_ms(pipeline_started, pipeline_finished),
        "retrieval_total": _elapsed_ms(pipeline_finished, retrieval_finished),
        "generation": _elapsed_ms(generation_started, finished),
        "total": _elapsed_ms(started, finished),
    }
    final_evidence_results = _final_evidence_results(
        retrieval.reranked_results,
        answer.evidence_chunks,
    )
    final_evidence = _build_final_evidence(final_evidence_results)
    answer = _attach_evidence_ids(answer, final_evidence)
    retrieval_trace = _build_retrieval_trace(retrieval, timing_ms, final_evidence)
    diagnostics = build_method_diagnostics(retrieval)
    return WorkbenchState(
        query=normalized_query,
        retrieval=retrieval,
        answer=answer,
        provider_status=provider_status,
        timing_ms=timing_ms,
        diagnostics=diagnostics,
        suggestions=_build_suggestions(answer, diagnostics),
        corpus_summary=corpus_summary,
        corpus_warnings=list(corpus_warnings or []),
        final_evidence_results=final_evidence_results,
        final_evidence=final_evidence,
        retrieval_trace=retrieval_trace,
        scope=_build_scope(corpus_summary, chunks),
    )


def build_retrieval_pipeline(
    chunks: list[Chunk], *, reranker: RerankerClient | None = None
) -> RetrievalPipeline:
    """Build retrieval indexes for a stable chunk list."""
    return RetrievalPipeline(chunks, reranker=reranker)


def build_corpus_signature(chunks: list[Chunk]) -> str:
    """Return a stable signature for Streamlit retrieval-resource caching."""
    payload = [
        {
            "chunk_id": chunk.chunk_id,
            "doc_id": chunk.doc_id,
            "source_file": chunk.source_file,
            "page": chunk.page,
            "type": chunk.type,
            "text_len": len(chunk.text),
        }
        for chunk in chunks
    ]
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _build_final_evidence(results: list[RetrievalResult]) -> list[EvidenceReference]:
    evidence: list[EvidenceReference] = []
    for index, result in enumerate(results, start=1):
        chunk = result.chunk
        evidence.append(
            EvidenceReference(
                evidence_id=f"E{index}",
                chunk_id=chunk.chunk_id,
                doc_id=chunk.doc_id,
                source_file=chunk.source_file,
                page=chunk.page,
                type=chunk.type,
                method=result.method,
                score=round(float(result.score), 4),
                confidence=_confidence_from_score(float(result.score)),
                preview=_chunk_preview(chunk),
                chunk=chunk,
            )
        )
    return evidence


def _attach_evidence_ids(
    answer: AnswerResponse, evidence: list[EvidenceReference]
) -> AnswerResponse:
    if not evidence:
        return answer
    evidence_by_chunk = {item.chunk_id: item.evidence_id for item in evidence}
    citations = [
        Citation(
            chunk_id=citation.chunk_id,
            source_file=citation.source_file,
            page=citation.page,
            evidence_id=evidence_by_chunk.get(citation.chunk_id),
        )
        for citation in answer.citations
    ]
    markers = [f"[{item.evidence_id}]" for item in evidence]
    answer_text = answer.answer
    if not answer.insufficient_evidence and not any(marker in answer_text for marker in markers):
        answer_text = _add_inline_markers(answer_text, markers)
    return answer.model_copy(update={"answer": answer_text, "citations": citations})


def _add_inline_markers(answer_text: str, markers: list[str]) -> str:
    text = _strip_references_block(answer_text).strip()
    if not text or not markers:
        return text
    sentences = _split_sentences(text)
    if not sentences:
        return f"{text.rstrip('.!?')} {markers[0]}."
    patched: list[str] = []
    for index, sentence in enumerate(sentences):
        marker = markers[min(index, len(markers) - 1)]
        patched.append(_sentence_with_marker(sentence, marker))
        if index + 1 >= len(markers):
            patched.extend(sentences[index + 1 :])
            break
    return " ".join(patched)


def _strip_references_block(answer_text: str) -> str:
    return re.sub(
        r"\n+\s*References:\s*(?:\[E\d+\]\s*)+$",
        "",
        str(answer_text or "").strip(),
        flags=re.IGNORECASE,
    )


def _split_sentences(text: str) -> list[str]:
    parts = re.findall(r"[^.!?]+[.!?]?", text)
    return [part.strip() for part in parts if part.strip()]


def _sentence_with_marker(sentence: str, marker: str) -> str:
    if marker in sentence:
        return sentence
    stripped = sentence.strip()
    punctuation = "." if not stripped[-1:] or stripped[-1] not in ".!?" else stripped[-1]
    body = stripped.rstrip(".!?").strip()
    return f"{body} {marker}{punctuation}"


def _build_retrieval_trace(
    retrieval: RetrievalPipelineOutput,
    timing_ms: dict[str, float],
    final_evidence: list[EvidenceReference],
) -> list[RetrievalTraceStage]:
    stages = [
        ("BM25", retrieval.bm25_results, "bm25"),
        ("Dense", retrieval.dense_results, "dense"),
        ("Fusion", retrieval.fusion_results, "fusion"),
        ("Reranker", retrieval.reranked_results, "reranker"),
    ]
    trace = [
        RetrievalTraceStage(
            stage=stage,
            result_count=len(results),
            top_score=round(float(results[0].score), 4) if results else 0.0,
            latency_ms=float(timing_ms.get(timing_key, 0.0)),
            confidence=_confidence_from_score(float(results[0].score)) if results else 0.0,
        )
        for stage, results, timing_key in stages
    ]
    trace.append(
        RetrievalTraceStage(
            stage="Final Evidence",
            result_count=len(final_evidence),
            top_score=final_evidence[0].score if final_evidence else 0.0,
            latency_ms=float(timing_ms.get("generation", 0.0)),
            confidence=final_evidence[0].confidence if final_evidence else 0.0,
        )
    )
    return trace


def _build_scope(
    corpus_summary: CorpusSummary | None, chunks: list[Chunk]
) -> dict[str, object]:
    return {
        "corpus_name": corpus_summary.corpus_name if corpus_summary else "Current corpus",
        "chunk_count": len(chunks),
        "source_count": len({chunk.source_file for chunk in chunks}),
        "doc_count": len({chunk.doc_id for chunk in chunks}),
    }


def _chunk_preview(chunk: Chunk, *, max_chars: int = 220) -> str:
    if chunk.metadata.caption:
        text = chunk.metadata.caption
    elif chunk.metadata.table_html:
        text = chunk.text or chunk.metadata.table_html
    else:
        text = chunk.text
    return text[:max_chars]


def build_method_diagnostics(
    retrieval: RetrievalPipelineOutput,
) -> list[MethodDiagnostic]:
    """Return stable method diagnostics for UI cards and tests."""
    method_groups = [
        ("bm25", retrieval.bm25_results),
        ("dense", retrieval.dense_results),
        ("fusion", retrieval.fusion_results),
        ("reranked", retrieval.reranked_results),
    ]
    return [
        _diagnostic_for_results(method, results)
        for method, results in method_groups
    ]


def _diagnostic_for_results(
    method: str,
    results: list[RetrievalResult],
) -> MethodDiagnostic:
    if not results:
        return MethodDiagnostic(
            method=method,
            result_count=0,
            top_score=0.0,
            confidence=0.0,
            confidence_label="none",
            recommendation="No candidates were returned; add documents or broaden the query.",
        )

    top_score = max(0.0, float(results[0].score))
    confidence = _confidence_from_score(top_score)
    label = _confidence_label(confidence)
    return MethodDiagnostic(
        method=method,
        result_count=len(results),
        top_score=round(top_score, 4),
        confidence=confidence,
        confidence_label=label,
        recommendation=_recommendation(method, label, len(results)),
    )


def _confidence_from_score(score: float) -> float:
    if score <= 0:
        return 0.0
    return round(min(1.0, score / (score + 1.0)), 3)


def _confidence_label(confidence: float) -> str:
    if confidence <= 0:
        return "none"
    if confidence >= 0.67:
        return "high"
    if confidence >= 0.34:
        return "medium"
    return "low"


def _recommendation(method: str, label: str, result_count: int) -> str:
    if label == "none":
        return "No usable evidence was found for this method."
    if method == "bm25":
        return "Use BM25 when exact course terms or acronyms appear in the question."
    if method == "dense":
        return "Dense retrieval helps when the question paraphrases the study material."
    if method == "fusion":
        return "Fusion is a balanced default because it combines lexical and semantic rankings."
    if method == "reranked":
        if label == "high":
            return "Reranked evidence is strong enough for the grounded answer path."
        return "Review the top evidence before trusting the answer; reranker confidence is limited."
    return f"{result_count} candidates are available for review."


def _build_suggestions(
    answer: AnswerResponse,
    diagnostics: list[MethodDiagnostic],
) -> list[str]:
    if answer.insufficient_evidence:
        return [
            "Add more course material or ask a narrower question.",
            "Check whether the selected corpus contains the topic.",
        ]

    reranked = next(
        (item for item in diagnostics if item.method == "reranked"),
        None,
    )
    suggestions = [
        "Open the evidence cards before using the final answer in a report.",
        "Compare BM25 and Dense tabs to see whether exact terms or paraphrases drove retrieval.",
    ]
    if reranked and reranked.confidence_label in {"low", "none"}:
        suggestions.append("Try a more specific query because reranked confidence is weak.")
    return suggestions


def _final_evidence_results(
    reranked_results: list[RetrievalResult],
    evidence_chunks: list[Chunk],
) -> list[RetrievalResult]:
    if not evidence_chunks:
        return []
    evidence_ids = {chunk.chunk_id for chunk in evidence_chunks}
    return [
        result
        for result in reranked_results
        if result.chunk_id in evidence_ids
    ]


def _elapsed_ms(start: float, end: float) -> float:
    return round((end - start) * 1000, 3)
