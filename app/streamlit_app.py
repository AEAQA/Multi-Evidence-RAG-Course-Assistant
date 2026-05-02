"""Streamlit MVP dashboard for the offline-first RAG study assistant."""

from __future__ import annotations

import streamlit as st

from rag_project.config import load_config
from rag_project.evaluation.sample_corpus import build_sample_evaluation_chunks
from rag_project.schemas import RetrievalResult
from rag_project.ui.dashboard_data import (
    build_sample_dashboard_state,
    load_or_create_evaluation_reports,
)


DEFAULT_QUERY = "What is overfitting and why does validation data matter?"


def main() -> None:
    """Run the Streamlit app."""
    config = load_config()

    st.set_page_config(
        page_title="RAG Study Assistant",
        page_icon="R",
        layout="wide",
    )
    _inject_style()
    _render_header(config.app_mode)

    page = st.sidebar.radio(
        "Workspace",
        ["RAG Assistant", "Evaluation Dashboard"],
        label_visibility="collapsed",
    )
    _render_sidebar_status(config)

    if page == "RAG Assistant":
        _render_rag_assistant()
    else:
        _render_evaluation_dashboard()


def _render_header(app_mode: str) -> None:
    st.markdown(
        f"""
        <section class="topline">
          <div>
            <div class="eyebrow">OFFLINE-FIRST RAG WORKSTATION</div>
            <h1>Evidence Retrieval Console</h1>
          </div>
          <div class="mode-pill">APP_MODE={app_mode}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar_status(config) -> None:
    st.sidebar.markdown("### Runtime")
    st.sidebar.code(
        "\n".join(
            [
                f"APP_MODE={config.app_mode}",
                f"LLM_PROVIDER={config.llm_provider}",
                f"RERANKER_PROVIDER={config.reranker_provider}",
                f"ASR_PROVIDER={config.asr_provider}",
                f"VISION_PROVIDER={config.vision_provider}",
            ]
        )
    )
    st.sidebar.markdown("### Corpus")
    st.sidebar.metric("sample chunks", len(build_sample_evaluation_chunks()))


def _render_rag_assistant() -> None:
    st.markdown('<div class="section-title">RAG Assistant</div>', unsafe_allow_html=True)
    query = st.text_input("Query", value=DEFAULT_QUERY)
    top_k = st.slider("Top-k evidence", min_value=1, max_value=5, value=5)

    if st.button("Run local retrieval", type="primary") or query:
        state = build_sample_dashboard_state(query, top_k=top_k)
        _render_answer(state.answer.answer, state.answer.insufficient_evidence)
        _render_evidence(state.answer.evidence_chunks)
        _render_retrieval_process(state.retrieval)
        with st.expander("Debug / Metadata", expanded=False):
            st.write(
                {
                    "query": state.query,
                    "retrieval_explanation": state.answer.retrieval_explanation,
                    "citations": [citation.model_dump() for citation in state.answer.citations],
                }
            )


def _render_answer(answer: str, insufficient_evidence: bool) -> None:
    if insufficient_evidence:
        st.warning(answer)
    else:
        st.markdown('<div class="answer-band">Final grounded answer</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="answer-text">{answer}</div>', unsafe_allow_html=True)


def _render_evidence(chunks) -> None:
    st.markdown('<div class="section-title">Evidence</div>', unsafe_allow_html=True)
    if not chunks:
        st.info("No evidence selected.")
        return

    for index, chunk in enumerate(chunks, start=1):
        st.markdown(
            f"""
            <article class="evidence-row">
              <div class="rank-block">{index}</div>
              <div>
                <div class="chunk-meta">{chunk.source_file} · page {chunk.page} · {chunk.type} · {chunk.chunk_id}</div>
                <div class="chunk-text">{_escape_preview(chunk.text)}</div>
              </div>
            </article>
            """,
            unsafe_allow_html=True,
        )


def _render_retrieval_process(retrieval) -> None:
    st.markdown('<div class="section-title">Retrieval Process</div>', unsafe_allow_html=True)
    tabs = st.tabs(["BM25", "Dense", "Fusion", "Reranked"])
    result_groups = [
        retrieval.bm25_results,
        retrieval.dense_results,
        retrieval.fusion_results,
        retrieval.reranked_results,
    ]
    for tab, results in zip(tabs, result_groups):
        with tab:
            st.dataframe(_results_to_frame(results), use_container_width=True, hide_index=True)


def _render_evaluation_dashboard() -> None:
    st.markdown(
        '<div class="section-title">Evaluation Dashboard</div>',
        unsafe_allow_html=True,
    )
    if st.button("Run local evaluation", type="primary"):
        reports = load_or_create_evaluation_reports()
    else:
        reports = load_or_create_evaluation_reports()

    summary = _summarize_metrics(reports.metrics)
    latency_summary = _summarize_latency(reports.latency)

    st.dataframe(summary, use_container_width=True, hide_index=True)

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("#### Recall@k")
        _render_metric_bars(summary, ["recall@1", "recall@3", "recall@5"])
    with col_right:
        st.markdown("#### Ranking quality")
        _render_metric_bars(summary, ["mrr@5", "ndcg@5"])

    st.markdown('<div class="section-title">Latency</div>', unsafe_allow_html=True)
    st.dataframe(latency_summary, use_container_width=True, hide_index=True)

    with st.expander("Error case viewer", expanded=True):
        st.markdown(reports.error_cases_markdown)


def _results_to_frame(results: list[RetrievalResult]) -> list[dict[str, object]]:
    rows = []
    for result in results:
        rows.append(
            {
                "rank": result.rank,
                "score": round(result.score, 4),
                "chunk_id": result.chunk_id,
                "source": result.chunk.source_file,
                "page": result.chunk.page,
                "type": result.chunk.type,
                "preview": result.chunk.text[:160],
            }
        )
    return pd.DataFrame(rows)


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


def _render_metric_bars(rows: list[dict[str, object]], metrics: list[str]) -> None:
    for row in rows:
        method = str(row["method"])
        for metric in metrics:
            value = float(row[metric])
            st.markdown(
                f"""
                <div class="metric-line">
                  <span>{method} · {metric}</span>
                  <div class="bar-shell"><div class="bar-fill" style="width:{value * 100:.1f}%"></div></div>
                  <b>{value:.3f}</b>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _escape_preview(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _inject_style() -> None:
    st.markdown(
        """
        <style>
        :root {
          --paper: #f4f1e8;
          --ink: #1f2528;
          --muted: #667074;
          --line: #d8d2c4;
          --cyan: #0f8b8d;
          --amber: #bd7b19;
          --graphite: #20272b;
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
          padding-top: 2rem;
          max-width: 1280px;
        }
        .topline {
          border-bottom: 2px solid var(--graphite);
          display: flex;
          justify-content: space-between;
          align-items: end;
          padding: 0 0 1rem 0;
          margin-bottom: 1.25rem;
        }
        .eyebrow {
          color: var(--amber);
          font-size: .78rem;
          font-weight: 800;
          letter-spacing: .08rem;
        }
        h1 {
          font-family: Georgia, "Times New Roman", serif;
          font-size: 3rem;
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
          margin: 1.2rem 0 .55rem 0;
          color: var(--cyan);
          font-weight: 900;
          text-transform: uppercase;
          letter-spacing: .06rem;
          border-left: 5px solid var(--amber);
          padding-left: .65rem;
        }
        .answer-band {
          margin-top: 1rem;
          background: var(--graphite);
          color: var(--paper);
          padding: .5rem .75rem;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: .05rem;
        }
        .answer-text {
          border: 1px solid var(--graphite);
          background: rgba(255,255,255,.46);
          padding: 1rem;
          font-size: 1.04rem;
          line-height: 1.55;
        }
        .evidence-row {
          display: grid;
          grid-template-columns: 3rem 1fr;
          gap: .85rem;
          border: 1px solid var(--line);
          border-left: 5px solid var(--cyan);
          background: rgba(255,255,255,.56);
          padding: .8rem;
          margin-bottom: .6rem;
        }
        .rank-block {
          background: var(--amber);
          color: white;
          height: 2.2rem;
          width: 2.2rem;
          display: grid;
          place-items: center;
          font-weight: 900;
          border-radius: 3px;
        }
        .chunk-meta {
          color: var(--muted);
          font-family: "Consolas", monospace;
          font-size: .82rem;
          margin-bottom: .25rem;
        }
        .chunk-text {
          color: var(--ink);
          line-height: 1.45;
        }
        .metric-line {
          display: grid;
          grid-template-columns: 8.5rem 1fr 3.5rem;
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
