"""Streamlit RAG Study Chat for the offline-first study assistant."""

from __future__ import annotations

from pathlib import Path
import json
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st

from rag_project.app_services.corpus_service import (
    DEFAULT_REGISTRY_PATH,
    CorpusBundle,
    CorpusSelection,
    CorpusSummary,
    DocumentRecord,
    delete_uploaded_document,
    ingest_uploaded_files,
    load_corpus_bundle,
    load_document_registry,
)
from rag_project.app_services.provider_status import ProviderStatus, build_provider_status
from rag_project.app_services.query_service import (
    MethodDiagnostic,
    WorkbenchState,
    build_corpus_signature,
    build_retrieval_pipeline,
    run_query,
)
from rag_project.config import load_config
from rag_project.providers import create_reranker_client
from rag_project.schemas import Chunk, EvidenceReference, RetrievalResult, RetrievalTraceStage
from rag_project.ui.dashboard_data import load_or_create_evaluation_reports


DEFAULT_QUERY = "What is overfitting and why does validation data matter?"


@st.cache_resource(show_spinner=False)
def _get_runtime_config():
    return load_config()


@st.cache_resource(show_spinner=False)
def _get_provider_status() -> ProviderStatus:
    return build_provider_status(_get_runtime_config())


def _registry_cache_token() -> tuple[str, float, int]:
    path = Path(DEFAULT_REGISTRY_PATH)
    if not path.exists():
        return (str(path), 0.0, 0)
    stat = path.stat()
    return (str(path), stat.st_mtime, stat.st_size)


@st.cache_data(show_spinner=False)
def _load_uploaded_documents_cached(
    registry_token: tuple[str, float, int],
) -> list[DocumentRecord]:
    del registry_token
    return load_document_registry()


@st.cache_data(show_spinner=False)
def _load_corpus_bundle_cached(
    mode: str,
    selected_doc_ids: tuple[str, ...],
    registry_token: tuple[str, float, int],
) -> CorpusBundle:
    del registry_token
    return load_corpus_bundle(
        CorpusSelection(mode=mode, selected_doc_ids=list(selected_doc_ids))
    )


@st.cache_data(show_spinner=False)
def _load_evaluation_reports_cached():
    return load_or_create_evaluation_reports()


def _serialize_chunks(chunks: list[Chunk]) -> str:
    return json.dumps(
        [chunk.model_dump(mode="json") for chunk in chunks],
        ensure_ascii=False,
        sort_keys=True,
    )


@st.cache_resource(show_spinner=False)
def _get_retrieval_pipeline_cached(
    chunk_payload: str,
    corpus_signature: str,
    reranker_provider_key: tuple[str, str, str, str],
):
    del corpus_signature, reranker_provider_key
    chunks = [Chunk.model_validate(item) for item in json.loads(chunk_payload)]
    return build_retrieval_pipeline(
        chunks,
        reranker=create_reranker_client(_get_runtime_config()),
    )


def _reranker_provider_key() -> tuple[str, str, str, str]:
    config = _get_runtime_config()
    return (
        config.app_mode,
        config.reranker_provider,
        config.reranker_model,
        "key-set" if config.siliconflow_api_key else "key-missing",
    )


def _clear_corpus_caches() -> None:
    _load_uploaded_documents_cached.clear()
    _load_corpus_bundle_cached.clear()
    _get_retrieval_pipeline_cached.clear()


