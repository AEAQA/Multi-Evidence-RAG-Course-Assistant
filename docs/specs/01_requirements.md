# Requirements

## Functional requirements

### FR1: Document ingestion

The system shall ingest course materials from local files.

MVP:

* `.txt`
* `.md` / `.markdown`
* text-based `.pdf`

Enhanced:

* PDF images
* PDF tables
* image/table metadata

### FR2: Chunking

The system shall split documents into chunks with metadata.

Each chunk should include:

* chunk_id
* doc_id
* source_file
* page
* type
* text
* metadata

### FR3: Retrieval

The system shall support:

* BM25 retrieval
* Dense retrieval
* Hybrid fusion
* Reranking

Material selection:

* users may optionally select which uploaded documents participate in retrieval;
* if no uploaded documents are selected, retrieval searches all uploaded/indexed documents by default;
* if one or more uploaded documents are selected, retrieval is restricted to chunks from those selected documents;
* document selection is only a corpus-scope filter, and retrieval results remain chunk-level.

### FR4: RAG answer generation

The system shall generate answers based only on retrieved evidence.

The answer shall include:

* final answer
* evidence list
* source file
* page number
* chunk ID

### FR5: Evaluation

The system shall evaluate retrieval methods using:

* Recall@1
* Recall@3
* Recall@5
* MRR@5
* NDCG@5
* latency

### FR6: Dashboard

The system shall provide a Streamlit three-panel RAG workbench showing:

* left panel: document upload, material selection, chunk count, document status, and RAG scope;
* center panel: chat-style text query input and final answer with citations;
* right panel: final evidence chunks, BM25 results, Dense results, Fusion results, Reranked results, scores, metadata, and optional latency/method summary.

Evaluation metrics remain available in the evaluation page, but the main
frontend must not read as a standalone chart-heavy analytics dashboard.

### FR7: Voice input

The system may support optional voice input.

If ASR is unavailable, the text input path must still work.

## Non-functional requirements

### NFR1: Offline-first

Unit tests and local demo must work without real API keys.

### NFR2: Cross-platform

The project must support Windows, macOS and Linux using Miniconda.

### NFR3: Security

The project must not commit `.env`, API keys, private datasets or large model weights.

### NFR4: Testability

Core modules must be testable without external services.

### NFR5: Maintainability

Code must be modular:

```text
ingestion
chunking
retrieval
reranking
generation
evaluation
frontend
```

## Out of scope for MVP

* Full production authentication
* Large-scale vector database
* Docker deployment
* React frontend
* Fine-tuning large language models
* Training large embedding models
