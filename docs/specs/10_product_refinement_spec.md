# Product Experience Refinement Spec

## Status

Implemented on the `react-fastapi-product-ui` branch.

This spec covers the product experience refinement work that was completed across multiple development stages.
RAG core. Streamlit remains a backup UI. The React UI remains a RAG evidence
workbench, not a generic chatbot.

## Product Goals

* Make historical chat citations usable: clicking `[E1]` in an older assistant
  response restores that turn's cached evidence and highlights the matching
  card in the right panel.
* Improve evidence readability without adding another LLM call by default.
* Make latency diagnostics clearly show when generation is the slow stage.
* Polish the frontend toward a minimal OpenWebUI/OpenAI-like product surface
  while preserving current-query retrieval analysis.

## Implemented Behavior

### Historical Evidence Linking

The React app stores every assistant message with its own `QueryResponse`.
The right Evidence Intelligence panel no longer depends only on the latest
response. Citation clicks receive both the evidence id and the message's cached
response:

```text
assistant message response -> citation click -> visible evidence response
```

When a user clicks a citation in a historical answer:

* the right panel switches to that answer's cached `final_evidence`,
  `retrieval_trace`, `retrieval`, `timing`, `scope` and diagnostics;
* the clicked evidence id is highlighted and scrolled into view;
* no FastAPI request is made and no RAG step is rerun;
* the right panel labels which query the evidence belongs to.

This is intentionally session-local. Stage 5B does not introduce a database,
server-side chat sessions or persistent browser history.

### Evidence Preview Quality

Evidence cards now prefer readable excerpts instead of hard character cuts:

* backend evidence previews use sentence-boundary truncation;
* preview length is increased for final evidence so users can inspect more
  context;
* long frontend previews include `Show more` / `Show less`;
* image evidence prefers thumbnails, then caption or nearby text fallback;
* meaningful table evidence can show a `Table summary` badge;
* noisy table/OCR/internal-id content remains deprioritized.

### Table Evidence Quality Filter

Low-quality table chunks are kept in retrieval diagnostics but are filtered out
before answer generation and before `E1` / `E2` / `E3` final evidence is built.

Invalid table evidence includes table chunks that:

* have no readable `table_summary`, `table_markdown`, `table_html`, `cells`,
  non-placeholder caption, nearby text or preview;
* only contain placeholders such as `(no text preview)` or
  `Table extracted from PDF.`;
* are too short to be useful as evidence;
* are dominated by repeated separators such as `|||||`;
* contain hash-like strings, internal ids, `chunk_id`, `doc_id` or OCR/table
  formatting noise.

Final evidence selection now:

* prefers text and image evidence by default;
* allows table evidence only when it has a readable summary/markdown/html/cell
  payload or readable fallback text;
* raises valid table evidence ahead of text/image evidence only when the query
  explicitly asks about table/formula/comparison/numerical data/columns/rows or
  equivalent Chinese terms;
* returns insufficient evidence when the only retrieved candidates are invalid
  table chunks.

The processed chunk cache may still contain old invalid table chunks. The
query-time filter prevents them from becoming cited evidence, so user data does
not need to be deleted. If an older uploaded PDF should benefit from newly
stored `table_summary`, `table_markdown` or `cells` metadata, re-ingest or
re-upload that document; do not delete user data automatically.

Stage 5B does not add a second evidence-refinement LLM call by default. That
would make the already-slow generation path slower. If later needed, it should
be optional and mock-backed.

### Latency Diagnostics

Per-query method analysis now separates retrieval and answer-generation timing:

```text
Pipeline build
BM25
Dense
Fusion
Reranker
Retrieval total
Generation
Total
```

This makes it clear when BM25/Dense/Fusion/Reranker are fast but the final LLM
generation dominates user-perceived latency.

The prompt builder also bounds each evidence block before sending it to the
LLM provider. This keeps prompts compact while preserving sentence boundaries
and inline citation requirements.

### Frontend Visual Direction

The React UI moves from the previous blue CourseMate-like palette to a quieter
OpenWebUI/OpenAI-like product style:

* neutral paper background and white panels;
* black primary actions with a restrained green accent;
* compact top bar and chat-first workspace;
* smoother panel, drawer, button and analysis transitions;
* `prefers-reduced-motion` support;
* upgraded empty/welcome state with starter research questions.

The product still foregrounds RAG evidence and retrieval analysis. The welcome
screen is not a marketing hero and does not hide the evidence workflow.

## API Contract Notes

Stage 5B does not require a breaking API change.

The existing `/api/query` response remains sufficient:

* `answer.text`
* `citations`
* `final_evidence`
* `retrieval_trace`
* `retrieval`
* `timing`
* `scope`
* `diagnostics`

The backend changed preview generation quality, not the field names. `timing`
already contains `generation`, `retrieval_total`, `pipeline_build` and `total`
when produced by `QueryService`.

## Testing

Added or updated tests cover:

* historical citation clicks restoring the matching cached evidence response;
* current-query latency analysis showing `Generation` and `Retrieval total`;
* sentence-boundary final evidence previews;
* invalid table chunks returning insufficient evidence rather than cited
  evidence;
* valid table chunks being allowed and prioritized for table/numerical queries;
* existing upload, scope, citation, retrieval-flow, method-analysis and resize
  behavior.

Verification commands:

```powershell
python scripts/dev.py ui-test
python scripts/dev.py test -- tests\unit\test_fastapi_api.py tests\unit\test_query_service.py tests\unit\test_generation.py -vv
npm.cmd run build
python scripts/dev.py test
python scripts/dev.py eval
python -m compileall scripts src tests app
```

On Windows sandboxed runs, `npm.cmd run build` may need escalation because
Vite/esbuild can fail with `spawn EPERM`.

Current verification:

* `python scripts/dev.py ui-test`: 12 React tests passed.
* focused FastAPI/query/generation regression: 21 tests passed.
* `npm.cmd run build`: passed after sandbox escalation.
* `python scripts/dev.py test`: 94 tests passed.
* `python scripts/dev.py eval`: completed and wrote evaluation reports.
* `python -m compileall scripts src tests app`: passed.

## Out Of Scope

* No RAG core rewrite.
* No Chroma, LangChain, Docker, ASR/TTS or database.
* No extra LLM evidence-refinement call by default.
* No persistent multi-session chat history.
* No removal of Streamlit backup or offline evaluation pipeline.
