from rag_project.audio.asr_client import MockASRClient
from rag_project.generation.llm_client import MockLLMClient
from rag_project.retrieval.reranker import MockRerankerClient
from rag_project.schemas import Chunk, ChunkMetadata
from rag_project.vision.caption_client import MockVisionCaptionClient


def _chunk(chunk_id: str, text: str) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        doc_id="doc001",
        source_file="sample.txt",
        page=1,
        type="text",
        text=text,
        metadata=ChunkMetadata(),
    )


def test_mock_llm_uses_evidence_and_citations() -> None:
    chunk = _chunk("doc001_page001_text_0001", "Overfitting is poor generalization.")

    response = MockLLMClient().generate_answer("What is overfitting?", [chunk])

    assert response.insufficient_evidence is False
    assert "Overfitting" in response.answer
    assert response.citations[0].chunk_id == chunk.chunk_id


def test_mock_llm_reports_insufficient_evidence() -> None:
    response = MockLLMClient().generate_answer("What is overfitting?", [])

    assert response.insufficient_evidence is True
    assert response.citations == []


def test_mock_reranker_is_deterministic() -> None:
    candidates = [
        _chunk("c1", "general text"),
        _chunk("c2", "overfitting validation overfitting"),
    ]

    results = MockRerankerClient().rerank("overfitting", candidates)

    assert [result.chunk_id for result in results] == ["c2", "c1"]
    assert [result.rank for result in results] == [1, 2]


def test_mock_asr_and_vision_clients_are_offline() -> None:
    assert MockASRClient().transcribe("query.wav").text == "mock transcribed question"
    assert (
        MockVisionCaptionClient()
        .caption("figure.png", nearby_text="CNN architecture diagram")
        .caption
        == "Mock caption based on nearby text: CNN architecture diagram"
    )
