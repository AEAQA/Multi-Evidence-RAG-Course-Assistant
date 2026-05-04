"""Lightweight PDF table extraction utilities."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

import fitz

from rag_project.ingestion.text_loader import default_doc_id
from rag_project.schemas import Chunk, ChunkMetadata


def extract_pdf_table_chunks(
    path: str | Path,
    *,
    doc_id: str | None = None,
) -> list[Chunk]:
    """Extract simple PDF tables as retrievable table chunks.

    Table detection is best-effort. Detector failures return an empty list.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    if not file_path.is_file():
        raise ValueError(f"PDF path is not a file: {file_path}")

    resolved_doc_id = doc_id or default_doc_id(file_path)
    chunks: list[Chunk] = []

    try:
        document = fitz.open(file_path)
    except Exception as exc:  # pragma: no cover - depends on fitz internals
        raise ValueError(f"Could not open PDF: {file_path}") from exc

    with document:
        for page_index, page in enumerate(document, start=1):
            try:
                tables = _find_page_tables(page)
            except Exception:
                return []

            page_table_count = 0
            for table in tables:
                page_table_count += 1
                chunk = _table_to_chunk(
                    table=table,
                    file_path=file_path,
                    doc_id=resolved_doc_id,
                    page_number=page_index,
                    table_number=page_table_count,
                )
                if chunk is not None:
                    chunks.append(chunk)

    return chunks


def _find_page_tables(page: fitz.Page) -> list[Any]:
    finder = getattr(page, "find_tables", None)
    if finder is None:
        return []
    result = finder()
    return list(getattr(result, "tables", []) or [])


def _table_to_chunk(
    *,
    table: Any,
    file_path: Path,
    doc_id: str,
    page_number: int,
    table_number: int,
) -> Chunk | None:
    try:
        rows = table.extract()
    except Exception:
        return None

    normalized_rows = _normalize_rows(rows)
    if not normalized_rows:
        return None

    text = "\n".join(" | ".join(row) for row in normalized_rows)
    chunk_id = f"{doc_id}_page{page_number:03d}_table_{table_number:04d}"
    return Chunk(
        chunk_id=chunk_id,
        doc_id=doc_id,
        source_file=file_path.name,
        page=page_number,
        type="table",
        text=text,
        metadata=ChunkMetadata(
            bbox=_table_bbox(table),
            table_html=_rows_to_html(normalized_rows),
            table_markdown=_rows_to_markdown(normalized_rows),
            table_summary=_rows_to_summary(normalized_rows),
            cells=normalized_rows,
            caption="Table extracted from PDF.",
        ),
    )


def _normalize_rows(rows: Any) -> list[list[str]]:
    normalized: list[list[str]] = []
    for row in rows or []:
        cells = [str(cell).strip() if cell is not None else "" for cell in row]
        if any(cells):
            normalized.append(cells)
    return normalized


def _rows_to_html(rows: list[list[str]]) -> str:
    rendered_rows = []
    for row in rows:
        cells = "".join(f"<td>{html.escape(cell)}</td>" for cell in row)
        rendered_rows.append(f"<tr>{cells}</tr>")
    return f"<table>{''.join(rendered_rows)}</table>"


def _rows_to_markdown(rows: list[list[str]]) -> str:
    return "\n".join(" | ".join(row) for row in rows)


def _rows_to_summary(rows: list[list[str]], *, max_chars: int = 360) -> str:
    text = " ".join(" | ".join(row) for row in rows)
    normalized = " ".join(text.split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[:max_chars].rstrip() + "..."


def _table_bbox(table: Any) -> list[float] | None:
    bbox = getattr(table, "bbox", None)
    if not bbox:
        return None
    try:
        return [float(value) for value in bbox]
    except (TypeError, ValueError):
        return None
