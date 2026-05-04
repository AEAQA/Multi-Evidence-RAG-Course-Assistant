# Final Project Summary

## Evidence-Grounded RAG Study Assistant: Comparing BM25, Dense Retrieval, Hybrid Fusion, and LLM-Based Reranking

**Course**: IEMS5726 — Data Science in Practice
**Project Type**: End-to-end data science system
**Technology**: React + TypeScript / FastAPI / Python RAG Core / Streamlit Backup

---

### 1. Problem Definition (10%)

University students regularly need to search across lecture PDFs, course notes, and other unstructured learning materials. Conventional keyword search (Ctrl+F) misses semantically relevant content — for example, searching for "model generalization" will not find a paragraph about "how well a model performs on unseen data." Meanwhile, generic large language model chatbots produce plausible-sounding but unverifiable answers that may hallucinate facts or invent citations. Standard RAG chatbots often present answers without revealing which retrieval strategy was used, which evidence was selected, or whether that evidence is reliable.

This project addresses these gaps by building an **evidence-grounded RAG study assistant** that:

- Retrieves real evidence from a local course knowledge base before generating any answer.
- **Systematically compares four retrieval strategies** — BM25 lexical retrieval, dense semantic retrieval, RRF hybrid fusion, and LLM-based reranking — making the retrieval process transparent and interpretable.
- **Verifies citations** against retrieved evidence and links each claim to its source document and page.
- **Filters low-quality evidence** such as placeholder table chunks and OCR noise.
- **Visualizes the retrieval pipeline** so users can understand exactly how an answer was derived.

This is not a generic chatbot. It is a data science system designed for evidence transparency and retrieval method comparison.

---

### 2. Data Science Pipeline (45%)

#### 2.1 Data Collection, Preprocessing, and Representation (15%)

**Document ingestion**: Course materials in PDF, TXT, and Markdown formats are processed through a unified ingestion pipeline. PDFs are parsed with PyMuPDF (fitz) for text extraction, embedded image occurrence detection with bounding box coordinates and nearby text, and lightweight table detection with HTML/markdown fallback representations. Uploaded files are stored under `data/processed/` (git-ignored).

**Chunk-level evidence representation**: Each document is split into overlapping word-based chunks with configurable size parameters (default 180 words, 30-word overlap). Every chunk carries structured metadata:

| Field | Description |
|---|---|
| `chunk_id` | Unique identifier (e.g., `doc001_page003_text_0001`) |
| `doc_id` | Parent document identifier |
| `source_file` | Original filename |
| `page` | PDF page number |
| `type` | One of `text`, `image`, or `table` |
| `text` | Retrievable content used for indexing and answer generation |
| `metadata` | Section title, image path, caption, nearby text, table HTML/markdown/cells |

This transforms unstructured course materials into searchable, typed evidence units with full source provenance.

**Image-aware evidence handling**: Embedded PDF images are extracted and saved locally. Each image chunk carries the bounding box, the extracted image file path, any caption metadata from the PDF, and nearby text from the surrounding page region. Mock vision captions are generated in offline mode. Image loading failures are non-blocking.

**Table extraction and quality filtering**: Lightweight table detection uses PyMuPDF's `find_tables()` API. Detected tables produce chunks with raw text, optional HTML table markup, and cell-level data. However, many detected tables contain primarily formatting fragments, repeated separator characters, or placeholder-like content. The system applies a content-quality filter that:
- Detects placeholder text (e.g., "Table extracted from PDF.")
- Identifies content dominated by separators (`|||||`) or box-drawing characters
- Checks for meaningful character ratios and readable content length
- Removes invalid table chunks from final cited evidence while preserving them in diagnostics

**Document scope control**: Users can restrict retrieval to specific uploaded documents, all uploaded documents, a built-in sample corpus, or combined scope. The corpus service maintains a JSON registry of uploaded documents with chunk counts by type.

**Evaluation dataset**: `data/eval/queries.jsonl` contains 10 manually labeled evaluation queries, each with `query_id`, `query` text, and `relevant_chunk_ids` referencing the synthetic evaluation corpus.

#### 2.2 Data Modeling (15%)

**BM25 lexical retrieval**: A pure Python implementation of Okapi BM25 using term frequency, inverse document frequency, and document length normalization with configurable `k1` and `b` parameters. Serves as the lexical baseline — strong for exact keyword matches, limited for semantic paraphrases. This custom implementation avoids a known `rank-bm25` NumPy import instability on Windows while preserving the intended BM25 ranking behavior.

