# Changelog

## Unreleased

### Added

* Initial project guidance.
* Cross-platform environment plan.
* SDD specs skeleton.
* Offline-first development policy.
* RAG architecture plan.
* Milestone 0 repository skeleton with `src`, `app`, `tests`, `data`, and `reports` directories.
* `.env.example`, `.gitignore`, README skeleton, package bootstrap, and pytest bootstrap tests.
* Placeholder evaluation entrypoint for `python scripts/dev.py eval`.
* Milestone 1 text ingestion with `.txt` loader, text-based PDF loader, and chunker.
* Shared Pydantic schemas for pages, chunks, citations, answer responses, rerank results, ASR, and vision captions.
* Mock/interface skeletons for LLM, reranker, ASR, and vision caption clients.
* Unit tests for ingestion, chunking, and mock clients.
* Milestone 2 retrieval baselines: pure-Python BM25, fake deterministic dense retrieval, reciprocal rank fusion, and retrieval pipeline.
* Shared `RetrievalResult` and `RetrievalPipelineOutput` schemas.
* Unit tests for BM25 ordering, dense determinism, hybrid fusion, and full retrieval pipeline output.
* Milestone 3 grounded answer generation with prompt builder, answer generator, evidence list, citations, and retrieval explanation.
* Prompt-injection-aware untrusted-context instruction for retrieved evidence.
* Unit tests for prompt safety, Top-5 evidence limits, insufficient evidence fallback, and answer generator outputs.

### Changed

* Fixed `environment.yml` syntax so Conda can parse the environment file.
* Updated `scripts/dev.py` to include `src` on `PYTHONPATH` for project commands.
* Updated `scripts/dev.py test` to use a workspace-local pytest temp directory.
* Expanded `scripts/dev.py clean` to remove pytest/cache artifacts after delivery.
* Extended answer response schema with `evidence_chunks` and `retrieval_explanation`.

### Known cleanup notes

* Some pytest temp directories from earlier Windows runs may remain if the OS reports `PermissionError`; they are ignored by git.

### Fixed

* Resolved Conda YAML parsing failure caused by invalid list syntax in `environment.yml`.
