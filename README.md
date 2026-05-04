# Evidence-Grounded RAG Study Assistant

**Evidence Workbench** — A retrieval-augmented question answering system that compares BM25 lexical retrieval, dense semantic retrieval, hybrid fusion, and LLM-based reranking before generating grounded answers from retrieved course evidence. Built for the IEMS5726 Data Science in Practice course.

This is not a generic chatbot. It is a data science system that demonstrates the full RAG pipeline: PDF ingestion, comparative retrieval (BM25 / Dense / Fusion / Reranker), evidence quality filtering, grounded answer generation with inline citations, citation verification, evidence intelligence visualization, PDF source page linking, and offline evaluation — all through a deployable two-panel product UI.

## Key Features

- **PDF / TXT / Markdown study material ingestion** with text, image, and table extraction via PyMuPDF
- **Chunk-level evidence retrieval** with structured metadata (source file, page, type, context)
- **Four retrieval strategies compared side-by-side** — BM25 lexical, Dense semantic (SHA256-based fake vectors offline), RRF Hybrid Fusion, Reranker precision filter
- **Intent-aware query planning** — deterministic router for material/non-material classification; multi-intent question decomposition with per-sub-question evidence support
- **Grounded answer generation** with inline `[E1][E2][E3]` citation markers and insufficient-evidence refusal
- **Citation-to-evidence linking** — click inline citations to scroll and highlight matching evidence cards
- **Evidence Intelligence panel** — cited evidence cards, retrieval flow visualization, method comparison, and per-query diagnostics
- **Evidence quality filtering** — invalid table placeholder detection; OCR noise and internal ID removal
- **PDF Open page linking** — serves source PDF at exact page via registry-backed endpoint; no `file://` or local path exposure
- **FastAPI backend** (8 endpoints) + **React product UI** (10 components, hand-rolled CSS)
- **Streamlit fallback** preserved at `app/streamlit_app.py`
- **Offline-first** — fully functional without API keys, GPU, or network; all providers have mock fallbacks
- **Optional SiliconFlow API mode** — drop-in real LLM, reranker, and query planner

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend (product) | Vite + React 18 + TypeScript, hand-rolled CSS |
| Frontend (backup) | Streamlit (preserved) |
| Backend API | FastAPI + uvicorn |
| BM25 Retrieval | Pure Python Okapi BM25 implementation |
| Dense Retrieval | SHA256 hashing vectors (offline) |
| Fusion | Reciprocal Rank Fusion (RRF, k=60) |
| Reranker | Mock heuristic / SiliconFlow API (optional) |
| LLM Generation | Mock deterministic / SiliconFlow API (optional) |
| Query Planning | Deterministic router + optional SiliconFlow JSON planner |
| PDF Ingestion | PyMuPDF (text, image, table extraction) |
| Testing | pytest (Python), Vitest (React) |
| Evaluation | Recall@k, MRR, NDCG offline pipeline |
| Environment | Conda, Python 3.11 |

## Project Structure

```
app/                          Streamlit backup
src/rag_project/              Core backend package
  api/main.py                 FastAPI adapter (8 endpoints)
  app_services/               QueryService, CorpusService, ProviderStatus
  retrieval/                  BM25, Dense, Fusion, Reranker, Pipeline
  generation/                 Prompt builder, LLM clients, answer generator
  query_planning/             Deterministic + SiliconFlow intent planners
  ingestion/                  PDF/TXT/MD loading, chunking, image/table extraction
  evaluation/                 Offline evaluation pipeline
  config.py, providers.py     Environment config + provider factory
  schemas.py                  Core Pydantic data models
frontend/src/                 React product UI
  components/                 10 React components
  api/client.ts               Typed API client
tests/                        Unit tests (Python + React)
data/eval/                    Evaluation queries (queries.jsonl)
docs/                         Documentation and specs
scripts/dev.py                Cross-platform command wrapper
```

## Setup

### 1. Create Conda environment

```bash
conda env create -f environment.yml
conda activate rag-study-assistant
```

### 2. Configure environment

```bash
cp .env.example .env
```