**Dense semantic retrieval**: A deterministic hashing-based approach using SHA256 vector embeddings. Each chunk text is hashed to produce a fixed-length pseudo-embedding vector. Query-chunk similarity is computed via cosine similarity over these hash-derived vectors. This provides dense-like ranking behavior (capturing textual overlap patterns through hash collision neighborhoods) without requiring model downloads, GPU, or API keys. Real MiniLM/SBERT embeddings are available as an optional enhancement in API mode.

**RRF hybrid fusion**: BM25 and dense rankings are combined using Reciprocal Rank Fusion: `RRF_score = 1/(k + rank)` with `k = 60`. This produces a fused ranking without requiring score calibration between the incommensurable BM25 and cosine similarity scales. The fusion score reflects ranking consensus rather than absolute relevance.

**Reranker precision filter**: A mock reranker reorders fusion candidates using rank position, chunk type preference, and content quality heuristics. An optional SiliconFlow API cross-encoder reranker provides semantic relevance re-scoring with automatic mock fallback on missing keys, network errors, or API failures.

**Intent-aware query planning**: A deterministic router classifies queries as material (triggering retrieval) or non-material (greetings, help requests, out-of-scope questions — returned without retrieval). Multi-intent questions (e.g., "What is Word2Vec? and what is a Transformer?") are decomposed into sub-questions. Each sub-question is retrieved independently, producing per-sub-question evidence with support status labels (`supported`, `insufficient evidence`, `partially supported`). An optional SiliconFlow JSON planner can improve decomposition granularity but falls back to deterministic planning on missing keys, API errors, or invalid JSON.

**Grounded answer generation**: The prompt builder constructs a safety-conscious prompt that labels evidence chunks as `[E1]`, `[E2]`, `[E3]` and explicitly marks retrieved context as untrusted reference material (prompt injection protection). The LLM is instructed to paraphrase, synthesize, and cite — never copy-paste raw evidence text. In offline mode, a mock LLM produces deterministic grounded answers. In API mode, a configurable SiliconFlow LLM generates higher-quality answers. The `generation_mode` field (`mock`, `llm`, `fallback`, `none`) clearly labels answer provenance.

**Evidence quality filtering**: Table chunks with placeholder text, hashes, repeated separators, or unreadable content are filtered before answer generation and before final evidence construction. Text and image chunks are preferred by default. Valid table evidence is promoted only for table-specific, numerical, comparison, or formula queries. Final evidence is capped at 5 cards globally and 1 card per sub-question for multi-intent queries. The query pipeline is not a single-path RAG; it is a comparative retrieval pipeline that produces parallel results for all four methods.

#### 2.3 Data Visualization (15%)

The React product UI is designed for evidence transparency, not decorative analytics. Key visualizations include:

- **Cited Evidence cards**: Each card displays evidence ID (E1/E2/E3), method badge, support label, sentence-boundary excerpt, source file, page number, evidence type, and an "Open page" link to the source PDF. Image evidence cards include thumbnails with graceful fallback. Internal identifiers are hidden in a collapsible "Developer details" section.

- **Retrieval Flow visualization**: A stage-by-stage diagram showing evidence movement through BM25 → Dense → Fusion → Reranker → Final Evidence. Each stage displays hit count, latency, contribution count to final evidence, and a match strength bar. A human-readable flow summary and a collapsible "How to read this" explainer make the flow accessible to non-experts.

- **Method Comparison**: Collapsible per-method diagnostic rows with rank badges, match strength tracks, chunk type labels, and preview text. Match strength is clearly labeled as method-relative (not cross-comparable). A "How It Works" section provides educational explanations for each retrieval method's mechanics and strengths.

- **Per-query diagnostics**: Coverage rate, chunk overlap across methods, rank movement tracking, latency by stage, citation coverage rate, source diversity, and score distribution. All derived from the current query response without requiring labeled relevance judgments.

- **Citation-to-evidence interaction**: Clicking an inline citation marker `[E1]` in the answer scrolls to and highlights the matching evidence card. Historical citation linking works client-side using cached query responses — no server-side session required.

- **Multi-intent sub-question support**: Evidence cards are tagged by sub-question. Per-sub-question support labels and evidence counts are displayed in the chat answer area.

The visualization serves the data science goal: making retrieval behavior observable, not just producing answers.

---

### 3. Deployment (15%)

