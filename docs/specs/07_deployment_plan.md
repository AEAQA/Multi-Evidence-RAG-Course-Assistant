# Deployment Plan

## MVP deployment

MVP deployment is local:

```bash
python -m streamlit run app/streamlit_app.py
```

## Environment setup

Use:

```bash
conda env create -f environment.yml
conda activate rag-study-assistant
python -m pytest
python -m streamlit run app/streamlit_app.py
```

## Local/offline mode

Default mode:

```text
APP_MODE=local
```

In local mode:

* no real API key is required;
* mock LLM is used;
* mock reranker is used;
* fake deterministic embedding may be used for tests.

## API-enhanced mode

Enable by editing local `.env`:

```text
APP_MODE=api
LLM_PROVIDER=siliconflow
RERANKER_PROVIDER=siliconflow
```

Actual API keys must be stored only in `.env`.

Do not commit `.env`.

## GitHub sharing

Before pushing:

```bash
python -m pytest
git status
```

Ensure the following files are not committed:

```text
.env
data/raw/private/
large model files
API keys
```

## GitHub Actions

Minimal CI should run:

```bash
python -m pytest
```

CI must not require API keys.

## Docker

Docker is optional and not part of MVP.

Add Docker only after:

* local app runs;
* tests pass;
* environment.yml is stable;
* collaborators need containerized setup;
* deployment requires it.

## Demo checklist

Before final presentation:

* app launches locally;
* sample documents are included;
* at least 10 evaluation queries exist;
* BM25/Dense/Fusion/Reranker comparison works;
* final answers show evidence and citations;
* image/table chunks are displayed if implemented;
* no real API keys are visible.
