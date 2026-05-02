"""ASR client interface and deterministic mock implementation."""

from __future__ import annotations

from typing import Protocol

from rag_project.schemas import ASRResponse


class ASRClient(Protocol):
    """Interface for converting voice input to text."""

    def transcribe(self, audio_path: str) -> ASRResponse:
        """Transcribe an audio file."""


class MockASRClient:
    """Offline ASR mock used when no API key is configured."""

    def transcribe(self, audio_path: str) -> ASRResponse:
        return ASRResponse(text="mock transcribed question", confidence=None)