**System architecture**: The system follows a layered architecture:
- **React + Vite + TypeScript frontend**: Hand-rolled CSS, 10 components, typed API contracts matching the FastAPI response schema.
- **FastAPI backend**: 8 JSON REST endpoints (`/api/status`, `/api/documents`, `/api/query`, `/api/documents/{id}/file`, `/api/evaluation/*`, etc.). The FastAPI layer is a thin adapter over existing `src/rag_project` services.
- **RAG service layer**: `QueryService` orchestrates the full pipeline. `CorpusService` manages document upload, registry persistence, chunk caching, and scope filtering. `ProviderStatus` reports provider configuration without exposing API keys.
- **Streamlit backup**: The original `app/streamlit_app.py` is preserved and imports the same service layer, ensuring feature parity.

**API response contract**: `POST /api/query` returns a structured response with `answer.text` (with inline citations), `answer.generation_mode`, `citations` (with evidence IDs), `final_evidence` (with previews, image URLs, and table summaries), `retrieval_trace` (per-stage timing and match strength), `retrieval` (parallel BM25/Dense/Fusion/Reranker result arrays), `timing`, `scope`, `query_plan`, `sub_question_support`, `support_label`, and diagnostics.

**PDF source page linking**: `GET /api/documents/{doc_id}/file` serves registered PDFs through a registry-backed endpoint. The endpoint validates the document registry, constrains files to the configured upload directory (path traversal prevention), and returns errors for missing or non-PDF files. The browser's built-in PDF viewer opens the file at the specified `#page=` fragment. No `file://` protocol or local filesystem paths are exposed.

**Environment and deployment modes**:
- **Local/offline mode** (`APP_MODE=local`): All providers use mock implementations. No API keys, GPU, network, or model downloads required.
- **API-enhanced mode** (`APP_MODE=api` + valid `.env`): Real SiliconFlow LLM, reranker, and optional query planner. Automatic mock fallback on missing keys or failures.
- **Conda environment**: `environment.yml` with Python 3.11 and all dependencies.
- **Cross-platform dev scripts**: `scripts/dev.py` for `test`, `run`, `api`, `ui-test`, `eval`, `api-smoke`, `clean`.

**UI/UX design**: Two-panel product layout (Chat Workspace | Evidence Intelligence). The evidence panel slides in from the right after the first query. The materials drawer is collapsible and opens at the bottom of the chat panel. Panel widths are proportion-based and resizable. All transitions respect `prefers-reduced-motion`.

---

### 4. Challenges (10%)

| Challenge | Description | Mitigation |
|---|---|---|
| **PDF extraction noise** | Extracted text from PDFs can contain formatting artifacts, repeated characters, and OCR noise | Content cleaning with regex-based noise removal; sentence-boundary truncation; hash/internal-ID pattern removal |
| **Table extraction producing placeholders** | Many detected tables contain only pipe characters, box-drawing symbols, or "Table extracted from PDF." | Content-quality filter checks character ratios, minimum readable length, and placeholder patterns; invalid tables filtered before answer generation |
| **Cross-method score incomparability** | BM25 scores, cosine similarity, RRF reciprocal ranks, and reranker scores operate on different scales | Match strength bars shown per-method only; tooltip explaining non-comparability; standalone CSS for flow bars to prevent cross-method visual confusion |
| **Multi-intent evidence explosion** | `n × top_k` retrieval candidates from multi-intent queries overwhelm the UI | Global cap of 5 final evidence cards, 1 per sub-question; deduplication by chunk ID or source/page/preview |
| **Misleading confidence scores** | Heuristic confidence derived from raw scores can suggest statistical certainty | Labels simplified to `supported`/`partial`/`low`/`none`; raw scores confined to developer details; `generation_mode` field labels answer provenance |
| **Citation grounding integrity** | Answer text may reference evidence IDs that don't map to actual evidence chunks | Citation mapping through `evidence_by_chunk` dictionary; unresolved citation warnings displayed in the UI |
| **Latency from reranker and LLM** | API calls to LLM and reranker dominate user-perceived latency | Per-stage latency tracking in diagnostics; timing breakdown distinguishes retrieval latency from generation latency |
| **Balancing product clarity with DS diagnostics** | Full retrieval diagnostics can overwhelm non-technical users | Information hierarchy: cited evidence and retrieval flow visible by default; method comparison, analysis, and diagnostics are collapsible |

---

### 5. Demonstration Video (10%)

Suggested demo flow (~5-7 minutes):

