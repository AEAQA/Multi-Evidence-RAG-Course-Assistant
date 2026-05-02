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
