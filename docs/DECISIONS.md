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


## Decision 018: Use Streamlit session-state highlighting for citations

Reason:

Streamlit does not provide a robust native pattern for inline citation anchors
that scroll and expand arbitrary right-panel elements without custom JavaScript.
M7-patch5 therefore assigns stable evidence IDs such as `E1`, `E2` and `E3`,
shows citation buttons below the answer, and stores the selected ID in
`st.session_state`. The Evidence Intelligence panel then moves, expands and
highlights the matching evidence card while keeping the MVP frontend simple,
testable and framework-stable.

## Decision 019: Add FastAPI as a thin product interface layer

Reason:

The React product UI needs stable JSON endpoints for upload, scope selection,
querying, evidence intelligence and evaluation visualization. The Stage 1
FastAPI adapter wraps existing app services and evaluation modules instead of
rewriting RAG algorithms or introducing Chroma, LangChain, Docker, ASR/TTS or a
new database. This keeps Streamlit as a backup while creating a product-ready
contract for React.

## Decision 020: Add minimal FastAPI runtime dependencies

Reason:

`fastapi`, `uvicorn`, `python-multipart` and `httpx` are required for the HTTP
adapter, local server startup, multipart document upload and TestClient-based
tests. They do not require API keys, network access during normal execution,
GPU, model downloads or changes to the offline RAG core.

## Decision 021: Make inline citation markers part of answer generation

Reason:

The React product UI needs stable citation-to-evidence linking without
guessing where support belongs in the answer. Stage 2 therefore labels evidence
as `[E1]`, `[E2]`, and `[E3]` in the grounded prompt and requires answer text to
place those markers directly after supported claims. The mock LLM follows the
same contract deterministically, so local/offline tests validate the product
behavior without API keys or network access.

## Decision 022: Use Vite React TypeScript for the product UI layer

Reason:

Stage 3 needs a product-like three-panel interface with typed API contracts,
component-level tests and fast local iteration while keeping Streamlit as a
backup. Vite + React + TypeScript provides a small frontend layer over the
existing FastAPI adapter without changing the RAG core, adding a database,
introducing streaming, or requiring API keys. The frontend uses mocked fetch
responses in tests so UI behavior remains offline-first.

## Decision 023: Separate per-query diagnostics from offline benchmark metrics

Reason:

Arbitrary user questions do not have labeled relevant chunk IDs, so true
Recall@k, MRR and NDCG cannot be computed for every chat turn. Stage 4 keeps
the reproducible evaluation pipeline as `Offline Benchmark` for the fixed eval
set, while the React right panel derives current-query proxy diagnostics from
the existing `/api/query` response. This avoids API churn and prevents the UI
from presenting heuristic coverage, overlap, latency or citation-resolution
signals as ground-truth evaluation scores.

## Decision 024: Remove fixed benchmark metrics from the primary React UI

Reason:

The fixed eval-set benchmark is useful for reports and reproducible method
comparison, but it distracts from the product task when users inspect a single
query. Stage 5A keeps `/api/evaluation/*`, reports and `python scripts/dev.py
eval`, but removes the benchmark section from the React main interface. The
right panel now focuses on current-query evidence, citation linking, retrieval
flow and proxy method diagnostics.

## Decision 025: Keep panel resize state local and non-persistent

Reason:

Resizable side panels improve the CourseMate-style workbench experience, but
persistent layout preferences are not needed for the current demo milestone.
Stage 5A keeps left/right widths in React state only, avoiding localStorage
schema, reset controls and extra test cases while still allowing users to
adjust the live view.

## Decision 026: Deprioritize noisy table chunks in final evidence display

Reason:

Table extraction from PDFs frequently produces content that is primarily
formatting fragments, pipe characters, box-drawing characters, internal
identifiers or repeated symbols rather than meaningful retrieval content.
P6 therefore filters final evidence to place text and image chunks first,
and only includes table chunks when they pass a content-quality threshold
(meaningful length, alpha/numeric ratio, absence of internal-ID patterns).
Table raw content remains available in diagnostic views but does not occupy
primary evidence cards unless the content is substantive.