1. **Setup and materials**: Start backend and frontend. Show the clean chat-first interface. Upload or select course materials. Show the materials drawer with document counts and chunk type breakdowns.
2. **Single question**: Ask "What is overfitting?" Show the grounded answer with inline `[E1]` `[E2]` citations. The evidence panel slides in automatically.
3. **Citation interaction**: Click `[E1]` — the right panel scrolls to and highlights the matching evidence card. Show the card's source file, page number, and preview text.
4. **PDF Open page**: Click "Open page" — the source PDF opens in a new browser tab at the exact cited page.
5. **Retrieval flow**: Scroll to the Retrieval Flow section. Show the 4-stage pipeline (BM25 → Dense → Fusion → Reranker → Final Evidence) with contribution counts and match strength bars. Expand "How to read this" for the educational explanation.
6. **Method comparison**: Expand the Method Comparison section. Click through BM25, Dense, Fusion, and Reranker tabs. Show the per-method diagnostic rows.
7. **Multi-intent query**: Ask "What is Word2Vec? and what is a Transformer?" Show the query plan decomposition, sub-question support statuses, and evidence cards tagged by sub-question.
8. **Diagnostics and filtering**: Show that diagnostics remain collapsed by default. Briefly expand to show timing and scope data.
9. **Summary**: Recap that this is a DS pipeline — from ingestion through retrieval comparison to verifiable grounded answers — not a generic chatbot.

---

### 6. Source Code and Report Submission (10%)

**Repository organization**: The project follows a clear directory structure with separation between frontend (`frontend/`), backend core (`src/rag_project/`), API adapter (`src/rag_project/api/`), Streamlit backup (`app/`), tests (`tests/`), documentation (`docs/`), evaluation data (`data/eval/`), and cross-platform scripts (`scripts/dev.py`).

**Environment reproducibility**: `environment.yml` defines all Conda dependencies with pinned Python 3.11. `.env.example` provides a template with all values set to `xxx` or `mock`. Default `APP_MODE=local` requires no external services.

**Git hygiene**: `.gitignore` covers Python cache, Conda environments, uploaded documents, processed data, evaluation reports, frontend build artifacts, Node modules, OS files, and logs. No API keys, private data, or large files are tracked.

**Test infrastructure**: 103 Python unit tests (pytest) and 13 React component tests (Vitest). All tests run offline without API keys, GPU, or model downloads. The mock provider pattern ensures deterministic test behavior.

**Evaluation pipeline**: `python scripts/dev.py eval` runs the offline evaluation across all four retrieval methods and writes reproducible metrics reports.

---

### 7. Innovation Points

1. **Comparative retrieval pipeline within a single query**: Rather than only reporting aggregate evaluation metrics, the system shows parallel results for BM25, Dense, Fusion, and Reranker on every query — enabling real-time method comparison and educational understanding of retrieval behavior.

2. **Evidence quality gate with content-aware filtering**: Table chunks are not simply included or excluded. They are evaluated for content quality (placeholder detection, character ratio analysis, pattern matching) and promoted only when the query explicitly asks for tabular, numerical, or comparative information. This is a practical data quality gate going beyond naive chunk-type routing.

3. **Intent-aware query routing with deterministic guard**: The optional LLM planner helps decompose complex queries, but a deterministic router remains authoritative for the material/non-material boundary — preventing the LLM from misclassifying course concepts or forcing retrieval on off-topic questions.

4. **Citation verification with PDF source traceability**: Every generated claim is linked to a specific evidence chunk via inline `[E1]` markers. Clicking a citation highlights the matching evidence card, and an "Open page" link serves the original PDF at the exact page through a registry-backed endpoint — enabling full evidence verification without exposing internal paths.

5. **Evidence Intelligence visualization**: The right panel is not a dump of raw retrieval results. It is organized by information priority (cited evidence → retrieval flow → method comparison → diagnostics), uses method-relative match strength bars, and includes educational explanations for each retrieval method.

6. **Offline-first architecture with identical API contracts**: Every provider has a mock implementation following the same interface and output contract as the real API implementation. The full pipeline — including citation contracts, multi-intent planning, and evidence filtering — is testable without any external dependencies.

---

### 8. References

- Robertson, S. E., Walker, S., Jones, S., Hancock-Beaulieu, M., & Gatford, M. (1995). Okapi at TREC-3. *Proceedings of TREC-3*.
- Cormack, G. V., Clarke, C. L. A., & Buettcher, S. (2009). Reciprocal Rank Fusion outperforms Condorcet and individual rank learning methods. *SIGIR 2009*.
- Lewis, P., et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *NeurIPS 2020*.
- Karpukhin, V., et al. (2020). Dense Passage Retrieval for Open-Domain Question Answering. *EMNLP 2020*.
- Willison, S. (2022–2024). Prompt injection attacks against LLM-powered applications.
- Greshake, K., et al. (2023). Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection. *arXiv:2302.12173*.
