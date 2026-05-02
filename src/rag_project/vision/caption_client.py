"""Vision caption client interface and deterministic mock implementation."""

from __future__ import annotations

from typing import Protocol

from rag_project.schemas import VisionCaptionResponse


class VisionCaptionClient(Protocol):
    """Interface for captioning extracted PDF images."""

    def caption(self, image_path: str, nearby_text: str | None = None) -> VisionCaptionResponse:
        """Caption an image using optional nearby text."""


class MockVisionCaptionClient:
    """Offline vision mock used when no API key is configured."""

    def caption(self, image_path: str, nearby_text: str | None = None) -> VisionCaptionResponse:
        if nearby_text:
            return VisionCaptionResponse(
                caption=f"Mock caption based on nearby text: {nearby_text}"
            )
        return VisionCaptionResponse(caption="Mock image caption")
