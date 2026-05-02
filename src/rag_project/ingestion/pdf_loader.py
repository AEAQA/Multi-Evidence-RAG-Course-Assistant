"""Text-based PDF loader using PyMuPDF."""

from __future__ import annotations

from pathlib import Path

import fitz

from rag_project.ingestion.text_loader import default_doc_id
from rag_project.schemas import DocumentPage


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
