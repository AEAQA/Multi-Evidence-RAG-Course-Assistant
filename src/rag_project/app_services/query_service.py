"""Query orchestration service for the Streamlit Evidence Workbench."""

from __future__ import annotations

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
from rag_project.retrieval.pipeline import RetrievalPipeline
from rag_project.schemas import AnswerResponse, Chunk, RetrievalPipelineOutput, RetrievalResult


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


class QueryService:
    """Run retrieval, answer generation, diagnostics, and timing."""

    def __init__(
        self,
        *,
        config: AppConfig | None = None,
        chunks: list[Chunk] | None = None,
    ) -> None:
        self.config = config or load_config()
        self.chunks = load_sample_corpus() if chunks is None else list(chunks)

    def run(self, query: str, *, top_k: int = 5) -> WorkbenchState:
        """Run the full workbench query path with provider fallback clients."""
        return _run_query(
            query=query,
            chunks=self.chunks,
            config=self.config,
            top_k=top_k,
        )


def run_query(
    query: str,
    corpus_bundle: CorpusBundle,
    *,
    config: AppConfig | None = None,
    top_k: int = 5,
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
    )


def _run_query(
    *,
    query: str,
    chunks: list[Chunk],
    config: AppConfig,
    top_k: int,
    corpus_summary: CorpusSummary | None = None,
    corpus_warnings: list[str] | None = None,
) -> WorkbenchState:
    normalized_query = query.strip()
    bounded_top_k = max(1, min(top_k, 10))
    provider_status = build_provider_status(config)

    started = perf_counter()
    retrieval = RetrievalPipeline(
        chunks,
        reranker=create_reranker_client(config),
    ).search(normalized_query, top_k=bounded_top_k)
    retrieval_finished = perf_counter()

    answer = AnswerGenerator(
        llm_client=create_llm_client(config),
        max_evidence=bounded_top_k,
    ).generate(normalized_query, retrieval.reranked_results)
    finished = perf_counter()

    diagnostics = build_method_diagnostics(retrieval)
    return WorkbenchState(
        query=normalized_query,
        retrieval=retrieval,
        answer=answer,
        provider_status=provider_status,
        timing_ms={
            "retrieval": _elapsed_ms(started, retrieval_finished),
            "generation": _elapsed_ms(retrieval_finished, finished),
            "total": _elapsed_ms(started, finished),
        },
        diagnostics=diagnostics,
        suggestions=_build_suggestions(answer, diagnostics),
        corpus_summary=corpus_summary,
        corpus_warnings=list(corpus_warnings or []),
        final_evidence_results=_final_evidence_results(
            retrieval.reranked_results,
            answer.evidence_chunks,
        ),
    )


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
