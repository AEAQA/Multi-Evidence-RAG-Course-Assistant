from __future__ import annotations

from pathlib import Path

import fitz

from rag_project.app_services.corpus_service import (
    CorpusSelection,
    SAMPLE_QUESTIONS,
    build_sample_corpus_summary,
    delete_uploaded_document,
    ingest_uploaded_files,
    load_corpus_bundle,
    load_sample_corpus,
    load_uploaded_corpus,
)


class FakeUpload:
    def __init__(self, name: str, data: bytes) -> None:
        self.name = name
        self._data = data

    def getvalue(self) -> bytes:
        return self._data


def _write_text_pdf(path: Path, text: str) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    document.save(path)
    document.close()


def test_load_sample_corpus_returns_public_chunks() -> None:
    chunks = load_sample_corpus()

    assert chunks
    assert all(chunk.source_file for chunk in chunks)


def test_sample_corpus_summary_counts_chunk_types_and_sources() -> None:
    summary = build_sample_corpus_summary()

    assert summary.corpus_name == "Synthetic course study corpus"
    assert summary.chunk_count > 0
    assert summary.type_counts["text"] == summary.chunk_count
    assert summary.source_files


def test_sample_corpus_summary_includes_sample_questions() -> None:
    summary = build_sample_corpus_summary()

    assert summary.sample_questions == SAMPLE_QUESTIONS
    assert len(summary.sample_questions) >= 3


def test_ingest_uploaded_txt_creates_chunks_and_registry_record(tmp_path: Path) -> None:
    result = ingest_uploaded_files(
        [
            FakeUpload(
                "notes.txt",
                b"Overfitting happens when a model memorizes training data. Validation data estimates generalization.",
            )
        ],
        upload_dir=tmp_path / "uploads",
        registry_path=tmp_path / "corpus_registry.json",
    )

    assert len(result.uploaded) == 1
    assert result.failed == []
    record = result.uploaded[0]
    assert record.filename == "notes.txt"
    assert record.chunk_count == 1
    assert record.type_counts["text"] == 1
    assert Path(record.stored_path).exists()

    bundle = load_uploaded_corpus(registry_path=tmp_path / "corpus_registry.json")
    assert bundle.summary.chunk_count == 1
    assert bundle.documents[0].filename == "notes.txt"
    assert bundle.chunks[0].source_file == "notes.txt"
    assert "Overfitting" in bundle.chunks[0].text


def test_ingest_uploaded_markdown_creates_chunks_and_registry_record(tmp_path: Path) -> None:
    result = ingest_uploaded_files(
        [
            FakeUpload(
                "lecture.md",
                b"# Retrieval\n\nHybrid retrieval combines lexical and semantic search.",
            )
        ],
        upload_dir=tmp_path / "uploads",
        registry_path=tmp_path / "corpus_registry.json",
    )

    assert len(result.uploaded) == 1
    assert result.failed == []
    assert result.uploaded[0].filename == "lecture.md"
    assert result.uploaded[0].type_counts["text"] == 1

    bundle = load_uploaded_corpus(registry_path=tmp_path / "corpus_registry.json")
    assert bundle.chunks[0].source_file == "lecture.md"
    assert "Hybrid retrieval" in bundle.chunks[0].text


def test_ingest_uploaded_text_pdf_creates_retrievable_chunks(tmp_path: Path) -> None:
    pdf_path = tmp_path / "lecture.pdf"
    _write_text_pdf(
        pdf_path,
        "Hybrid retrieval combines BM25 lexical matching and dense semantic retrieval.",
    )

    result = ingest_uploaded_files(
        [FakeUpload("lecture.pdf", pdf_path.read_bytes())],
        upload_dir=tmp_path / "uploads",
        registry_path=tmp_path / "corpus_registry.json",
        image_output_dir=tmp_path / "images",
    )

    assert len(result.uploaded) == 1
    assert result.failed == []
    assert result.uploaded[0].type_counts["text"] >= 1

    bundle = load_uploaded_corpus(
        registry_path=tmp_path / "corpus_registry.json",
        image_output_dir=tmp_path / "images",
    )
    assert any("Hybrid retrieval" in chunk.text for chunk in bundle.chunks)


