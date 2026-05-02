"""Configuration helpers for local/offline-first execution."""

from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_APP_MODE = "local"
DEFAULT_LLM_PROVIDER = "mock"
DEFAULT_RERANKER_PROVIDER = "mock"
DEFAULT_ASR_PROVIDER = "mock"
DEFAULT_VISION_PROVIDER = "mock"


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration loaded from environment variables."""

    app_mode: str = DEFAULT_APP_MODE
    llm_provider: str = DEFAULT_LLM_PROVIDER
    reranker_provider: str = DEFAULT_RERANKER_PROVIDER
    asr_provider: str = DEFAULT_ASR_PROVIDER
    vision_provider: str = DEFAULT_VISION_PROVIDER

    @property
    def is_local(self) -> bool:
        return self.app_mode == "local"


def load_config() -> AppConfig:
    """Load configuration without requiring secrets in local mode."""
    return AppConfig(
        app_mode=os.getenv("APP_MODE", DEFAULT_APP_MODE),
        llm_provider=os.getenv("LLM_PROVIDER", DEFAULT_LLM_PROVIDER),
        reranker_provider=os.getenv("RERANKER_PROVIDER", DEFAULT_RERANKER_PROVIDER),
        asr_provider=os.getenv("ASR_PROVIDER", DEFAULT_ASR_PROVIDER),
        vision_provider=os.getenv("VISION_PROVIDER", DEFAULT_VISION_PROVIDER),
    )
