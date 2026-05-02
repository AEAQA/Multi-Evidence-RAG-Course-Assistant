from pathlib import Path

import fitz
import pytest

from rag_project.ingestion.chunker import chunk_pages
from rag_project.ingestion.pdf_loader import load_pdf
from rag_project.ingestion.text_loader import load_text_file
from rag_project.schemas import Chunk


def test_load_text_file_returns_single_page(tmp_path: Path) -> None:
    path = tmp_path / "lecture.txt"
    path.write_text("Overfitting means memorizing training data.", encoding="utf-8")

    pages = load_text_file(path)

    assert len(pages) == 1
    assert pages[0].doc_id == "lecture"
    assert pages[0].page == 1
    assert pages[0].text == "Overfitting means memorizing training data."


def test_load_text_file_rejects_missing_path(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_text_file(tmp_path / "missing.txt")


def test_load_pdf_extracts_text_pages(tmp_path: Path) -> None:
    path = tmp_path / "sample.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Dense retrieval finds semantic matches.")
    document.save(path)
    document.close()

    pages = load_pdf(path)

    assert len(pages) == 1
    assert pages[0].source_file == "sample.pdf"
    assert pages[0].page == 1
    assert "Dense retrieval" in pages[0].text


def test_load_pdf_rejects_pdf_without_text(tmp_path: Path) -> None:
    path = tmp_path / "blank.pdf"
    document = fitz.open()
    document.new_page()
    document.save(path)
    document.close()

    with pytest.raises(ValueError, match="No extractable text"):
        load_pdf(path)


def test_chunk_pages_preserves_metadata_and_chunk_type(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("A " * 120, encoding="utf-8")
    pages = load_text_file(path, doc_id="doc001")

    chunks = chunk_pages(pages, max_words=50, overlap_words=10)

    assert len(chunks) == 3
    assert all(isinstance(chunk, Chunk) for chunk in chunks)
    assert chunks[0].chunk_id == "doc001_page001_text_0001"
    assert chunks[0].type == "text"
    assert chunks[0].source_file == "notes.txt"
    assert chunks[0].page == 1
    assert chunks[1].text.startswith("A")


def test_chunk_pages_rejects_invalid_overlap(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("short text", encoding="utf-8")
    pages = load_text_file(path)

    with pytest.raises(ValueError, match="overlap_words"):
        chunk_pages(pages, max_words=10, overlap_words=10)
