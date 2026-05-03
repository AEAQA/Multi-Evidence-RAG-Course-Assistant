# Frontend And Backend Redesign Spec

## Purpose

This spec records the post-M7 review of the current Streamlit dashboard against
the `frontend_reference/` CourseMate project. It defines a more user-friendly
interface and backend organization for the final demo phase without copying the
reference project 1:1.

The current project must remain:

* an evidence-first RAG study assistant;
* a retrieval-method comparison system;
* offline-first with optional SiliconFlow API enhancement;
* testable without API keys, network, GPU or private data.

## Current Issues

### Provider configuration confusion

`VISION_PROVIDER` and `ASR_PROVIDER` are provider names, not model names.

Correct optional vision config:

```text
VISION_PROVIDER=siliconflow
VISION_MODEL=Qwen/Qwen3-VL-32B-Instruct
```

Current M7 ASR behavior:

```text
ASR_PROVIDER=mock
ASR_MODEL=mock-asr
```

Real ASR is not wired yet. Setting `ASR_PROVIDER=FunAudioLLM/SenseVoiceSmall`
will not enable live ASR because the provider factory intentionally returns the
mock ASR client in M7.

### Streamlit launch path

When `app/streamlit_app.py` is launched directly from IDE tooling, Python may
not include `src/` on `sys.path`, causing:

```text
ModuleNotFoundError: No module named 'rag_project'
```

The app should keep the local `src` path bootstrap, while `scripts/dev.py run`
remains the recommended launch command.

### Frontend interaction gaps

The current M5/M7 dashboard works, but still feels like a technical inspection
page:

* no uploaded corpus management in the UI;
* no persistent session history;
* no explicit “query is running” state beyond Streamlit rerun behavior;
* default query can trigger work too eagerly;
* evidence exists but does not feel like a live investigation panel;
* API/provider state is visible but not actionable;
* ASR and vision status can look configured even when the live path is still
  mock/fallback;
* evaluation is useful but disconnected from the query workflow.

## Reference Project Lessons

The `frontend_reference/` project should be used as a design reference, not as a
code template.

Useful patterns to adapt:

* three-zone layout: knowledge/session sidebar, main question workspace,
  evidence/diagnostics panel;
* document upload with progress and selected document scope;
* persistent sessions with reload/delete;
* status badges for model, ASR, TTS, chunks and service health;
* media controls for voice, image upload and camera;
* source cards with mode, retrieved chunk count, scope and fallback notes;
* explicit empty states, loading states and failure messages;
* streaming-style progressive answer display, where feasible.

Patterns not to copy directly:

* generic tutor-chat framing;
* vector database dependency before final demo needs it;
* Docker/TTS/multi-service complexity unless M8 explicitly requires it;
* decorative UI choices that make evidence and method comparison less legible.

## Target Product Shape

The final UI should be an **Evidence Workbench**, not a chatbox.

### Page 1: Study Query Workbench

Layout:

```text
Left: Corpus + session controls
Center: Query composer + answer
Right: Evidence + retrieval diagnostics
```

Left panel:

* sample corpus selector;
* optional local document upload for `.txt` and `.pdf`;
* uploaded document list with chunk count and type counts;
* selected corpus scope;
* provider status badges with safe key status only;
* new session / clear session controls.

Center panel:

* question input;
* run button that is the only trigger for retrieval;
* optional voice input placeholder until real ASR is wired;
* final grounded answer;
* citations directly attached to the answer;
* clear insufficient-evidence warning when no evidence is available.

Right panel:

* evidence summary: mode, selected corpus, retrieved count, fallback status;
* evidence cards with chunk type, source, page, score, chunk id and preview;
* image thumbnail and metadata when `image_path` exists;
* table preview when `table_html` exists;
* retrieval tabs for BM25, Dense, Fusion and Reranked outputs;
* debug expander for prompt/provider metadata.

### Page 2: Evaluation Dashboard

Keep this page, but connect it better to the workbench:

