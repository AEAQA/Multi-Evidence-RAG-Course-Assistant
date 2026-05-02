# Project Memory

## Current status

Milestone 0 repository bootstrap implemented.

Current milestone:

```text
Milestone 5: Streamlit MVP dashboard complete
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
* `C:\Users\liangy\miniconda3\envs\rag-study-assistant\python.exe scripts\dev.py test` passes with 37 tests.
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

## What is missing

Remaining items after Milestone 5:

* image-aware ingestion

## Key commands

```bash
conda env create -f environment.yml
conda activate rag-study-assistant
python -m pytest
python -m streamlit run app/streamlit_app.py
python scripts/dev.py test
python scripts/dev.py run
python scripts/dev.py eval
```

## Known issues

* The global/current Python detected before environment creation was 3.13.9. Use the Conda environment from `environment.yml` for Python 3.11.
* `conda run -n rag-study-assistant python -m pytest` hit Windows/Conda wrapper output issues; direct environment Python works.
* `python scripts/dev.py clean` removes `__pycache__` successfully, but some pytest temp directories created by earlier sandboxed runs still return Windows `PermissionError`. They are ignored by git and may need manual deletion after closing any process holding them.

## Next step

Start Milestone 6: image-aware ingestion enhancement.
