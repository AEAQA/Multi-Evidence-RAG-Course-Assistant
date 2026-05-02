# Voice-enabled Image-aware RAG Study Assistant

Offline-first Data Science in Practice project comparing BM25, dense retrieval, hybrid fusion, reranking, and grounded RAG answer generation over course materials.

This is not a generic chatbot. The system retrieves evidence from local study materials before generating answers with citations.

## Current Status

Milestone 7 optional SiliconFlow API mode is implemented. M7-patch1 adds a
more usable Streamlit Evidence Workbench while preserving offline/mock defaults.

## Environment

Create the recommended Conda environment:

```bash
conda env create -f environment.yml
conda activate rag-study-assistant
```

Local/offline mode is the default and does not require API keys.

## Commands

```bash
python scripts/dev.py info
python scripts/dev.py test
python scripts/dev.py run
python scripts/dev.py eval
python scripts/dev.py api-smoke
```

If `conda run` has encoding issues on Windows, call the environment Python directly:

```powershell
C:\Users\liangy\miniconda3\envs\rag-study-assistant\python.exe -m pytest --basetemp pytest_runs\manual
```

## Project Layout

```text
app/                 Streamlit frontend
src/rag_project/     Core backend package
tests/               Unit and integration tests
data/samples/        Public sample documents
data/eval/           Evaluation queries
data/raw/            Local private raw data, ignored by git
reports/             Evaluation reports and figures
docs/specs/          SDD project specifications
```

## Implemented Baselines

Current local/offline retrieval methods:

```text
BM25-only
Fake dense-only
BM25 + dense reciprocal rank fusion
BM25 + dense fusion + mock reranker
```

## Grounded Generation

Current local/offline answer generation:

```text
Top-k retrieved evidence
→ prompt with untrusted-context warning
→ mock LLM answer
→ citations + evidence list + retrieval explanation
```

If no evidence is available, the generator returns an insufficient-evidence response instead of inventing an answer.

## Evaluation

Run the local/offline retrieval evaluation:

```bash
python scripts/dev.py eval
```

The evaluator reads `data/eval/queries.jsonl`, compares BM25, fake dense, fusion, and reranked retrieval, then writes:

```text
reports/evaluation/retrieval_metrics.csv
reports/evaluation/latency_metrics.csv
reports/evaluation/error_cases.md
```

## Dashboard

Run the Streamlit MVP dashboard:

```bash
python scripts/dev.py run
```

The app includes:

```text
Study Query Workbench
Evaluation Dashboard
```

The Study Query Workbench uses the public synthetic sample corpus, requires an
explicit `Run evidence query` click, shows a grounded answer with citations,
highlights collapsible evidence cards, and exposes BM25, Dense, Fusion, and
Reranked diagnostics with confidence labels and recommendations. The Evaluation
Dashboard reads or creates local reports and displays method summary, recall,
ranking quality, latency, and weak cases.

ASR and TTS are not live features in M7-patch1. ASR remains a mock/planned
status in the UI until a real audio input path and provider client are added.

## Image-Aware PDF Ingestion

The original text-only PDF loader remains available through `load_pdf()`.
Milestone 6 adds `load_pdf_chunks()` for unified text, image, and lightweight
table chunks:

```python
from rag_project.ingestion import load_pdf_chunks

chunks = load_pdf_chunks("data/raw/lecture.pdf")
```

Image chunks include local image path, page, source file, bbox, nearby text, and
mock/fallback caption metadata. Caption failures, image save failures, no-image
PDFs, and table detection failures are non-blocking. Extracted images are saved
under `data/processed/images/`, which is ignored by git.

## Safety

Do not commit `.env`, real API keys, private datasets, large model weights, or private course materials.

## API Keys

Copy `.env.example` to `.env` for local secrets. Keep default mock providers for offline mode:

```text
APP_MODE=local
LLM_PROVIDER=mock
RERANKER_PROVIDER=mock
ASR_PROVIDER=mock
VISION_PROVIDER=mock
```

Real API keys, when added in later milestones, belong only in `.env`.

## Optional SiliconFlow API Mode

Keep `.env.example` committed, but put real secrets only in local `.env`:

```text
APP_MODE=api

LLM_PROVIDER=siliconflow
LLM_MODEL=<your SiliconFlow chat model>

RERANKER_PROVIDER=siliconflow
RERANKER_MODEL=<your SiliconFlow reranker model>

VISION_PROVIDER=mock
ASR_PROVIDER=mock

SILICONFLOW_API_KEY=<your local key>
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
```

Run an optional smoke check:

```bash
python scripts/dev.py api-smoke
```

Without a key, the app and smoke command use mock fallback. With a key, the
Streamlit sidebar should show `SILICONFLOW_API_KEY=set` and must never show the
real key value.

For final visual checking, run:

```bash
python scripts/dev.py run
```

Confirm that RAG Assistant still shows evidence, citations, retrieval method
tabs, and a final answer. API failures should fall back to mock output instead
of crashing.
