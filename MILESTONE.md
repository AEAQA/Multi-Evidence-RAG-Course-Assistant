# Milestone Plan: Offline-First RAG Study Assistant

## Implementation status

Completed:

* Milestone 0: Repository Bootstrap And Environment Fix
* Milestone 1: Text/PDF Ingestion MVP
* Milestone 2: Retrieval Baselines
* Milestone 3: Grounded Answer Generation
* Milestone 4 step 1: Evaluation Metrics Foundation
* Milestone 4: Evaluation Pipeline
* Milestone 5: Streamlit MVP Dashboard
* Milestone 6: Image-Aware Ingestion Enhancement
* Milestone 7: Optional API-Enhanced Mode
* M7-patch1: Streamlit Evidence Workbench
* M7-patch2: Chat-Centered RAG Study Assistant With Local Document Upload
* M7-patch3: Three-Panel RAG Workbench With Material Scope Refinement

Next:

* Milestone 8: Final Report And Demo Packaging

## Summary

当前项目已完成到 `Milestone 7: Optional API-Enhanced Mode`。初始只读检查结果：

- 系统：Windows。
- Conda：已安装，`conda 25.9.1`。
- 当前 Python：`3.13.9`，但项目推荐环境应使用 `Python 3.11`。
- `docs/specs/`、`PROJECT_MEMORY.md`、`DECISIONS.md`、`CHANGELOG.md` 已存在。
- `src/`、`app/`、`tests/`、`data/`、`reports/` 尚未建立。
- 当前目录不是 git 仓库，暂时无法用 git checkpoint 回滚。
- `environment.yml` 目前不是合法 YAML，Conda dry-run 报错：`* conda-forge` 这种写法被解析为 YAML alias，应改为 `- conda-forge`。

## Milestones

### Milestone 0: Repository Bootstrap And Environment Fix

目标：让项目具备可安装、可测试、可回滚的最小骨架。

实施内容：

- 修复 `environment.yml` YAML 语法，保持 Python 3.11、Miniconda、CPU-friendly 依赖。
- 初始化项目骨架：
  - `src/rag_project/`
  - `tests/unit/`
  - `tests/integration/`
  - `app/`
  - `data/samples/`
  - `data/eval/`
  - `data/raw/`
  - `reports/`
- 添加 `.gitignore`、`.env.example`、README skeleton、基础 package 文件。
- 添加最小 placeholder 测试，确保 `python -m pytest` 可运行。
- 若用户同意，将当前目录初始化为 git 仓库并创建初始 checkpoint。
- 更新 `docs/PROJECT_MEMORY.md` 和 `docs/CHANGELOG.md`。

验收：

- `conda env create -f environment.yml --dry-run` 不再因 YAML 失败。
- `python -m pytest` 通过。
- local/offline mode 不依赖 API key。

### Milestone 1: Text/PDF Ingestion MVP

目标：完成 text-only RAG 的数据入口。

实施内容：

- 实现 `.txt` loader 和 text-based `.pdf` loader。
- 实现 chunk schema 与 text chunking。
- 每个 chunk 包含 `chunk_id/doc_id/source_file/page/type/text/metadata`。
- 添加小型 sample document 或 synthetic fixture。
- 使用 `$pdf` skill 辅助 PDF ingestion 设计，但暂不做图片/table extraction。
- 更新 data schema/spec 中必要细节。

验收：

- `.txt` 和 text PDF 可被加载并切 chunk。
- 空页、无文本 PDF、坏路径有明确 fallback。
- 单元测试覆盖 loader、chunker、schema。

### Milestone 2: Retrieval Baselines

目标：实现可比较的检索基线。

实施内容：

- BM25 retriever。
- Fake deterministic dense retriever。
- Hybrid fusion，例如 reciprocal rank fusion。
- Mock reranker。
- Retrieval result schema 与 rank/score 输出统一。
- 所有实现保持 offline-first，不下载模型。

验收：

- 支持：
  - BM25-only
  - Dense-only
  - BM25 + Dense fusion
  - BM25 + Dense fusion + reranker
- Dense 单元测试只使用 deterministic fake embedding。
- 测试覆盖排序、空语料、重复 chunk、top-k 边界。

### Milestone 3: Grounded Answer Generation

目标：完成 evidence-first 的 mock RAG answer pipeline。

实施内容：

- Prompt builder 明确声明 retrieved context 是不可信资料。
- Mock LLM client 只基于 Top-3/Top-5 evidence 生成 deterministic answer。
- 证据不足时返回 insufficient evidence。
- 输出 answer、citations、evidence list、retrieval explanation。
- 不接入真实 API，先完成 mock/local mode。

验收：

- 无 evidence 时不自由发挥。
- Prompt injection 文本不会被当作系统指令。
- citations 包含 chunk_id、source_file、page。

### Milestone 4: Evaluation Pipeline

目标：让项目具备数据科学评估闭环。

实施内容：

- 实现 Recall@1/3/5、MRR@5、NDCG@5、latency。
- 支持读取 `data/eval/queries.jsonl`。
- 输出：
  - `reports/evaluation/retrieval_metrics.csv`
  - `reports/evaluation/latency_metrics.csv`
  - `reports/evaluation/error_cases.md`
- 添加 10-30 条 MVP evaluation queries。

验收：

- 四种 retrieval 方法可统一评估。
- evaluation 可通过 `python scripts/dev.py eval` 执行。
- 单元测试覆盖指标计算。

### Milestone 5: Streamlit MVP Dashboard

目标：提供可演示的本地 dashboard，而不是普通 chatbox。

实施内容：

