# Decisions

## Decision 001: Use Streamlit for MVP frontend

Reason:

Streamlit allows fast development of a working dashboard with minimal frontend complexity. React/Vite may be considered after the MVP is stable.

## Decision 002: Use Miniconda for environment management

Reason:

The team develops on Windows and macOS. Miniconda with `environment.yml` provides a consistent cross-platform setup.

## Decision 003: Use offline-first development

Reason:

The project must be testable without API keys, GPU or external network access. API-enhanced mode is optional.

## Decision 004: Use BM25 as lexical baseline

Reason:

BM25 is simple, interpretable and CPU-friendly. It provides a strong traditional retrieval baseline.

## Decision 005: Use lightweight dense retrieval as DL component

Reason:

Dense retrieval provides semantic search capability while remaining feasible on ordinary laptops. Unit tests use fake deterministic embeddings; optional demo mode may use MiniLM/SBERT.

## Decision 006: Defer Docker

Reason:

Docker adds setup complexity and is unnecessary before the local app and tests are stable.

## Decision 007: Use reciprocal rank fusion for M2 hybrid retrieval

Reason:

Reciprocal rank fusion combines BM25 and dense rankings without requiring score calibration. It is deterministic, simple to test, and suitable for the offline-first MVP.

## Decision 008: Use hashing vectors for fake dense retrieval tests

Reason:

Hashing vectors provide deterministic dense-like behavior without model downloads, GPU, API keys, or network access. Real MiniLM/SBERT remains optional for later demo mode only.

## Decision 009: Use pure-Python BM25 for the offline baseline

Reason:

The Windows Conda environment triggered a fatal NumPy import exception through `rank-bm25`, which cannot be caught inside Python. A small pure-Python BM25 implementation keeps the lexical baseline deterministic and testable while preserving the intended BM25 behavior.

## Decision 010: Treat retrieved context as untrusted reference material

Reason:

Course PDFs and chunks may contain prompt injection text. The prompt builder explicitly tells the LLM not to follow instructions inside retrieved context and the mock answer generator only uses selected evidence chunks for answer content and citations.

## Decision 011: Avoid Pandas import in the Streamlit MVP path

Reason:

The Windows Conda environment can trigger a fatal NumPy import exception through Pandas. The MVP dashboard reads evaluation CSV files with the Python standard library and uses Streamlit-native tables plus lightweight HTML bars so local/offline tests remain stable.

## Decision 012: Use PyMuPDF best-effort image and table extraction for M6

Reason:

PyMuPDF is already part of the project environment and can extract image files,
image occurrence rectangles and lightweight table metadata without new services.
M6 keeps image/table ingestion offline-first by using mock vision captions,
caption fallback text, and non-blocking table detection instead of OCR, external
vision APIs or heavy multimodal retrieval.

## Decision 013: Use provider factories for optional SiliconFlow integration

Reason:

M7 must support real API demos without making the project depend on API keys,
network access or provider availability. Provider factories keep mock behavior
as the default, create SiliconFlow clients only when local `.env` is complete,
and preserve deterministic unit tests by allowing HTTP calls to be faked.

## Decision 014: Add an app service layer before any FastAPI/React migration

Reason:

M7-patch1 improves the Streamlit demo without changing the core RAG pipeline.
`QueryService`, `CorpusService` and `ProviderStatus` keep UI orchestration out
of `app/streamlit_app.py` while preserving offline-first tests. This creates a
stable boundary that can later be reused by FastAPI/React if the final demo
requires it.

## Decision 015: Use heuristic confidence labels only for UI guidance

Reason:

BM25, fake dense retrieval, reciprocal rank fusion and mock/API reranking do not
share calibrated score scales. M7-patch1 therefore presents confidence as a
simple UI diagnostic derived from the top score, not as a statistical
probability or model certainty. The label helps users inspect evidence and
compare methods without changing evaluation metrics.

## Decision 016: Keep M7-patch2 on Streamlit instead of FastAPI/React

Reason:

The existing Streamlit plus app-service-layer architecture already supports
offline retrieval, grounded generation, evaluation, provider fallback and tests.
M7-patch2 needs document upload and a more user-friendly chat surface, not a
backend replacement. FastAPI/React, Chroma, Docker, ASR and TTS remain deferred
because they would expand deployment and test scope without improving the core
retrieval-comparison milestone.

## Decision 017: Store uploaded demo documents under ignored local storage

Reason:

Local upload is needed for a credible RAG study assistant demo, but private
course files must not enter git. Uploaded files and the corpus registry are kept
under `data/processed/`, which is ignored. The registry stores metadata only and
chunks are rebuilt from local files when the corpus is loaded.
