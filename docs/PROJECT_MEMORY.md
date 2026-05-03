# Project Memory

## Current status

Milestone 7 optional API-enhanced mode implemented.

Current milestone:

```text
Milestone 7: Optional SiliconFlow API-enhanced mode complete
M7-patch1: Streamlit Evidence Workbench complete
M7-patch2: Chat-centered RAG Study Chat with local document upload complete
M7-patch3: Three-panel RAG workbench with material scope refinement complete
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
* `C:\Users\liangy\miniconda3\envs\rag-study-assistant\python.exe scripts\dev.py test` passes with 78 tests.

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
* Uploaded files and the local corpus registry live under `data/processed/`, which is ignored by git.
* M7-patch2 keeps FastAPI/React deferred; Streamlit remains the MVP UI.

## Next step

Start Milestone 8: final report and demo packaging.
