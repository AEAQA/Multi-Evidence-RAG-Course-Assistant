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
