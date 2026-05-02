# System Architecture

## High-level architecture

```text
User
→ Streamlit UI
→ Query Processor
→ Retrieval Pipeline
→ Reranker
→ Answer Generator
→ Evidence Display
```

## Data pipeline

```text
Raw documents
→ PDF/Text loader
→ Text/image/table extraction
→ Chunking
→ Chunk metadata
→ Index construction
→ Retrieval
→ Evaluation
```

## Milestone 6 image-aware ingestion path

```text
PDF
→ text extraction with existing PyMuPDF loader
→ image occurrence extraction with image files, bbox and nearby text
→ lightweight table detection with text/html fallback
→ unified Chunk list
→ BM25 / fake dense / fusion / reranked retrieval
```

The image-aware path is best-effort and offline-first. Images use mock caption
fallbacks and tables use PyMuPDF metadata/text extraction only. OCR, heavy
multimodal embeddings and external vision APIs remain out of scope until later
milestones.

## RAG pipeline

```text
Text Query / Voice Query
→ ASR if needed
→ query preprocessing
→ BM25 retrieval
→ Dense retrieval
→ candidate fusion
→ reranking
→ Top-k evidence selection
→ prompt construction
→ LLM answer generation
→ answer with citations
```

## Suggested project structure

```text
app/
  streamlit_app.py

src/rag_project/
  config.py
  schemas.py

  ingestion/
    pdf_loader.py
    image_extractor.py
    table_extractor.py
    chunker.py

  indexing/
    storage.py
    bm25_index.py
    dense_index.py

  retrieval/
    bm25_retriever.py
    dense_retriever.py
    fusion.py
    reranker.py

  generation/
    prompt_builder.py
    llm_client.py
    answer_generator.py

  audio/
    asr_client.py

  vision/
    caption_client.py

  evaluation/
    metrics.py
    run_evaluation.py

  utils/

tests/
  unit/
  integration/

docs/
  specs/
```

## Execution modes

### local/offline mode

```text
mock LLM
mock reranker
fake deterministic embedding
local BM25
local evaluation
```

### local-demo mode

```text
local PDF ingestion
BM25
optional MiniLM/SBERT
Streamlit dashboard
```

### api-enhanced mode

```text
external LLM API
external reranker API
optional ASR API
optional vision caption API
```

## Design priorities

1. Text-only RAG baseline first.
2. Evaluation pipeline second.
3. Streamlit dashboard third.
4. Image-aware ingestion fourth.
5. API integration fifth.
