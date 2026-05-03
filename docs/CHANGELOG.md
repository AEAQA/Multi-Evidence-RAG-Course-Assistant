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
* Milestone 7 optional SiliconFlow API-enhanced mode with provider factories, LLM client, reranker client, vision caption client, and mock fallbacks.
* `python scripts/dev.py api-smoke` for optional live API smoke checks.
* Unit tests for SiliconFlow fake response parsing, API failure fallback, config redaction, and no-key provider fallback.
* Frontend/backend redesign spec based on the `frontend_reference/` review.
* M7-patch1 app service layer for provider status, corpus summary and query orchestration.
* M7-patch1 workbench diagnostics with method confidence labels, recommendations, timing and suggestions.
* Unit tests for provider status, corpus service, query service and explicit workbench run behavior.
* M7-patch2 local `.txt` and `.pdf` upload support for the Streamlit app.
* Local uploaded-corpus registry under ignored `data/processed/corpus_registry.json`.
* Corpus selection for sample-only, uploaded-only, and combined sample + uploaded querying.
* Unit tests for upload ingestion, registry failures, delete behavior, combined corpus loading, and selected chunk querying.
* M7-patch3 `.md` and `.markdown` upload support.
* M7-patch3 scored final evidence results for the right evidence panel.
* Unit tests for optional material selection semantics and chunk-level evidence row metadata.
* M7-patch4 processed chunk cache for uploaded documents under ignored `data/processed/chunks/`.
* M7-patch4 timing instrumentation for app reruns, document metadata/chunk loading, upload ingestion, BM25, dense retrieval, fusion, reranker, generation, and total query time.
* Unit tests for chunk-cache loading, metadata-only registry reads, legacy registry cache upgrade, prebuilt retrieval pipeline usage, and stable corpus signatures.
* M7-patch5 evidence IDs, final evidence rows, retrieval trace stages and query scope output for citation-aware UI interaction.
* Unit tests for evidence markers, evidence IDs, retrieval trace output and Streamlit score helper behavior.
* Stage 1 FastAPI adapter under `src/rag_project/api/` for health, status, documents, upload, delete, query and evaluation endpoints.
* FastAPI `TestClient` coverage for endpoint shape, upload/query/delete flow, unsupported upload handling and offline evaluation.
* Stage 2 prompt-driven grounded answer contract with inline evidence markers in generated answer text.
* Tests for natural-language mock answers, marker-to-citation mapping and FastAPI inline citation response shape.
* Stage 3 Vite + React + TypeScript product UI under `frontend/`.
* React Knowledge Base, Grounded Study Chat and Evidence Intelligence panels.
* Typed React API client for status, documents, upload, delete, query and evaluation summary endpoints.
* Inline citation-anchor rendering and evidence-card highlight behavior for markers such as `[E1]`.
* Mocked React tests for three-panel rendering, document state, upload failure, scope payloads, citation linking, retrieval method tabs and diagnostics.
* `python scripts/dev.py ui` and `python scripts/dev.py ui-test` commands.
* Stage 4 React per-query method analysis behind `Analyze methods`.
* Current-query coverage, rank-overlap, latency, score-distribution, citation-coverage and source-diversity cards derived from `/api/query`.
* Safe insufficient-evidence method-analysis empty state.

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
* Streamlit runtime sidebar now shows provider/model status and redacted SiliconFlow key status.
* Dashboard query execution now injects provider-created LLM and reranker clients while preserving mock fallback.
* Streamlit app now bootstraps the local `src` path when launched directly from IDE tooling.
* Config repr no longer exposes the SiliconFlow API key in assertion failures or logs.
* `.env.example` clarifies provider-vs-model fields for optional vision and deferred ASR.
* Streamlit Page 1 is now `Study Query Workbench` with explicit button-triggered retrieval instead of default query auto-run.
* Evidence display now uses collapsible evidence cards and a separate diagnostics panel for BM25, Dense, Fusion and Reranked methods.
* Evaluation Dashboard is grouped into method summary, recall coverage, ranking quality, latency and weak cases sections.
* Streamlit Page 1 is now `RAG Study Chat`, with answer/citation flow as the primary surface and retrieval details moved into expanders.
* README/spec positioning now allows `RAG chatbot` wording while clarifying that the project is not a generic LLM chatbox.
* Streamlit Page 1 now uses a fixed three-panel RAG workbench: materials on the left, chat in the center, evidence/retrieval methods on the right.
* Uploaded document selection now acts as an optional corpus-scope filter; empty selection searches all uploaded documents.
* Uploaded corpus loading now reads processed chunk caches on normal reruns instead of reprocessing raw PDFs/text/markdown files.
* Streamlit now caches runtime/provider state, uploaded metadata, corpus bundles, evaluation reports, and retrieval pipelines.
* Query orchestration can accept a prebuilt retrieval pipeline so BM25 and fake dense indexes can be reused for the active corpus.
* Streamlit primary UI now behaves as a single-page Evidence Intelligence workbench rather than a separate dashboard-led experience.
* Center answer panel now includes citation marker controls that highlight matching evidence in the right panel.
* Evaluation metrics are now integrated into a collapsed right-panel section so DS evidence remains available without dominating the chat experience.
* The single-page Streamlit workbench now hides the legacy sidebar and uses a wider main container.
* `environment.yml` now includes FastAPI runtime/test dependencies: `fastapi`, `uvicorn`, `python-multipart` and `httpx`.
* `scripts/dev.py` now includes `python scripts/dev.py api` for the FastAPI adapter.
* Grounded prompts now label evidence as `[E1]`, `[E2]`, and `[E3]` and instruct providers to use inline citation markers.
* Mock LLM fallback now produces deterministic natural-language answers instead of concatenating raw chunk text behind `Based on the retrieved evidence`.
* QueryService now avoids trailing `References:` blocks for grounded answers and preserves inline marker-to-evidence mapping.
* `.gitignore` now ignores local frontend dependency/build/test artifacts.
* `.gitignore` now ignores TypeScript build-info files and Vite config emit
  artifacts produced by frontend production builds.
* `scripts/dev.py` resolves `npm.cmd` on Windows and adds the common Node
  install directory to child-process PATH for frontend commands.
* Right-panel `Evaluation metrics` is now `Offline Benchmark` and explicitly
  labels Recall/MRR/NDCG as fixed eval-set metrics rather than current-query
  scores.

### Known cleanup notes

* Some pytest temp directories from earlier Windows runs may remain if the OS reports `PermissionError`; they are ignored by git.
* On Windows PowerShell, use `npm.cmd` or `scripts/dev.py` if `npm.ps1` is
  blocked by execution policy.

### Fixed

* Resolved Conda YAML parsing failure caused by invalid list syntax in `environment.yml`.
* Fixed Streamlit/PyArrow dataframe conversion for image metadata by rendering `bbox` as a string instead of mixing list and scalar values.
* Verified Method Comparison has non-empty BM25, Dense, Fusion and Reranked groups for the sample query path.