* show latest evaluation timestamp;
* show method ranking summary;
* expose Recall@1/3/5, MRR@5, NDCG@5 and latency;
* include error case viewer;
* allow a local rerun through internal evaluation functions;
* never require API keys.

### Page 3: Demo Readiness

Add a final-demo checklist page in M8:

* environment status;
* provider status;
* API smoke result;
* evaluation report availability;
* sample query list;
* limitations and fallback notes;
* “what to show in presentation” script.

## Backend Architecture Changes

The current modules are good for unit testing, but the UI needs a higher-level
service layer so Streamlit does not orchestrate too much directly.

Add an application service layer:

```text
src/rag_project/app_services/
  corpus_service.py
  query_service.py
  session_store.py
  provider_status.py
```

Responsibilities:

* `CorpusService`
  * load sample corpus;
  * ingest uploaded `.txt` / `.pdf` files through existing loaders;
  * return document summaries and chunk type counts;
  * keep uploaded corpus in local ignored storage.

* `QueryService`
  * run retrieval pipeline;
  * call answer generator;
  * return one structured workbench state object;
  * include provider/fallback status and timing.

* `SessionStore`
  * persist recent local sessions under ignored local state;
  * store query, answer, citations, evidence and selected corpus scope;
  * avoid storing API keys or private document content in tracked files.

* `ProviderStatus`
  * normalize `mock`, `siliconflow`, `fallback`, `missing key` states;
  * expose safe UI labels only.

## Interaction And Loading Rules

* Do not run retrieval just because a query string exists.
* Use an explicit run button.
* Use `st.spinner` or status containers for ingestion, retrieval and evaluation.
* Cache stable sample corpus and existing evaluation reports.
* Show bounded previews for long evidence text.
* Show actionable messages:
  * missing key: “Using mock fallback”;
  * unsupported ASR provider: “ASR live path not implemented in M7”;
  * API failure: “SiliconFlow failed, mock fallback used”;
  * no evidence: “Insufficient evidence”.
* Never show real API keys in UI, logs or exceptions.

## Provider Configuration Rules

Recommended stable demo config:

```text
APP_MODE=api
LLM_PROVIDER=siliconflow
LLM_MODEL=<chat model>
RERANKER_PROVIDER=siliconflow
RERANKER_MODEL=<reranker model>
VISION_PROVIDER=mock
VISION_MODEL=mock-vision
ASR_PROVIDER=mock
ASR_MODEL=mock-asr
SILICONFLOW_API_KEY=<local key>
```

Optional vision demo:

```text
VISION_PROVIDER=siliconflow
VISION_MODEL=Qwen/Qwen3-VL-32B-Instruct
```

Deferred real ASR:

```text
ASR_PROVIDER=siliconflow
ASR_MODEL=FunAudioLLM/SenseVoiceSmall
```

Real ASR requires a new `SiliconFlowASRClient`, browser audio upload handling
and Streamlit audio input UX. Until that is implemented, ASR must be shown as
mock/fallback.

## Recommended Implementation Steps

1. Fix current UX blockers:
   * direct Streamlit launch path;
   * no auto-run on query field value;
   * explicit loading/error containers;
   * clear ASR/Vision provider status labels.

2. Add app service layer:
   * `QueryService`;
   * `ProviderStatus`;
   * structured workbench response schema.

3. Rebuild Streamlit page 1 as Evidence Workbench:
   * left corpus/session panel;
   * center query/answer panel;
   * right evidence/method panel.

4. Add local document upload:
   * `.txt` and `.pdf`;
   * image-aware PDF chunks;
   * local ignored storage;
   * selected corpus scope.

5. Add session history:
   * local JSON store;
   * no secrets;
   * reload/delete sessions.

6. Add final demo readiness page:
   * API smoke status;
   * evaluation readiness;
   * presentation script checklist.

7. Optional later work:
   * real SiliconFlow ASR client;
   * streaming answer display;
   * FastAPI + static frontend if Streamlit becomes too limiting.

## Acceptance Criteria

