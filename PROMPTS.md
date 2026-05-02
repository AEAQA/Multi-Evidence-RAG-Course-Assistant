# Prompts
在实现对应任务的时候请检索并参考对应的流程进行。

## 1. 第一次初始化仓库
Read AGENTS.md and ENVIRONMENT.md first. Then read docs/specs/00_project_brief.md, 01_requirements.md and 02_system_architecture.md.

Implement Milestone 0 only:
- create repository skeleton;
- create .env.example, .gitignore, README skeleton;
- create Python package structure under src/rag_project;
- create placeholder tests;
- ensure `python -m pytest` passes in local/offline mode.

Do not add real API keys. Do not install optional large dependencies. Update docs/PROJECT_MEMORY.md, docs/DECISIONS.md if needed, and docs/CHANGELOG.md.

## 2. 做 PDF ingestion 时
Use the $pdf skill if available.

Read AGENTS.md, ENVIRONMENT.md, docs/specs/02_system_architecture.md and docs/specs/03_data_schema.md.

Implement the first version of PDF/text ingestion only:
- load text from small text-based PDFs;
- create text chunks with metadata;
- add unit tests with a tiny sample file or synthetic fixture;
- do not implement image/table extraction yet.

Keep local/offline mode working. Run tests and update PROJECT_MEMORY and CHANGELOG.

## 3. 做前端时
Use the $frontend-design skill if available.

Read AGENTS.md and docs/specs/06_ui_spec.md.

Implement a minimal Streamlit dashboard:
- text query input;
- show final mock answer;
- show evidence list;
- show BM25/Dense/Fusion/Reranked panels as placeholders if backend is not ready.

Do not introduce React. Do not require API keys. Add a smoke test if feasible. Update docs.

## 4. 做测试和 review 时
Use the $webapp-testing skill if available.

Review the current uncommitted changes against AGENTS.md and docs/specs.
Check for:
- broken local/offline mode;
- missing tests;
- real secrets accidentally committed;
- platform-specific commands;
- API dependency in unit tests;
- documentation not updated.

Run `python -m pytest` and summarize failures or risks.

## 5. 继续上一次工作
Read AGENTS.md, docs/PROJECT_MEMORY.md and docs/CHANGELOG.md first.

Continue from the current milestone recorded in PROJECT_MEMORY.
Before coding, summarize:
- what is already done;
- what remains;
- which files you will edit;
- which tests you will run.

Then implement only the next smallest step.