# Final Project Summary

## Evidence-Grounded RAG Study Assistant: Comparing BM25, Dense Retrieval, Hybrid Fusion, and LLM-Based Reranking

**Course**: IEMS5726 — Data Science in Practice
**Tech**: React + TypeScript / FastAPI / Python RAG Core / Streamlit Backup
**Tests**: 103 Python tests, 13 React tests

---

### 1. Problem Definition

University students need to search across lecture PDFs and course materials. Conventional keyword search misses semantically relevant content, while generic chatbots produce plausible-sounding but unverifiable answers. This project builds a **retrieval-augmented generation (RAG) study assistant** that retrieves real evidence from a local course knowledge base before generating any answer. Crucially, it **systematically compares four retrieval strategies** — BM25, dense retrieval, RRF hybrid fusion, and reranking — making the retrieval process transparent, interpretable, and empirically evaluated. This is a data science pipeline, not a conversational agent.

### 2. Data Collection, Preprocessing, and Representation

**Document ingestion**: Course PDFs are processed via PyMuPDF for text extraction, embedded image occurrence detection with bounding boxes and nearby text, and lightweight table detection with HTML/markdown fallback. Uploaded files are stored under git-ignored `data/processed/`.

**Chunk schema**: Each document is split into chunks with `chunk_id`, `doc_id`, `source_file`, `page`, `type` (text/image/table), `text`, and rich `metadata` including section titles, image paths, captions, table HTML/markdown/cells, and bounding boxes. A document registry (JSON) tracks metadata; chunks are cached for performance.

**Evaluation dataset**: `data/eval/queries.jsonl` contains 10 manually labeled queries, each with `query_id`, `query` text, and `relevant_chunk_ids` for offline evaluation.

### 3. Data Modeling

**BM25**: Pure Python Okapi BM25 implementation (Decision 009). Serves as the lexical baseline — strong for exact keyword matches, limited for semantic paraphrases.

**Fake Dense Retrieval**: SHA256 hashing vectors approximate dense embeddings without model downloads (Decision 008). Cosine similarity provides semantic-like ranking behavior while keeping tests deterministic and offline.

**RRF Fusion**: Reciprocal Rank Fusion (`1/(k+rank)`, k=60) combines BM25 and dense rankings without score calibration (Decision 007). The fusion score reflects ranking consensus, not semantic similarity.

**Reranker**: Mock reranker applies rank-based reordering with type preferences. Optional SiliconFlow API reranker provides semantic relevance scoring with mock fallback.

**Intent-Aware Query Planning** (Decision 032): A deterministic router classifies queries as material/non-material. Multi-intent questions (e.g., "What is A? and what is B?") are decomposed into sub-questions, each independently retrieved. Sub-questions are assigned support status labels.

**Grounded Answer Generation**: Prompt builder marks retrieved context as untrusted reference material (Decision 010). Evidence chunks carry `[E1]/[E2]/[E3]` labels. The LLM is instructed to paraphrase, synthesize, and cite — never copy-paste. Mock LLM provides deterministic offline generation.

**Evidence Quality Filtering** (Decisions 026, 031): Table chunks with placeholder text ("Table extracted from PDF."), hashes, repeated separators, or unreadable content are filtered from final evidence. Text and image chunks are preferred. Valid table evidence is promoted only for table-specific queries.

### 4. Data Visualization

The React product UI provides a Evidence Intelligence Panel with:
- **Cited Evidence cards**: E1/E2/E3 with source, page, support label, sentence-boundary preview, and Open page link
- **Retrieval Flow**: BM25 → Dense → Fusion → Reranker → Final Evidence, with contribution counts, match strength bars, and a human-readable flow summary
- **Method Comparison**: Collapsible `<details>` with per-method rows, rank badges, and rank tracks (method-specific, not cross-comparable)
- **MethodHowItWorks**: Educational explanations for each retrieval method
- **Per-query diagnostics**: Coverage, overlap, rank movement, latency, citation coverage, source diversity, score distribution
- **Sub-question support**: Evidence tagged by sub-question for multi-intent queries
- **Citation linking**: Clicking `[E1]` scrolls and highlights matching evidence card
- **PDF source linking**: Open registered PDFs at exact page via browser

### 5. Deployment

- **FastAPI backend**: 8 endpoints over `src/rag_project/` services
- **React + Vite + TypeScript frontend**: Hand-rolled CSS, 10 components
- **Streamlit backup**: Preserved for reference and fallback
- **Conda environment**: `environment.yml`, Python 3.11
- **Cross-platform scripts**: `scripts/dev.py` for test/run/api/eval/ui-test
- **Provider factory pattern**: Mock/API with automatic fallback on missing keys or failures
- **Offline-first**: All functionality works without API keys, GPU, or network

### 6. Challenges and Limitations

| Challenge | Mitigation |
|---|---|
| Table extraction quality varies across PDFs | Content-quality filter removes placeholder chunks; table evidence promoted only for table queries |
| Cross-method score incomparability | Match strength bars within each method; tooltip explaining non-comparability |
| Multi-intent answer synthesis | Sub-question evidence grouping; support status labels; generation mode indicator |
| Mock LLM fluency vs API LLM | `generation_mode` field (`mock`/`llm`/`fallback`) clearly labels answer source |
| Evaluation dataset size (10 queries) | Supplmented with per-query proxy diagnostics |
| Real ASR/TTS deferred | Scaffolding exists; providers set to mock |

### 7. Innovation Points

1. **Systematic retrieval comparison within a single query** — real-time visualization of how each method finds evidence
2. **Evidence quality filtering with content-aware promotion** — table chunks evaluated for quality, promoted only for table queries
3. **Intent-aware query planning with deterministic routing guard** — LLM helps with decomposition but deterministic router is authoritative
4. **Citation verification through inline markers** — every claim linked to a specific evidence chunk
5. **PDF source page linking** — verify evidence in full context without exposing internal paths
6. **Historical citation linking without server-side sessions** — cached QueryResponse stores in React state
7. **Method comparison designed for pedagogy** — "How It Works" explanations make retrieval concepts accessible
8. **Offline-first with identical API-mode contracts** — full pipeline testable without external dependencies

### 8. Demo Highlights

- Upload course materials → ask a grounded question → click citations to verify
- Multi-intent query decomposition with sub-question support status
- Retrieval Flow visualization and method comparison
- PDF Open page from evidence card
- Historical citation inspection
- Evaluation pipeline: `python scripts/dev.py eval`

### 9. References

- Robertson et al. (1995). Okapi at TREC-3
- Cormack et al. (2009). Reciprocal Rank Fusion (SIGIR)
- Lewis et al. (2020). Retrieval-Augmented Generation (NeurIPS)
- Karpukhin et al. (2020). Dense Passage Retrieval (EMNLP)
- Willison (2022-2024). Prompt Injection
