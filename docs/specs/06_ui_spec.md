# UI Specification

## Frontend framework

MVP uses:

```text
Streamlit
```

React/Vite is out of scope until the MVP is stable.

## Main pages

### Page 1: RAG Assistant

Components:

* corpus selector or document upload
* text query input
* optional audio query upload
* run query button
* final answer panel
* evidence panel
* retrieval process panel

### Page 2: Evaluation Dashboard

Components:

* method comparison table
* Recall@k chart
* MRR/NDCG chart
* latency chart
* error case viewer

## RAG Assistant layout

Recommended sections:

```text
1. Input
2. Final Answer
3. Evidence
4. Retrieval Process
5. Debug / Metadata
```

## Retrieval process panel

Show:

```text
BM25 Top-k
Dense Top-k
Fusion candidates
Reranked Top-k
```

Each result should include:

* rank
* score
* chunk text preview
* source file
* page
* type
* chunk_id

## Evidence panel

Each evidence item should show:

* source file
* page number
* chunk ID
* chunk type
* text preview
* image thumbnail if available
* table preview if available

## UI principles

* Do not build only a chatbox.
* Show the retrieval process clearly.
* Make evidence more visible than the final answer.
* Support local/offline mode.
* If API is unavailable, show mock answer rather than crashing.
* If evidence is insufficient, show a clear warning.

## Milestone 5 implementation status

The MVP Streamlit dashboard implements two pages:

* `RAG Assistant`
* `Evaluation Dashboard`

RAG Assistant behavior:

* uses the public synthetic evaluation corpus;
* accepts a text query and Top-k control;
* runs BM25, fake dense, fusion, and mock reranked retrieval;
* generates a grounded mock answer from reranked evidence;
* shows evidence before retrieval-debug details;
* shows BM25, Dense, Fusion, and Reranked result tables.

Evaluation Dashboard behavior:

* reads or creates local evaluation reports;
* shows method comparison metrics;
* shows Recall@k, MRR/NDCG, and latency charts;
* displays the Markdown error case viewer.

MVP constraints:

* no React;
* no real API key required;
* no private corpus upload handling yet;
* no image/table preview beyond schema-compatible placeholders.

## Milestone 6 evidence display

The evidence panel supports image-aware chunk metadata:

* image chunks can show `image_path`, `bbox`, `caption`, and `nearby_text`;
* if the extracted image file exists locally, Streamlit can render a small thumbnail;
* table chunks can show `table_html` preview text;
* retrieval result tables include image path, caption, and bbox columns when present.

Private PDF upload and corpus management remain deferred. M6 only adds the
display path for chunks produced by offline image-aware ingestion.

## Milestone 7 API status display

The sidebar displays safe provider status for API-enhanced mode:

* `APP_MODE`
* provider names and model ids
* `SILICONFLOW_API_KEY=set` or `missing`
* SiliconFlow base URL

The UI must never display the real API key. RAG Assistant continues to show
evidence, final answer, retrieval process tabs, and debug metadata when API
providers fall back to mock clients.

## M7-patch1 Evidence Workbench

Page 1 is renamed to:

```text
Study Query Workbench
```

Required behavior:

* retrieval must only run when the user clicks `Run evidence query`;
* typing or changing the default query must not automatically run retrieval;
* the page uses a three-column workbench:
  * left: corpus scope, sample questions and provider status;
  * center: query composer, grounded answer, citations and suggestions;
  * right: evidence cards and retrieval diagnostics;
* provider status must show safe state labels such as `mock`, `siliconflow`,
  `missing-key` and `unsupported-asr`;
* real API keys must never be displayed;
* ASR must be shown as mock/planned until a real ASR client and audio UI are
  implemented;
* evidence chunks must be collapsible and include chunk id, source, page,
  type, preview and image/table metadata when available;
* retrieval diagnostics must show BM25, Dense, Fusion and Reranked result
  groups plus a simple confidence label and recommendation for each method.

Page 2 remains:

```text
Evaluation Dashboard
```