## Decision 027: Hide internal chunk/document IDs from user-facing UI

Reason:

Raw chunk_id, doc_id, hash values and stored paths are implementation
details that degrade the product experience. P6 moves these fields into a
collapsible Developer details section on evidence cards and removes them
from method comparison rows. The underlying IDs remain available for
citation-to-evidence resolution, debugging and API consumers.

## Decision 028: Convert from three-column to two-column product layout

Reason:

The previous layout (Knowledge Base | Chat | Evidence Intelligence) caused
horizontal crowding, especially with the resizable side panels. P6 moves
the Knowledge Base into a collapsible materials drawer within the main
workspace, resulting in a two-column layout (Chat Workspace | Evidence
Intelligence). This gives the chat area more breathing room while keeping
document management accessible via a toggle button. The Evidence
Intelligence panel retains a wider default width for comfortable inspection
of evidence cards, retrieval flow and method analysis.

## Decision 029: Keep historical evidence linking client-side for Stage 5B

Reason:

Stage 5B needs users to click citations in earlier chat turns and inspect the
matching evidence, but the current demo does not need persistent server-side
chat history. Each assistant message already stores its full `/api/query`
response in React state, so the Evidence Intelligence panel can switch to that
cached response without rerunning retrieval or adding a database/session layer.
This preserves offline-first behavior and avoids changing the FastAPI contract.

## Decision 030: Improve evidence previews without a second model call

Reason:

Evidence cards were sometimes hard to read because raw chunks were truncated
mid-sentence. Adding a separate LLM or small-model evidence-refinement step
would increase latency and require another provider fallback path. Stage 5B
therefore uses deterministic cleaning, sentence-boundary excerpts, expandable
cards and bounded prompt evidence blocks. A model-based evidence refiner remains
deferred unless a later milestone explicitly approves it.

## Decision 031: Filter invalid table chunks from cited evidence

Reason:

Lightweight PDF table detection can create placeholder or formatting-only table
chunks such as `Table extracted from PDF.` or empty/no-preview rows. These
chunks may still be useful for diagnostics, but they are not reliable evidence
for grounded answers. The query service now filters invalid table chunks before
answer generation and final evidence construction, while preserving them in
retrieval method rows. Valid table chunks are allowed only when they contain
readable summary/HTML/markdown/cell/fallback text, and table evidence is
promoted only for explicit table, numerical, comparison, row/column or formula
queries. This avoids citing unreadable tables without deleting table extraction
or user data.

## Decision 032: Add intent-aware query planning before retrieval

Reason:

Multi-intent questions such as `what is word2vec? and what is transformer?`
were previously retrieved as one combined string, which could support only one
part while lowering the apparent confidence for the whole answer. Stage 6 adds
a planner layer before retrieval. The default planner is deterministic and
offline, while an optional SiliconFlow JSON planner can be enabled through
configuration and falls back on missing keys, provider errors or invalid JSON.
The RAG retrieval algorithms remain unchanged; each planned sub-question simply
gets its own retrieval query and evidence support status.

## Decision 033: Serve uploaded PDFs through a registry-backed endpoint

Reason:

Evidence cards need a way to open the original PDF page without exposing local
filesystem paths or using `file://`. Stage 6 serves registered uploaded PDFs
through `GET /api/documents/{doc_id}/file` and lets React link to
`/api/documents/{doc_id}/file#page={page}`. The endpoint checks the document
registry, constrains files to the configured upload directory, returns errors
for missing/non-PDF files, and does not expose `stored_path` or
`chunk_cache_path` in public document payloads.

## Decision 034: Cap multi-intent final evidence and preserve LLM synthesis

Reason:

Per-sub-question retrieval can produce `n * top_k` candidates, which is useful
for diagnostics but too noisy for the primary Evidence Intelligence panel.
Stage 6 now separates internal retrieval candidates from final cited evidence:
the current UI contract uses at most five final evidence cards globally and at
most one final evidence card per sub-question, deduped by chunk id or
source/page/preview. The answer planner still only plans retrieval; final
multi-intent answers are generated through the configured answer LLM in API
mode, with deterministic mock/fallback generation clearly marked by
`answer.generation_mode`.
