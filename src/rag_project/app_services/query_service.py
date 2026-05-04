"""Query orchestration service for the Streamlit Evidence Workbench."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
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
from rag_project.generation.prompt_builder import build_multi_intent_question
from rag_project.providers import (
    create_intent_planner,
    create_llm_client,
    create_reranker_client,
)
from rag_project.query_planning.intent_planner import QueryPlan, SubQuestionPlan
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
    SubQuestionSupport,
)

MAX_FINAL_EVIDENCE = 5
MAX_EVIDENCE_PER_SUBQUESTION = 1


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
    query_plan: QueryPlan | None = None
    sub_question_support: list[SubQuestionSupport] = Field(default_factory=list)
    support_label: str = "insufficient evidence"
    answer_mode: str = "grounded"
    evidence_panel_mode: str = "show"


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

    def run(self, query: str, *, top_k: int = 3) -> WorkbenchState:
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
    top_k: int = 3,
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
    query_plan = create_intent_planner(config).plan(
        normalized_query,
        top_k=bounded_top_k,
        available_evidence_types=["text", "image", "table_summary"],
        available_document_count=len({chunk.doc_id for chunk in chunks}),
    )
    if not query_plan.requires_retrieval:
        finished = perf_counter()
        return _no_retrieval_state(
            query=normalized_query,
            query_plan=query_plan,
            provider_status=provider_status,
            started=started,
            finished=finished,
            corpus_summary=corpus_summary,
            corpus_warnings=corpus_warnings,
            chunks=chunks,
        )

    pipeline_started = perf_counter()
    pipeline = retrieval_pipeline or build_retrieval_pipeline(
        chunks,
        reranker=create_reranker_client(config),
    )
    pipeline_finished = perf_counter()

    if not query_plan.sub_questions:
        query_plan = query_plan.model_copy(
            update={
                "sub_questions": [
                    SubQuestionPlan(
                        id="Q1",
                        question=normalized_query,
                        retrieval_query=normalized_query,
                        top_k=bounded_top_k,
                    )
                ]
            }
        )

    if query_plan.is_multi_intent:
        retrieval, retrieval_timings, sub_results = _run_planned_retrieval(
            pipeline,
            query_plan,
            top_k=bounded_top_k,
        )
    else:
        retrieval, retrieval_timings = pipeline.search_with_timing(
            query_plan.sub_questions[0].retrieval_query,
            top_k=bounded_top_k,
        )
        sub_results = {query_plan.sub_questions[0].id: retrieval.reranked_results}
    retrieval_finished = perf_counter()

    generation_started = perf_counter()
    if query_plan.is_multi_intent:
        final_evidence_results, sub_question_support = _select_multi_intent_final_results(
            query_plan,
            sub_results,
            max_final_evidence=MAX_FINAL_EVIDENCE,
            max_per_subquestion=MAX_EVIDENCE_PER_SUBQUESTION,
        )
        final_evidence = _build_final_evidence(final_evidence_results)
        final_evidence = _attach_sub_question_ids(final_evidence, query_plan, sub_results)
        sub_question_support = _bind_support_evidence_ids(
            sub_question_support,
            final_evidence,
        )
        synthesis_question = build_multi_intent_question(
            normalized_query,
            [
                support.model_dump(mode="json")
                for support in sub_question_support
            ],
        )
        answer = AnswerGenerator(
            llm_client=create_llm_client(config),
            max_evidence=len(final_evidence_results) or 1,
        ).generate(synthesis_question, final_evidence_results)
    else:
        answer_results = _answer_candidate_results(
            normalized_query,
            retrieval.reranked_results,
            max_results=bounded_top_k,
        )
        answer = AnswerGenerator(
            llm_client=create_llm_client(config),
            max_evidence=bounded_top_k,
        ).generate(normalized_query, answer_results)
        sub_question_support = []
        final_evidence_results = _final_evidence_results(
            retrieval.reranked_results,
            answer.evidence_chunks,
        )
        final_evidence = _build_final_evidence(final_evidence_results)
    finished = perf_counter()

    timing_ms = {
        **retrieval_timings,
        "pipeline_build": _elapsed_ms(pipeline_started, pipeline_finished),
        "retrieval_total": _elapsed_ms(pipeline_finished, retrieval_finished),
        "generation": _elapsed_ms(generation_started, finished),
        "total": _elapsed_ms(started, finished),
    }
    answer = _attach_evidence_ids(answer, final_evidence)
    support_label = _overall_support_label(answer, sub_question_support)
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
        query_plan=query_plan,
        sub_question_support=sub_question_support,
        support_label=support_label,
        answer_mode=answer.answer_mode,
        evidence_panel_mode=query_plan.evidence_panel_mode,
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


def _no_retrieval_state(
    *,
    query: str,
    query_plan: QueryPlan,
    provider_status: ProviderStatus,
    started: float,
    finished: float,
    corpus_summary: CorpusSummary | None,
    corpus_warnings: list[str] | None,
    chunks: list[Chunk],
) -> WorkbenchState:
    answer = _build_no_retrieval_answer(query, query_plan)
    timing_ms = {
        "bm25": 0.0,
        "dense": 0.0,
        "fusion": 0.0,
        "reranker": 0.0,
        "retrieval": 0.0,
        "pipeline_build": 0.0,
        "retrieval_total": 0.0,
        "generation": 0.0,
        "total": _elapsed_ms(started, finished),
    }
    return WorkbenchState(
        query=query,
        retrieval=RetrievalPipelineOutput(),
        answer=answer,
        provider_status=provider_status,
        timing_ms=timing_ms,
        diagnostics=[],
        suggestions=_no_retrieval_suggestions(query_plan),
        corpus_summary=corpus_summary,
        corpus_warnings=list(corpus_warnings or []),
        final_evidence_results=[],
        final_evidence=[],
        retrieval_trace=[],
        scope=_build_scope(corpus_summary, chunks),
        query_plan=query_plan,
        sub_question_support=[],
        support_label="insufficient evidence",
        answer_mode=query_plan.answer_mode,
        evidence_panel_mode=query_plan.evidence_panel_mode,
    )


def _build_no_retrieval_answer(query: str, query_plan: QueryPlan) -> AnswerResponse:
    if query_plan.answer_mode == "help":
        text = (
            "App help: upload PDFs, TXT, MD, or Markdown files with Manage Materials, "
            "choose Sample, Uploaded, or Combined scope, then ask a question about the "
            "selected study materials. Grounded answers show inline citations like [E1]; "
            "click a citation to inspect the matching evidence card. Open page appears "
            "for registered PDF evidence when a page number is available."
        )
    elif query_plan.answer_mode == "refusal":
        text = (
            "This assistant is designed for study-material questions. Please ask about "
            "your uploaded documents, selected course notes, or the retrieval evidence."
        )
    else:
        text = _general_answer_text(query)

    return AnswerResponse(
        answer=text,
        citations=[],
        insufficient_evidence=True,
        evidence_chunks=[],
        retrieval_explanation="No document retrieval was used for this answer.",
        generation_mode="mock",
        answer_mode=query_plan.answer_mode,
    )


def _general_answer_text(query: str) -> str:
    lowered = query.lower()
    if "weather" in lowered or "天气" in lowered:
        return (
            "General answer: I cannot check live weather from the local RAG workbench. "
            "This response is not grounded in uploaded materials."
        )
    if "joke" in lowered or "笑话" in lowered:
        return (
            "General answer: I can keep the conversation light, but this response is "
            "not grounded in uploaded materials. Ask about your course notes when you "
            "want evidence-backed citations."
        )
    return (
        "General answer: this looks like a question outside the selected study "
        "materials, so no document evidence was used. Ask about uploaded course "
        "notes to receive grounded citations and retrieval evidence."
    )


def _no_retrieval_suggestions(query_plan: QueryPlan) -> list[str]:
    if query_plan.answer_mode == "help":
        return ["Upload materials first, then ask a content question to enable evidence."]
    if query_plan.answer_mode == "refusal":
        return ["Try asking about a concept, section, figure, or formula in your study materials."]
    return ["Ask about uploaded documents or course notes to get a grounded answer with citations."]


def _run_planned_retrieval(
    pipeline: RetrievalPipeline,
    query_plan: QueryPlan,
    *,
    top_k: int,
) -> tuple[RetrievalPipelineOutput, dict[str, float], dict[str, list[RetrievalResult]]]:
    outputs: list[RetrievalPipelineOutput] = []
    timings: list[dict[str, float]] = []
    sub_results: dict[str, list[RetrievalResult]] = {}

    for sub_question in query_plan.sub_questions:
        output, timing = pipeline.search_with_timing(
            sub_question.retrieval_query,
            top_k=max(1, min(sub_question.top_k or top_k, 10)),
        )
        filtered = _planned_answer_candidate_results(
            sub_question,
            output.reranked_results,
            max_results=top_k,
        )
        sub_results[sub_question.id] = filtered
        outputs.append(output)
        timings.append(timing)

    merged = RetrievalPipelineOutput(
        bm25_results=_merge_results([output.bm25_results for output in outputs], top_k=top_k),
        dense_results=_merge_results([output.dense_results for output in outputs], top_k=top_k),
        fusion_results=_merge_results([output.fusion_results for output in outputs], top_k=top_k),
        reranked_results=_merge_results(list(sub_results.values()), top_k=top_k * len(query_plan.sub_questions)),
    )
    return merged, _sum_timings(timings), sub_results


def _merge_results(
    groups: list[list[RetrievalResult]],
    *,
    top_k: int,
) -> list[RetrievalResult]:
    by_chunk: dict[str, RetrievalResult] = {}
    for group in groups:
        for result in group:
            current = by_chunk.get(result.chunk_id)
            if current is None or result.score > current.score:
                by_chunk[result.chunk_id] = result
    ranked = sorted(by_chunk.values(), key=lambda result: result.score, reverse=True)
    return [
        result.model_copy(update={"rank": index})
        for index, result in enumerate(ranked[:top_k], start=1)
    ]


def _sum_timings(rows: list[dict[str, float]]) -> dict[str, float]:
    keys = sorted({key for row in rows for key in row})
    return {
        key: round(sum(float(row.get(key, 0.0)) for row in rows), 3)
        for key in keys
    }


def _planned_answer_candidate_results(
    sub_question: SubQuestionPlan,
    reranked_results: list[RetrievalResult],
    *,
    max_results: int,
) -> list[RetrievalResult]:
    valid = [
        result
        for result in reranked_results
        if is_valid_table_evidence(result.chunk)
    ]
    if not valid:
        return []

    if sub_question.table_allowed:
        tables = [result for result in valid if result.chunk.type == "table"]
        other = [result for result in valid if result.chunk.type != "table"]
        return (tables + other)[:max_results]
    preferred = [
        result
        for result in valid
        if result.chunk.type in {"text", "image"}
        and (result.chunk.type != "image" or sub_question.image_allowed)
    ]
    tables = [result for result in valid if result.chunk.type == "table"]
    return (preferred + tables)[:max_results]


def _generate_multi_intent_answer(
    query_plan: QueryPlan,
    sub_results: dict[str, list[RetrievalResult]],
    *,
    max_results: int,
) -> tuple[AnswerResponse, list[SubQuestionSupport]]:
    answer_sections: list[str] = []
    citations: list[Citation] = []
    evidence_chunks: list[Chunk] = []
    supports: list[SubQuestionSupport] = []

    for sub_question in query_plan.sub_questions:
        results = sub_results.get(sub_question.id, [])[:max_results]
        chunks = [result.chunk for result in results]
        if not chunks:
            answer_sections.append(
                f"{sub_question.id}. {sub_question.question}\n"
                "The retrieved materials do not contain enough evidence for this part."
            )
            supports.append(
                SubQuestionSupport(
                    id=sub_question.id,
                    question=sub_question.question,
                    intent=sub_question.intent,
                    retrieval_query=sub_question.retrieval_query,
                    support_label="insufficient evidence",
                    evidence_ids=[],
                    insufficient_evidence=True,
                )
            )
            continue

        marker_tokens = [
            f"[[{sub_question.id}:{chunk.chunk_id}]]"
            for chunk in chunks
        ]
        sentence = _first_supported_sentence(chunks[0])
        answer_sections.append(
            f"{sub_question.id}. {sub_question.question}\n"
            f"The materials support this part: {sentence} {marker_tokens[0]}."
        )
        citations.extend(
            Citation(
                chunk_id=chunk.chunk_id,
                source_file=chunk.source_file,
                page=chunk.page,
            )
            for chunk in chunks
        )
        evidence_chunks.extend(chunks)
        label = "supported" if len(chunks) >= 1 else "insufficient evidence"
        supports.append(
            SubQuestionSupport(
                id=sub_question.id,
                question=sub_question.question,
                intent=sub_question.intent,
                retrieval_query=sub_question.retrieval_query,
                support_label=label,
                evidence_ids=[],
                insufficient_evidence=False,
            )
        )

    insufficient = all(item.insufficient_evidence for item in supports)
    explanation = (
        "Intent-aware query planning split the query into "
        f"{len(query_plan.sub_questions)} sub-questions and retrieved evidence "
        "for each part separately."
    )
    return (
        AnswerResponse(
            answer="\n\n".join(answer_sections),
            citations=citations,
            insufficient_evidence=insufficient,
            evidence_chunks=_dedupe_chunks(evidence_chunks),
            retrieval_explanation=explanation,
        ),
        supports,
    )


def _select_multi_intent_final_results(
    query_plan: QueryPlan,
    sub_results: dict[str, list[RetrievalResult]],
    *,
    max_final_evidence: int,
    max_per_subquestion: int,
) -> tuple[list[RetrievalResult], list[SubQuestionSupport]]:
    selected: list[RetrievalResult] = []
    supports: list[SubQuestionSupport] = []
    used_keys: set[str] = set()

    for sub_question in query_plan.sub_questions:
        candidates = _rank_sub_question_candidates(
            sub_question,
            sub_results.get(sub_question.id, []),
        )
        picked_for_sub: list[RetrievalResult] = []
        for candidate in candidates:
            key = _dedupe_result_key(candidate)
            if key in used_keys:
                continue
            if len(picked_for_sub) >= max_per_subquestion:
                break
            if len(selected) >= max_final_evidence:
                break
            used_keys.add(key)
            picked_for_sub.append(candidate)
            selected.append(candidate)

        supports.append(
            SubQuestionSupport(
                id=sub_question.id,
                question=sub_question.question,
                intent=sub_question.intent,
                retrieval_query=sub_question.retrieval_query,
                support_label="supported" if picked_for_sub else "insufficient evidence",
                evidence_ids=[],
                insufficient_evidence=not picked_for_sub,
            )
        )

    return selected, supports


def _rank_sub_question_candidates(
    sub_question: SubQuestionPlan,
    candidates: list[RetrievalResult],
) -> list[RetrievalResult]:
    valid = [candidate for candidate in candidates if is_valid_table_evidence(candidate.chunk)]

    def sort_key(result: RetrievalResult) -> tuple[int, float, int]:
        type_bonus = 2 if result.chunk.type in {"text", "image"} else 0
        if result.chunk.type == "table" and sub_question.table_allowed:
            type_bonus = 1
        if result.chunk.type == "table" and not sub_question.table_allowed:
            type_bonus = -1
        return (type_bonus, float(result.score), -int(result.rank))

    return sorted(valid, key=sort_key, reverse=True)


def _dedupe_result_key(result: RetrievalResult) -> str:
    if result.chunk_id:
        return f"chunk:{result.chunk_id}"
    preview = _clean_display_text(_chunk_preview(result.chunk, max_chars=160)).lower()
    return f"approx:{result.chunk.source_file}:{result.chunk.page}:{preview}"


def _dedupe_chunks(chunks: list[Chunk]) -> list[Chunk]:
    seen: set[str] = set()
    deduped: list[Chunk] = []
    for chunk in chunks:
        if chunk.chunk_id in seen:
            continue
        seen.add(chunk.chunk_id)
        deduped.append(chunk)
    return deduped


def _first_supported_sentence(chunk: Chunk) -> str:
    preview = _chunk_preview(chunk, max_chars=240) or _clean_display_text(chunk.text)
    if not preview:
        return "the selected evidence is relevant"
    parts = _split_sentences(preview)
    return parts[0].rstrip(".!?") if parts else preview.rstrip(".!?")


def _build_final_evidence(results: list[RetrievalResult]) -> list[EvidenceReference]:
    evidence: list[EvidenceReference] = []
    for index, result in enumerate(results, start=1):
        chunk = result.chunk
        confidence = _confidence_from_score(float(result.score))
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
                confidence=confidence,
                preview=_chunk_preview(chunk),
                image_url=_evidence_image_url(chunk),
                table_summary=_chunk_preview(chunk) if _table_summary_available(chunk) else None,
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
    sub_marker_by_chunk = {
        f"[[{item.sub_question_id}:{item.chunk_id}]]": f"[{item.evidence_id}]"
        for item in evidence
        if item.sub_question_id
    }
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
    for placeholder, marker in sub_marker_by_chunk.items():
        answer_text = answer_text.replace(placeholder, marker)
    if not answer.insufficient_evidence and not any(marker in answer_text for marker in markers):
        answer_text = _add_inline_markers(answer_text, markers)
    answer_text = _clean_answer_text(answer_text)
    return answer.model_copy(update={"answer": answer_text, "citations": citations})


def _clean_answer_text(text: str) -> str:
    text = _clean_display_text(text)
    text = re.sub(r"\b(chunk_id|doc_id|internal_id)\s*[:=]\s*\S+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bpage_\d+_(text|image|table)_\d+\b", "[ref]", text)
    text = " ".join(text.split())
    return text.strip()


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


def _chunk_preview(chunk: Chunk, *, max_chars: int = 520) -> str:
    if chunk.type == "table":
        if not is_valid_table_evidence(chunk):
            return ""
        text = _best_table_preview_text(chunk)
        if text:
            return _sentence_boundary_excerpt(_clean_display_text(text), max_chars=max_chars)
        return ""
    if chunk.type == "image" and chunk.metadata.image_path:
        if chunk.metadata.caption:
            return _sentence_boundary_excerpt(_clean_display_text(chunk.metadata.caption), max_chars=max_chars)
        nearby = chunk.metadata.nearby_text or chunk.text or ""
        return _sentence_boundary_excerpt(_clean_display_text(nearby), max_chars=max_chars)
    if chunk.metadata.caption:
        text = chunk.metadata.caption
    else:
        text = chunk.text
    return _sentence_boundary_excerpt(_clean_display_text(text), max_chars=max_chars)


def _clean_display_text(text: str) -> str:
    if not text:
        return ""
    text = " ".join(str(text).split())
    text = re.sub(r"\|{3,}", " ", text)
    text = re.sub(r"\|{2,3}", " | ", text)
    text = re.sub(r"[│┃┆┇┊┋╎╏╌╍]{2,}", " ", text)
    text = re.sub(r"[^\S\r\n]{2,}", " ", text)
    text = re.sub(r"([a-f0-9]{40,})", "[hash]", text)
    text = re.sub(r"\b[a-f0-9]{32}\b", "[hash]", text)
    return text.strip()


def _sentence_boundary_excerpt(text: str, *, max_chars: int) -> str:
    normalized = " ".join(str(text or "").split())
    if len(normalized) <= max_chars:
        return normalized
    window = normalized[: max_chars + 1]
    boundary = max(
        window.rfind(". "),
        window.rfind("? "),
        window.rfind("! "),
        window.rfind("; "),
    )
    if boundary > max_chars // 3:
        return window[: boundary + 1].strip() + "..."
    return normalized[:max_chars].rstrip() + "..."


def _is_noisy_table_content(chunk: Chunk) -> bool:
    return not is_valid_table_evidence(chunk)


def is_valid_table_evidence(chunk: Chunk) -> bool:
    """Return whether a table chunk is readable enough for cited evidence."""
    if chunk.type != "table":
        return True

    rich_payloads = [
        _metadata_text(chunk, "table_summary"),
        _metadata_text(chunk, "table_markdown"),
        _html_to_text(_metadata_text(chunk, "table_html")),
        _cells_to_text(getattr(chunk.metadata, "cells", None)),
    ]
    for payload in rich_payloads:
        if _is_readable_table_text(payload, min_chars=24):
            return True

    caption = _metadata_text(chunk, "caption")
    if _is_placeholder_table_text(caption):
        caption = ""

    fallback_payloads = [
        caption,
        _metadata_text(chunk, "nearby_text"),
        chunk.text or "",
    ]
    return any(
        _is_readable_table_text(payload, min_chars=80)
        for payload in fallback_payloads
    )


def _best_table_preview_text(chunk: Chunk) -> str:
    candidates = [
        _metadata_text(chunk, "table_summary"),
        _metadata_text(chunk, "table_markdown"),
        _html_to_text(_metadata_text(chunk, "table_html")),
        _cells_to_text(getattr(chunk.metadata, "cells", None)),
        _metadata_text(chunk, "nearby_text"),
        chunk.text or "",
    ]
    for candidate in candidates:
        if _is_readable_table_text(candidate, min_chars=24):
            return candidate
    return ""


def _metadata_text(chunk: Chunk, field: str) -> str:
    value = getattr(chunk.metadata, field, None)
    return str(value or "")


def _html_to_text(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", str(value or ""))


def _cells_to_text(cells: object) -> str:
    if not isinstance(cells, list):
        return ""
    rows: list[str] = []
    for row in cells:
        if isinstance(row, list):
            rows.append(" | ".join(str(cell or "").strip() for cell in row))
    return " ".join(rows)


def _is_readable_table_text(text: str, *, min_chars: int) -> bool:
    cleaned = _clean_display_text(_html_to_text(text))
    if _is_placeholder_table_text(cleaned):
        return False
    if len(cleaned.strip()) < min_chars:
        return False
    if cleaned.count("|") > len(cleaned) * 0.15:
        return False
    if re.search(r"(internal[_\s]?id|_id\b|chunk_id|doc_id)", cleaned, re.IGNORECASE):
        return False
    if re.search(r"\b[a-f0-9]{32,}\b", cleaned, re.IGNORECASE):
        return False
    repeated_symbol_count = len(re.findall(r"[|_\-=]{4,}", cleaned))
    if repeated_symbol_count:
        return False
    readable = re.findall(r"[a-zA-Z\u4e00-\u9fff\d]", cleaned)
    if len(readable) < 15:
        return False
    alpha_digit_ratio = len(readable) / max(len(cleaned), 1)
    return alpha_digit_ratio >= 0.12


def _is_placeholder_table_text(text: str) -> bool:
    normalized = " ".join(str(text or "").strip().lower().split())
    normalized = normalized.strip(".")
    return normalized in {
        "",
        "(no text preview)",
        "no text preview",
        "table extracted from pdf",
        "no table content",
        "empty table",
    }


def _legacy_noisy_table_content(chunk: Chunk) -> bool:
    caption = chunk.metadata.caption or ""
    if caption.strip().lower() == "table extracted from pdf.":
        return True
    if re.match(r"^\s*Table extracted from PDF\.\s*$", caption):
        return True
    text = chunk.text or ""
    if chunk.metadata.table_html:
        html_text = re.sub(r"<[^>]+>", " ", chunk.metadata.table_html)
        html_text = " ".join(html_text.split())
        if html_text:
            text = html_text
    text = " ".join(text.split())
    if not text:
        return True
    text_lower = text.lower().strip()
    placeholder_patterns = [
        "table extracted from pdf",
        "no table content",
        "empty table",
    ]
    for pattern in placeholder_patterns:
        if text_lower == pattern:
            return True
    noise_patterns = [
        r"^\s*\|+\s*$",
        r"^\s*[│┃]+(.)*[│┃]+\s*$",
    ]
    for pattern in noise_patterns:
        if re.search(pattern, text):
            return True
    alpha_ratio = len(re.findall(r"[a-zA-Z]", text)) / max(len(text), 1)
    if alpha_ratio < 0.05 and not re.search(r"[\u4e00-\u9fff\d]", text):
        return True
    if re.search(r"(internal[_\s]?id|_id\b|chunk_id|doc_id)", text, re.IGNORECASE):
        return True
    return False


def _table_summary_available(chunk: Chunk) -> bool:
    if chunk.type != "table":
        return False
    return is_valid_table_evidence(chunk) and bool(_best_table_preview_text(chunk))


def _evidence_image_url(chunk: Chunk) -> str | None:
    image_path = chunk.metadata.image_path
    if not image_path:
        return None
    return f"/api/static/images/{Path(image_path).name}"


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
    result_by_id = {result.chunk_id: result for result in reranked_results}
    ordered = [
        result_by_id[chunk.chunk_id]
        for chunk in evidence_chunks
        if chunk.chunk_id in result_by_id
    ]
    return [result for result in ordered if is_valid_table_evidence(result.chunk)]


def _answer_candidate_results(
    query: str,
    reranked_results: list[RetrievalResult],
    *,
    max_results: int,
) -> list[RetrievalResult]:
    valid = [
        result
        for result in reranked_results
        if is_valid_table_evidence(result.chunk)
    ]
    if not valid:
        return []

    if _query_prefers_tables(query):
        tables = [result for result in valid if result.chunk.type == "table"]
        other = [result for result in valid if result.chunk.type != "table"]
        return (tables + other)[:max_results]

    text_image = [result for result in valid if result.chunk.type in {"text", "image"}]
    tables = [result for result in valid if result.chunk.type == "table"]
    return (text_image + tables)[:max_results]


def _query_prefers_tables(query: str) -> bool:
    normalized = str(query or "").lower()
    table_terms = {
        "table",
        "formula",
        "comparison",
        "numerical",
        "numeric",
        "number",
        "numbers",
        "columns",
        "column",
        "rows",
        "row",
        "data",
        "metric",
        "metrics",
        "score",
        "scores",
        "表格",
        "数据",
        "数值",
        "对比",
        "公式",
        "列",
        "行",
    }
    return any(term in normalized for term in table_terms)


def _attach_sub_question_ids(
    evidence: list[EvidenceReference],
    query_plan: QueryPlan,
    sub_results: dict[str, list[RetrievalResult]],
) -> list[EvidenceReference]:
    chunk_to_sub: dict[str, str] = {}
    for sub_question in query_plan.sub_questions:
        for result in sub_results.get(sub_question.id, []):
            chunk_to_sub.setdefault(result.chunk_id, sub_question.id)
    return [
        item.model_copy(
            update={
                "sub_question_id": chunk_to_sub.get(item.chunk_id),
                "support_label": "supported",
            }
        )
        for item in evidence
    ]


def _bind_support_evidence_ids(
    supports: list[SubQuestionSupport],
    final_evidence: list[EvidenceReference],
) -> list[SubQuestionSupport]:
    ids_by_sub: dict[str, list[str]] = {}
    for item in final_evidence:
        if item.sub_question_id:
            ids_by_sub.setdefault(item.sub_question_id, []).append(item.evidence_id)

    bound: list[SubQuestionSupport] = []
    for support in supports:
        evidence_ids = ids_by_sub.get(support.id, [])
        if support.insufficient_evidence:
            label = "insufficient evidence"
        elif evidence_ids:
            label = "supported"
        else:
            label = "insufficient evidence"
        bound.append(
            support.model_copy(
                update={
                    "evidence_ids": evidence_ids,
                    "support_label": label,
                    "insufficient_evidence": label == "insufficient evidence",
                }
            )
        )
    return bound


def _overall_support_label(
    answer: AnswerResponse,
    supports: list[SubQuestionSupport],
) -> str:
    if not supports:
        return "insufficient evidence" if answer.insufficient_evidence else "supported"
    labels = {support.support_label for support in supports}
    if labels == {"supported"}:
        return "supported"
    if labels == {"insufficient evidence"}:
        return "insufficient evidence"
    if "supported" in labels or "low support" in labels:
        return "partially supported"
    return "low support"


def _elapsed_ms(start: float, end: float) -> float:
    return round((end - start) * 1000, 3)