Default local/offline mode requires no API keys. Keep `APP_MODE=local` with all providers set to `mock`.

### 3. Install frontend dependencies

```bash
cd frontend
npm install
```

### 4. Review key commands

```bash
python scripts/dev.py info          # Environment status
python scripts/dev.py api           # Start FastAPI backend
python scripts/dev.py run           # Start Streamlit backup
python scripts/dev.py test          # Run Python tests
python scripts/dev.py ui-test       # Run React tests
python scripts/dev.py eval          # Run offline evaluation
```

## Running the Application

### Start the backend

```bash
python scripts/dev.py api
```

FastAPI starts at `http://localhost:8000`. Swagger docs are available at `/docs`.

### Start the frontend

```bash
cd frontend
npm run dev
```

The Vite dev server starts at `http://localhost:5173` and proxies API requests to the backend.

### Using the application

1. Open `http://localhost:5173` in a browser.
2. Click **Manage Materials** at the bottom of the chat panel to open the materials drawer.
3. Upload course PDFs or use the built-in sample corpus.
4. Choose a retrieval scope (Sample + Uploads, Uploaded only, or Sample only).
5. Type a question in the input area and press **Enter** to send.
6. Read the grounded answer with inline citation markers `[E1]`, `[E2]`, `[E3]`.
7. The Evidence Intelligence panel slides in from the right showing:
   - **Cited Evidence cards** — source file, page, evidence type, preview text
   - **Retrieval Flow** — BM25 → Dense → Fusion → Reranker → Final Evidence
   - **Method Comparison** (collapsible) — per-method diagnostic rows
8. Click a citation `[E1]` to highlight and scroll to the matching evidence card.
9. Click **Open page** on an evidence card to view the source PDF at the exact page.

### (Alternative) Streamlit backup

```bash
python scripts/dev.py run
```

The Streamlit app provides a three-panel RAG workbench with the same service layer.

## Optional SiliconFlow API Mode

For higher-quality answers, configure `.env` with real SiliconFlow credentials:

```text
APP_MODE=api
LLM_PROVIDER=siliconflow
LLM_MODEL=deepseek-ai/DeepSeek-V3
RERANKER_PROVIDER=siliconflow
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
SILICONFLOW_API_KEY=<your-key>
```

Without a valid key, the system falls back to mock providers automatically.

## Validation / Tests

```bash
python scripts/dev.py test          # 103 Python unit tests
python scripts/dev.py ui-test       # 13 React component tests
python scripts/dev.py eval          # Offline evaluation (writes reports/)
python -m compileall scripts src tests app  # Syntax check
```

Basic manual smoke test:
1. Start backend and frontend as described in Running the Application.
2. Select the sample corpus scope.
3. Ask "What is overfitting?" — verify that a grounded answer with `[E1]` citation appears.
4. The evidence panel should slide in with at least one evidence card.
5. Click `[E1]` — the matching card should highlight.
6. Ask "What is Word2Vec? and what is a Transformer?" — verify multi-intent decomposition with sub-question support labels.

## Known Limitations and Future Work

The current version completes the core data science pipeline required for this course. The following areas represent natural directions for further product development:

- **Fuller multimodal evidence** — extended support for video, audio, and complex table rendering
- **Voice interaction** — ASR/TTS scaffolding exists in the codebase; a real audio input path would enable hands-free study
- **Stronger multilingual support** — current coverage for Chinese and other non-English queries is limited
- **Table reconstruction** — HTML rendering of detected tables directly in evidence cards
- **Larger labelled evaluation dataset** — more diverse annotated queries for robust benchmarking
- **Deployment hardening** — HTTPS, authentication, rate limiting, and production containerization

## Safety

- **Do not commit `.env`** — use `.env.example` as a reference template
- **Private data is git-ignored** — `data/raw/`, `data/processed/`, and `reports/` are excluded
- **Prompt injection protection** — retrieved document context is explicitly marked as untrusted reference material
- **No hallucination** — the generator refuses to answer when retrieved evidence is insufficient
- **API keys never exposed** — the UI shows only redacted status (`set`/`missing`)