M7-patch1 groups evaluation content into method summary, recall coverage,
ranking quality, latency and weak cases sections. It continues to read/create
local reports without Pandas, API keys or network calls.

## M7-patch2 Chat-Centered RAG UI

Page 1 is renamed to:

```text
RAG Study Chat
```

Required behavior:

* the first viewport should feel like a study assistant, not a retrieval log;
* the central path is upload/select corpus -> ask question -> answer with
  citations;
* `.txt` and `.pdf` upload must be visible from the main page;
* uploaded files are local demo data and must be stored only under ignored
  `data/processed/` paths;
* users can query sample corpus, uploaded corpus, or combined corpus;
* citations and compact evidence preview remain close to the final answer;
* BM25, Dense, Fusion, Reranked top-k tables and method diagnostics are hidden
  by default inside `Explain how this answer was retrieved`;
* latency and provider/debug metadata are hidden by default inside `Debug view`;
* the Evaluation Dashboard remains the place for full Recall@k, MRR@5,
  NDCG@5, latency and error-case analysis.

Terminology:

* acceptable: `RAG-based study assistant`, `RAG chatbot`,
  `retrieval-augmented question answering system`;
* avoid: describing the project as a plain LLM chatbot or a simple API wrapper.

## M7-patch3 Three-Panel RAG Workbench

The frontend should be designed as a three-panel RAG workbench rather than a
standalone analytics dashboard. The center panel may remain a clean
chatbot-style interface, but the left panel must control the knowledge base and
selected materials, while the right panel must expose evidence, retrieval
method outputs, scores and source metadata. This ensures that the interface
demonstrates the data science pipeline rather than only presenting a generic
chatbot.

Required layout:

```text
Left: Materials / Knowledge Base
Center: Chat Interface
Right: Evidence and Retrieval Methods
```

Left panel:

* upload `.pdf`, `.txt`, `.md`, and `.markdown` files;
* list uploaded documents;
* allow optional document selection for retrieval scope;
* show `doc_id`, filename, chunk count, chunk type counts, document status, and RAG enabled/disabled state;
* if no uploaded documents are selected, uploaded retrieval searches all uploaded documents;
* if one or more uploaded documents are selected, uploaded retrieval is restricted to selected `doc_id`s.

Center panel:

* keep the interface clean and chat-focused;
* support text query first;
* show grounded final answer;
* show citations or citation table next to the answer;
* voice input remains optional and mock/planned until implemented.

Right panel:

* show final evidence chunks used for answer generation;
* show `chunk_id`, `doc_id`, `source_file`, `page`, chunk type, retrieval method, score/confidence, and preview;
* show BM25 Top-k, Dense Retrieval Top-k, Hybrid Fusion candidates, and Reranked Top-k in method tabs;
* show insufficient-evidence warning when final evidence is weak or absent;
* optionally show latency and compact method comparison summary.


## M7-patch5 Single-Page Evidence Intelligence Workbench

The MVP frontend is a single-page Streamlit RAG workbench inspired by the
CourseMate three-panel interaction pattern. CourseMate is a visual and
interaction reference only; the project remains Streamlit and does not migrate
to React, Gradio, FastAPI, Docker or a new frontend framework in this patch.

Required layout:

```text
Left: Knowledge Base / Materials
Center: Chat
Right: Evidence Intelligence
```

Left panel behavior:

* uploads `.pdf`, `.txt`, `.md`, and `.markdown` materials;
* lists uploaded documents with filename, chunk count, type summary and status;
* controls retrieval scope through all-documents or selected-documents behavior;
* selection defines the corpus scope, while retrieval remains chunk-level.

Center panel behavior:

* remains clean and chat-focused;
* shows the assistant answer as the primary conversational output;
* answer text includes stable citation markers such as `[E1]`, `[E2]`, `[E3]`;
* citation buttons such as `View E1` update Streamlit session state instead of
  relying on custom JavaScript anchors;
* clicking a citation button highlights and expands the matching evidence card
  in the right panel.

Right panel behavior:

* is named `Evidence Intelligence`;
* shows cited evidence first, labeled as `E1`, `E2`, `E3`;
* each evidence item shows source file, page, chunk id, doc id, type, method,
  score, confidence bar, preview and image/table metadata when available;
* shows retrieval flow cards for `BM25 -> Dense -> Fusion -> Reranker -> Final Evidence`;
* each retrieval flow card shows top-k count, best score, latency and a
  confidence bar;
* method comparison uses tabs with rank cards, score bars, latency/diagnostic
  badges and an optional raw-row expander;
* Recall@k, MRR, NDCG, latency and error cases are integrated into a collapsed
  `Evaluation metrics` section, not a dominant analytics page.

The separate Evaluation Dashboard implementation may remain as a legacy helper,
but the primary user experience should route evaluation and debug details
through the right-side Evidence Intelligence panel.

## React/FastAPI Product UI Target

The product UI target is a React three-panel RAG workbench inspired by `frontend_reference/CourseMate.jsx`. The reference is visual and interaction guidance only; do not copy it directly.

Required layout:

```text
Left: Knowledge Base
Center: Chat
Right: Evidence Intelligence
```

Left panel controls the corpus scope:

* upload PDF/TXT/MD files;
* list uploaded/indexed documents;
* allow all-documents or selected-documents retrieval;
* show chunk count, document type summary, status, and RAG enabled state.

Center panel is chat-focused:

* full-height bounded layout;
* scrollable messages;
* fixed input area;
* natural language grounded answers;
* inline citations directly after supported claims, for example `[E1]`.

Right panel is the data science explanation layer:

* evidence cards labeled `E1`, `E2`, `E3`;
* source file, page, chunk id, chunk type, method, score, and preview;
* BM25 -> Dense -> Fusion -> Reranker -> Final Evidence flow;
* BM25, Dense, Fusion, and Reranker method comparison;
* score bars, latency badges, method contribution summary;
* per-query retrieval method analysis behind an `Analyze methods` control;
* fixed Recall@k, MRR, NDCG, latency, and error cases in a collapsed
  `Offline Benchmark` section that is explicitly labeled as fixed eval-set
  data.

Citation interaction:

* `[E1]` is an inline anchor, not a separate button;
* clicking `[E1]` scrolls to and highlights Evidence E1 in the right panel;
* the answer remains readable even if JavaScript scrolling fails.

## Stage 1 Product API Availability

The React product UI should consume the Stage 1 FastAPI adapter instead of
calling Streamlit or Python app services directly.

Required frontend data sources:

* left Knowledge Base panel calls `GET /api/documents`,
  `POST /api/documents/upload` and `DELETE /api/documents/{doc_id}`;
* center Chat calls `POST /api/query`;
* right Evidence Intelligence renders `final_evidence`, `retrieval_trace`,
  `retrieval`, `timing`, `scope`, `diagnostics` and evaluation endpoints;
* provider/status badges call `GET /api/status`.

The Streamlit implementation remains the backup UI and should not be removed by
the React migration.

## Stage 2 Inline Citation Contract

React should treat citation markers in `answer.text` as first-class inline
anchors.

Rendering rules:

* parse markers that match `[E1]`, `[E2]`, `[E3]`, and so on;
* render each marker as an inline anchor inside the answer text;
* use `citations[].evidence_id` and `final_evidence[].evidence_id` to resolve
  the target evidence card;
* clicking the anchor should scroll to and highlight the corresponding evidence
  card in the right Evidence Intelligence panel;
* if a marker cannot be resolved, keep the marker visible as plain text and do
  not hide the answer.

Backend expectation:

* grounded answer text should already include citation markers directly after
  supported claims;
* React should not need to synthesize a separate `References` block for normal
  grounded answers.

## Stage 3 React Workbench Implementation

The React product UI is implemented under `frontend/` as a Vite + React +
TypeScript application.

Implemented layout:

```text
Left: Knowledge Base
Center: Grounded Study Chat
Right: Evidence Intelligence
```

Left panel:

