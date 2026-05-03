"""Corpus helpers for the Streamlit Evidence Workbench."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Literal
import uuid

from pydantic import BaseModel, Field

from rag_project.evaluation.sample_corpus import build_sample_evaluation_chunks
from rag_project.ingestion.chunker import chunk_pages
from rag_project.ingestion.pdf_loader import load_pdf_chunks
from rag_project.ingestion.text_loader import load_text_file
from rag_project.schemas import Chunk

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_UPLOAD_DIR = ROOT / "data" / "processed" / "uploads"
DEFAULT_REGISTRY_PATH = ROOT / "data" / "processed" / "corpus_registry.json"
DEFAULT_UPLOAD_IMAGE_DIR = ROOT / "data" / "processed" / "images"
SUPPORTED_UPLOAD_SUFFIXES = {".txt", ".md", ".markdown", ".pdf"}

SAMPLE_QUESTIONS: list[str] = [
    "What is overfitting and why does validation data matter?",
    "How does reranking improve retrieval quality?",
    "When should we prefer hybrid retrieval over BM25 alone?",
    "What does NDCG measure in retrieval evaluation?",
]


class CorpusSummary(BaseModel):
    """Lightweight corpus summary for the workbench sidebar."""

    corpus_name: str
    chunk_count: int
    type_counts: dict[str, int] = Field(default_factory=dict)
    source_files: list[str] = Field(default_factory=list)
    sample_questions: list[str] = Field(default_factory=list)


class DocumentRecord(BaseModel):
    """Metadata for one locally uploaded document."""

    doc_id: str
    filename: str
    stored_path: str
    chunk_count: int
    type_counts: dict[str, int] = Field(default_factory=dict)
    created_at: str


class UploadFailure(BaseModel):
    """One non-blocking upload failure."""

    filename: str
    error: str


class UploadResult(BaseModel):
    """Result of a batch local upload."""

    uploaded: list[DocumentRecord] = Field(default_factory=list)
    failed: list[UploadFailure] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CorpusSelection(BaseModel):
    """User-selected corpus scope for one query."""

    mode: Literal["sample", "uploaded", "combined"] = "combined"
    selected_doc_ids: list[str] = Field(default_factory=list)


class CorpusBundle(BaseModel):
    """Resolved corpus chunks plus display metadata."""

    chunks: list[Chunk] = Field(default_factory=list)
    summary: CorpusSummary
    documents: list[DocumentRecord] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def load_sample_corpus() -> list[Chunk]:
    """Load the public synthetic sample corpus."""
    return build_sample_evaluation_chunks()


def build_sample_corpus_summary(chunks: list[Chunk] | None = None) -> CorpusSummary:
    """Summarize the sample corpus without requiring Pandas."""
    corpus_chunks = chunks if chunks is not None else load_sample_corpus()
    type_counts = Counter(chunk.type for chunk in corpus_chunks)
    source_files = sorted({chunk.source_file for chunk in corpus_chunks})
    return CorpusSummary(
        corpus_name="Synthetic course study corpus",
        chunk_count=len(corpus_chunks),
        type_counts=dict(sorted(type_counts.items())),
        source_files=source_files,
        sample_questions=SAMPLE_QUESTIONS,
    )


def ingest_uploaded_files(
    files: list[Any],
    *,
    upload_dir: str | Path = DEFAULT_UPLOAD_DIR,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
    image_output_dir: str | Path = DEFAULT_UPLOAD_IMAGE_DIR,
) -> UploadResult:
    """Save and ingest uploaded .txt/.pdf files with non-blocking failures."""
    upload_root = Path(upload_dir)
    upload_root.mkdir(parents=True, exist_ok=True)
    registry = _load_registry(Path(registry_path))
    uploaded: list[DocumentRecord] = []
    failed: list[UploadFailure] = []

    for upload in files:
        filename = Path(str(getattr(upload, "name", "") or "")).name
        if not filename:
            failed.append(UploadFailure(filename="unknown", error="Missing filename"))
            continue

        suffix = Path(filename).suffix.lower()
        if suffix not in SUPPORTED_UPLOAD_SUFFIXES:
            failed.append(
                UploadFailure(
                    filename=filename,
                    error="Unsupported file type. Only .txt, .md, and .pdf are supported.",
                )
            )
            continue

        doc_id = uuid.uuid4().hex[:12]
        stored_path = upload_root / f"{doc_id}_{_slugify(filename)}"
        try:
            data = _read_upload_bytes(upload)
            if not data:
                raise ValueError("Uploaded file is empty")
            stored_path.write_bytes(data)
            chunks = _load_chunks_for_record(
                stored_path,
                doc_id=doc_id,
                filename=filename,
                image_output_dir=image_output_dir,
            )
            if not chunks:
                raise ValueError("No readable chunks were produced")
            record = DocumentRecord(
                doc_id=doc_id,
                filename=filename,
                stored_path=str(stored_path),
                chunk_count=len(chunks),
                type_counts=_type_counts(chunks),
                created_at=_utcnow_iso(),
            )
        except Exception as exc:
            if stored_path.exists():
                stored_path.unlink(missing_ok=True)
            failed.append(UploadFailure(filename=filename, error=str(exc)))
            continue

        registry[doc_id] = record
        uploaded.append(record)

    _save_registry(Path(registry_path), registry)
    return UploadResult(uploaded=uploaded, failed=failed)


def load_uploaded_corpus(
    *,
    selected_doc_ids: list[str] | None = None,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
    image_output_dir: str | Path = DEFAULT_UPLOAD_IMAGE_DIR,
) -> CorpusBundle:
    """Load chunks for uploaded documents from the local registry."""
    registry = _load_registry(Path(registry_path))
    selected = set(selected_doc_ids or [])
    records = [
        record
        for record in registry.values()
        if not selected or record.doc_id in selected
    ]
    records.sort(key=lambda record: record.created_at, reverse=True)

    chunks: list[Chunk] = []
    warnings: list[str] = []
    for record in records:
        try:
            chunks.extend(
                _load_chunks_for_record(
                    Path(record.stored_path),
                    doc_id=record.doc_id,
                    filename=record.filename,
                    image_output_dir=image_output_dir,
                )
            )
        except Exception as exc:
            warnings.append(f"{record.filename}: {exc}")

    return CorpusBundle(
        chunks=chunks,
        summary=_build_summary(
            "Uploaded study documents",
            chunks,
            sample_questions=SAMPLE_QUESTIONS,
        ),
        documents=records,
        warnings=warnings,
    )


def load_corpus_bundle(
    selection: CorpusSelection | None = None,
    *,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
    image_output_dir: str | Path = DEFAULT_UPLOAD_IMAGE_DIR,
) -> CorpusBundle:
    """Resolve the sample/uploaded/combined corpus selection."""
    resolved = selection or CorpusSelection()
    sample_chunks = load_sample_corpus() if resolved.mode in {"sample", "combined"} else []
    uploaded = (
        load_uploaded_corpus(
            selected_doc_ids=resolved.selected_doc_ids,
            registry_path=registry_path,
            image_output_dir=image_output_dir,
        )
        if resolved.mode in {"uploaded", "combined"}
        else CorpusBundle(
            chunks=[],
            summary=_build_summary("Uploaded study documents", []),
            documents=[],
        )
    )
    chunks = [*sample_chunks, *uploaded.chunks]
    corpus_name = {
        "sample": "Synthetic course study corpus",
        "uploaded": "Uploaded study documents",
        "combined": "Sample + uploaded study corpus",
    }[resolved.mode]
    return CorpusBundle(
        chunks=chunks,
        summary=_build_summary(
            corpus_name,
            chunks,
            sample_questions=SAMPLE_QUESTIONS,
        ),
        documents=uploaded.documents,
        warnings=uploaded.warnings,
    )


def delete_uploaded_document(
    doc_id: str,
    *,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
) -> bool:
    """Delete one uploaded document record and its stored file."""
    registry_file = Path(registry_path)
    registry = _load_registry(registry_file)
    record = registry.pop(doc_id, None)
    if record is None:
        return False
    Path(record.stored_path).unlink(missing_ok=True)
    _save_registry(registry_file, registry)
    return True


def _load_chunks_for_record(
    path: Path,
    *,
    doc_id: str,
    filename: str,
    image_output_dir: str | Path,
) -> list[Chunk]:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".markdown"}:
        chunks = chunk_pages(load_text_file(path, doc_id=doc_id))
    elif suffix == ".pdf":
        chunks = load_pdf_chunks(
            path,
            doc_id=doc_id,
            image_output_dir=image_output_dir,
        )
    else:
        raise ValueError("Unsupported file type")

    for chunk in chunks:
        chunk.source_file = filename
    return chunks


def _load_registry(path: Path) -> dict[str, DocumentRecord]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    records: dict[str, DocumentRecord] = {}
    for doc_id, value in payload.items():
        try:
            record = DocumentRecord.model_validate(value)
        except Exception:
            continue
        records[str(doc_id)] = record
    return records


def _save_registry(path: Path, registry: dict[str, DocumentRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        doc_id: record.model_dump()
        for doc_id, record in sorted(registry.items())
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_summary(
    corpus_name: str,
    chunks: list[Chunk],
    *,
    sample_questions: list[str] | None = None,
) -> CorpusSummary:
    type_counts = Counter(chunk.type for chunk in chunks)
    source_files = sorted({chunk.source_file for chunk in chunks})
    return CorpusSummary(
        corpus_name=corpus_name,
        chunk_count=len(chunks),
        type_counts=dict(sorted(type_counts.items())),
        source_files=source_files,
        sample_questions=list(sample_questions or []),
    )


def _type_counts(chunks: list[Chunk]) -> dict[str, int]:
    return dict(sorted(Counter(chunk.type for chunk in chunks).items()))


def _read_upload_bytes(upload: Any) -> bytes:
    if hasattr(upload, "getvalue"):
        data = upload.getvalue()
    elif hasattr(upload, "read"):
        data = upload.read()
    else:
        raise ValueError("Upload object does not provide file bytes")
    if isinstance(data, str):
        return data.encode("utf-8")
    return bytes(data)


def _slugify(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", filename).strip("-")
    return cleaned or "document"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
