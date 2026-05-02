from __future__ import annotations

import base64
from pathlib import Path

import fitz
import pytest

from rag_project.ingestion.image_extractor import extract_pdf_image_chunks
from rag_project.ingestion.pdf_loader import load_pdf_chunks
from rag_project.schemas import VisionCaptionResponse


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


class FailingCaptionClient:
    def caption(
        self, image_path: str, nearby_text: str | None = None
    ) -> VisionCaptionResponse:
        raise RuntimeError("caption provider unavailable")


def _write_pdf_with_image(path: Path, *, text: str | None = None) -> None:
    document = fitz.open()
    page = document.new_page()
    if text:
        page.insert_text((72, 72), text)
    page.insert_image(fitz.Rect(72, 110, 172, 210), stream=PNG_1X1)
    document.save(path)
    document.close()


def test_extract_pdf_image_chunks_saves_image_metadata_and_caption(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "figures.pdf"
    _write_pdf_with_image(
        pdf_path,
        text="The figure below shows a convolutional network architecture.",
    )

    chunks = extract_pdf_image_chunks(
        pdf_path,
        output_dir=tmp_path / "images",
        doc_id="doc001",
    )

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.chunk_id == "doc001_page001_image_0001"
    assert chunk.type == "image"
    assert chunk.source_file == "figures.pdf"
    assert chunk.page == 1
    assert chunk.metadata.image_path is not None
    assert Path(chunk.metadata.image_path).exists()
    assert chunk.metadata.bbox is not None
    assert chunk.metadata.caption is not None
    assert chunk.metadata.nearby_text is not None
    assert "convolutional network" in chunk.metadata.nearby_text
    assert chunk.text


def test_extract_pdf_image_chunks_uses_fallback_when_caption_fails(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "caption_failure.pdf"
    _write_pdf_with_image(pdf_path, text="A nearby description of a pipeline diagram.")

    chunks = extract_pdf_image_chunks(
        pdf_path,
        output_dir=tmp_path / "images",
        caption_client=FailingCaptionClient(),
    )

    assert len(chunks) == 1
    assert chunks[0].metadata.caption == "Image extracted from PDF."
    assert "nearby description" in chunks[0].text


def test_extract_pdf_image_chunks_returns_empty_for_no_image_pdf(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "text_only.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "This PDF has no embedded images.")
    document.save(pdf_path)
    document.close()

    assert extract_pdf_image_chunks(pdf_path, output_dir=tmp_path / "images") == []


def test_load_pdf_chunks_accepts_image_only_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "image_only.pdf"
    _write_pdf_with_image(pdf_path)

    chunks = load_pdf_chunks(
        pdf_path,
        image_output_dir=tmp_path / "images",
        include_tables=False,
    )

    assert [chunk.type for chunk in chunks] == ["image"]
    assert chunks[0].metadata.image_path is not None


def test_load_pdf_chunks_returns_mixed_text_and_image_chunks(tmp_path: Path) -> None:
    pdf_path = tmp_path / "mixed.pdf"
    _write_pdf_with_image(
        pdf_path,
        text="Hybrid retrieval combines lexical and semantic evidence.",
    )

    chunks = load_pdf_chunks(
        pdf_path,
        image_output_dir=tmp_path / "images",
        include_tables=False,
    )

    assert {chunk.type for chunk in chunks} == {"text", "image"}
