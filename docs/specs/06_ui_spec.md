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
