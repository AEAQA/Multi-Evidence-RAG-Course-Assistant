# Product Overview

## Evidence-Grounded RAG Study Assistant — Product Guide

### Target Users

University students and researchers who work with course PDFs, lecture notes, and study materials. The system is designed for users who want to:

- Ask questions about their course content and get answers grounded in their own materials
- Understand *why* an answer was given (which document, which page)
- See how different retrieval strategies find relevant evidence
- Verify answers by jumping directly to the source PDF page

### Core User Flow

```
1. Upload course PDFs → 2. Select scope → 3. Ask a question → 4. Read grounded answer
                                                            → 5. Click citations to inspect evidence
                                                            → 6. Open source PDF at exact page
```

### Two-Column Interface

The product UI uses a two-column layout designed for evidence-first interaction:

```
┌──────────────────────────────┬─────────────────────────────────┐
│ CHAT WORKSPACE               │ EVIDENCE INTELLIGENCE            │
│                              │                                 │
│ [Scope pill] [Top-k]         │ Quick nav: [E1] [E2] [E3]       │
│ ─────────────────────────── │ ─────────────────────────────── │
│ Message history              │ Cited Evidence cards             │
│  User: "What is overfitting" │  E1: Text evidence, page 3       │
│  Asst: "Based on the         │  E2: Text evidence, page 5       │
│   course material,            │                                 │
│   overfitting occurs [E1]..." │ Retrieval Flow                  │
│                              │  BM25 → Dense → Fusion → Reranker│
│ [Manage Materials]           │                                 │
│ [Show/Hide Evidence]         │ Method Comparison [collapsible]  │
│ ─────────────────────────── │  BM25 | Dense | Fusion | Reranker│
│ [Enter your question...] [>] │                                 │
└──────────────────────────────┴─────────────────────────────────┘
```

**Key design decisions:**

- Evidence slides in from the right after the first query (not visible on startup, keeping the initial chat workspace clean).
- The right panel is resizable (drag the vertical handle) from 25% to 50% of screen width.
- The Materials Drawer opens at the bottom of the chat panel when needed — not occupying permanent screen space.

### Evidence Intelligence Panel

The right panel is organized in order of importance:

1. **Cited Evidence** (always visible) — Final evidence cards (E1, E2, E3) with type, source, page, support label, and preview text
2. **Retrieval Flow** (always visible) — How evidence moved through the 4-stage pipeline, with match strength bars
3. **Method Comparison** (collapsible) — Per-method diagnostic rows showing what each method found
4. **Diagnostics** (collapsible) — Raw timing, scope, warnings, and suggestions

### Citation-to-Evidence Interaction

When you click `[E1]` in the answer:
1. The right panel scrolls to the E1 evidence card
2. The card highlights with a blue left border
3. All metadata is immediately visible

For historical citations (clicking [E1] in a previous answer):
4. The right panel switches to that answer's cached evidence
5. No new API call is made
6. The panel header shows which question the evidence belongs to

### PDF Open Page

Each evidence card shows an **"Open page"** link when the source is a registered PDF. Clicking opens the PDF in a new browser tab, scrolling directly to the cited page. This lets you verify the evidence in its full context.

### Multi-Intent Queries

Questions like "What is overfitting? and what is regularization?" are automatically detected and decomposed. Each sub-question is:
- Retrieved independently
- Assigned a support status (supported / insufficient evidence)
- Displayed with its evidence cards (tagged by sub-question)

### Why This Is Not a Generic Chatbot

- Every answer is based on retrieved evidence from your materials, not the LLM's training data.
- Every claim carries an inline citation that you can click to verify.
- The retrieval process is transparent — you can see exactly which methods found which evidence.
- When evidence is insufficient, the system tells you rather than inventing an answer.
- The interface is designed for evidence inspection, not just conversation.
