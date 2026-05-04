"""JSON-first FastAPI adapter over the existing RAG app services."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from rag_project.app_services.corpus_service import (
    CorpusSelection,
    delete_uploaded_document,
    ingest_uploaded_files,
    load_corpus_bundle,
    load_document_registry,
)
from rag_project.app_services.provider_status import build_provider_status
from rag_project.app_services.query_service import WorkbenchState, run_query
from rag_project.config import AppConfig, load_config
from rag_project.evaluation.loader import load_evaluation_queries
from rag_project.evaluation.run_evaluation import DEFAULT_QUERY_PATH
from rag_project.evaluation.runner import (
    EvaluationResult,
    evaluate_retrieval_methods,
    write_evaluation_reports,
)
from rag_project.evaluation.sample_corpus import build_sample_evaluation_chunks
from rag_project.schemas import RetrievalResult

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REGISTRY_PATH = ROOT / "data" / "processed" / "corpus_registry.json"
DEFAULT_UPLOAD_DIR = ROOT / "data" / "processed" / "uploads"
DEFAULT_IMAGE_DIR = ROOT / "data" / "processed" / "images"
DEFAULT_CHUNK_CACHE_DIR = ROOT / "data" / "processed" / "chunks"
DEFAULT_REPORT_DIR = ROOT / "reports" / "evaluation"


class ApiPaths(BaseModel):
    """Filesystem locations used by the FastAPI adapter."""

    registry_path: Path = DEFAULT_REGISTRY_PATH
    upload_dir: Path = DEFAULT_UPLOAD_DIR
    image_output_dir: Path = DEFAULT_IMAGE_DIR
    chunk_cache_dir: Path = DEFAULT_CHUNK_CACHE_DIR
    eval_query_path: Path = DEFAULT_QUERY_PATH
    report_dir: Path = DEFAULT_REPORT_DIR


class QueryScopeRequest(BaseModel):
    """Corpus scope selected by the React product UI."""

    mode: Literal["sample", "uploaded", "combined"] = "combined"
    selected_doc_ids: list[str] = Field(default_factory=list)


class QueryRequest(BaseModel):
    """RAG query request contract for the product UI."""

    query: str = Field(min_length=1)
    top_k: int = 3
    scope: QueryScopeRequest = Field(default_factory=QueryScopeRequest)


class EvaluationRunRequest(BaseModel):
    """Offline evaluation request."""

    top_k: int = 5
    write_reports: bool = True


class UploadedFileAdapter:
    """Sync adapter for FastAPI UploadFile objects used by corpus_service."""

    def __init__(self, name: str, data: bytes) -> None:
        self.name = name
        self._data = data

    def getvalue(self) -> bytes:
        return self._data


def create_app(
    *,
    config: AppConfig | None = None,
    paths: ApiPaths | None = None,
) -> FastAPI:
    """Create a FastAPI app with injectable paths for isolated tests."""
    runtime_config = config or load_config()
    runtime_paths = paths or ApiPaths()
    app = FastAPI(
        title="RAG Study Assistant API",
        version="0.1.0",
        description="FastAPI adapter for the offline-first RAG study assistant.",
    )
    app.state.config = runtime_config
    app.state.paths = runtime_paths

    images_dir = runtime_paths.image_output_dir
    if images_dir.exists():
        app.mount(
            "/api/static/images",
            StaticFiles(directory=str(images_dir)),
            name="static_images",
        )

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        records = load_document_registry(registry_path=runtime_paths.registry_path)
        return {
            "status": "ok",
            "service": "rag-study-assistant-api",
            "mode": runtime_config.app_mode,
            "document_count": len(records),
            "total_chunks": sum(record.chunk_count for record in records),
        }

    @app.get("/api/status")
    def status() -> dict[str, Any]:
        provider_status = build_provider_status(runtime_config)
        documents = load_document_registry(registry_path=runtime_paths.registry_path)
        return {
            "status": "ok",
            "provider_status": provider_status.model_dump(mode="json"),
            "runtime": runtime_config.safe_runtime_status(),
            "document_count": len(documents),
            "total_chunks": sum(record.chunk_count for record in documents),
            "streamlit_backup": "available",
            "api": {
                "streaming": False,
                "react_product_ui_ready": True,
            },
        }

    @app.get("/api/documents")
    def documents() -> dict[str, Any]:
        records = load_document_registry(registry_path=runtime_paths.registry_path)
        return {
            "documents": [_document_payload(record) for record in records],
            "total_chunks": sum(record.chunk_count for record in records),
        }

    @app.post("/api/documents/upload")
    async def upload_documents(files: list[UploadFile] = File(...)) -> dict[str, Any]:
        adapters = [
            UploadedFileAdapter(
                name=upload.filename or "unknown",
                data=await upload.read(),
            )
            for upload in files
        ]
        result = ingest_uploaded_files(
            adapters,
            upload_dir=runtime_paths.upload_dir,
            registry_path=runtime_paths.registry_path,
            image_output_dir=runtime_paths.image_output_dir,
            chunk_cache_dir=runtime_paths.chunk_cache_dir,
        )
        records = load_document_registry(registry_path=runtime_paths.registry_path)
        return {
            "uploaded": [_document_payload(record) for record in result.uploaded],
            "failed": [failure.model_dump(mode="json") for failure in result.failed],
            "warnings": result.warnings,
            "documents": [_document_payload(record) for record in records],
            "total_chunks": sum(record.chunk_count for record in records),
        }

    @app.delete("/api/documents/{doc_id}")
    def delete_document(doc_id: str) -> dict[str, Any]:
        deleted = delete_uploaded_document(
            doc_id,
            registry_path=runtime_paths.registry_path,
        )
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found")
        records = load_document_registry(registry_path=runtime_paths.registry_path)
        return {
            "deleted": {"doc_id": doc_id},
            "documents": [_document_payload(record) for record in records],
            "total_chunks": sum(record.chunk_count for record in records),
        }

    @app.get("/api/documents/{doc_id}/file")
    def document_file(doc_id: str) -> FileResponse:
        records = load_document_registry(registry_path=runtime_paths.registry_path)
        record = next((item for item in records if item.doc_id == doc_id), None)
        if record is None:
            raise HTTPException(status_code=404, detail="Document not found")
        path = Path(record.stored_path).resolve()
        upload_root = runtime_paths.upload_dir.resolve()
        if upload_root not in path.parents:
            raise HTTPException(status_code=403, detail="Document path is not allowed")
        if not path.exists():
            raise HTTPException(status_code=404, detail="Document file not found")
        if path.suffix.lower() != ".pdf":
            raise HTTPException(status_code=400, detail="Document is not a PDF")
        return FileResponse(
            path,
            media_type="application/pdf",
            filename=record.filename,
            headers={
                "Content-Disposition": f'inline; filename="{record.filename}"'
            },
        )

    @app.post("/api/query")
    def query(request: QueryRequest) -> dict[str, Any]:
        selection = CorpusSelection(
            mode=request.scope.mode,
            selected_doc_ids=request.scope.selected_doc_ids,
        )
        bundle = load_corpus_bundle(
            selection,
            registry_path=runtime_paths.registry_path,
            image_output_dir=runtime_paths.image_output_dir,
            chunk_cache_dir=runtime_paths.chunk_cache_dir,
        )
        state = run_query(
            request.query,
            bundle,
            config=runtime_config,
            top_k=request.top_k,
        )
        return _query_response(state)

    @app.get("/api/evaluation/summary")
    def evaluation_summary() -> dict[str, Any]:
        metrics_path = runtime_paths.report_dir / "retrieval_metrics.csv"
        latency_path = runtime_paths.report_dir / "latency_metrics.csv"
        return {
            "available": metrics_path.exists() and latency_path.exists(),
            "summary_by_method": _summary_from_metric_csv(metrics_path),
            "latency_by_method": _latency_from_csv(latency_path),
            "report_paths": {
                "retrieval_metrics": str(metrics_path),
                "latency_metrics": str(latency_path),
                "error_cases": str(runtime_paths.report_dir / "error_cases.md"),
            },
        }

    @app.post("/api/evaluation/run")
    def evaluation_run(request: EvaluationRunRequest | None = None) -> dict[str, Any]:
        resolved_request = request or EvaluationRunRequest()
        result = _run_offline_evaluation(
            query_path=runtime_paths.eval_query_path,
            top_k=resolved_request.top_k,
        )
        written_paths: list[Path] = []
        if resolved_request.write_reports:
            written_paths = write_evaluation_reports(result, runtime_paths.report_dir)
        return {
            "summary_by_method": result.summary_by_method,
            "metric_rows": result.metric_rows,
            "latency_rows": result.latency_rows,
            "error_cases_markdown": result.error_cases_markdown,
            "written_paths": [str(path) for path in written_paths],
        }

    return app


def _run_offline_evaluation(*, query_path: Path, top_k: int) -> EvaluationResult:
    queries = load_evaluation_queries(query_path)
    chunks = build_sample_evaluation_chunks()
    return evaluate_retrieval_methods(chunks, queries, top_k=max(1, min(top_k, 10)))


def _document_payload(record: Any) -> dict[str, Any]:
    payload = record.model_dump(mode="json")
    payload.pop("stored_path", None)
    payload.pop("chunk_cache_path", None)
    payload["is_pdf"] = str(record.filename).lower().endswith(".pdf")
    payload["source_url"] = (
        f"/api/documents/{record.doc_id}/file" if payload["is_pdf"] else None
    )
    return payload


def _query_response(state: WorkbenchState) -> dict[str, Any]:
    grounding_status = (
        "insufficient_evidence"
        if state.answer.insufficient_evidence
        else "grounded"
    )
    return {
        "query": state.query,
        "answer": {
            "text": state.answer.answer,
            "style": "detailed",
            "grounding_status": grounding_status,
            "retrieval_explanation": state.answer.retrieval_explanation,
            "generation_mode": state.answer.generation_mode,
        },
        "citations": [
            _citation_payload(citation, state.final_evidence)
            for citation in state.answer.citations
        ],
        "final_evidence": [
            {
                "evidence_id": evidence.evidence_id,
                "chunk_id": evidence.chunk_id,
                "doc_id": evidence.doc_id,
                "source_file": evidence.source_file,
                "page": evidence.page,
                "type": evidence.type,
                "method": evidence.method,
                "score": evidence.score,
                "confidence": evidence.confidence,
                "support_label": evidence.support_label,
                "sub_question_id": evidence.sub_question_id,
                "preview": evidence.preview,
                "image_url": evidence.image_url,
                "table_summary": evidence.table_summary,
                "source_url": _source_url(evidence),
            }
            for evidence in state.final_evidence
        ],
        "retrieval_trace": [
            stage.model_dump(mode="json") for stage in state.retrieval_trace
        ],
        "retrieval": {
            "bm25": _result_rows(state.retrieval.bm25_results),
            "dense": _result_rows(state.retrieval.dense_results),
            "fusion": _result_rows(state.retrieval.fusion_results),
            "reranked": _result_rows(state.retrieval.reranked_results),
        },
        "timing": state.timing_ms,
        "scope": state.scope,
        "diagnostics": [
            diagnostic.model_dump(mode="json") for diagnostic in state.diagnostics
        ],
        "provider_status": state.provider_status.model_dump(mode="json"),
        "warnings": state.corpus_warnings,
        "suggestions": state.suggestions,
        "query_plan": state.query_plan.model_dump(mode="json") if state.query_plan else None,
        "sub_question_support": [
            item.model_dump(mode="json") for item in state.sub_question_support
        ],
        "support_label": state.support_label,
    }


def _citation_payload(citation: Any, final_evidence: list[Any]) -> dict[str, Any]:
    evidence_by_chunk = {item.chunk_id: item for item in final_evidence}
    evidence = evidence_by_chunk.get(citation.chunk_id)
    return {
        "evidence_id": citation.evidence_id,
        "chunk_id": citation.chunk_id,
        "doc_id": evidence.doc_id if evidence else None,
        "source_file": citation.source_file,
        "page": citation.page,
    }


def _result_rows(results: list[RetrievalResult]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in results:
        chunk = result.chunk
        rows.append(
            {
                "rank": result.rank,
                "score": round(float(result.score), 4),
                "method": result.method,
                "chunk_id": chunk.chunk_id,
                "doc_id": chunk.doc_id,
                "source_file": chunk.source_file,
                "page": chunk.page,
                "type": chunk.type,
                "preview": _preview(chunk.text),
            }
        )
    return rows


def _source_url(evidence: Any) -> str | None:
    if not evidence.doc_id or not evidence.page:
        return None
    if not str(evidence.source_file).lower().endswith(".pdf"):
        return None
    return f"/api/documents/{evidence.doc_id}/file#page={evidence.page}"


def _preview(text: str, *, max_chars: int = 360) -> str:
    normalized = " ".join(str(text or "").split())
    if len(normalized) <= max_chars:
        return normalized
    window = normalized[: max_chars + 1]
    boundary = max(
        window.rfind(". "),
        window.rfind("? "),
        window.rfind("! "),
        window.rfind("; "),
    )
    if boundary > max_chars // 3:
        return window[: boundary + 1].strip() + "..."
    return normalized[:max_chars].rstrip() + "..."


def _summary_from_metric_csv(path: Path) -> dict[str, dict[str, float]]:
    rows = _read_csv_rows(path)
    if not rows:
        return {}
    methods = sorted({row.get("method", "") for row in rows if row.get("method")})
    summary: dict[str, dict[str, float]] = {}
    for method in methods:
        method_rows = [row for row in rows if row.get("method") == method]
        metric_names = [
            name for name in method_rows[0].keys() if name not in {"query_id", "method"}
        ]
        summary[method] = {
            name: _mean([float(row.get(name, 0.0)) for row in method_rows])
            for name in metric_names
        }
    return summary


def _latency_from_csv(path: Path) -> dict[str, float]:
    rows = _read_csv_rows(path)
    methods = sorted({row.get("method", "") for row in rows if row.get("method")})
    return {
        method: _mean(
            [float(row.get("latency_ms", 0.0)) for row in rows if row.get("method") == method]
        )
        for method in methods
    }


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 6)


app = create_app()