* User can ask a question without understanding implementation details.
* Evidence is more prominent than final answer.
* Retrieval method comparison remains visible.
* Provider state is understandable and never exposes secrets.
* Missing or failing API providers do not crash the UI.
* Uploaded local documents can be selected for a query.
* Sessions can be saved and revisited locally.
* Evaluation dashboard remains reproducible offline.
* Tests continue to pass without API keys or network access.

## M7-patch1 Implementation Status

Implemented in M7-patch1:

* `src/rag_project/app_services/provider_status.py`
  * normalizes provider state into `mock`, `siliconflow`,
    `missing-key`, `missing-model`, `unsupported-provider` and
    `unsupported-asr`;
  * exposes only safe status fields and never returns a real API key.
* `src/rag_project/app_services/corpus_service.py`
  * returns the public synthetic sample corpus summary;
  * reports chunk counts, type counts, source files and sample questions.
* `src/rag_project/app_services/query_service.py`
  * wraps retrieval, reranking, grounded answer generation, timing,
    suggestions and method diagnostics;
  * preserves mock fallback through the existing provider factories.
* Streamlit Page 1 is now `Study Query Workbench`:
  * retrieval only runs after the explicit `Run evidence query` button;
  * the layout is a three-column workbench: corpus/provider, query/answer,
    evidence/diagnostics;
  * evidence chunks are shown in collapsible expanders;
  * retrieval methods are shown in tabs and method diagnostics are shown with
    confidence bars and recommendations;
  * ASR is clearly marked as mock/planned when a non-mock ASR provider is
    configured.
* Evaluation Dashboard groups method summary, recall coverage, ranking
  quality, latency and weak cases into focused expanders.

Deferred after M7-patch1:

* persistent uploaded corpus management;
* local session history;
* real SiliconFlow ASR;
* TTS;
* FastAPI + React migration.

## M7-patch2 Implementation Status

M7-patch2 shifts the first page from an inspection-first workbench to a
chat-centered RAG study assistant while keeping retrieval transparency available
on demand.

Implemented:

* Page 1 is now `RAG Study Chat`.
* The main interaction is a central study-question box with a grounded natural
  language answer and citations.
* `.txt` and `.pdf` uploads are supported from the Streamlit UI.
* Uploaded files are stored under ignored local storage:

```text
data/processed/uploads/
data/processed/corpus_registry.json
```

* Uploaded `.txt` files use the existing text loader and chunker.
* Uploaded `.pdf` files use the image-aware `load_pdf_chunks()` path with
  text/image/table fallback behavior.
* Corpus scope supports sample only, uploaded only, and sample + uploaded.
* Uploaded document selection and deletion are local-only and do not require a
  database or API server.
* BM25, Dense, Fusion, Reranked top-k results, method confidence, latency and
  debug metadata are hidden by default under `Explain how this answer was
  retrieved` and `Debug view`.

Product positioning:

* The project may be described as a RAG-based study assistant or RAG chatbot.
* It must not be described or implemented as a generic LLM chatbox.
* The core contribution remains the comparison of retrieval strategies and
  their effect on grounded RAG answer quality.

Architecture decision:

* FastAPI/React remains deferred until after M8 or a dedicated migration
  milestone.
* M7-patch2 intentionally keeps Streamlit as the MVP dashboard and reuses the
  existing app service layer instead of introducing Chroma, Docker, or a local
  database.

## React/FastAPI Migration Status

A future branch-level migration will move the product UI from Streamlit to React + FastAPI while preserving the existing RAG core.

Migration rules:

* Streamlit remains a backup implementation.
* FastAPI is an interface layer over existing app services.
* React implements the product-like three-panel workbench.
* `frontend_reference/` is required reading before implementation, but old code must not be copied directly.
* Answers should become prompt-driven natural language with inline citations, not retrieval-result concatenation.
* The right-side Evidence Intelligence panel must continue to expose retrieval method comparison and evaluation signals.

Detailed staged plan: `docs/specs/09_react_fastapi_product_ui_plan.md`.