def test_ingest_uploaded_files_reports_failures_without_crashing(tmp_path: Path) -> None:
    result = ingest_uploaded_files(
        [
            FakeUpload("empty.txt", b""),
            FakeUpload("table.csv", b"a,b\n1,2"),
            FakeUpload("bad.pdf", b"not a real pdf"),
        ],
        upload_dir=tmp_path / "uploads",
        registry_path=tmp_path / "corpus_registry.json",
    )

    assert result.uploaded == []
    assert len(result.failed) == 3
    assert {failure.filename for failure in result.failed} == {
        "empty.txt",
        "table.csv",
        "bad.pdf",
    }


def test_delete_uploaded_document_removes_registry_record(tmp_path: Path) -> None:
    result = ingest_uploaded_files(
        [FakeUpload("notes.txt", b"Retrieval augmented generation uses citations.")],
        upload_dir=tmp_path / "uploads",
        registry_path=tmp_path / "corpus_registry.json",
    )
    record = result.uploaded[0]

    assert delete_uploaded_document(
        record.doc_id,
        registry_path=tmp_path / "corpus_registry.json",
    )

    bundle = load_uploaded_corpus(registry_path=tmp_path / "corpus_registry.json")
    assert bundle.documents == []
    assert bundle.chunks == []


def test_load_corpus_bundle_combines_sample_and_uploaded_chunks(tmp_path: Path) -> None:
    result = ingest_uploaded_files(
        [FakeUpload("custom.txt", b"Custom document explains cross encoder reranking.")],
        upload_dir=tmp_path / "uploads",
        registry_path=tmp_path / "corpus_registry.json",
    )
    selection = CorpusSelection(
        mode="combined",
        selected_doc_ids=[result.uploaded[0].doc_id],
    )

    bundle = load_corpus_bundle(
        selection,
        registry_path=tmp_path / "corpus_registry.json",
    )

    assert bundle.summary.chunk_count > len(load_sample_corpus())
    assert any(chunk.source_file == "custom.txt" for chunk in bundle.chunks)
    assert any(chunk.source_file != "custom.txt" for chunk in bundle.chunks)


def test_uploaded_scope_with_no_selection_loads_all_uploaded_documents(tmp_path: Path) -> None:
    ingest_uploaded_files(
        [
            FakeUpload("first.txt", b"First uploaded document discusses BM25."),
            FakeUpload("second.txt", b"Second uploaded document discusses reranking."),
        ],
        upload_dir=tmp_path / "uploads",
        registry_path=tmp_path / "corpus_registry.json",
    )

    bundle = load_corpus_bundle(
        CorpusSelection(mode="uploaded", selected_doc_ids=[]),
        registry_path=tmp_path / "corpus_registry.json",
    )

    assert {chunk.source_file for chunk in bundle.chunks} == {
        "first.txt",
        "second.txt",
    }
    assert len(bundle.documents) == 2


def test_uploaded_scope_with_selection_restricts_to_selected_documents(tmp_path: Path) -> None:
    result = ingest_uploaded_files(
        [
            FakeUpload("first.txt", b"First uploaded document discusses BM25."),
            FakeUpload("second.txt", b"Second uploaded document discusses reranking."),
        ],
        upload_dir=tmp_path / "uploads",
        registry_path=tmp_path / "corpus_registry.json",
    )
    selected_doc_id = result.uploaded[0].doc_id

    bundle = load_corpus_bundle(
        CorpusSelection(mode="uploaded", selected_doc_ids=[selected_doc_id]),
        registry_path=tmp_path / "corpus_registry.json",
    )

    assert {record.doc_id for record in bundle.documents} == {selected_doc_id}
    assert {chunk.doc_id for chunk in bundle.chunks} == {selected_doc_id}


def test_combined_scope_with_selection_keeps_sample_and_selected_uploaded(
    tmp_path: Path,
) -> None:
    result = ingest_uploaded_files(
        [
            FakeUpload("first.txt", b"First uploaded document discusses BM25."),
            FakeUpload("second.txt", b"Second uploaded document discusses reranking."),
        ],
        upload_dir=tmp_path / "uploads",
        registry_path=tmp_path / "corpus_registry.json",
    )
    selected_doc_id = result.uploaded[1].doc_id

    bundle = load_corpus_bundle(
        CorpusSelection(mode="combined", selected_doc_ids=[selected_doc_id]),
        registry_path=tmp_path / "corpus_registry.json",
    )

    assert any(chunk.doc_id == selected_doc_id for chunk in bundle.chunks)
    assert not any(chunk.source_file == "first.txt" for chunk in bundle.chunks)
    assert any(chunk.source_file != "second.txt" for chunk in bundle.chunks)
