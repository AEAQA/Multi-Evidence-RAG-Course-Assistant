"""Small public synthetic corpus for offline evaluation smoke tests."""

from __future__ import annotations

from rag_project.schemas import Chunk, ChunkMetadata


def build_sample_evaluation_chunks() -> list[Chunk]:
    """Return deterministic chunks referenced by data/eval/queries.jsonl."""
    texts = {
        "eval_page001_text_0001": (
            "Overfitting occurs when a model memorizes training data and fails "
            "to generalize to unseen validation examples."
        ),
        "eval_page001_text_0002": (
            "Validation data estimates generalization performance and helps "
            "select models without touching the test set."
        ),
        "eval_page001_text_0003": (
            "BM25 is a lexical retrieval method that ranks documents using "
            "term frequency, inverse document frequency, and document length."
        ),
        "eval_page001_text_0004": (
            "Dense retrieval represents queries and chunks as vectors so that "
            "semantic similarity can be measured with cosine similarity."
        ),
        "eval_page001_text_0005": (
            "Hybrid fusion combines lexical and dense rankings to improve "
            "recall when keyword and semantic signals are complementary."
        ),
        "eval_page001_text_0006": (
            "Reranking reorders candidate chunks after retrieval using a more "
            "focused relevance model or deterministic mock scorer."
        ),
        "eval_page001_text_0007": (
            "Grounded answer generation should cite retrieved evidence and "
            "avoid answering when the context is insufficient."
        ),
        "eval_page001_text_0008": (
            "Prompt injection can appear inside retrieved documents, so the "
            "system treats retrieved context as untrusted reference material."
        ),
        "eval_page001_text_0009": (
            "Recall at k measures whether at least one relevant evidence chunk "
            "appears within the top k retrieved results."
        ),
        "eval_page001_text_0010": (
            "MRR measures how early the first relevant result appears, while "
            "NDCG measures ranking quality with position discounts."
        ),
    }

    return [
        Chunk(
            chunk_id=chunk_id,
            doc_id="eval",
            source_file="sample_eval_corpus.txt",
            page=1,
            type="text",
            text=text,
            metadata=ChunkMetadata(section_title="Synthetic Evaluation Corpus"),
        )
        for chunk_id, text in texts.items()
    ]
