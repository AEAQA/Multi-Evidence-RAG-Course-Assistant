# Project Brief

## Project title

**Voice-enabled Image-aware RAG Study Assistant: Comparing BM25, Dense Retrieval, Hybrid Fusion and LLM-based Reranking**

## Project type

Data Science in Practice final project.

## Core problem

Students often need to search across lecture PDFs, notes, FAQ documents and course materials. Standard keyword search may miss semantically relevant content, while ordinary LLM chatbots may hallucinate because they answer without grounding in the provided documents.

This project builds a retrieval-augmented study assistant that retrieves evidence from a local course knowledge base before generating answers.

## Core idea

The system compares multiple retrieval strategies:

```text
BM25-only
Dense-only
BM25 + Dense hybrid fusion
BM25 + Dense fusion + reranker
Full RAG answer generation
```

The final system uses a hierarchical RAG pipeline:

```text
Text/Voice Query
→ query preprocessing
→ BM25 retrieval
→ Dense retrieval
→ candidate fusion
→ reranking
→ evidence selection
→ grounded answer generation
```

## Expected contribution

The project is not simply a chatbot. It is a data science system that demonstrates:

* PDF data ingestion
* image/table-aware preprocessing
* chunk representation
* retrieval modeling
* reranking
* grounded generation
* evaluation metrics
* visualization
* deployable dashboard

## Constraints

* Must run on ordinary laptops.
* Must not require strong GPU.
* Must work in local/offline mode.
* Must not require API keys for tests.
* Must support Windows/macOS/Linux development.
