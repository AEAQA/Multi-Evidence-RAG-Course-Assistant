from pathlib import Path

import fitz

from rag_project.ingestion.table_extractor import extract_pdf_table_chunks


def test_extract_pdf_table_chunks_returns_empty_for_non_table_pdf(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "no_table.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "A plain text page without table structure.")
    document.save(pdf_path)
    document.close()

    assert extract_pdf_table_chunks(pdf_path) == []


def test_extract_pdf_table_chunks_returns_empty_when_detection_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    pdf_path = tmp_path / "table_detection_failure.pdf"
    document = fitz.open()
    document.new_page()
    document.save(pdf_path)
    document.close()

    def fail_find_tables(page):
        raise RuntimeError("table detector unavailable")

    monkeypatch.setattr(
        "rag_project.ingestion.table_extractor._find_page_tables",
        fail_find_tables,
    )

    assert extract_pdf_table_chunks(pdf_path) == []