* loads status and document metadata from the FastAPI adapter;
* uploads PDF/TXT/MD/MARKDOWN files through `/api/documents/upload`;
* lists document ID, filename, chunk count and type summary;
* supports sample, uploaded and combined retrieval scope;
* supports selected-document filtering and deletion.

Center panel:

* submits questions to `/api/query`;
* preserves a chat transcript for the current page session;
* renders grounded natural-language answers from `answer.text`;
* parses `[E1]`, `[E2]`, and later markers into inline citation anchors.

Right panel:

* shows `final_evidence` cards before diagnostics;
* highlights and scrolls to the matching card when an inline citation is clicked;
* renders retrieval flow stages, BM25/Dense/Fusion/Reranker method tabs,
  score bars, timing, scope, suggestions and current-query method analysis.

Verification:

* `python scripts/dev.py ui-test` passes 6 mocked React tests covering the
  intended offline UI behavior.
* `python scripts/dev.py test` passes the full local/offline Python suite after
  the React UI addition.

## Stage 4 Per-Query Method Analysis

The React Evidence Intelligence panel separates current-query diagnostics from
fixed benchmark evaluation.

Default right-panel behavior:

* show cited `final_evidence` first;
* show the BM25 -> Dense -> Fusion -> Reranker -> Final Evidence flow;
* show method tabs for top-k rows;
* keep detailed method analysis hidden until the user clicks `Analyze methods`;
* keep fixed evaluation reports collapsed as `Offline Benchmark`.

`Analyze methods` behavior:

* derives analysis from the active `/api/query` response and does not call the
  backend again;
* computes final-evidence coverage for BM25, Dense, Fusion and Reranker top-k
  rows;
* shows rank agreement as top-k overlap between retrieval methods;
* shows latency bars for the current query;
* shows method score distributions with compact bars;
* shows citation coverage by checking answer markers against returned
  citations;
* shows source and chunk-type diversity across final evidence;
* for insufficient evidence, shows a safe empty state rather than pretending
  Recall/MRR/NDCG can be computed.

`Offline Benchmark` behavior:

* uses `/api/evaluation/summary`;
* is collapsed by default;
* states that metrics come from the fixed eval set and are not current-query
  scores;
* remains useful for final reports and reproducible method comparison.

Verification:

* `python scripts/dev.py ui-test` passes 8 mocked React tests after Stage 4.
* `npm.cmd run build` passes after sandbox escalation for Vite/esbuild
  child-process execution.
* Backend regression remains unchanged because Stage 4 does not alter the API
  contract.

## Stage 5A CourseMate-Style Product Polish

The React product UI keeps the RAG workbench structure but adopts lighter
CourseMate-inspired interaction and visual treatment.

Layout behavior:

* a slim top header shows product identity and safe runtime/API state;
* the three panels remain Knowledge Base, Grounded Study Chat and Evidence
  Intelligence;
* draggable vertical handles resize the left and right side panels;
* resize width bounds are enforced in the frontend and are not persisted in v1;
* below the responsive breakpoint, resize handles are hidden and the layout
  falls back to a single column.

Evidence and evaluation behavior:

* React no longer calls `/api/evaluation/summary` during normal startup;
* the React main UI no longer renders `Offline Benchmark`;
* offline evaluation remains available through the FastAPI evaluation endpoints,
  reports and `python scripts/dev.py eval`;
* `image` chunks display as `Image evidence`;
* `text`, `table` and unknown chunks display as `Text evidence` until a later
  milestone adds a true table preview.

Visual direction:

* use softer panels, 9-12px radii, light shadows, compact rounded controls and
  blue/cyan accents;
* keep the center chat app-like and approachable;
* keep the right panel evidence-first so the product is still visibly a RAG
  retrieval workbench, not a generic chatbot.

Verification:

* `python scripts/dev.py ui-test` passes 10 mocked React tests after Stage 5A.
* `npm.cmd run build` passes after sandbox escalation for Vite/esbuild
  child-process execution.
* `python scripts/dev.py test` and `python scripts/dev.py eval` continue to
  pass because the offline evaluation pipeline was preserved.
