"""Provider factories for optional API-enhanced mode."""

from __future__ import annotations

from rag_project.audio.asr_client import ASRClient, MockASRClient
from rag_project.config import AppConfig
from rag_project.generation.llm_client import LLMClient, MockLLMClient
from rag_project.generation.siliconflow_client import SiliconFlowLLMClient
from rag_project.query_planning.intent_planner import (
    DeterministicIntentPlanner,
    IntentPlanner,
)
from rag_project.query_planning.siliconflow_intent_planner import (
    SiliconFlowIntentPlanner,
)
from rag_project.retrieval.reranker import MockRerankerClient, RerankerClient
from rag_project.retrieval.siliconflow_reranker import SiliconFlowRerankerClient
from rag_project.vision.caption_client import (
    MockVisionCaptionClient,
    VisionCaptionClient,
)
from rag_project.vision.siliconflow_caption_client import SiliconFlowVisionCaptionClient


def create_llm_client(config: AppConfig) -> LLMClient:
    """Create an LLM client with mock fallback as the default."""
    if _provider_enabled(config, config.llm_provider, config.llm_model):
        return SiliconFlowLLMClient(
            api_key=config.siliconflow_api_key,
            model=config.llm_model,
            base_url=config.siliconflow_base_url,
            timeout=config.api_timeout_seconds,
        )
    return MockLLMClient()


def create_intent_planner(config: AppConfig) -> IntentPlanner:
    """Create an intent planner with deterministic local fallback."""
    provider = config.intent_planner_provider.lower()
    if (
        config.app_mode == "api"
        and provider == "siliconflow"
        and bool(config.intent_planner_model)
        and config.intent_planner_model != "mock-intent-planner"
        and config.siliconflow_ready
    ):
        return SiliconFlowIntentPlanner(
            api_key=config.siliconflow_api_key,
            model=config.intent_planner_model,
            base_url=config.intent_planner_base_url,
            timeout=config.api_timeout_seconds,
            temperature=config.intent_planner_temperature,
            max_tokens=config.intent_planner_max_tokens,
        )
    return DeterministicIntentPlanner()


def create_reranker_client(config: AppConfig) -> RerankerClient:
    """Create a reranker client with mock fallback as the default."""
    if _provider_enabled(config, config.reranker_provider, config.reranker_model):
        return SiliconFlowRerankerClient(
            api_key=config.siliconflow_api_key,
            model=config.reranker_model,
            base_url=config.siliconflow_base_url,
            timeout=config.api_timeout_seconds,
        )
    return MockRerankerClient()


def create_vision_caption_client(config: AppConfig) -> VisionCaptionClient:
    """Create a vision caption client with mock fallback as the default."""
    if _provider_enabled(config, config.vision_provider, config.vision_model):
        return SiliconFlowVisionCaptionClient(
            api_key=config.siliconflow_api_key,
            model=config.vision_model,
            base_url=config.siliconflow_base_url,
            timeout=config.api_timeout_seconds,
        )
    return MockVisionCaptionClient()


def create_asr_client(config: AppConfig) -> ASRClient:
    """Create an ASR client.

    M7 keeps ASR in mock mode; real ASR is an optional later integration path.
    """
    return MockASRClient()


def _provider_enabled(config: AppConfig, provider: str, model: str) -> bool:
    return (
        config.app_mode == "api"
        and provider.lower() == "siliconflow"
        and bool(model)
        and model != "mock-llm"
        and model != "mock-reranker"
        and model != "mock-vision"
        and config.siliconflow_ready
    )
