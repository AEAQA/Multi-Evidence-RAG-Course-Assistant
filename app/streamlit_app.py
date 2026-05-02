"""Minimal Streamlit entrypoint for the RAG study assistant."""

from __future__ import annotations

import streamlit as st

from rag_project.config import load_config


def main() -> None:
    config = load_config()

    st.set_page_config(
        page_title="RAG Study Assistant",
        page_icon="R",
        layout="wide",
    )

    st.title("RAG Study Assistant")
    st.caption("Offline-first evidence retrieval dashboard.")

    st.info(
        "Milestone 0 bootstrap is installed. Ingestion, retrieval, evaluation, "
        "and evidence display will be added in later milestones."
    )

    st.write(
        {
            "APP_MODE": config.app_mode,
            "LLM_PROVIDER": config.llm_provider,
            "RERANKER_PROVIDER": config.reranker_provider,
        }
    )


if __name__ == "__main__":
    main()
