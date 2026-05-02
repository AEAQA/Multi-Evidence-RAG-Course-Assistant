"""Streamlit Evidence Workbench for the offline-first RAG study assistant."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st

from rag_project.app_services.corpus_service import build_sample_corpus_summary
from rag_project.app_services.provider_status import ProviderStatus, build_provider_status
from rag_project.app_services.query_service import MethodDiagnostic, WorkbenchState
from rag_project.config import load_config
from rag_project.schemas import Chunk, RetrievalResult
from rag_project.ui.dashboard_data import (
    build_sample_dashboard_state,
    load_or_create_evaluation_reports,
)


DEFAULT_QUERY = "What is overfitting and why does validation data matter?"


def main() -> None:
    """Run the Streamlit app."""
    config = load_config()
    provider_status = build_provider_status(config)

    st.set_page_config(
        page_title="RAG Study Assistant",
        page_icon="R",
        layout="wide",
    )
    _inject_style()
    _render_header(config.app_mode)

    page = st.sidebar.radio(
        "Workspace",
        ["Study Query Workbench", "Evaluation Dashboard"],
        label_visibility="collapsed",
    )
    _render_sidebar_status(provider_status)

    if page == "Study Query Workbench":
        _render_study_query_workbench(provider_status)
    else:
        _render_evaluation_dashboard()


def _render_header(app_mode: str) -> None:
    st.markdown(
        f"""
        <section class="topline">
          <div>
            <div class="eyebrow">OFFLINE-FIRST RAG WORKSTATION</div>
            <h1>Evidence Workbench</h1>
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


def _render_study_query_workbench(provider_status: ProviderStatus) -> None:
    summary = build_sample_corpus_summary()
    _ensure_workbench_session()

    left, center, right = st.columns([0.82, 1.42, 1.18], gap="large")

    with left:
        _render_corpus_panel(summary)
        _render_provider_status_panel(provider_status)

    with center:
        _render_query_panel()

    run_clicked = st.session_state.pop("run_workbench_query", False)
    query = st.session_state.get("workbench_query", "")
    top_k = int(st.session_state.get("workbench_top_k", 5))

    if _should_run_query(run_clicked, query):
        with st.spinner("Retrieving evidence, reranking candidates, and generating a grounded answer..."):
            try:
                st.session_state["last_workbench_state"] = build_sample_dashboard_state(
                    query,
                    top_k=top_k,
                    config=load_config(),
                )
            except Exception as exc:  # pragma: no cover - defensive Streamlit fallback
                st.session_state["last_workbench_error"] = str(exc)

    state = st.session_state.get("last_workbench_state")
    error = st.session_state.pop("last_workbench_error", None)

    with center:
        if error:
            st.error(f"Workbench query failed. Mock/local fallback remains available. Error: {error}")
        if isinstance(state, WorkbenchState):
            _render_answer_panel(state)
        else:
            _render_empty_workbench()

    with right:
        if isinstance(state, WorkbenchState):
            _render_evidence_panel(state)
            _render_diagnostics_panel(state)
        else:
            _render_evidence_placeholder()


def _ensure_workbench_session() -> None:
    if "workbench_query" not in st.session_state:
        st.session_state["workbench_query"] = DEFAULT_QUERY
    if "workbench_top_k" not in st.session_state:
        st.session_state["workbench_top_k"] = 5


