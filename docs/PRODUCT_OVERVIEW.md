# Product Overview

## Evidence-Grounded RAG Study Assistant — Product Guide

### Target Users

- University students working with course PDFs and lecture notes who want to ask questions about their materials
- Learners who need to verify answers by seeing the original source material and understanding which retrieval strategy found each piece of evidence
- Course reviewers and instructors evaluating how retrieval-augmented generation systems handle course content
- Anyone who values answer traceability over accepting a single opaque AI response

### Product Value

This is not a generic chatbot. The system is designed for evidence transparency:

- **Answers are grounded in retrieved evidence** from your course materials, not the LLM's training data.
- **Every claim carries an inline citation** (`[E1]`, `[E2]`, `[E3]`) that you can click to inspect the supporting evidence.
- **The retrieval process is visible** — you can see which methods found which evidence and how evidence moved through the pipeline.
- **Evidence can be verified at the source** — click "Open page" to view the original PDF at the exact cited page.
- **When evidence is insufficient**, the system explicitly reports this rather than generating unsupported text.
- **Low-quality evidence is filtered** — placeholder table chunks and OCR noise are detected and excluded from final answers.

### User Workflow

1. **Prepare materials** — Upload course PDFs, TXT files, or Markdown notes through the Materials drawer. The system ingests documents, extracts text/images/tables, and builds searchable indexes.
2. **Choose scope** — Select which documents to search: the built-in sample corpus, all uploaded documents, specific uploaded documents, or a combination.
3. **Ask a question** — Type a question and press Enter. The system performs retrieval, evidence selection, and answer generation.
4. **Read the grounded answer** — The answer appears in the chat workspace with inline citation markers. The Evidence Intelligence panel slides in from the right.
5. **Click a citation** — Clicking `[E1]` highlights the matching evidence card and scrolls it into view. The card shows source file, page, evidence type, and text preview.
6. **Open the source page** — Click "Open page" to view the original PDF at the exact page in a new browser tab.
7. **Inspect the retrieval journey** — Optionally expand the Retrieval Flow visualization and Method Comparison sections to see how each retrieval stage contributed.

### UI Design

The interface uses a two-column product layout:

```
┌──────────────────────────┬──────────────────────────────┐
│ CHAT WORKSPACE           │ EVIDENCE INTELLIGENCE         │
│                          │                               │
│ [Scope pill] [Top-k]     │ Quick nav: [E1] [E2] [E3]    │
│ ──────────────────────── │ ──────────────────────────── │
│ Message history          │ Cited Evidence cards (E1..E3) │
│                          │                               │
│                          │ Retrieval Flow                │
│ [Materials drawer —      │  BM25 → Dense → Fusion →      │
│  toggleable at bottom]   │   Reranker → Final Evidence   │
│                          │                               │
│                          │ Method Comparison [collapsible]│
│ [Manage Materials]       │ Diagnostics [collapsible]     │
│ [Show/Hide Evidence]     │                               │
│ ──────────────────────── │                               │
│ [Enter question...] [>]  │                               │
└──────────────────────────┴──────────────────────────────┘
```

Key layout characteristics:
- **Chat-first startup**: The initial view shows only the chat workspace. The evidence panel slides in after the first query.
- **Proportion-based resizing**: The evidence panel width is adjustable from 25% to 50% of the screen width by dragging the vertical handle.
- **Materials drawer**: Opens at the bottom of the chat panel on demand — does not permanently occupy screen space.
- **Information hierarchy**: Sections are ordered by priority — cited evidence and retrieval flow are visible by default; method comparison and diagnostics are collapsible.

### Product Design Decisions

**Why two-panel instead of three-panel layout?**
The original three-panel layout (Knowledge Base | Chat | Evidence Intelligence) caused horizontal crowding, especially with resizable panels. Moving the Knowledge Base into a collapsible drawer at the bottom of the chat panel (Decision 028) gives the chat and evidence panels more breathing room while keeping document management accessible via a toggle button.

**Why evidence first, diagnostics later?**
The primary user value is understanding what evidence supports an answer. The right panel prioritizes cited evidence cards and the retrieval flow visualization. Detailed diagnostics — method rows, score distributions, latency breakdowns, and developer details — are available through collapsible sections but do not dominate the default view.

**Why are raw chunk IDs and internal identifiers hidden?**
Raw implementation details such as `chunk_id`, `doc_id`, hash values, and internal paths are implementation artifacts that degrade readability (Decision 027). They remain available in a collapsible "Developer details" section for debugging and API consumers, but the user-facing evidence card shows only the evidence ID, source filename, page number, evidence type, method badge, and clean preview text.

**Why might a question not show evidence?**
The intent planner classifies queries using a deterministic router. General questions (greetings, help requests), out-of-scope queries, and questions where no relevant evidence was found are returned without triggering retrieval. This prevents the system from fabricating citations or generating unsupported answers.

**Why is table evidence filtered?**
Lightweight PDF table detection frequently produces low-quality chunks containing formatting fragments, placeholder text, or repeated separator characters. These chunks are detected by the quality gate and excluded from final evidence to prevent users from seeing meaningless evidence cards. Table chunks with real content are preserved and promoted when queries explicitly reference tables, numerical data, or comparisons (Decisions 026, 031).

### Future Product Extensions

The current version completes the core data science pipeline from ingestion through retrieval comparison to verifiable grounded answers. The following areas represent natural directions for further product development, not current deficiencies:

- **Fuller multimodal interaction** — Extended support for video, audio, and complex table reconstruction with HTML rendering in evidence cards
- **Voice interaction** — ASR scaffolding exists in the codebase; a real ASR client, browser microphone integration, and TTS output would enable hands-free study workflows
- **Stronger Chinese and multilingual query support** — Current coverage for non-English queries is limited; multilingual tokenization and evaluation would expand the user base
- **Table reconstruction** — HTML rendering of detected tables directly in evidence cards, rather than relying on text-only previews
- **Larger benchmark dataset** — A more diverse set of annotated evaluation queries, potentially including course-specific multi-intent and comparison-style questions
- **Deployment hardening** — HTTPS enforcement, authentication, rate limiting, and production containerization for broader access
