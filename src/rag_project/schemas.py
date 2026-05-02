"""Shared schemas for the RAG pipeline."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ChunkType = Literal["text", "image", "table"]
SUPPORTED_CHUNK_TYPES: tuple[str, ...] = ("text", "image", "table")


class DocumentPage(BaseModel):
    """Extracted text for one source page."""

    doc_id: str
    source_file: str
    page: int
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChunkMetadata(BaseModel):
    """Optional metadata shared by text, image, and table chunks."""

    section_title: str | None = None
    bbox: list[float] | None = None
    image_path: str | None = None
    caption: str | None = None
    nearby_text: str | None = None
    table_html: str | None = None


class Chunk(BaseModel):
    """A retrievable unit used by indexing, retrieval, and generation."""

    chunk_id: str
    doc_id: str
    source_file: str
    page: int
    type: ChunkType
    text: str
    metadata: ChunkMetadata = Field(default_factory=ChunkMetadata)


class Citation(BaseModel):
    chunk_id: str
    source_file: str
    page: int


class AnswerResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    insufficient_evidence: bool = False


class RerankResult(BaseModel):
    chunk_id: str
    score: float
    rank: int


class ASRResponse(BaseModel):
    text: str
    confidence: float | None = None


class VisionCaptionResponse(BaseModel):
    caption: str
