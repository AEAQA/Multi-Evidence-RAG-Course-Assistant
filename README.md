# Voice-enabled Image-aware RAG Study Assistant

Offline-first Data Science in Practice project comparing BM25, dense retrieval, hybrid fusion, reranking, and grounded RAG answer generation over course materials.

This is not a generic chatbot. The system retrieves evidence from local study materials before generating answers with citations.

## Current Status

Milestone 2 retrieval baselines are implemented.

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
RAG Assistant
Evaluation Dashboard
```

The RAG Assistant uses the public synthetic sample corpus, shows the grounded mock answer, highlights retrieved evidence, and exposes BM25, Dense, Fusion, and Reranked result tables. The Evaluation Dashboard reads or creates local reports and displays retrieval metrics, latency, and error cases.

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
