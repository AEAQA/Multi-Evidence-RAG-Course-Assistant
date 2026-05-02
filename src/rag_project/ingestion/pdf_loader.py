"""Text-based PDF loader using PyMuPDF."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import fitz

from rag_project.ingestion.chunker import chunk_pages
from rag_project.ingestion.image_extractor import (
    DEFAULT_IMAGE_OUTPUT_DIR,
    extract_pdf_image_chunks,
)
from rag_project.ingestion.table_extractor import extract_pdf_table_chunks
from rag_project.ingestion.text_loader import default_doc_id
from rag_project.schemas import Chunk, DocumentPage
from rag_project.vision.caption_client import VisionCaptionClient


def load_pdf(path: str | Path, doc_id: str | None = None) -> list[DocumentPage]:
    """Extract text from a small text-based PDF.

    Image and table extraction are intentionally deferred to the
    image-aware ingestion milestone.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    if not file_path.is_file():
        raise ValueError(f"PDF path is not a file: {file_path}")

    resolved_doc_id = doc_id or default_doc_id(file_path)
    pages: list[DocumentPage] = []

    try:
        document = fitz.open(file_path)
    except Exception as exc:  # pragma: no cover - depends on fitz internals
        raise ValueError(f"Could not open PDF: {file_path}") from exc

    with document:
        for index, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            if not text:
                continue
            pages.append(
                DocumentPage(
                    doc_id=resolved_doc_id,
                    source_file=file_path.name,
                    page=index,
                    text=text,
                    metadata={"loader": "pymupdf"},
                )
            )

    if not pages:
        raise ValueError(f"No extractable text found in PDF: {file_path}")

    return pages


def load_pdf_chunks(
    path: str | Path,
    *,
    doc_id: str | None = None,
    include_images: bool = True,
    include_tables: bool = True,
    image_output_dir: str | Path = DEFAULT_IMAGE_OUTPUT_DIR,
    caption_client: VisionCaptionClient | None = None,
    chunk_options: dict[str, Any] | None = None,
) -> list[Chunk]:
    """Load text, image, and lightweight table chunks from a PDF.

    Text-only loader behavior remains unchanged in ``load_pdf``. This helper is
    the image-aware ingestion entrypoint and keeps each extraction branch
    best-effort so one failed modality does not block the others.
    """
    file_path = Path(path)
    resolved_doc_id = doc_id or default_doc_id(file_path)
    chunks: list[Chunk] = []
    errors: list[str] = []

    try:
        pages = load_pdf(file_path, doc_id=resolved_doc_id)
        chunks.extend(chunk_pages(pages, **(chunk_options or {})))
    except ValueError as exc:
        errors.append(str(exc))

    if include_images:
        try:
            chunks.extend(
                extract_pdf_image_chunks(
                    file_path,
                    output_dir=image_output_dir,
                    doc_id=resolved_doc_id,
                    caption_client=caption_client,
                )
            )
        except ValueError as exc:
            errors.append(str(exc))

    if include_tables:
        try:
            chunks.extend(extract_pdf_table_chunks(file_path, doc_id=resolved_doc_id))
        except ValueError as exc:
            errors.append(str(exc))

    if not chunks:
        detail = "; ".join(errors) if errors else "no extractable text, images, or tables"
        raise ValueError(f"No extractable PDF chunks found in {file_path}: {detail}")

    return chunks
