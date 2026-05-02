from rag_project.retrieval.bm25_retriever import BM25Retriever
from rag_project.retrieval.dense_retriever import FakeDenseRetriever
from rag_project.retrieval.fusion import reciprocal_rank_fusion
from rag_project.retrieval.pipeline import RetrievalPipeline
from rag_project.schemas import Chunk, ChunkMetadata, RetrievalResult


def _chunk(chunk_id: str, text: str) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        doc_id="doc001",
        source_file="lecture.txt",
        page=1,
        type="text",
        text=text,
        metadata=ChunkMetadata(),
    )


def _chunks() -> list[Chunk]:
    return [
        _chunk("c1", "overfitting validation generalization model"),
        _chunk("c2", "neural network dense retrieval embeddings"),
        _chunk("c3", "course logistics office hours grading"),
    ]


def test_bm25_orders_matching_chunks_and_respects_top_k() -> None:
    retriever = BM25Retriever(_chunks())

    results = retriever.search("overfitting validation", top_k=2)

    assert [result.chunk_id for result in results] == ["c1", "c2"]
    assert [result.rank for result in results] == [1, 2]
    assert all(result.method == "bm25" for result in results)


def test_bm25_handles_empty_corpus_and_non_positive_top_k() -> None:
    retriever = BM25Retriever([])

    assert retriever.search("anything", top_k=5) == []
    assert BM25Retriever(_chunks()).search("anything", top_k=0) == []


def test_fake_dense_retriever_is_deterministic_and_offline() -> None:
    retriever = FakeDenseRetriever(_chunks(), dimensions=64)

    first = retriever.search("dense retrieval embeddings", top_k=2)
    second = retriever.search("dense retrieval embeddings", top_k=2)

    assert [result.chunk_id for result in first] == [result.chunk_id for result in second]
    assert first[0].chunk_id == "c2"
    assert all(result.method == "dense" for result in first)


def test_fusion_merges_duplicate_chunks_and_assigns_stable_ranks() -> None:
    chunks = _chunks()
    bm25 = [
        RetrievalResult(chunk_id="c1", score=10.0, rank=1, method="bm25", chunk=chunks[0]),
        RetrievalResult(chunk_id="c2", score=4.0, rank=2, method="bm25", chunk=chunks[1]),
    ]
    dense = [
        RetrievalResult(chunk_id="c2", score=0.9, rank=1, method="dense", chunk=chunks[1]),
        RetrievalResult(chunk_id="c3", score=0.7, rank=2, method="dense", chunk=chunks[2]),
    ]

    fused = reciprocal_rank_fusion([bm25, dense], top_k=3, k=60)

    assert [result.chunk_id for result in fused] == ["c2", "c1", "c3"]
    assert [result.rank for result in fused] == [1, 2, 3]
    assert all(result.method == "fusion" for result in fused)


def test_retrieval_pipeline_returns_all_m2_baselines() -> None:
    pipeline = RetrievalPipeline(_chunks())

    output = pipeline.search("overfitting validation", top_k=2)

    assert output.bm25_results[0].chunk_id == "c1"
    assert output.dense_results
    assert output.fusion_results
    assert output.reranked_results
    assert all(result.method == "reranked" for result in output.reranked_results)
