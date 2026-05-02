"""Plain text document loader."""

from __future__ import annotations

from pathlib import Path

from rag_project.schemas import DocumentPage


def default_doc_id(path: Path) -> str:
    """Create a stable document id from a file name."""
    return path.stem.replace(" ", "_").lower()


def load_text_file(path: str | Path, doc_id: str | None = None) -> list[DocumentPage]:
    """Load a UTF-8 text file as a single-page document."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Text file not found: {file_path}")
    if not file_path.is_file():
        raise ValueError(f"Text path is not a file: {file_path}")

    text = file_path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Text file has no content: {file_path}")

    return [
        DocumentPage(
            doc_id=doc_id or default_doc_id(file_path),
            source_file=file_path.name,
            page=1,
            text=text,
            metadata={"loader": "text"},
        )
    ]
