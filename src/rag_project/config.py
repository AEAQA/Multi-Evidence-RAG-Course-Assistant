"""Configuration helpers for local/offline-first execution."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


DEFAULT_APP_MODE = "local"
DEFAULT_LLM_PROVIDER = "mock"
DEFAULT_RERANKER_PROVIDER = "mock"
DEFAULT_ASR_PROVIDER = "mock"
DEFAULT_VISION_PROVIDER = "mock"
DEFAULT_INTENT_PLANNER_PROVIDER = "mock"
DEFAULT_LLM_MODEL = "mock-llm"
DEFAULT_RERANKER_MODEL = "mock-reranker"
DEFAULT_ASR_MODEL = "mock-asr"
DEFAULT_VISION_MODEL = "mock-vision"
DEFAULT_INTENT_PLANNER_MODEL = "mock-intent-planner"
DEFAULT_INTENT_PLANNER_TEMPERATURE = 0.0
DEFAULT_INTENT_PLANNER_MAX_TOKENS = 800
DEFAULT_SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
DEFAULT_API_TIMEOUT_SECONDS = 90.0


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration loaded from environment variables."""

    app_mode: str = DEFAULT_APP_MODE
    llm_provider: str = DEFAULT_LLM_PROVIDER
    reranker_provider: str = DEFAULT_RERANKER_PROVIDER
    asr_provider: str = DEFAULT_ASR_PROVIDER
    vision_provider: str = DEFAULT_VISION_PROVIDER
    intent_planner_provider: str = DEFAULT_INTENT_PLANNER_PROVIDER
    llm_model: str = DEFAULT_LLM_MODEL
    reranker_model: str = DEFAULT_RERANKER_MODEL
    asr_model: str = DEFAULT_ASR_MODEL
    vision_model: str = DEFAULT_VISION_MODEL
    intent_planner_model: str = DEFAULT_INTENT_PLANNER_MODEL
    intent_planner_base_url: str = DEFAULT_SILICONFLOW_BASE_URL
    intent_planner_temperature: float = DEFAULT_INTENT_PLANNER_TEMPERATURE
    intent_planner_max_tokens: int = DEFAULT_INTENT_PLANNER_MAX_TOKENS
    siliconflow_api_key: str = field(default="", repr=False)
    siliconflow_base_url: str = DEFAULT_SILICONFLOW_BASE_URL
    api_timeout_seconds: float = DEFAULT_API_TIMEOUT_SECONDS

    @property
    def is_local(self) -> bool:
        return self.app_mode == "local"

    @property
    def api_key_status(self) -> str:
        return "set" if self.siliconflow_api_key else "missing"

    @property
    def siliconflow_ready(self) -> bool:
        return bool(self.siliconflow_api_key and self.siliconflow_base_url)

    def safe_runtime_status(self) -> dict[str, str]:
        """Return UI/log-safe runtime config without exposing secrets."""
        return {
            "APP_MODE": self.app_mode,
            "LLM_PROVIDER": self.llm_provider,
            "LLM_MODEL": self.llm_model,
            "RERANKER_PROVIDER": self.reranker_provider,
            "RERANKER_MODEL": self.reranker_model,
            "ASR_PROVIDER": self.asr_provider,
            "ASR_MODEL": self.asr_model,
            "VISION_PROVIDER": self.vision_provider,
            "VISION_MODEL": self.vision_model,
            "INTENT_PLANNER_PROVIDER": self.intent_planner_provider,
            "INTENT_PLANNER_MODEL": self.intent_planner_model,
            "SILICONFLOW_API_KEY": self.api_key_status,
            "SILICONFLOW_BASE_URL": self.siliconflow_base_url,
        }


def load_config(
    env_path: str | Path | None = None,
    *,
    load_env_file: bool = True,
) -> AppConfig:
    """Load configuration without requiring secrets in local mode."""
    if load_env_file:
        if env_path is None:
            load_dotenv()
        else:
            load_dotenv(dotenv_path=env_path, override=True)

    return AppConfig(
        app_mode=os.getenv("APP_MODE", DEFAULT_APP_MODE),
        llm_provider=os.getenv("LLM_PROVIDER", DEFAULT_LLM_PROVIDER),
        reranker_provider=os.getenv("RERANKER_PROVIDER", DEFAULT_RERANKER_PROVIDER),
        asr_provider=os.getenv("ASR_PROVIDER", DEFAULT_ASR_PROVIDER),
        vision_provider=os.getenv("VISION_PROVIDER", DEFAULT_VISION_PROVIDER),
        intent_planner_provider=os.getenv(
            "INTENT_PLANNER_PROVIDER", DEFAULT_INTENT_PLANNER_PROVIDER
        ),
        llm_model=os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL),
        reranker_model=os.getenv("RERANKER_MODEL", DEFAULT_RERANKER_MODEL),
        asr_model=os.getenv("ASR_MODEL", DEFAULT_ASR_MODEL),
        vision_model=os.getenv("VISION_MODEL", DEFAULT_VISION_MODEL),
        intent_planner_model=os.getenv(
            "INTENT_PLANNER_MODEL", DEFAULT_INTENT_PLANNER_MODEL
        ),
        intent_planner_base_url=os.getenv(
            "INTENT_PLANNER_BASE_URL",
            os.getenv("SILICONFLOW_BASE_URL", DEFAULT_SILICONFLOW_BASE_URL),
        ).rstrip("/"),
        intent_planner_temperature=_float_env(
            "INTENT_PLANNER_TEMPERATURE", DEFAULT_INTENT_PLANNER_TEMPERATURE
        ),
        intent_planner_max_tokens=_int_env(
            "INTENT_PLANNER_MAX_TOKENS", DEFAULT_INTENT_PLANNER_MAX_TOKENS
        ),
        siliconflow_api_key=os.getenv("SILICONFLOW_API_KEY", ""),
        siliconflow_base_url=os.getenv(
            "SILICONFLOW_BASE_URL", DEFAULT_SILICONFLOW_BASE_URL
        ).rstrip("/"),
        api_timeout_seconds=_float_env(
            "API_TIMEOUT_SECONDS", DEFAULT_API_TIMEOUT_SECONDS
        ),
    )


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default
