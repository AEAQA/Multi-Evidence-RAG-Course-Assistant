# Evidence-Grounded RAG Study Assistant

**Evidence Workbench** — A retrieval-augmented question answering system that compares BM25 lexical retrieval, dense semantic retrieval, hybrid fusion, and LLM-based reranking before generating grounded answers from retrieved evidence. Built for the IEMS5726 Data Science in Practice course.

This is not a generic chatbot. It is a data science system demonstrating the full RAG pipeline: PDF ingestion, multi-strategy retrieval, evidence filtering, grounded generation with inline citations, offline evaluation, and a deployable product UI.

## Core Features

- **Multi-format document ingestion** — PDF, TXT, MD loaded via PyMuPDF with text, image, and table extraction
- **Four retrieval strategies compared side-by-side** — BM25 (lexical), Dense (semantic, SHA256 fake vectors offline), RRF Hybrid Fusion, Reranker
- **Intent-aware query planning** — Deterministic router + optional SiliconFlow planner; multi-intent decomposition
- **Grounded answer generation** — Top-K evidence used with inline `[E1][E2][E3]` citation markers; refused when evidence insufficient
- **Citation-to-evidence linking** — Click inline [E1] to scroll and highlight matching evidence card
- **PDF Open Page** — Click evidence source to open PDF at exact page via browser
- **Evidence quality filtering** — Table placeholder chunks and OCR noise detected and removed
- **Evidence Intelligence Panel** — Cited evidence cards, Retrieval Flow, Method Comparison, per-query diagnostics
- **Historical citation linking** — Clicking citations in older messages restores that turn's cached evidence
- **Collapsible Materials Drawer** — Upload and select knowledge-base scope
- **MethodHowItWorks** — Educational explanations for BM25/Dense/Fusion/Reranker
- **Two-column layout** — Chat Workspace (left) | Evidence Intelligence (right)
- **Offline-first** — Fully functional in local mode with no API keys, GPU, or network
- **Optional SiliconFlow API mode** — Drop-in real LLM and reranker
- **Streamlit backup preserved** — Original MVP dashboard at `app/streamlit_app.py`

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend (product) | Vite + React 18 + TypeScript, hand-rolled CSS |
| Frontend (backup) | Streamlit (preserved) |
| Backend API | FastAPI + uvicorn |
| RAG Core | Pure Python, offline-first |
| BM25 | Pure Python BM25 implementation |
| Dense Retrieval | SHA256 hashing vectors (offline) / SBERT (optional) |
| Fusion | Reciprocal Rank Fusion (RRF) |
| Reranker | Mock (offline) / SiliconFlow API (optional) |
| LLM Generation | Mock (offline) / SiliconFlow API (optional) |
| Query Planning | Deterministic router + optional SiliconFlow planner |
| PDF Ingestion | PyMuPDF (text, image, table extraction) |
| Testing | pytest (103 Python tests), Vitest (13 React tests) |
| Evaluation | Offline Recall@k, MRR, NDCG pipeline |
| Environment | Miniconda, Python 3.11 |

## Quick Start

### 1. Create environment

```bash
conda env create -f environment.yml
conda activate rag-study-assistant
```

### 2. Configure

```bash
cp .env.example .env
```

Default local/offline mode requires no API keys. Keep `APP_MODE=local`.

### 3. Start backend

```bash
python scripts/dev.py api
# → http://localhost:8000, Swagger docs at /docs
```

### 4. Start frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173 (proxies to backend)
```

### 5. (Alternative) Streamlit backup

```bash
python scripts/dev.py run
```

## Key Commands

```bash
python scripts/dev.py info          # Environment status
python scripts/dev.py api           # FastAPI backend
python scripts/dev.py run           # Streamlit backup
python scripts/dev.py test          # All Python tests (103)
python scripts/dev.py ui-test       # React tests (13)
python scripts/dev.py eval          # Offline evaluation
python scripts/dev.py api-smoke     # SiliconFlow smoke check
python scripts/dev.py clean         # Remove artifacts
```

## Project Structure

```
app/                        Streamlit backup
src/rag_project/            Core backend
  api/                      FastAPI adapter
  app_services/             QueryService, CorpusService, ProviderStatus
  retrieval/                BM25, Dense, Fusion, Reranker, Pipeline
  generation/               PromptBuilder + LLM clients
  query_planning/           Intent planner (deterministic + SiliconFlow)
  ingestion/                PDF/text/image/table loading
  evaluation/               Offline evaluation pipeline
frontend/src/               React product UI
  components/               10 React components
  api/client.ts             Typed API client
tests/                      Unit tests
data/eval/                  Evaluation queries (queries.jsonl)
docs/                       Documentation and specs
scripts/dev.py              Cross-platform command wrapper
```

## How It Works

```text
User Query
 → Intent Planner (route + decompose)
 → Per-sub-question Retrieval (BM25 + Dense → Fusion → Reranker)
 → Evidence Filtering (table quality, type preference)
 → Answer Generation (grounded prompt + inline citations)
 → Citation Mapping → UI Display
```

## Optional SiliconFlow API Mode

For higher-quality answers, configure `.env`:

```text
APP_MODE=api
LLM_PROVIDER=siliconflow
LLM_MODEL=deepseek-ai/DeepSeek-V3
RERANKER_PROVIDER=siliconflow
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
SILICONFLOW_API_KEY=<your-key>
```

Without a valid key, the system falls back to mock providers. The UI never exposes the real key value.

## Tests

```bash
python scripts/dev.py test          # 103 Python tests
python scripts/dev.py ui-test       # 13 React tests
python scripts/dev.py eval          # Offline evaluation
python -m compileall scripts src tests app  # Syntax check
```

## Future Work

- Deeper multimodal evidence (video, audio, complex table rendering)
- Voice interaction (ASR scaffolding exists, not productized)
- Chinese and multilingual query support
- Stronger table reconstruction with HTML rendering in evidence cards
- Richer evaluation dataset with more annotated queries
- Deployment hardening (HTTPS, auth, rate limiting)

## Safety

- Do not commit `.env` — use `.env.example` as template
- Do not commit private data (`data/raw/`, `data/processed/`, `reports/` are git-ignored)
- Prompt injection protection: retrieved context is marked as untrusted reference material
- LLM refuses to answer when evidence is insufficient rather than hallucinating
- API keys never exposed in UI or logs
