from __future__ import annotations

from pathlib import Path
import uuid

from rag_project.config import AppConfig, load_config
from rag_project.generation.llm_client import MockLLMClient
from rag_project.generation.siliconflow_client import SiliconFlowLLMClient
from rag_project.providers import create_llm_client, create_reranker_client
from rag_project.retrieval.reranker import MockRerankerClient
from rag_project.retrieval.siliconflow_reranker import SiliconFlowRerankerClient
from rag_project.schemas import Chunk, ChunkMetadata
from rag_project.vision.caption_client import MockVisionCaptionClient
from rag_project.vision.siliconflow_caption_client import SiliconFlowVisionCaptionClient


def _chunk(chunk_id: str = "c1", text: str = "overfitting validation") -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        doc_id="doc001",
        source_file="sample.txt",
        page=1,
        type="text",
        text=text,
        metadata=ChunkMetadata(),
    )


def _test_root() -> Path:
    root = Path("pytest_runs") / f"api_providers_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_load_config_reads_dotenv_and_redacts_key_status(
    monkeypatch,
) -> None:
    env_path = _test_root() / ".env"
    env_path.write_text(
        "\n".join(
            [
                "APP_MODE=api",
                "LLM_PROVIDER=siliconflow",
                "LLM_MODEL=deepseek-ai/DeepSeek-V3",
                "SILICONFLOW_API_KEY=secret-key",
                "SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("SILICONFLOW_API_KEY", raising=False)

    config = load_config(env_path=env_path)

    assert config.app_mode == "api"
    assert config.llm_provider == "siliconflow"
    assert config.llm_model == "deepseek-ai/DeepSeek-V3"
    assert config.siliconflow_api_key == "secret-key"
    assert config.api_key_status == "set"
    assert "secret-key" not in config.safe_runtime_status().values()


def test_provider_factory_uses_mock_without_key() -> None:
    config = AppConfig(
        app_mode="api",
        llm_provider="siliconflow",
        llm_model="deepseek-ai/DeepSeek-V3",
        siliconflow_api_key="",
    )

    assert isinstance(create_llm_client(config), MockLLMClient)
    assert isinstance(create_reranker_client(config), MockRerankerClient)


def test_provider_factory_uses_siliconflow_when_configured() -> None:
    config = AppConfig(
        app_mode="api",
        llm_provider="siliconflow",
        llm_model="deepseek-ai/DeepSeek-V3",
        reranker_provider="siliconflow",
        reranker_model="BAAI/bge-reranker-v2-m3",
        siliconflow_api_key="secret-key",
    )

    assert isinstance(create_llm_client(config), SiliconFlowLLMClient)
    assert isinstance(create_reranker_client(config), SiliconFlowRerankerClient)


def test_siliconflow_llm_parses_fake_response() -> None:
    def fake_post(url, *, headers, json, timeout):
        assert url.endswith("/chat/completions")
        assert headers["Authorization"] == "Bearer secret-key"
        return {
            "choices": [
                {"message": {"content": "Evidence-grounded API answer."}}
            ]
        }

    client = SiliconFlowLLMClient(
        api_key="secret-key",
        model="deepseek-ai/DeepSeek-V3",
        post_json=fake_post,
    )

    response = client.generate_answer("What is overfitting?", [_chunk()])

    assert response.answer == "Evidence-grounded API answer."
    assert response.citations[0].chunk_id == "c1"
    assert response.insufficient_evidence is False


def test_siliconflow_llm_failure_falls_back_to_mock() -> None:
    def failing_post(url, *, headers, json, timeout):
        raise RuntimeError("network unavailable")

    client = SiliconFlowLLMClient(
        api_key="secret-key",
        model="deepseek-ai/DeepSeek-V3",
        post_json=failing_post,
    )

    response = client.generate_answer("What is overfitting?", [_chunk()])

    assert response.answer.startswith("The materials indicate")
    assert "[E1]" in response.answer
    assert "fallback" in response.retrieval_explanation.lower()


def test_siliconflow_reranker_maps_indexes_to_chunk_ids() -> None:
    chunks = [
        _chunk("c1", "general text"),
        _chunk("c2", "overfitting validation evidence"),
    ]

    def fake_post(url, *, headers, json, timeout):
        assert url.endswith("/rerank")
        assert json["documents"] == [chunk.text for chunk in chunks]
        return {"results": [{"index": 1, "relevance_score": 0.9}]}

    client = SiliconFlowRerankerClient(
        api_key="secret-key",
        model="BAAI/bge-reranker-v2-m3",
        post_json=fake_post,
    )

    results = client.rerank("overfitting", chunks)

    assert results[0].chunk_id == "c2"
    assert results[0].score == 0.9


def test_siliconflow_reranker_failure_falls_back_to_mock() -> None:
    def failing_post(url, *, headers, json, timeout):
        raise RuntimeError("network unavailable")

    client = SiliconFlowRerankerClient(
        api_key="secret-key",
        model="BAAI/bge-reranker-v2-m3",
        post_json=failing_post,
    )

    results = client.rerank(
        "overfitting",
        [_chunk("c1", "general text"), _chunk("c2", "overfitting")],
    )

    assert results[0].chunk_id == "c2"


def test_siliconflow_vision_failure_falls_back_to_mock() -> None:
    image_path = _test_root() / "image.png"
    image_path.write_bytes(b"not-a-real-image-but-no-network")

    def failing_post(url, *, headers, json, timeout):
        raise RuntimeError("network unavailable")

    client = SiliconFlowVisionCaptionClient(
        api_key="secret-key",
        model="Qwen/Qwen2.5-VL-72B-Instruct",
        post_json=failing_post,
        fallback_client=MockVisionCaptionClient(),
    )

    response = client.caption(str(image_path), nearby_text="CNN diagram")

    assert response.caption == "Mock caption based on nearby text: CNN diagram"