def main() -> None:
    """Run the Streamlit app."""
    rerun_started = perf_counter()
    config = _get_runtime_config()
    provider_status = _get_provider_status()

    st.set_page_config(
        page_title="RAG Study Assistant",
        page_icon="R",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _inject_style()
    _render_header(config.app_mode)

    _render_rag_workbench(provider_status)

    st.session_state["last_rerun_ms"] = round((perf_counter() - rerun_started) * 1000, 3)


def _render_header(app_mode: str) -> None:
    st.markdown(
        f"""
        <section class="topline">
          <div>
            <div class="eyebrow">RAG-BASED STUDY ASSISTANT</div>
            <h1>Ask your course materials</h1>
          </div>
          <div class="mode-pill">APP_MODE={_escape_preview(app_mode)}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar_status(provider_status: ProviderStatus) -> None:
    st.sidebar.markdown("### Runtime")
    for component in provider_status.components:
        state_class = _status_class(component.state)
        st.sidebar.markdown(
            f"""
            <div class="side-status">
              <span>{component.component.upper()}</span>
              <b class="{state_class}">{component.state}</b>
              <small>{_escape_preview(component.provider)} / {_escape_preview(component.model)}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.sidebar.caption(f"SiliconFlow key: {provider_status.api_key_status}")
    st.sidebar.caption("API keys are never displayed in the app.")


def _render_rag_workbench(provider_status: ProviderStatus) -> None:
    _ensure_chat_session()
    upload_status = _handle_upload_action()
    doc_load_started = perf_counter()
    all_uploaded = _load_uploaded_documents_cached(_registry_cache_token())
    st.session_state["document_metadata_loading_ms"] = round(
        (perf_counter() - doc_load_started) * 1000, 3
    )

    left, center, right = st.columns([0.74, 1.36, 1.0], gap="large")
    with left:
        selection = _render_corpus_manager(all_uploaded, upload_status)
        _render_provider_status_panel(provider_status)

    if st.session_state.get("rag_enabled", True):
        corpus_load_started = perf_counter()
        corpus_bundle = _load_corpus_bundle_cached(
            selection.mode,
            tuple(selection.selected_doc_ids),
            _registry_cache_token(),
        )
        st.session_state["document_chunk_loading_ms"] = round(
            (perf_counter() - corpus_load_started) * 1000, 3
        )
    else:
        corpus_bundle = CorpusBundle(
            chunks=[],
            summary=CorpusSummary(corpus_name="RAG retrieval disabled", chunk_count=0),
            documents=[],
            warnings=["RAG retrieval is disabled. Enable it to search selected materials."],
        )

    with center:
        _render_chat_composer(corpus_bundle)

        run_clicked = st.session_state.pop("run_workbench_query", False)
        query = st.session_state.get("workbench_query", "")
        top_k = int(st.session_state.get("workbench_top_k", 5))
        if _should_run_query(run_clicked, query):
            with st.spinner("Retrieving evidence, reranking candidates, and drafting a grounded answer..."):
                try:
                    corpus_signature = build_corpus_signature(corpus_bundle.chunks)
                    retrieval_pipeline = _get_retrieval_pipeline_cached(
                        _serialize_chunks(corpus_bundle.chunks),
                        corpus_signature,
                        _reranker_provider_key(),
                    )
                    st.session_state["last_corpus_signature"] = corpus_signature
                    st.session_state["last_workbench_state"] = run_query(
                        query,
                        corpus_bundle,
                        top_k=top_k,
                        config=_get_runtime_config(),
                        retrieval_pipeline=retrieval_pipeline,
                    )
                except Exception as exc:  # pragma: no cover - defensive Streamlit fallback
                    st.session_state["last_workbench_error"] = str(exc)

        state = st.session_state.get("last_workbench_state")
        error = st.session_state.pop("last_workbench_error", None)
        if error:
            st.error(f"RAG query failed. Mock/local fallback remains available. Error: {error}")
        if isinstance(state, WorkbenchState):
            _render_answer_panel(state)
        else:
            _render_empty_chat_state()

    with right:
        if isinstance(state, WorkbenchState):
            _render_right_evidence_panel(state)
        else:
            _render_right_placeholder()


def _ensure_chat_session() -> None:
    defaults = {
        "workbench_query": DEFAULT_QUERY,
        "workbench_top_k": 5,
        "corpus_mode": "combined",
        "selected_doc_ids": [],
        "rag_enabled": True,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _handle_upload_action():
    files = st.session_state.get("pending_upload_files") or []
    if st.session_state.pop("ingest_pending_uploads", False) and files:
        upload_started = perf_counter()
        result = ingest_uploaded_files(files)
        st.session_state["upload_ingestion_ms"] = round(
            (perf_counter() - upload_started) * 1000, 3
        )
        _clear_corpus_caches()
        selected = set(st.session_state.get("selected_doc_ids", []))
        selected.update(record.doc_id for record in result.uploaded)
        st.session_state["selected_doc_ids"] = sorted(selected)
        return result
    return None


def _render_corpus_manager(
    documents: list[DocumentRecord],
    upload_status,
) -> CorpusSelection:
    st.markdown('<div class="section-title">Knowledge Base</div>', unsafe_allow_html=True)
    st.file_uploader(
        "Upload lecture notes or PDFs",
        type=["txt", "md", "markdown", "pdf"],
        accept_multiple_files=True,
        key="pending_upload_files",
    )
    if st.button("Add files to local corpus", type="primary", use_container_width=True):
        st.session_state["ingest_pending_uploads"] = True
        st.rerun()

    if upload_status:
        if upload_status.uploaded:
            st.success(f"Added {len(upload_status.uploaded)} document(s).")
        for failure in upload_status.failed:
            st.warning(f"{failure.filename}: {failure.error}")

    mode = st.radio(
        "Corpus scope",
        ["combined", "sample", "uploaded"],
        key="corpus_mode",
        format_func=lambda value: {
            "combined": "Sample + uploaded",
            "sample": "Sample only",
            "uploaded": "Uploaded only",
        }[value],
    )
    rag_enabled = st.checkbox("RAG retrieval enabled", key="rag_enabled")

    selected_doc_ids = _render_document_selector(documents)
    selected_count = len(selected_doc_ids)
    active_scope = (
        "all uploaded documents"
        if documents and selected_count == 0
        else f"{selected_count} selected document(s)"
    )
    st.markdown(
        f"""
        <div class="scope-chip">
          <b>RAG {'enabled' if rag_enabled else 'disabled'}</b>
          <span>{_escape_preview(mode)} scope | {_escape_preview(active_scope)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return CorpusSelection(mode=mode, selected_doc_ids=selected_doc_ids)


def _render_document_selector(documents: list[DocumentRecord]) -> list[str]:
    if not documents:
        st.info("No local documents uploaded yet. The sample corpus is still available.")
        st.session_state["selected_doc_ids"] = []
        return []

    selected = set(st.session_state.get("selected_doc_ids", []))
    valid_ids = {record.doc_id for record in documents}
    selected &= valid_ids
    st.session_state["selected_doc_ids"] = sorted(selected)

    with st.expander("Uploaded documents", expanded=True):
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Select all", use_container_width=True):
                selected = set(valid_ids)
                st.session_state["selected_doc_ids"] = sorted(selected)
        with col_b:
            if st.button("Clear", use_container_width=True):
                selected = set()
                st.session_state["selected_doc_ids"] = []

        for record in documents:
            checked = record.doc_id in selected
            type_text = ", ".join(
                f"{key}:{value}"
                for key, value in sorted(record.type_counts.items())
            )
            if st.checkbox(
                f"{record.filename} ({record.chunk_count} chunks)",
                value=checked,
                key=f"doc_select_{record.doc_id}",
            ):
                selected.add(record.doc_id)
            else:
                selected.discard(record.doc_id)
            st.caption(f"`{record.doc_id}` | {type_text or 'no chunks'} | ready")

            if st.button("Delete", key=f"doc_delete_{record.doc_id}"):
                delete_uploaded_document(record.doc_id)
                _clear_corpus_caches()
                st.session_state["selected_doc_ids"] = [
                    doc_id
                    for doc_id in st.session_state.get("selected_doc_ids", [])
                    if doc_id != record.doc_id
                ]
                st.rerun()

    st.session_state["selected_doc_ids"] = sorted(selected)
    return sorted(selected)


def _render_provider_status_panel(provider_status: ProviderStatus) -> None:
    st.markdown('<div class="section-title">Provider Status</div>', unsafe_allow_html=True)
    for item in provider_status.components:
        st.markdown(
            f"""
            <div class="provider-row">
              <div><b>{item.component.upper()}</b><span>{_escape_preview(item.provider)} / {_escape_preview(item.model)}</span></div>
              <em class="{_status_class(item.state)}">{item.state}</em>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.caption("ASR/TTS live paths are deferred; mock fallback remains active.")


def _render_chat_composer(corpus_bundle: CorpusBundle) -> None:
    st.markdown(
        f"""
        <div class="chat-shell">
          <div class="chat-kicker">ACTIVE KNOWLEDGE BASE</div>
          <div class="chat-scope">{_escape_preview(corpus_bundle.summary.corpus_name)}</div>
          <div class="answer-meta">
            <span>{corpus_bundle.summary.chunk_count} chunks</span>
            <span>{len(corpus_bundle.summary.source_files)} sources</span>
            <span>{len(corpus_bundle.documents)} uploaded docs in scope</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for warning in corpus_bundle.warnings:
        st.warning(warning)

    st.text_area(
        "Ask a study question",
        key="workbench_query",
        height=130,
        placeholder="Ask about your uploaded notes, lecture PDFs, or the sample corpus...",
    )
    cols = st.columns([0.42, 0.58])
    with cols[0]:
        st.slider(
            "Evidence Top-k",
            min_value=1,
            max_value=5,
            key="workbench_top_k",
        )
    with cols[1]:
        if st.button("Ask with RAG", type="primary", use_container_width=True):
            st.session_state["run_workbench_query"] = True


def _render_answer_panel(state: WorkbenchState) -> None:
    summary = state.corpus_summary or CorpusSummary(corpus_name="Current corpus", chunk_count=0)
    st.markdown(
        f"""
        <div class="chat-message assistant-msg">
          <div class="message-avatar">RA</div>
          <div class="message-body">
            <div class="answer-meta">
              <span>{len(state.final_evidence)} cited evidence chunks</span>
              <span>{state.timing_ms.get("total", 0):.1f} ms total</span>
              <span>{_escape_preview(summary.corpus_name)}</span>
            </div>
            <div class="answer-text">{_escape_preview(state.answer.answer)}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if state.answer.insufficient_evidence:
        st.warning("Insufficient evidence. Review the Evidence Intelligence panel before using this answer.")

    if state.final_evidence:
        st.markdown("#### Cited evidence")
        cols = st.columns(min(3, len(state.final_evidence)))
        for index, evidence in enumerate(state.final_evidence):
            with cols[index % len(cols)]:
                if st.button(
                    f"View {evidence.evidence_id}",
                    key=f"view_{evidence.evidence_id}",
                    use_container_width=True,
                ):
                    st.session_state["active_evidence_id"] = evidence.evidence_id
        st.caption("Citation buttons highlight the matching evidence in the right panel.")


def _render_right_placeholder() -> None:
    st.markdown('<div class="section-title">Evidence Intelligence</div>', unsafe_allow_html=True)
    st.info("Run a RAG query to inspect cited chunks and retrieval method outputs.")


def _render_right_evidence_panel(state: WorkbenchState) -> None:
    st.markdown('<div class="section-title">Evidence Intelligence</div>', unsafe_allow_html=True)
    weak = state.answer.insufficient_evidence or not state.final_evidence
    if weak:
        st.warning("Insufficient or weak evidence. Review retrieved chunks before trusting the answer.")

    active_id = st.session_state.get("active_evidence_id")
    _render_cited_evidence(state.final_evidence, active_id=active_id)
    _render_retrieval_flow(state.retrieval_trace)
    _render_method_comparison(state)
    _render_integrated_evaluation_metrics()

    with st.expander("Debug view", expanded=False):
        st.write(
            {
                "query": state.query,
                "scope": state.scope,
                "active_evidence_id": active_id,
                "provider_status": state.provider_status.as_runtime_dict(),
                "timing_ms": {
                    **state.timing_ms,
                    "last_rerun": st.session_state.get("last_rerun_ms", 0),
                    "document_metadata_loading": st.session_state.get("document_metadata_loading_ms", 0),
                    "document_chunk_loading": st.session_state.get("document_chunk_loading_ms", 0),
                    "upload_ingestion": st.session_state.get("upload_ingestion_ms", 0),
                },
                "corpus_signature": st.session_state.get("last_corpus_signature", ""),
                "retrieval_explanation": state.answer.retrieval_explanation,
                "diagnostics": _diagnostics_to_rows(state.diagnostics),
                "corpus_warnings": state.corpus_warnings,
            }
        )


def _render_cited_evidence(
    evidence_items: list[EvidenceReference], *, active_id: str | None
) -> None:
    st.markdown("#### Cited Evidence")
    if not evidence_items:
        st.info("No final evidence chunks were selected.")
        return

    ordered = sorted(
        evidence_items,
        key=lambda item: (item.evidence_id != active_id, item.evidence_id),
    )
    for evidence in ordered:
        active = evidence.evidence_id == active_id
        title = (
            f"{evidence.evidence_id} | {evidence.source_file} p.{evidence.page} | "
            f"{evidence.type} | score {evidence.score:.3f}"
        )
        with st.expander(title, expanded=active or evidence.evidence_id == "E1"):
            if active:
                st.markdown('<div class="active-evidence">Selected from answer</div>', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="evidence-chip {'evidence-active' if active else ''}">
                  <b>{_escape_preview(evidence.evidence_id)} | {_escape_preview(evidence.method.upper())}</b>
                  <span>chunk_id={_escape_preview(evidence.chunk_id)} | doc_id={_escape_preview(evidence.doc_id)}</span>
                  <span>{_escape_preview(evidence.preview)}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.progress(evidence.confidence)
            st.caption(f"confidence={evidence.confidence:.3f} | source={evidence.source_file} | page={evidence.page}")
            _render_chunk_media(evidence.chunk)


def _render_retrieval_flow(trace: list[RetrievalTraceStage]) -> None:
    with st.expander("Retrieval flow", expanded=True):
        if not trace:
            st.info("Run a query to see retrieval flow diagnostics.")
            return
        cols = st.columns(len(trace))
        for col, stage in zip(cols, trace):
            with col:
                st.markdown(
                    f"""
                    <div class="flow-card">
                      <b>{_escape_preview(stage.stage)}</b>
                      <span>{stage.result_count} top-k</span>
                      <span>best {stage.top_score:.3f}</span>
                      <em>{stage.latency_ms:.1f} ms</em>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.progress(stage.confidence)


def _render_method_comparison(state: WorkbenchState) -> None:
    with st.expander("Method comparison", expanded=True):
        tabs = st.tabs(["BM25", "Dense", "Fusion", "Reranked"])
        result_groups = [
            state.retrieval.bm25_results,
            state.retrieval.dense_results,
            state.retrieval.fusion_results,
            state.retrieval.reranked_results,
        ]
        diagnostics = {item.method: item for item in state.diagnostics}
        methods = ["bm25", "dense", "fusion", "reranked"]
        for tab, method, results in zip(tabs, methods, result_groups):
            with tab:
                diagnostic = diagnostics.get(method)
                if diagnostic:
                    st.markdown(
                        f"**{method.upper()}** | {diagnostic.confidence_label} | "
                        f"{diagnostic.result_count} results"
                    )
                    st.progress(diagnostic.confidence)
                    st.caption(diagnostic.recommendation)
                _render_rank_cards(results)
                with st.expander("Raw rows", expanded=False):
                    st.dataframe(_results_to_frame(results), use_container_width=True, hide_index=True)


def _render_rank_cards(results: list[RetrievalResult]) -> None:
    if not results:
        st.info("No candidates returned.")
        return
    for result in results[:5]:
        confidence = _score_to_confidence(float(result.score))
        st.markdown(
            f"""
            <div class="rank-card">
              <b>#{result.rank} | {_escape_preview(result.chunk.source_file)} p.{result.chunk.page}</b>
              <span>{_escape_preview(result.chunk_id)}</span>
              <span>{_escape_preview(_chunk_preview(result.chunk, max_chars=120))}</span>
              <em>score {result.score:.3f}</em>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(confidence)


def _render_integrated_evaluation_metrics() -> None:
    with st.expander("Evaluation metrics", expanded=False):
        reports = _load_evaluation_reports_cached()
        summary = _summarize_metrics(reports.metrics)
        latency_summary = _summarize_latency(reports.latency)
        best_method = _best_method(summary)
        if best_method:
            st.success(
                f"Best NDCG@5: {best_method['method']} "
                f"({float(best_method['ndcg@5']):.3f})"
            )
        _render_metric_bars(summary, ["recall@1", "recall@3", "recall@5"])
        _render_metric_bars(summary, ["mrr@5", "ndcg@5"])
        _render_latency_bars(latency_summary)
        with st.expander("Error/debug cases", expanded=False):
            st.markdown(reports.error_cases_markdown)


def _render_empty_chat_state() -> None:
    st.markdown(
        """
        <div class="empty-state">
          <b>Upload notes or use the sample corpus, then ask a question.</b>
          <span>The main answer stays here. Retrieval traces, evidence rankings, and debug details are available after each answer.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_evaluation_dashboard() -> None:
    st.markdown(
        '<div class="section-title">Evaluation Dashboard</div>',
        unsafe_allow_html=True,
    )
    if st.button("Run local evaluation", type="primary"):
        with st.spinner("Running local retrieval evaluation..."):
            reports = load_or_create_evaluation_reports()
            _load_evaluation_reports_cached.clear()
    else:
        reports = _load_evaluation_reports_cached()

    summary = _summarize_metrics(reports.metrics)
    latency_summary = _summarize_latency(reports.latency)

    best_method = _best_method(summary)
    with st.expander("Method summary", expanded=True):
        if best_method:
            st.success(
                f"Best current method by NDCG@5: {best_method['method']} "
                f"({float(best_method['ndcg@5']):.3f})."
            )
        st.dataframe(summary, use_container_width=True, hide_index=True)

    with st.expander("Recall coverage", expanded=True):
        _render_metric_bars(summary, ["recall@1", "recall@3", "recall@5"])

    with st.expander("Ranking quality", expanded=True):
        _render_metric_bars(summary, ["mrr@5", "ndcg@5"])

    with st.expander("Latency", expanded=False):
        st.dataframe(latency_summary, use_container_width=True, hide_index=True)
        _render_latency_bars(latency_summary)

    with st.expander("Weak cases", expanded=True):
        st.markdown(reports.error_cases_markdown)


def _should_run_query(run_clicked: bool, query: str) -> bool:
    """Return whether the workbench should execute a query."""
    return bool(run_clicked and query.strip())


def _results_to_frame(results: list[RetrievalResult]) -> list[dict[str, object]]:
    rows = []
    for result in results:
        metadata = result.chunk.metadata
        rows.append(
            {
                "rank": result.rank,
                "score": round(result.score, 4),
                "method": result.method,
                "chunk_id": result.chunk_id,
                "doc_id": result.chunk.doc_id,
                "source_file": result.chunk.source_file,
                "page": result.chunk.page,
                "type": result.chunk.type,
                "preview": _chunk_preview(result.chunk, max_chars=160),
                "image_path": metadata.image_path or "",
                "caption": metadata.caption or "",
                "bbox": _format_bbox(metadata.bbox),
            }
        )
    return rows


def _format_bbox(bbox: object) -> str:
    if not bbox:
        return ""
    if isinstance(bbox, (list, tuple)):
        return ", ".join(str(value) for value in bbox)
    return str(bbox)


def _diagnostics_to_rows(
    diagnostics: list[MethodDiagnostic],
) -> list[dict[str, object]]:
    return [
        {
            "method": item.method,
            "results": item.result_count,
            "top_score": item.top_score,
            "confidence": item.confidence_label,
            "confidence_value": item.confidence,
            "recommendation": item.recommendation,
        }
        for item in diagnostics
    ]


def _render_chunk_media(chunk: Chunk) -> None:
    image_path = chunk.metadata.image_path
    if not image_path:
        return
    path = Path(image_path)
    if path.exists():
        st.image(str(path), caption=chunk.metadata.caption or chunk.chunk_id, width=220)


def _chunk_preview(chunk: Chunk, *, max_chars: int = 240) -> str:
    if chunk.metadata.caption:
        text = chunk.metadata.caption
    elif chunk.metadata.table_html:
        text = chunk.text or chunk.metadata.table_html
    else:
        text = chunk.text
    return text[:max_chars]


def _summarize_metrics(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    metric_names = ["recall@1", "recall@3", "recall@5", "mrr@5", "ndcg@5"]
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["method"], []).append(row)

    summary = []
    for method, method_rows in sorted(grouped.items()):
        summary_row: dict[str, object] = {"method": method}
        for metric in metric_names:
            values = [float(row[metric]) for row in method_rows]
            summary_row[metric] = round(sum(values) / len(values), 3)
        summary.append(summary_row)
    return summary


def _summarize_latency(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    grouped: dict[str, list[float]] = {}
    for row in rows:
        grouped.setdefault(row["method"], []).append(float(row["latency_ms"]))
    return [
        {"method": method, "latency_ms": round(sum(values) / len(values), 3)}
        for method, values in sorted(grouped.items())
    ]


def _best_method(summary: list[dict[str, object]]) -> dict[str, object] | None:
    if not summary:
        return None
    return max(summary, key=lambda row: float(row["ndcg@5"]))


def _render_metric_bars(rows: list[dict[str, object]], metrics: list[str]) -> None:
    for row in rows:
        method = str(row["method"])
        for metric in metrics:
            value = float(row[metric])
            st.markdown(
                f"""
                <div class="metric-line">
                  <span>{method} | {metric}</span>
                  <div class="bar-shell"><div class="bar-fill" style="width:{value * 100:.1f}%"></div></div>
                  <b>{value:.3f}</b>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_latency_bars(rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    max_latency = max(float(row["latency_ms"]) for row in rows) or 1.0
    for row in rows:
        method = str(row["method"])
        value = float(row["latency_ms"])
        width = min(100.0, value / max_latency * 100)
        st.markdown(
            f"""
            <div class="metric-line">
              <span>{method}</span>
              <div class="bar-shell"><div class="bar-fill latency-fill" style="width:{width:.1f}%"></div></div>
              <b>{value:.1f} ms</b>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _score_to_confidence(score: float) -> float:
    if score <= 0:
        return 0.0
    return round(min(1.0, score / (score + 1.0)), 3)


def _status_class(state: str) -> str:
    if state in {"siliconflow", "mock"}:
        return "status-ok"
    if state in {"missing-key", "missing-model", "unsupported-asr"}:
        return "status-warn"
    return "status-muted"


def _escape_preview(text: object) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _inject_style() -> None:
    st.markdown(
        """
        <style>
        :root {
          --paper: #f3efe6;
          --ink: #20272b;
          --muted: #667074;
          --line: #d4cbb9;
          --cyan: #0d7f83;
          --amber: #b7791f;
          --graphite: #20272b;
          --green: #34785f;
          --red: #a64d3c;
        }
        .stApp {
          background:
            linear-gradient(90deg, rgba(32,39,43,.045) 1px, transparent 1px),
            linear-gradient(0deg, rgba(32,39,43,.035) 1px, transparent 1px),
            var(--paper);
          background-size: 28px 28px;
          color: var(--ink);
        }
        .block-container {
          padding-top: 1.4rem;
          max-width: 1680px;
        }
        .topline {
          border-bottom: 2px solid var(--graphite);
          display: flex;
          justify-content: space-between;
          align-items: end;
          padding: 0 0 1rem 0;
          margin-bottom: 1.1rem;
        }
        .eyebrow {
          color: var(--amber);
          font-size: .78rem;
          font-weight: 800;
          letter-spacing: .08rem;
        }
        h1 {
          font-family: Georgia, "Times New Roman", serif;
          font-size: 2.85rem;
          line-height: 1;
          margin: .2rem 0 0 0;
          letter-spacing: 0;
        }
        .mode-pill {
          background: var(--graphite);
          color: var(--paper);
          padding: .55rem .75rem;
          border-radius: 4px;
          font-family: "Consolas", monospace;
          font-size: .85rem;
        }
        .section-title {
          margin: 1.05rem 0 .55rem 0;
          color: var(--cyan);
          font-weight: 900;
          text-transform: uppercase;
          letter-spacing: .06rem;
          border-left: 5px solid var(--amber);
          padding-left: .65rem;
        }
        .chat-shell,
        .empty-state,
        .scope-chip {
          border: 1px solid var(--line);
          border-left: 5px solid var(--graphite);
          background: rgba(255,255,255,.62);
          padding: 1rem;
          margin-bottom: .8rem;
        }
        .scope-chip {
          padding: .65rem .75rem;
        }
        .scope-chip b,
        .scope-chip span {
          display: block;
        }
        .scope-chip span {
          color: var(--muted);
          font-size: .82rem;
          margin-top: .2rem;
        }
        .chat-kicker {
          color: var(--amber);
          font-size: .72rem;
          font-weight: 900;
          letter-spacing: .08rem;
        }
        .chat-scope {
          font-family: Georgia, "Times New Roman", serif;
          font-size: 1.35rem;
          font-weight: 700;
          margin-top: .15rem;
        }
        .provider-row,
        .side-status {
          border: 1px solid rgba(255,255,255,.14);
          background: rgba(255,255,255,.09);
          display: flex;
          justify-content: space-between;
          gap: .65rem;
          padding: .5rem .6rem;
          margin: .35rem 0;
        }
        .provider-row {
          border-color: var(--line);
          background: rgba(255,255,255,.5);
        }
        .provider-row span,
        .side-status small {
          display: block;
          color: var(--muted);
          font-size: .76rem;
          overflow-wrap: anywhere;
        }
        .side-status span {
          font-weight: 800;
        }
        .status-ok {
          color: var(--green) !important;
          font-weight: 900;
        }
        .status-warn {
          color: var(--amber) !important;
          font-weight: 900;
        }
        .status-muted {
          color: var(--muted) !important;
          font-weight: 900;
        }
        .answer-meta {
          display: flex;
          flex-wrap: wrap;
          gap: .5rem;
          margin: .65rem 0;
        }
        .answer-meta span {
          background: rgba(13,127,131,.12);
          border: 1px solid rgba(13,127,131,.25);
          color: var(--cyan);
          padding: .22rem .45rem;
          font-size: .78rem;
          font-weight: 800;
        }
        .answer-text {
          border: 1px solid var(--graphite);
          background: rgba(255,255,255,.7);
          padding: 1.1rem;
          font-size: 1.04rem;
          line-height: 1.58;
          margin-top: .75rem;
        }
        .empty-state b,
        .empty-state span {
          display: block;
        }
        .empty-state span {
          color: var(--muted);
          margin-top: .35rem;
        }
        .evidence-chip {
          border: 1px solid var(--line);
          border-left: 4px solid var(--cyan);
          background: rgba(255,255,255,.56);
          padding: .65rem .75rem;
          margin: .5rem 0;
        }
        .evidence-chip b,
        .evidence-chip span {
          display: block;
        }
        .evidence-chip span {
          color: var(--muted);
          margin-top: .25rem;
          line-height: 1.45;
        }

        .chat-message {
          display: flex;
          align-items: flex-start;
          gap: .75rem;
          margin: .75rem 0;
        }
        .message-avatar {
          width: 2.15rem;
          height: 2.15rem;
          border-radius: 50%;
          background: var(--graphite);
          color: var(--paper);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: .75rem;
          font-weight: 900;
          flex: 0 0 auto;
        }
        .message-body {
          flex: 1;
          min-width: 0;
        }
        .active-evidence {
          background: rgba(183,121,31,.18);
          border: 1px solid rgba(183,121,31,.34);
          color: var(--amber);
          font-weight: 900;
          padding: .35rem .5rem;
          margin-bottom: .5rem;
        }
        .evidence-active {
          border-left-color: var(--amber) !important;
          background: rgba(183,121,31,.12) !important;
        }
        .flow-card,
        .rank-card {
          border: 1px solid var(--line);
          background: rgba(255,255,255,.62);
          padding: .65rem .7rem;
          margin: .4rem 0;
        }
        .flow-card b, .flow-card span, .flow-card em,
        .rank-card b, .rank-card span, .rank-card em {
          display: block;
        }
        .flow-card b {
          color: var(--cyan);
        }
        .flow-card span, .rank-card span {
          color: var(--muted);
          font-size: .78rem;
          overflow-wrap: anywhere;
          margin-top: .18rem;
        }
        .flow-card em, .rank-card em {
          color: var(--amber);
          font-style: normal;
          font-weight: 900;
          margin-top: .25rem;
          font-size: .78rem;
        }
        .metric-line {
          display: grid;
          grid-template-columns: 8.5rem 1fr 4.2rem;
          align-items: center;
          gap: .6rem;
          font-size: .86rem;
          margin: .35rem 0;
        }
        .bar-shell {
          height: .55rem;
          background: rgba(32,39,43,.16);
          border: 1px solid rgba(32,39,43,.2);
        }
        .bar-fill {
          height: 100%;
          background: linear-gradient(90deg, var(--cyan), var(--amber));
        }
        .latency-fill {
          background: linear-gradient(90deg, var(--amber), var(--red));
        }
        section[data-testid="stSidebar"] {
          display: none;
        }
        div[data-testid="stSidebarCollapsedControl"] {
          display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
