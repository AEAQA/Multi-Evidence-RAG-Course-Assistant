# Requirements

## Functional requirements

### FR1: Document ingestion

The system shall ingest course materials from local files.

MVP:

* `.txt`
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

The system shall provide a Streamlit dashboard showing:

* document upload or corpus selection
* query input
* final answer
* evidence
* BM25 results
* Dense results
* Fusion results
* Reranked results
* evaluation metrics

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
