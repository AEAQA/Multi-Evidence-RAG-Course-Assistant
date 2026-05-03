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
