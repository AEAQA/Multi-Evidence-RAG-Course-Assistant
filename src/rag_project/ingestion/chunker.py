"""Text chunking for extracted document pages."""

from __future__ import annotations

from rag_project.schemas import Chunk, ChunkMetadata, DocumentPage


def chunk_pages(
    pages: list[DocumentPage],
    *,
    max_words: int = 180,
    overlap_words: int = 30,
) -> list[Chunk]:
    """Split pages into overlapping word chunks."""
    if max_words <= 0:
        raise ValueError("max_words must be positive")
    if overlap_words < 0 or overlap_words >= max_words:
        raise ValueError("overlap_words must be non-negative and smaller than max_words")

    chunks: list[Chunk] = []
    per_doc_counts: dict[tuple[str, int], int] = {}
    step = max_words - overlap_words

    for page in pages:
        words = page.text.split()
        if not words:
            continue

        for start in range(0, len(words), step):
            chunk_words = words[start : start + max_words]
            if not chunk_words:
                continue

            key = (page.doc_id, page.page)
            per_doc_counts[key] = per_doc_counts.get(key, 0) + 1
            chunk_number = per_doc_counts[key]
            chunk_id = f"{page.doc_id}_page{page.page:03d}_text_{chunk_number:04d}"

            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    doc_id=page.doc_id,
                    source_file=page.source_file,
                    page=page.page,
                    type="text",
                    text=" ".join(chunk_words),
                    metadata=ChunkMetadata(
                        section_title=page.metadata.get("section_title")
                    ),
                )
            )

            if start + max_words >= len(words):
                break

    return chunks
