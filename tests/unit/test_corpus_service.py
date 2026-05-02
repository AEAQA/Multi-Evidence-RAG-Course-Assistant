from rag_project.app_services.corpus_service import (
    SAMPLE_QUESTIONS,
    build_sample_corpus_summary,
    load_sample_corpus,
)


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
