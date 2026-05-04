# Report Outline

## Evidence-Grounded RAG Study Assistant — Final Report Structure

### 1. Problem Definition (10%)

- What gap does this project address?
- Why keyword search and generic chatbots are insufficient for course material QA
- The need for verifiable, evidence-grounded answers with retrievable sources
- Positioning: retrieval comparison system, not a chatbot

### 2. Data Collection, Preprocessing, and Representation (part of 45%)

#### 2.1 Document Sources
- Course lecture PDFs (privacy-protected, local upload)
- Evaluation query dataset: 10 manually labeled queries with relevant chunk IDs

#### 2.2 Ingestion Pipeline
- PyMuPDF text extraction, paragraph-level chunking
- Image occurrence extraction (bounding boxes, nearby text, mock captions)
- Lightweight table detection (HTML/markdown fallback)
- Chunk typing: text, image, table

#### 2.3 Data Representation
- Chunk schema: chunk_id, doc_id, source_file, page, type, text, metadata
- Bounding boxes, captions, nearby text, table HTML/markdown/cells
- Document registry (JSON) and chunk cache for performance

### 3. Data Modeling (part of 45%)

#### 3.1 BM25 Lexical Retrieval
- Pure Python Okapi BM25 implementation
- Term frequency, IDF, document length normalization
- Serves as lexical baseline

#### 3.2 Dense Semantic Retrieval
- SHA256 hashing vectors for offline deterministic behavior
- Cosine similarity ranking
- Captures semantic patterns through hash collision neighborhoods

#### 3.3 Reciprocal Rank Fusion (RRF)
- Combines BM25 and dense rankings without score calibration
- Formula: `1/(k + rank)` with k=60

#### 3.4 Reranker Precision Filter
- Mock reranker: rank-based reordering with type preferences
- Optional SiliconFlow API reranker for semantic relevance scoring

#### 3.5 Intent-Aware Query Planning
- Deterministic router: material vs non-material query classification
- Multi-intent question decomposition
- Sub-question evidence support tracking

#### 3.6 Grounded Answer Generation
- Prompt construction with untrusted-context isolation
- Inline citation marker contract ([E1], [E2], [E3])
- Insufficient-evidence refusal pathway
- Evidence quality filtering (table placeholder removal)

### 4. Data Visualization (part of 45%)

- Evidence Intelligence Panel: cited evidence cards, retrieval flow, method comparison
- Match strength bars (method-relative, not cross-comparable)
- Rank movement analysis (BM25/Dense rank → Final rank tracking)
- Citation coverage and source diversity metrics
- MethodHowItWorks educational explanations
- Sub-question support visualization for multi-intent queries
- PDF source page linking for evidence verification

### 5. Deployment (15%)

- FastAPI backend adapter (8 endpoints)
- React + Vite + TypeScript product UI
- Streamlit backup (preserved)
- Conda environment + cross-platform dev scripts
- Provider factory pattern (mock/API with fallback)
- Offline-first default (no API keys, GPU, or network required)

### 6. Challenges and Limitations (10%)

- Table extraction quality varies across PDFs
- Cross-method score incomparability (BM25 vs cosine vs RRF vs reranker)
- Multi-intent answer synthesis quality
- Mock LLM fluency vs real API LLM
- Evaluation dataset size (10-30 queries)
- Real ASR/TTS deferred

### 7. Demo Video (10%)

- See [DEMO_SCRIPT.md](DEMO_SCRIPT.md)

### 8. Source Code and Report Submission (10%)

- Complete project structure documented in [README.md](../README.md)
- 103 Python tests, 13 React tests
- Build verification steps
- Evaluation pipeline with reproducible metrics

### 9. Innovation Points

- Systematic retrieval comparison within a single query
- Evidence quality filtering with content-aware promotion
- Intent-aware query planning with deterministic routing guard
- Citation verification through inline markers with PDF linking
- Historical citation linking without server-side sessions
- Offline-first architecture with identical API-mode contracts

### 10. References

- Robertson et al. (1995). Okapi at TREC-3 (BM25)
- Cormack et al. (2009). Reciprocal Rank Fusion (RRF)
- Lewis et al. (2020). Retrieval-Augmented Generation (RAG)
- Karpukhin et al. (2020). Dense Passage Retrieval (DPR)
- Willison (2022-2024). Prompt Injection attacks