def _render_corpus_panel(summary) -> None:
    st.markdown('<div class="section-title">Corpus Scope</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="workbench-panel">
          <div class="panel-kicker">ACTIVE CORPUS</div>
          <h3>{_escape_preview(summary.corpus_name)}</h3>
          <div class="stat-grid">
            <div><b>{summary.chunk_count}</b><span>chunks</span></div>
            <div><b>{len(summary.source_files)}</b><span>sources</span></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Chunk types")
    for chunk_type, count in summary.type_counts.items():
        st.markdown(f"`{chunk_type}` {count}")

    with st.expander("Sample questions", expanded=True):
        for index, question in enumerate(summary.sample_questions, start=1):
            if st.button(question, key=f"sample_question_{index}", use_container_width=True):
                st.session_state["workbench_query"] = question


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
        st.caption(item.detail)
    st.info("ASR live path is planned/deferred in M7-patch1; mock fallback remains active.")


def _render_query_panel() -> None:
    st.markdown('<div class="section-title">Query And Answer</div>', unsafe_allow_html=True)
    st.text_area(
        "Study question",
        key="workbench_query",
        height=115,
        placeholder="Ask a question about the selected study corpus...",
    )
    st.slider(
        "Evidence Top-k",
        min_value=1,
        max_value=5,
        key="workbench_top_k",
    )
    run_clicked = st.button("Run evidence query", type="primary", use_container_width=True)
    if run_clicked:
        st.session_state["run_workbench_query"] = True


def _render_answer_panel(state: WorkbenchState) -> None:
    st.markdown(
        f"""
        <div class="answer-meta">
          <span>{len(state.answer.evidence_chunks)} evidence chunks</span>
          <span>{state.timing_ms.get("total", 0):.1f} ms total</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if state.answer.insufficient_evidence:
        st.warning(state.answer.answer)
    else:
        st.markdown('<div class="answer-band">Grounded answer</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="answer-text">{_escape_preview(state.answer.answer)}</div>', unsafe_allow_html=True)

    if state.answer.citations:
        st.markdown("#### Citations")
        st.dataframe(
            [
                {
                    "chunk_id": citation.chunk_id,
                    "source": citation.source_file,
                    "page": citation.page,
                }
                for citation in state.answer.citations
            ],
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Next actions", expanded=True):
        for suggestion in state.suggestions:
            st.markdown(f"- {suggestion}")


def _render_empty_workbench() -> None:
    st.markdown(
        """
        <div class="empty-state">
          <b>No query has been run in this session.</b>
          <span>Choose a sample question or write your own, then click Run evidence query.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_evidence_placeholder() -> None:
    st.markdown('<div class="section-title">Evidence</div>', unsafe_allow_html=True)
    st.info("Evidence cards will appear here after an explicit query run.")
    st.markdown('<div class="section-title">Diagnostics</div>', unsafe_allow_html=True)
    st.info("Retrieval method confidence and result tabs will appear here.")


def _render_evidence_panel(state: WorkbenchState) -> None:
    st.markdown('<div class="section-title">Evidence</div>', unsafe_allow_html=True)
    if not state.answer.evidence_chunks:
        st.warning("Insufficient evidence: no reranked chunks were selected.")
        return

    for index, chunk in enumerate(state.answer.evidence_chunks, start=1):
        label = f"#{index} {chunk.type} | {chunk.source_file} p.{chunk.page} | {chunk.chunk_id}"
        with st.expander(label, expanded=index <= 2):
            st.markdown(f'<div class="chunk-text">{_escape_preview(chunk.text)}</div>', unsafe_allow_html=True)
            _render_chunk_metadata(chunk)
            _render_chunk_media(chunk)


def _render_diagnostics_panel(state: WorkbenchState) -> None:
    st.markdown('<div class="section-title">Diagnostics</div>', unsafe_allow_html=True)
    for diagnostic in state.diagnostics:
        with st.expander(
            f"{diagnostic.method.upper()} | {diagnostic.confidence_label} | {diagnostic.result_count} results",
            expanded=diagnostic.method == "reranked",
        ):
            st.progress(diagnostic.confidence)
            st.caption(diagnostic.recommendation)

    tabs = st.tabs(["BM25", "Dense", "Fusion", "Reranked"])
    result_groups = [
        state.retrieval.bm25_results,
        state.retrieval.dense_results,
        state.retrieval.fusion_results,
        state.retrieval.reranked_results,
    ]
    for tab, results in zip(tabs, result_groups):
        with tab:
            st.dataframe(_results_to_frame(results), use_container_width=True, hide_index=True)

    with st.expander("Debug / Metadata", expanded=False):
        st.write(
            {
                "query": state.query,
                "provider_status": state.provider_status.as_runtime_dict(),
                "timing_ms": state.timing_ms,
                "retrieval_explanation": state.answer.retrieval_explanation,
                "diagnostics": _diagnostics_to_rows(state.diagnostics),
            }
        )


def _render_evaluation_dashboard() -> None:
    st.markdown(
        '<div class="section-title">Evaluation Dashboard</div>',
        unsafe_allow_html=True,
    )
    if st.button("Run local evaluation", type="primary"):
        with st.spinner("Running local retrieval evaluation..."):
            reports = load_or_create_evaluation_reports()
    else:
        reports = load_or_create_evaluation_reports()

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
                "chunk_id": result.chunk_id,
                "source": result.chunk.source_file,
                "page": result.chunk.page,
                "type": result.chunk.type,
                "preview": result.chunk.text[:160],
                "image_path": metadata.image_path or "",
                "caption": metadata.caption or "",
                "bbox": metadata.bbox or "",
            }
        )
    return rows


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


