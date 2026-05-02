from rag_project.app_services.provider_status import build_provider_status
from rag_project.config import AppConfig


def test_provider_status_reports_local_mock_state() -> None:
    status = build_provider_status(AppConfig())

    assert status.app_mode == "local"
    assert status.api_key_status == "missing"
    assert status.by_component["llm"].state == "mock"
    assert status.by_component["reranker"].state == "mock"
    assert status.by_component["vision"].state == "mock"
    assert status.by_component["asr"].state == "mock"


def test_provider_status_reports_siliconflow_key_set_without_exposing_key() -> None:
    config = AppConfig(
        app_mode="api",
        llm_provider="siliconflow",
        llm_model="deepseek-ai/DeepSeek-V3",
        reranker_provider="siliconflow",
        reranker_model="BAAI/bge-reranker-v2-m3",
        siliconflow_api_key="secret-key",
    )

    status = build_provider_status(config)
    dumped = str(status.model_dump())

    assert status.api_key_status == "set"
    assert status.by_component["llm"].state == "siliconflow"
    assert status.by_component["reranker"].state == "siliconflow"
    assert "secret-key" not in dumped


def test_provider_status_reports_missing_key_fallback() -> None:
    config = AppConfig(
        app_mode="api",
        llm_provider="siliconflow",
        llm_model="deepseek-ai/DeepSeek-V3",
        siliconflow_api_key="",
    )

    status = build_provider_status(config)

    assert status.by_component["llm"].state == "missing-key"
    assert "mock fallback" in status.by_component["llm"].detail.lower()


def test_provider_status_marks_non_mock_asr_as_deferred() -> None:
    config = AppConfig(
        app_mode="api",
        asr_provider="siliconflow",
        asr_model="FunAudioLLM/SenseVoiceSmall",
        siliconflow_api_key="secret-key",
    )

    status = build_provider_status(config)

    assert status.by_component["asr"].state == "unsupported-asr"
    assert "deferred" in status.by_component["asr"].detail.lower()
