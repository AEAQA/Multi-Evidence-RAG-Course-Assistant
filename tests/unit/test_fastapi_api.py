from pathlib import Path
import re
import uuid

import fitz
import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("multipart")

from fastapi.testclient import TestClient

from rag_project.api.main import ApiPaths, create_app
from rag_project.config import AppConfig


def _test_root() -> Path:
    root = Path("pytest_runs") / f"fastapi_api_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _client(root: Path) -> TestClient:
    app = create_app(
        config=AppConfig(),
        paths=ApiPaths(
            registry_path=root / "corpus_registry.json",
            upload_dir=root / "uploads",
            image_output_dir=root / "images",
            chunk_cache_dir=root / "chunks",
            eval_query_path=Path("data/eval/queries.jsonl"),
            report_dir=root / "reports",
        ),
    )
    return TestClient(app)


def test_health_and_status_are_secret_free() -> None:
    client = _client(_test_root())

    health = client.get("/api/health").json()
    status = client.get("/api/status").json()

    assert health["status"] == "ok"
    assert health["document_count"] == 0
    assert status["runtime"]["SILICONFLOW_API_KEY"] == "missing"
    assert "secret" not in str(status).lower()
    assert status["api"]["streaming"] is False


def test_documents_empty_registry() -> None:
    client = _client(_test_root())

    response = client.get("/api/documents")

    assert response.status_code == 200
    assert response.json() == {"documents": [], "total_chunks": 0}


def test_upload_query_and_delete_uploaded_text_document() -> None:
    client = _client(_test_root())
    upload_response = client.post(
        "/api/documents/upload",
        files={
            "files": (
                "notes.txt",
                b"Alpha calibration uses held-out validation data. Reranking selects final evidence.",
                "text/plain",
            )
        },
    )

    assert upload_response.status_code == 200
    payload = upload_response.json()
    assert payload["failed"] == []
    assert len(payload["uploaded"]) == 1
    record = payload["uploaded"][0]
    assert record["filename"] == "notes.txt"
    assert record["chunk_count"] == 1
    assert "stored_path" not in record
    assert "chunk_cache_path" not in record

    query_response = client.post(
        "/api/query",
        json={
            "query": "What does alpha calibration use?",
            "top_k": 3,
            "scope": {
                "mode": "uploaded",
                "selected_doc_ids": [record["doc_id"]],
            },
        },
    )
    assert query_response.status_code == 200
    query_payload = query_response.json()
    assert query_payload["answer"]["text"]
    assert query_payload["answer"]["grounding_status"] == "grounded"
    assert query_payload["citations"]
    assert query_payload["final_evidence"]
    assert query_payload["final_evidence"][0]["evidence_id"] == "E1"
    assert "[E1]" in query_payload["answer"]["text"]
    assert "References:" not in query_payload["answer"]["text"]
    markers = set(re.findall(r"\[(E\d+)\]", query_payload["answer"]["text"]))
    citation_ids = {item["evidence_id"] for item in query_payload["citations"]}
    evidence_ids = {item["evidence_id"] for item in query_payload["final_evidence"]}
    assert markers <= citation_ids
    assert markers <= evidence_ids
    assert [stage["stage"] for stage in query_payload["retrieval_trace"]] == [
        "BM25",
        "Dense",
        "Fusion",
        "Reranker",
        "Final Evidence",
    ]
    assert query_payload["scope"]["doc_count"] == 1
    assert set(query_payload["retrieval"]) == {"bm25", "dense", "fusion", "reranked"}
    assert "total" in query_payload["timing"]
    assert query_payload["query_plan"]["sub_questions"]
    assert query_payload["support_label"] == "supported"

    delete_response = client.delete(f"/api/documents/{record['doc_id']}")
    assert delete_response.status_code == 200
    assert delete_response.json()["documents"] == []


def test_pdf_source_endpoint_serves_registered_pdf_without_local_path() -> None:
    client = _client(_test_root())
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Word2Vec appears on this PDF page.")
    pdf_bytes = document.tobytes()
    document.close()

    upload_response = client.post(
        "/api/documents/upload",
        files={"files": ("lecture.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload_response.status_code == 200
    record = upload_response.json()["uploaded"][0]
    assert record["is_pdf"] is True
    assert record["source_url"] == f"/api/documents/{record['doc_id']}/file"
    assert "stored_path" not in record

    file_response = client.get(f"/api/documents/{record['doc_id']}/file")
    assert file_response.status_code == 200
    assert file_response.headers["content-type"].startswith("application/pdf")
    assert file_response.headers["content-disposition"].startswith("inline")


def test_multi_intent_query_response_includes_support_status() -> None:
    client = _client(_test_root())
    client.post(
        "/api/documents/upload",
        files={
            "files": (
                "notes.txt",
                b"Word2Vec learns word embeddings from context. A transformer uses self-attention over tokens.",
                "text/plain",
            )
        },
    )

    response = client.post(
        "/api/query",
        json={
            "query": "what is word2vec? and what is transformer?",
            "top_k": 3,
            "scope": {"mode": "uploaded", "selected_doc_ids": []},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["query_plan"]["is_multi_intent"] is True
    assert len(payload["sub_question_support"]) == 2
    assert payload["support_label"] in {"supported", "partially supported"}
    assert payload["answer"]["generation_mode"] in {"mock", "llm", "fallback"}


def test_unsupported_upload_is_reported_without_crashing() -> None:
    client = _client(_test_root())

    response = client.post(
        "/api/documents/upload",
        files={"files": ("table.csv", b"a,b\n1,2", "text/csv")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["uploaded"] == []
    assert payload["failed"][0]["filename"] == "table.csv"


def test_evaluation_summary_and_run_are_offline() -> None:
    client = _client(_test_root())

    empty_summary = client.get("/api/evaluation/summary").json()
    assert empty_summary["available"] is False

    run_response = client.post(
        "/api/evaluation/run",
        json={"top_k": 5, "write_reports": True},
    )
    assert run_response.status_code == 200
    payload = run_response.json()
    assert {"bm25", "dense", "fusion", "reranked"} <= set(payload["summary_by_method"])
    assert payload["metric_rows"]
    assert payload["latency_rows"]
    assert payload["written_paths"]

    summary = client.get("/api/evaluation/summary").json()
    assert summary["available"] is True
    assert "bm25" in summary["summary_by_method"]
    assert "bm25" in summary["latency_by_method"]