def _render_chunk_metadata(chunk: Chunk) -> None:
    rows = _chunk_metadata_rows(chunk)
    if not rows:
        return
    st.markdown(
        "<div class=\"metadata-grid\">"
        + "".join(
            f"<div><b>{_escape_preview(label)}</b><span>{_escape_preview(value)}</span></div>"
            for label, value in rows
        )
        + "</div>",
        unsafe_allow_html=True,
    )


def _render_chunk_media(chunk: Chunk) -> None:
    image_path = chunk.metadata.image_path
    if not image_path:
        return
    path = Path(image_path)
    if path.exists():
        st.image(str(path), caption=chunk.metadata.caption or chunk.chunk_id, width=220)


def _chunk_metadata_rows(chunk: Chunk) -> list[tuple[str, str]]:
    metadata = chunk.metadata
    rows = []
    if metadata.image_path:
        rows.append(("image_path", metadata.image_path))
    if metadata.bbox:
        rows.append(("bbox", ", ".join(f"{value:.1f}" for value in metadata.bbox)))
    if metadata.caption:
        rows.append(("caption", metadata.caption))
    if metadata.nearby_text:
        rows.append(("nearby_text", metadata.nearby_text[:220]))
    if metadata.table_html:
        rows.append(("table", metadata.table_html[:220]))
    return rows


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
          max-width: 1480px;
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
          font-size: 2.7rem;
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
        .workbench-panel,
        .empty-state {
          border: 1px solid var(--line);
          border-left: 5px solid var(--graphite);
          background: rgba(255,255,255,.55);
          padding: .85rem;
        }
        .panel-kicker {
          color: var(--amber);
          font-size: .72rem;
          font-weight: 900;
          letter-spacing: .08rem;
        }
        .workbench-panel h3 {
          font-size: 1.05rem;
          margin: .25rem 0 .75rem 0;
        }
        .stat-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: .45rem;
        }
        .stat-grid div {
          border-top: 1px solid var(--line);
          padding-top: .4rem;
        }
        .stat-grid b {
          display: block;
          font-size: 1.35rem;
        }
        .stat-grid span {
          color: var(--muted);
          font-size: .8rem;
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
          gap: .5rem;
          margin: .75rem 0 .25rem 0;
        }
        .answer-meta span {
          background: rgba(13,127,131,.12);
          border: 1px solid rgba(13,127,131,.25);
          color: var(--cyan);
          padding: .22rem .45rem;
          font-size: .78rem;
          font-weight: 800;
        }
        .answer-band {
          margin-top: .75rem;
          background: var(--graphite);
          color: var(--paper);
          padding: .5rem .75rem;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: .05rem;
        }
        .answer-text {
          border: 1px solid var(--graphite);
          background: rgba(255,255,255,.56);
          padding: 1rem;
          font-size: 1.02rem;
          line-height: 1.55;
        }
        .empty-state b,
        .empty-state span {
          display: block;
        }
        .empty-state span {
          color: var(--muted);
          margin-top: .35rem;
        }
        .chunk-text {
          color: var(--ink);
          line-height: 1.45;
          background: rgba(255,255,255,.5);
          border-left: 4px solid var(--cyan);
          padding: .65rem .75rem;
        }
        .metadata-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr));
          gap: .35rem .65rem;
          margin: .65rem 0;
          font-size: .82rem;
        }
        .metadata-grid div {
          border: 1px solid var(--line);
          background: rgba(255,255,255,.42);
          padding: .35rem .45rem;
        }
        .metadata-grid b {
          color: var(--amber);
          display: block;
          font-family: "Consolas", monospace;
          font-size: .74rem;
        }
        .metadata-grid span {
          color: var(--ink);
          overflow-wrap: anywhere;
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
        div[data-testid="stSidebar"] {
          background: #222a2e;
          color: var(--paper);
        }
        div[data-testid="stSidebar"] * {
          color: inherit;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
