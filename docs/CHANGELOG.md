# Changelog

## Unreleased

### Added

* Initial project guidance.
* Cross-platform environment plan.
* SDD specs skeleton.
* Offline-first development policy.
* RAG architecture plan.
* Milestone 0 repository skeleton with `src`, `app`, `tests`, `data`, and `reports` directories.
* `.env.example`, `.gitignore`, README skeleton, package bootstrap, and pytest bootstrap tests.
* Placeholder evaluation entrypoint for `python scripts/dev.py eval`.
* Milestone 1 text ingestion with `.txt` loader, text-based PDF loader, and chunker.
* Shared Pydantic schemas for pages, chunks, citations, answer responses, rerank results, ASR, and vision captions.
* Mock/interface skeletons for LLM, reranker, ASR, and vision caption clients.
* Unit tests for ingestion, chunking, and mock clients.
* Milestone 2 retrieval baselines: pure-Python BM25, fake deterministic dense retrieval, reciprocal rank fusion, and retrieval pipeline.
* Shared `RetrievalResult` and `RetrievalPipelineOutput` schemas.
* Unit tests for BM25 ordering, dense determinism, hybrid fusion, and full retrieval pipeline output.
* Milestone 3 grounded answer generation with prompt builder, answer generator, evidence list, citations, and retrieval explanation.
* Prompt-injection-aware untrusted-context instruction for retrieved evidence.
* Unit tests for prompt safety, Top-5 evidence limits, insufficient evidence fallback, and answer generator outputs.
* Milestone 4 retrieval metrics foundation: Recall@1/3/5, MRR@5, NDCG@5, one-query evaluation, and mean metric aggregation.
* Unit tests for retrieval metric edge cases and aggregation.
* Milestone 4 evaluation query loader, offline evaluation runner, latency rows, CSV/Markdown report writers, and 10-query synthetic evaluation dataset.
* Unit tests for evaluation JSONL loading, retrieval method evaluation, latency rows, and report file creation.
* Milestone 5 Streamlit MVP dashboard with RAG Assistant and Evaluation Dashboard pages.
* Dashboard data helpers for sample RAG state and local evaluation report loading/creation.
* Dashboard smoke tests for app import, local RAG state, no-key local mode, and report creation.
* Milestone 6 image-aware PDF ingestion with image extraction, metadata, mock caption fallback, and unified image chunks.
* Lightweight PDF table extraction fallback that returns table chunks when PyMuPDF detects simple tables.
* Unit tests for image-only PDFs, caption failure fallback, no-image PDFs, table failure fallback, image chunk retrieval, and image metadata dashboard rows.

### Changed

* Fixed `environment.yml` syntax so Conda can parse the environment file.
* Updated `scripts/dev.py` to include `src` on `PYTHONPATH` for project commands.
* Updated `scripts/dev.py test` to use a workspace-local pytest temp directory.
* Expanded `scripts/dev.py clean` to remove pytest/cache artifacts after delivery.
* Extended answer response schema with `evidence_chunks` and `retrieval_explanation`.
* Replaced placeholder evaluation entrypoint with local/offline `python scripts/dev.py eval` pipeline.
* Replaced placeholder Streamlit page with a working evidence-first local dashboard.
* Dashboard CSV loading uses the Python standard library to avoid Pandas/NumPy import instability on Windows.
* Streamlit evidence display now shows image metadata and thumbnails when extracted image files are available.
* Fixed retrieval result table formatting to avoid a hidden Pandas dependency in the Streamlit path.

### Known cleanup notes

* Some pytest temp directories from earlier Windows runs may remain if the OS reports `PermissionError`; they are ignored by git.

### Fixed

* Resolved Conda YAML parsing failure caused by invalid list syntax in `environment.yml`.
