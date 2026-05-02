"""Optional live API smoke check for API-enhanced mode."""

from __future__ import annotations

from rag_project.config import load_config
from rag_project.generation.answer_generator import AnswerGenerator
from rag_project.providers import create_llm_client, create_reranker_client
from rag_project.retrieval.pipeline import RetrievalPipeline
from rag_project.schemas import Chunk, ChunkMetadata


def main() -> int:
    """Run a small API smoke test when SiliconFlow credentials are configured."""
    config = load_config()
    if not config.siliconflow_ready or config.app_mode != "api":
        print("API smoke skipped / using mock fallback.")
        print("Set APP_MODE=api and SILICONFLOW_API_KEY in local .env to run live smoke.")
        return 0

    chunks = [
        Chunk(
            chunk_id="smoke_page001_text_0001",
            doc_id="smoke",
            source_file="smoke.txt",
            page=1,
            type="text",
            text="Overfitting means a model fits training data but generalizes poorly.",
            metadata=ChunkMetadata(),
        )
    ]
    retrieval = RetrievalPipeline(
        chunks,
        reranker=create_reranker_client(config),
    ).search("What is overfitting?", top_k=1)
    answer = AnswerGenerator(
        llm_client=create_llm_client(config),
        max_evidence=1,
    ).generate("What is overfitting?", retrieval.reranked_results)

    print("API smoke completed.")
    print(f"LLM_PROVIDER={config.llm_provider}")
    print(f"RERANKER_PROVIDER={config.reranker_provider}")
    print(f"SILICONFLOW_API_KEY={config.api_key_status}")
    print(f"answer_preview={answer.answer[:160]}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
