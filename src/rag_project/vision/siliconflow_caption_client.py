"""Optional SiliconFlow vision caption client with mock fallback."""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import Any, Callable

from rag_project.http_client import post_json as default_post_json
from rag_project.schemas import VisionCaptionResponse
from rag_project.vision.caption_client import (
    MockVisionCaptionClient,
    VisionCaptionClient,
)

PostJson = Callable[..., dict[str, Any]]


class SiliconFlowVisionCaptionClient:
    """Best-effort SiliconFlow VLM caption client."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = "https://api.siliconflow.cn/v1",
        timeout: float = 30.0,
        fallback_client: VisionCaptionClient | None = None,
        post_json: PostJson = default_post_json,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.fallback_client = fallback_client or MockVisionCaptionClient()
        self.post_json = post_json

    def caption(
        self, image_path: str, nearby_text: str | None = None
    ) -> VisionCaptionResponse:
        """Caption an image, falling back to the mock caption client on failure."""
        try:
            image_url = _image_to_data_url(image_path)
            data = self.post_json(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        "Caption this PDF figure for retrieval. "
                                        f"Nearby text: {nearby_text or '<none>'}"
                                    ),
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": image_url},
                                },
                            ],
                        }
                    ],
                    "temperature": 0,
                },
                timeout=self.timeout,
            )
            caption = _extract_chat_text(data)
            if not caption:
                raise ValueError("SiliconFlow response did not include caption text")
            return VisionCaptionResponse(caption=caption)
        except Exception:
            return self.fallback_client.caption(image_path, nearby_text=nearby_text)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }


def _image_to_data_url(image_path: str) -> str:
    path = Path(image_path)
    mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _extract_chat_text(data: dict[str, Any]) -> str:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, dict):
        return ""
    message = first.get("message")
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    return content.strip() if isinstance(content, str) else ""
