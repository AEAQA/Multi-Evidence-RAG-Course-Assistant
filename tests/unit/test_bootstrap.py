from rag_project import __version__
from rag_project.config import load_config
from rag_project.evaluation.run_evaluation import main as run_evaluation
from rag_project.schemas import SUPPORTED_CHUNK_TYPES


def test_package_imports() -> None:
    assert __version__ == "0.1.0"


def test_local_mode_defaults_do_not_require_api_keys(monkeypatch) -> None:
    monkeypatch.delenv("APP_MODE", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)

    config = load_config()

    assert config.is_local
    assert config.llm_provider == "mock"


def test_chunk_type_contract_includes_future_image_aware_types() -> None:
    assert SUPPORTED_CHUNK_TYPES == ("text", "image", "table")


def test_evaluation_entrypoint_placeholder_is_available() -> None:
    assert run_evaluation() == 0
