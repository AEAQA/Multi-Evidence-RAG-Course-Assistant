# Decisions

## Decision 001: Use Streamlit for MVP frontend

Reason:

Streamlit allows fast development of a working dashboard with minimal frontend complexity. React/Vite may be considered after the MVP is stable.

## Decision 002: Use Miniconda for environment management

Reason:

The team develops on Windows and macOS. Miniconda with `environment.yml` provides a consistent cross-platform setup.

## Decision 003: Use offline-first development

Reason:

The project must be testable without API keys, GPU or external network access. API-enhanced mode is optional.

## Decision 004: Use BM25 as lexical baseline

Reason:

BM25 is simple, interpretable and CPU-friendly. It provides a strong traditional retrieval baseline.

## Decision 005: Use lightweight dense retrieval as DL component

Reason:

Dense retrieval provides semantic search capability while remaining feasible on ordinary laptops. Unit tests use fake deterministic embeddings; optional demo mode may use MiniLM/SBERT.

## Decision 006: Defer Docker

Reason:

Docker adds setup complexity and is unnecessary before the local app and tests are stable.

## Decision 007: Use reciprocal rank fusion for M2 hybrid retrieval

Reason:

Reciprocal rank fusion combines BM25 and dense rankings without requiring score calibration. It is deterministic, simple to test, and suitable for the offline-first MVP.

## Decision 008: Use hashing vectors for fake dense retrieval tests

Reason:

Hashing vectors provide deterministic dense-like behavior without model downloads, GPU, API keys, or network access. Real MiniLM/SBERT remains optional for later demo mode only.

## Decision 009: Use pure-Python BM25 for the offline baseline

Reason:

The Windows Conda environment triggered a fatal NumPy import exception through `rank-bm25`, which cannot be caught inside Python. A small pure-Python BM25 implementation keeps the lexical baseline deterministic and testable while preserving the intended BM25 behavior.
