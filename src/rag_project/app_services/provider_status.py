"""Safe provider status helpers for UI and smoke checks."""

from __future__ import annotations

from pydantic import BaseModel, Field

from rag_project.config import AppConfig

SILICONFLOW_COMPONENTS = {"llm", "reranker", "vision"}


class ProviderComponentStatus(BaseModel):
    """Secret-free status for one provider-backed component."""

    component: str
    provider: str
    model: str
    state: str
    detail: str


class ProviderStatus(BaseModel):
    """Secret-free runtime provider status for the workbench."""

    app_mode: str
    api_key_status: str
    base_url: str
    components: list[ProviderComponentStatus] = Field(default_factory=list)

    @property
    def by_component(self) -> dict[str, ProviderComponentStatus]:
        return {item.component: item for item in self.components}

    def as_runtime_dict(self) -> dict[str, str]:
        """Return compact values suitable for Streamlit/sidebar rendering."""
        rows = {
            "APP_MODE": self.app_mode,
            "SILICONFLOW_API_KEY": self.api_key_status,
            "SILICONFLOW_BASE_URL": self.base_url,
        }
        for item in self.components:
            prefix = item.component.upper()
            rows[f"{prefix}_PROVIDER"] = item.provider
            rows[f"{prefix}_MODEL"] = item.model
            rows[f"{prefix}_STATE"] = item.state
        return rows


def build_provider_status(config: AppConfig) -> ProviderStatus:
    """Build a UI-safe provider status object without exposing secrets."""
    components = [
        _component_status(
            component="llm",
            provider=config.llm_provider,
            model=config.llm_model,
            config=config,
        ),
        _component_status(
            component="reranker",
            provider=config.reranker_provider,
            model=config.reranker_model,
            config=config,
        ),
        _component_status(
            component="vision",
            provider=config.vision_provider,
            model=config.vision_model,
            config=config,
        ),
        _asr_status(config),
    ]
    return ProviderStatus(
        app_mode=config.app_mode,
        api_key_status=config.api_key_status,
        base_url=config.siliconflow_base_url,
        components=components,
    )


def _component_status(
    *,
    component: str,
    provider: str,
    model: str,
    config: AppConfig,
) -> ProviderComponentStatus:
    provider_name = provider.lower()
    if provider_name == "mock" or config.app_mode == "local":
        return ProviderComponentStatus(
            component=component,
            provider=provider,
            model=model,
            state="mock",
            detail="Local mock provider is active.",
        )

    if provider_name != "siliconflow":
        return ProviderComponentStatus(
            component=component,
            provider=provider,
            model=model,
            state="unsupported-provider",
            detail="Unsupported provider setting; mock fallback will be used.",
        )

    if not config.siliconflow_api_key:
        return ProviderComponentStatus(
            component=component,
            provider=provider,
            model=model,
            state="missing-key",
            detail="SiliconFlow key is missing; mock fallback will be used.",
        )

    if not model or model.startswith("mock-"):
        return ProviderComponentStatus(
            component=component,
            provider=provider,
            model=model,
            state="missing-model",
            detail="SiliconFlow model is not configured; mock fallback will be used.",
        )

    return ProviderComponentStatus(
        component=component,
        provider=provider,
        model=model,
        state="siliconflow",
        detail="SiliconFlow live path is configured with mock fallback on failure.",
    )


def _asr_status(config: AppConfig) -> ProviderComponentStatus:
    if config.asr_provider.lower() == "mock" or config.app_mode == "local":
        return ProviderComponentStatus(
            component="asr",
            provider=config.asr_provider,
            model=config.asr_model,
            state="mock",
            detail="ASR mock fallback is active; live ASR is deferred.",
        )

    return ProviderComponentStatus(
        component="asr",
        provider=config.asr_provider,
        model=config.asr_model,
        state="unsupported-asr",
        detail="ASR live path is deferred in M7-patch1; mock fallback remains active.",
    )
