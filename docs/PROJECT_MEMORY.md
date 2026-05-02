# Project Memory

## Current status

Milestone 0 repository bootstrap implemented.

Current milestone:

```text
Milestone 2: Retrieval baselines complete
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
* `C:\Users\liangy\miniconda3\envs\rag-study-assistant\python.exe scripts\dev.py test` passes with 19 tests.
* BM25 lexical retrieval works in local/offline mode.
* Fake deterministic dense retrieval works without external models, GPU, API keys, or network calls.
* Reciprocal rank fusion merges BM25 and dense results.
* Retrieval pipeline returns BM25-only, dense-only, hybrid fusion, and fusion + mock reranker outputs.
* `scripts/dev.py clean` removes pytest/cache artifacts generated during delivery.

## What is missing

Remaining items after Milestone 2:

* evaluation module
* Streamlit dashboard
* grounded answer generation
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

Start Milestone 3: grounded answer generation with prompt-injection-aware prompt building and mock LLM answer generation.
