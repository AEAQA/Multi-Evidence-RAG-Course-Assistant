# ENVIRONMENT.md

## 1. Purpose

This file defines the cross-platform development environment for the project.

The project is developed on:

```text
Windows + Miniconda
macOS + Miniconda
Linux / sandbox environment
```

All setup, test and run commands should be cross-platform whenever possible.

The project must not depend on a strong GPU. The default environment should support CPU-friendly development.

---

## 2. Recommended Python version

Recommended version:

```text
Python 3.11
```

Check Python version:

```bash
python --version
```

or:

```bash
python -c "import sys; print(sys.version)"
```

---

## 3. Canonical environment file

The canonical environment file is:

```text
environment.yml
```

Environment name:

```text
rag-study-assistant
```

Create environment:

```bash
conda env create -f environment.yml
conda activate rag-study-assistant
```

Update environment:

```bash
conda env update -f environment.yml --prune
conda activate rag-study-assistant
```

Remove and recreate environment:

```bash
conda env remove -n rag-study-assistant
conda env create -f environment.yml
conda activate rag-study-assistant
```

---

## 4. Windows PowerShell setup

```powershell
conda env create -f environment.yml
conda activate rag-study-assistant
python --version
python -m pytest
```

If PowerShell cannot activate conda:

```powershell
conda init powershell
```

Then restart PowerShell.

Run app:

```powershell
python -m streamlit run app/streamlit_app.py
```

---

## 5. macOS / Linux setup

```bash
conda env create -f environment.yml
conda activate rag-study-assistant
python --version
python -m pytest
```

Run app:

```bash
python -m streamlit run app/streamlit_app.py
```

---

## 6. Cross-platform command policy

Prefer:

```bash
python -m pytest
python -m streamlit run app/streamlit_app.py
python scripts/dev.py test
python scripts/dev.py run
python scripts/dev.py eval
```

Avoid relying only on:

```bash
make test
source .venv/bin/activate
```

because these may not work on Windows by default.

---

## 7. scripts/dev.py

`scripts/dev.py` is a cross-platform command wrapper for both human developers and coding agents.

It should support:

```bash
python scripts/dev.py test
python scripts/dev.py run
python scripts/dev.py api
python scripts/dev.py ui
python scripts/dev.py ui-test
python scripts/dev.py eval
python scripts/dev.py clean
python scripts/dev.py info
```

This script is not strictly required, but it is recommended because it avoids platform-specific shell differences.

---

## 8. Environment variables

Create local `.env` from `.env.example`.

Do not commit `.env`.

Default local mode:

```text
APP_MODE=local

LLM_PROVIDER=mock
LLM_MODEL=mock-llm

RERANKER_PROVIDER=mock
RERANKER_MODEL=mock-reranker

ASR_PROVIDER=mock
ASR_MODEL=mock-asr

VISION_PROVIDER=mock
VISION_MODEL=mock-vision

OPENAI_API_KEY=xxx
SILICONFLOW_API_KEY=xxx
ANTHROPIC_API_KEY=xxx
```

In local mode, the system must run without real API keys.

---

## 9. Dependency policy

Base dependencies should be CPU-friendly and cross-platform.

Core dependencies:

```text
pymupdf
rank-bm25
numpy
pandas
scikit-learn
pydantic
python-dotenv
streamlit
pytest
matplotlib
plotly
requests
openai
```

Optional dependencies:

```text
sentence-transformers
faiss-cpu
hnswlib
```

Do not make unit tests depend on optional dependencies.

---

## 10. Dense retrieval dependency note

For unit tests, use fake deterministic embeddings.

Do not make unit tests depend on:

```text
sentence-transformers
MiniLM
SBERT
external model download
GPU
internet access
```

Real embedding models may be used only in local-demo or API-enhanced mode.

If `faiss-cpu` causes installation issues on Windows, use `scikit-learn` cosine similarity or `NearestNeighbors` as fallback.

---

## 11. Docker policy

Docker is not required for MVP.

Add Docker only if:

* the app already runs locally;
* tests pass;
* environment setup becomes difficult for collaboration;
* deployment requires containerization.

Until then, use Miniconda + environment.yml + scripts/dev.py.

---

## 12. Verification checklist

After setup, run:

```bash
python -c "import platform; print(platform.system())"
python -c "import sys; print(sys.executable)"
python -m pytest
```

Run app:

```bash
python -m streamlit run app/streamlit_app.py
```

If API keys are missing, the app should still run in mock/local mode.

React product UI commands require Node/npm:

```bash
cd frontend
npm install
cd ..
python scripts/dev.py api
python scripts/dev.py ui
python scripts/dev.py ui-test
```

On Windows PowerShell, `npm --version` may resolve to `npm.ps1` and be blocked
by execution policy. `scripts/dev.py` uses `npm.cmd` and adds the common Node
installation directory to the child-process PATH, so prefer:

```powershell
python scripts/dev.py ui-test
```

---

## 13. Common troubleshooting

### Conda command not found

Check:

```bash
conda --version
```

If not found, install Miniconda and restart terminal.

### Environment already exists

Update:

```bash
conda env update -f environment.yml --prune
```

or recreate:

```bash
conda env remove -n rag-study-assistant
conda env create -f environment.yml
```

### Streamlit command not found

Use:

```bash
python -m streamlit run app/streamlit_app.py
```

instead of:

```bash
streamlit run app/streamlit_app.py
```

### PyMuPDF import issue

The package is installed as `pymupdf`, but commonly imported as:

```python
import fitz
```
