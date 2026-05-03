# Project Memory

## Current status

Milestone 7 optional API-enhanced mode implemented.

Current milestone:

```text
Milestone 7: Optional SiliconFlow API-enhanced mode complete
M7-patch1: Streamlit Evidence Workbench complete
M7-patch2: Chat-centered RAG Study Chat with local document upload complete
M7-patch3: Three-panel RAG workbench with material scope refinement complete
M7-patch4: Streamlit performance stabilization complete
M7-patch5: Single-page Evidence Intelligence workbench refinement complete
Stage 1: FastAPI backend layer complete
Stage 2: Prompt-driven grounded answer contract complete
Stage 3: React three-panel product UI complete
```

## What works now

* `environment.yml` is valid YAML for the Miniconda environment.
* `conda env create -f environment.yml --dry-run` succeeds on Windows when Conda has permission to access its environment/cache directories.
* Basic Python package exists under `src/rag_project`.
* Local/offline configuration defaults to mock providers and does not require API keys.
* Minimal Streamlit entrypoint exists at `app/streamlit_app.py`.
* Minimal pytest suite exists under `tests/unit`.
* `python scripts/dev.py test` and `python scripts/dev.py eval` have valid entrypoints.
* `python -m compileall src tests app scripts` passes with the currently available Python.
* `.txt` files can be loaded into `DocumentPage` records.
* Text-based PDFs can be loaded with PyMuPDF.
* Text pages can be split into metadata-preserving text chunks.
* Mock/interface skeletons exist for LLM, reranker, ASR, and vision caption clients.
* `C:\Users\liangy\miniconda3\envs\rag-study-assistant\python.exe scripts\dev.py test` passes with 54 tests.
* BM25 lexical retrieval works in local/offline mode.
* Fake deterministic dense retrieval works without external models, GPU, API keys, or network calls.
* Reciprocal rank fusion merges BM25 and dense results.
* Retrieval pipeline returns BM25-only, dense-only, hybrid fusion, and fusion + mock reranker outputs.
* `scripts/dev.py clean` removes pytest/cache artifacts generated during delivery.
* Prompt builder marks retrieved context as untrusted reference material and blocks prompt-injection instructions from being treated as system instructions.
* Answer generator selects Top-5 evidence, calls the mock LLM, and returns answer, citations, evidence chunks, and retrieval explanation.
* Mock LLM reports insufficient evidence when no chunks are available.
* Retrieval metrics foundation is implemented: Recall@1/3/5, MRR@5, NDCG@5, one-query evaluation, and mean metric aggregation.
* Evaluation query loader reads `data/eval/queries.jsonl`.
* Offline evaluation runner compares BM25, dense, fusion, and reranked retrieval.
* Evaluation runner records per-query latency and writes reports under `reports/evaluation/`.
* A 10-query synthetic evaluation dataset is available for local smoke runs.
* `C:\Users\liangy\miniconda3\envs\rag-study-assistant\python.exe scripts\dev.py eval` writes retrieval metrics, latency metrics, and error cases reports.
* Streamlit MVP dashboard has two pages: RAG Assistant and Evaluation Dashboard.
* RAG Assistant runs local sample retrieval, grounded mock answer generation, evidence display, and method result panels.
* Evaluation Dashboard reads or creates local reports and displays metrics, charts, latency, and error cases.
* Streamlit app smoke check starts successfully in headless mode.
* Image-aware PDF ingestion can extract embedded PDF images into `image` chunks with image path, bbox, nearby text, mock/fallback caption, and retrievable text.
* `load_pdf_chunks()` can return mixed text, image, and lightweight table chunks while preserving the original `load_pdf()` text-page behavior.
* Image-only PDFs can produce retrievable image chunks.
* Caption failures, image save failures, no-image PDFs, and table detection failures have non-blocking fallbacks.
* Streamlit evidence display can show image metadata and local thumbnails when image files exist.
* Optional SiliconFlow provider clients exist for LLM answer generation, reranking, and best-effort vision captioning.
* Provider factories create SiliconFlow clients only when `APP_MODE=api`, provider/model settings, and `SILICONFLOW_API_KEY` are present.
* Missing API configuration or API failures fall back to mock clients.
* Streamlit runtime status shows provider/model values and redacted `SILICONFLOW_API_KEY=set/missing` only.
* `python scripts/dev.py api-smoke` is available for optional live API smoke checks.
* Streamlit can be launched directly from IDE tooling because `app/streamlit_app.py` bootstraps the local `src` path.
* `docs/specs/08_frontend_backend_redesign_spec.md` records the frontend/backend redesign direction after reviewing `frontend_reference/`.
* A lightweight app service layer exists under `src/rag_project/app_services/`.
* Provider status is normalized into UI-safe labels and never exposes the SiliconFlow API key.
* Sample corpus summary and sample questions are available for the workbench.
* Query orchestration is encapsulated by `QueryService`, including retrieval, answer generation, timing, suggestions and method diagnostics.
* Streamlit Page 1 is now `Study Query Workbench` and no longer auto-runs retrieval from the default query text.
* Evidence chunks are shown in collapsible cards, and BM25/Dense/Fusion/Reranked diagnostics include confidence bars and recommendations.
* Evaluation Dashboard sections are grouped into method summary, recall coverage, ranking quality, latency and weak cases.
* Streamlit Page 1 is now `RAG Study Chat`, with upload/select corpus -> ask question -> answer with citations as the main interaction.
* `.txt` and `.pdf` files can be uploaded locally from the Streamlit UI.
* Uploaded documents are stored under ignored `data/processed/uploads/`.
* Uploaded corpus metadata is stored in ignored `data/processed/corpus_registry.json`.
* Uploaded PDFs use the existing image-aware `load_pdf_chunks()` path.
* Corpus scope supports sample only, uploaded only, and sample + uploaded.
* Retrieval details are available in expanders instead of occupying the main answer surface.
* Streamlit Page 1 uses a three-panel layout: Materials / Knowledge Base, Chat, and Evidence / Retrieval.
* Uploaded `.md` and `.markdown` files are supported through the text loader and chunker path.
* If no uploaded documents are selected, uploaded retrieval searches all uploaded documents by default.
* If uploaded documents are selected, retrieval is restricted to chunks from those selected `doc_id`s.
* Final answer evidence is represented by scored reranked `RetrievalResult` rows for the right evidence panel.
* Uploaded documents now write processed chunk caches under ignored `data/processed/chunks/` during upload ingestion.
* Normal Streamlit reruns load uploaded document metadata from the registry without loading chunks.
* Uploaded corpus loading reads cached chunks and only falls back to raw ingestion for legacy registry records without cache metadata.
* Streamlit caches provider/config state, uploaded metadata, corpus bundles, evaluation reports, and retrieval pipelines with `st.cache_resource` / `st.cache_data`.
* Retrieval pipelines can be reused by corpus signature instead of rebuilding BM25 and fake dense indexes for every query.
* Query timing now reports BM25, dense, fusion, reranker, retrieval, pipeline build, generation, and total timings.
* The right-panel debug view includes rerun, document metadata loading, chunk loading, upload ingestion, and corpus signature diagnostics.
* Streamlit now presents the main experience as a single-page three-panel RAG workbench instead of a separate analytics-dominant dashboard.
* The center chat answer includes stable evidence markers such as `[E1]`, `[E2]`, and `[E3]`.
* Citation buttons update Streamlit session state so the right Evidence Intelligence panel can highlight the selected evidence card.
* Query output now includes `final_evidence`, `retrieval_trace`, and `scope` fields for product-like evidence interaction.
* Evidence Intelligence integrates cited evidence, retrieval flow cards, method comparison tabs, evaluation metrics and debug details in the right panel.
* Streamlit dataframe rows now serialize image/table `bbox` metadata as strings to avoid PyArrow mixed list/scalar conversion errors.
* The legacy Streamlit sidebar is hidden so the single-page workbench uses the full browser width.
* Method comparison output is verified to include BM25, Dense, Fusion and Reranked results for the sample query path.
* `C:\Users\liangy\miniconda3\envs\rag-study-assistant\python.exe scripts\dev.py test` passes with 91 tests.
* Stage 1 FastAPI adapter exists under `src/rag_project/api/`.
* FastAPI exposes health, status, documents, upload, delete, query and evaluation endpoints for the React product UI.
* `POST /api/query` returns product-ready answer text, citations, final evidence, retrieval trace, method result groups, timing, scope and diagnostics.
* The FastAPI app factory accepts temporary registry/upload/cache/report paths for isolated tests.
* `python scripts/dev.py api` starts the FastAPI adapter with uvicorn.
* `python scripts/dev.py test -- tests/unit/test_fastapi_api.py -vv` passes 5 FastAPI endpoint tests.
* `python scripts/dev.py eval` completes and writes retrieval metrics, latency metrics and error cases reports after Stage 1.
* Stage 2 prompt-driven grounded answer contract is implemented.
* Grounded prompts label evidence blocks as `[E1]`, `[E2]`, `[E3]` and request inline citation markers after supported claims.
* Mock LLM fallback now returns deterministic natural-language answers with inline citation markers instead of raw chunk concatenation.
* QueryService no longer appends a trailing `References:` block for grounded answers.
* `/api/query` inline markers resolve through both `citations` and `final_evidence`.
* `python scripts/dev.py test -- tests/unit/test_generation.py tests/unit/test_query_service.py tests/unit/test_fastapi_api.py tests/unit/test_api_providers.py tests/unit/test_mock_clients.py -vv` passes 30 Stage 2-related tests.
* `python scripts/dev.py test` passes 91 tests after Stage 2.
* `python scripts/dev.py eval` completes after Stage 2 and rewrites retrieval metrics, latency metrics and error cases reports.
* `frontend/` now contains a Vite + React + TypeScript product UI for the FastAPI adapter.
* The React UI implements the Stage 3 three-panel workbench: Knowledge Base, Grounded Study Chat and Evidence Intelligence.
* React loads status/documents/evaluation summary, uploads and deletes local documents, submits `/api/query`, and renders evidence intelligence from the Stage 1/2 response contract.
* React parses inline citation markers such as `[E1]` into anchors and highlights the matching right-panel evidence card.
* Mocked React tests are written for the three-panel shell, document state, upload failure, selected scope payloads, citation linking, retrieval methods and diagnostics.
* `python scripts/dev.py ui` and `python scripts/dev.py ui-test` are available for the React frontend.
* `C:\Users\liangy\miniconda3\envs\rag-study-assistant\python.exe scripts\dev.py test -- tests\unit\test_fastapi_api.py tests\unit\test_query_service.py tests\unit\test_generation.py -vv` passes 18 focused Stage 3 regression tests.
* `C:\Users\liangy\miniconda3\envs\rag-study-assistant\python.exe scripts\dev.py ui-test` passes 6 mocked React tests after Node/npm installation.
* `C:\Users\liangy\miniconda3\envs\rag-study-assistant\python.exe scripts\dev.py test` passes 91 Python tests after Stage 3 frontend verification.
* `C:\Users\liangy\miniconda3\envs\rag-study-assistant\python.exe scripts\dev.py eval` completes after Stage 3 and rewrites retrieval metrics, latency metrics and error cases reports.
* Stage 4 per-query retrieval method analysis is implemented in the React Evidence Intelligence panel.
* `Analyze methods` derives current-query coverage, overlap, latency, score distribution, citation coverage and source/type diversity from the existing `/api/query` response without rerunning RAG.
* The fixed evaluation section is now labeled `Offline Benchmark` and explains that Recall/MRR/NDCG come from the fixed eval set, not the active conversation.
* Insufficient-evidence query responses show a safe method-analysis empty state instead of pretending current-query Recall/MRR/NDCG are available.
* `C:\Users\liangy\miniconda3\envs\rag-study-assistant\python.exe scripts\dev.py ui-test` passes 8 mocked React tests after Stage 4.
* `C:\Program Files\nodejs\npm.cmd run build` passes after sandbox escalation for Vite/esbuild child-process execution.
* `C:\Users\liangy\miniconda3\envs\rag-study-assistant\python.exe scripts\dev.py test -- tests\unit\test_fastapi_api.py tests\unit\test_query_service.py -vv` passes 13 focused backend regression tests after Stage 4.
* `C:\Users\liangy\miniconda3\envs\rag-study-assistant\python.exe scripts\dev.py test` passes 91 Python tests after Stage 4.
* `C:\Users\liangy\miniconda3\envs\rag-study-assistant\python.exe scripts\dev.py eval` completes after Stage 4 and rewrites retrieval metrics, latency metrics and error cases reports.
* `C:\Users\liangy\miniconda3\envs\rag-study-assistant\python.exe -m compileall scripts src tests app` passes after Stage 4.
* Stage 5A React product UI simplification is implemented.
* React no longer loads `/api/evaluation/summary` on startup and no longer shows `Offline Benchmark` in the primary UI.
* The evaluation API, reports and `python scripts/dev.py eval` pipeline remain intact for fixed eval-set assessment.
* The React layout now has bounded draggable resize handles for the left Knowledge Base and right Evidence Intelligence panels.
* Evidence display now labels `image` chunks as `Image evidence` and downgrades `table` or unknown types to `Text evidence` until a real table preview exists.
* Evidence Intelligence code is split into evidence card, retrieval flow, method analysis and score bar components.
* The UI styling is updated toward a lighter CourseMate-like product surface with a slim top bar, softer panels, rounded controls and blue/cyan accents.
* `C:\Users\liangy\miniconda3\envs\rag-study-assistant\python.exe scripts\dev.py ui-test` passes 10 mocked React tests after Stage 5A.
* `C:\Program Files\nodejs\npm.cmd run build` passes after sandbox escalation for Vite/esbuild child-process execution after Stage 5A.
* `C:\Users\liangy\miniconda3\envs\rag-study-assistant\python.exe scripts\dev.py test -- tests\unit\test_fastapi_api.py tests\unit\test_query_service.py -vv` passes 13 focused backend regression tests after Stage 5A.
* `C:\Users\liangy\miniconda3\envs\rag-study-assistant\python.exe scripts\dev.py test` passes 91 Python tests after Stage 5A.
* `C:\Users\liangy\miniconda3\envs\rag-study-assistant\python.exe scripts\dev.py eval` completes after Stage 5A and rewrites retrieval metrics, latency metrics and error cases reports.
* `C:\Users\liangy\miniconda3\envs\rag-study-assistant\python.exe -m compileall scripts src tests app` passes after Stage 5A.