- 使用 Streamlit。
- 页面 1：RAG Assistant。
  - corpus selector 或 sample corpus
  - text query input
  - final answer
  - evidence panel
  - BM25/Dense/Fusion/Reranked panels
- 页面 2：Evaluation Dashboard。
  - metrics table
  - Recall/MRR/NDCG/latency charts
- 使用 `$frontend-design` skill 约束 UI，不引入 React。

验收：

- `python scripts/dev.py run` 可启动。
- 没有 API key 时仍显示 mock answer 和 evidence。
- evidence 比 final answer 更显眼。

### Milestone 6: Image-Aware Ingestion Enhancement

目标：增强 PDF ingestion，但不做重型 multimodal RAG。

实施内容：

- 抽取 PDF image metadata。
- 保存 image path/page/source/bbox/nearby_text。
- Vision caption client 先使用 mock fallback。
- 增加 `image` chunk 类型。
- table extraction 只做轻量 metadata/table text fallback，复杂表格可延后。

验收：

- 图片 caption 失败不阻塞 ingestion。
- image chunk 可进入 unified index。
- UI evidence panel 可显示 image metadata 或 thumbnail。

### Milestone 7: Optional API-Enhanced Mode

目标：在 MVP 稳定后接入真实 API，但保持 mock fallback。

实施内容：

- LLM provider interface。
- Reranker provider interface。
- Optional ASR provider interface。
- Optional vision caption provider interface。
- `.env.example` 只保留 placeholder，不提交真实 key。

验收：

- 无 key 时自动 mock fallback。
- 单元测试不访问网络。
- API mode 仅作为 demo/integration path。

### Milestone 8: Final Report And Demo Packaging

目标：面向期末展示整理成果。

实施内容：

- README 完整化。
- Demo script。
- Evaluation figures。
- Error analysis。
- Limitations/challenges。
- Deployment instructions。
- 检查项目描述，避免写成普通 chatbot 或推荐系统。

验收：

- app 可本地启动。
- tests 通过。
- retrieval comparison 结果可复现。
- 无 `.env`、私有 PDF、API key、大模型权重进入 git。

## Environment Plan

`environment.yml` 当前依赖方向基本合理，但语法必须先修：

```yaml
name: rag-study-assistant

channels:
  - conda-forge
  - defaults

dependencies:
  - python=3.11
  - pip
  - numpy
  - pandas
  - scikit-learn
  - matplotlib
  - pytest
  - pip:
      - pymupdf
      - rank-bm25
      - pydantic
      - python-dotenv
      - streamlit
      - plotly
      - requests
      - openai
```

暂不加入 `sentence-transformers`、`faiss-cpu`、Docker、LangChain、React。

## Test Plan

每个 milestone 都必须至少运行：

```bash
python -m pytest
```

环境和开发命令优先使用：

```bash
python scripts/dev.py info
python scripts/dev.py test
python scripts/dev.py run
python scripts/dev.py eval
```

核心测试策略：

- Unit tests 不依赖 API key、GPU、外网、真实 embedding model。
- Dense retrieval 测试使用 deterministic fake embedding。
- LLM/reranker/ASR/vision client 都先 mock。
- PDF 测试使用小型 synthetic fixture 或公开 sample。

## Assumptions

- 默认开发模式为 `APP_MODE=local`。
- 用户先安装 Miniconda 环境，我后续只基于修复后的 `environment.yml` 开发。
- MVP 优先完成 text-only RAG baseline，再做 image-aware ingestion。
- 如果需要回滚记录，Milestone 0 中应先初始化 git 仓库并创建初始 checkpoint。

---

## React/FastAPI Product UI Staged Migration

This section tracks the `react-fastapi-product-ui` branch. It does not replace the original offline-first RAG milestone plan above.

### Stage 0: Documentation And Migration Contract

Status: documented.

Goal: capture the FastAPI + React migration plan without changing core code.

Deliverables:

* `AGENTS.md` migration rules;
* `docs/specs/09_react_fastapi_product_ui_plan.md`;
* architecture/API/UI/redesign spec updates;
* Streamlit backup policy;
* frontend_reference reading instructions.

### Stage 1: FastAPI Backend Layer

Status: complete.

Goal: expose existing RAG services through JSON-first FastAPI endpoints.

Delivered:

* `src/rag_project/api/main.py` exposes health, status, documents, upload,
  delete, query and evaluation endpoints.
* The API wraps existing corpus, query, provider status and evaluation services.
* `POST /api/query` returns answer text, citations, final evidence, retrieval
  trace, method result groups, timing, scope and diagnostics.
* `tests/unit/test_fastapi_api.py` covers the Stage 1 endpoint contract using
  temporary local storage paths.
* `python scripts/dev.py api` starts the FastAPI adapter.
* `environment.yml` includes FastAPI runtime/test dependencies.
* Verified with `python scripts/dev.py test` passing 90 tests and
  `python scripts/dev.py eval` completing offline reports.

### Stage 2: Prompt-Driven Grounded Answer Contract

Status: planned.

Goal: replace chunk-concatenation style responses with prompt-driven natural language answers and inline citation markers.

### Stage 3: React Three-Panel Product UI

Status: planned.

Goal: implement left Knowledge Base, center Chat, and right Evidence Intelligence panels.

### Stage 4: Evaluation Visualization

Status: planned.

Goal: integrate retrieval and evaluation metrics into the right-side Evidence Intelligence panel using visual summaries.

### Stage 5: Demo Packaging

Status: planned.

Goal: document startup, demo flow, fallback behavior, API smoke checks, and final presentation steps.
