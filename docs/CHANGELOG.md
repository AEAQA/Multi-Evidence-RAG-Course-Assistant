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

### Changed

* Fixed `environment.yml` syntax so Conda can parse the environment file.
* Updated `scripts/dev.py` to include `src` on `PYTHONPATH` for project commands.
* Updated `scripts/dev.py test` to use a workspace-local pytest temp directory.

### Fixed

* Resolved Conda YAML parsing failure caused by invalid list syntax in `environment.yml`.