## What is missing

Remaining items after Milestone 7:

* final report and demo packaging
* optional local session history
* optional richer uploaded document management
* optional real ASR/TTS demo enhancement

## Key commands

```bash
conda env create -f environment.yml
conda activate rag-study-assistant
python -m pytest
python -m streamlit run app/streamlit_app.py
python scripts/dev.py test
python scripts/dev.py run
python scripts/dev.py api
python scripts/dev.py eval
python scripts/dev.py api-smoke
```

## Known issues

* The global/current Python detected before environment creation was 3.13.9. Use the Conda environment from `environment.yml` for Python 3.11.
* `conda run -n rag-study-assistant python -m pytest` hit Windows/Conda wrapper output issues; direct environment Python works.
* `python scripts/dev.py clean` removes `__pycache__` successfully, but some pytest temp directories created by earlier sandboxed runs still return Windows `PermissionError`. They are ignored by git and may need manual deletion after closing any process holding them.
* Real ASR is not implemented in M7. `ASR_PROVIDER` should remain `mock` until a SiliconFlow ASR client and browser audio flow are added.
* `VISION_PROVIDER` must be a provider name such as `mock` or `siliconflow`; put the model id in `VISION_MODEL`.
* M7-patch1 method confidence labels are UI diagnostics, not statistically calibrated probabilities.
* Uploaded files, processed image assets, registry metadata, and chunk caches live under `data/processed/`, which is ignored by git.
* M7-patch2 keeps FastAPI/React deferred; Streamlit remains the MVP UI.
* `python -m pytest` may hit Windows temp-directory `PermissionError`; use a workspace-local `--basetemp` path if needed.
* Stage 1 FastAPI tests require `fastapi`, `uvicorn`, `python-multipart` and `httpx`; keep the Conda environment synchronized with `environment.yml`.
* On Windows PowerShell, `npm --version` may hit the `npm.ps1` execution policy
  even when Node is installed. `scripts/dev.py` resolves `npm.cmd` and
  temporarily adds `C:\Program Files\nodejs` to the child-process PATH.

## Next step

Continue with full-stack browser verification and Stage 5 demo packaging.
