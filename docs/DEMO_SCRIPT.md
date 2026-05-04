# Demo Script

## Evidence-Grounded RAG Study Assistant — Demo Walkthrough (~5-7 minutes)

### Preparation

1. Start the FastAPI backend: `python scripts/dev.py api`
2. Start the React frontend: `cd frontend && npm run dev`
3. Open browser at `http://localhost:5173`
4. Ensure `APP_MODE=local` in `.env` (offline demo)

### Scene 1: Initial State (10 sec)

- Show the chat-first interface: clean, centered welcome screen
- Point out the scope pill ("All materials"), Top-k selector (default 3)
- No evidence panel visible yet
- **Narration**: "The Evidence Workbench starts as a simple chat interface. Nothing is cluttered — the evidence and analytics appear only when needed."

### Scene 2: Upload Course Materials (30 sec)

- Click "Manage Materials" at the bottom of the chat
- Show the Materials Drawer sliding up with stats (0 docs, 0 chunks)
- Upload a sample course PDF (or use the built-in sample corpus)
- Show the upload completing: doc count, chunk counts by type
- Select scope: "Sample + Uploads" or "Uploaded only"
- Close the drawer
- **Narration**: "Materials are ingested with image and table extraction. Chunks are typed — text, image, or table — and each carries source file and page metadata."

### Scene 3: Single Question Query (60 sec)

- Type: "What is overfitting and why does validation data matter?"
- Press Enter to send
- **Wait for answer** — the evidence panel slides in from the right
- Read the answer that appears, pointing out:
  - `[E1]` and `[E2]` inline citation markers
  - The answer is in natural language, not raw chunk text
  - The meta line showing grounding status, evidence count, and response time
- **Narration**: "The answer is grounded in retrieved evidence. Each mark links to a specific chunk from the course materials."

### Scene 4: Citation-to-Evidence Linking (30 sec)

- Click `[E1]` in the answer
- Show the right panel scrolling to the E1 evidence card and highlighting it
- Point out the card's information: source file, page number, evidence type, support label
- Show the "Open page" link
- Click "Open page" → PDF opens in new tab at the cited page
- **Narration**: "Clicking a citation reveals the evidence and opens the source PDF at exactly the right page."

### Scene 5: Multi-Intent Query (45 sec)

- Type: "What is Word2Vec? and what is a Transformer?"
- Press Enter to send
- Show the query plan: sub-questions detected, each retrieved independently
- Point out the sub-question support status (Q1 supported by E1, Q2 supported by E2)
- Show that evidence cards are tagged by sub-question
- **Narration**: "Multi-intent questions are automatically decomposed. Each part is retrieved and verified independently."

### Scene 6: Retrieval Flow (30 sec)

- In the right panel, scroll to "Retrieval Flow"
- Show the 4-stage pipeline: BM25 → Dense → Fusion → Reranker → Final Evidence
- Point out:
  - Each stage's hit count and latency
  - Contribution counts ("Contributed 2/2 final")
  - Match strength bars with tooltip explaining they're not cross-comparable
  - The flow summary paragraph
  - Click "How to read this" for the educational explanation
- **Narration**: "The Retrieval Flow shows exactly how evidence moved through four stages — and makes clear that scores are method-specific, not comparable across different approaches."

### Scene 7: Method Comparison (45 sec)

- Expand the "Method Comparison" collapsible section
- Click through the method tabs: BM25, Dense, Fusion, Reranker
- Show the rank badges (#1, #2, #3) and match strength tracks
- Click "Analyze methods" to show the diagnostic grid:
  - Final evidence coverage (which methods contributed to final evidence)
  - Rank movement (how evidence ranks changed across stages)
  - Latency by stage
  - Citation coverage
  - Source diversity
  - Score distribution
- **Narration**: "Each retrieval method's output is available for inspection. Method analysis helps understand the differences between lexical and semantic approaches."

### Scene 8: Historical Citation (20 sec)

- Scroll up to the first answer (the overfitting question)
- Click `[E2]` in that older answer
- Show the right panel switching to that answer's cached evidence
- The panel header now shows "For: What is overfitting..."
- **Narration**: "Even after asking more questions, you can inspect evidence from earlier answers without rerunning anything."

### Scene 9: Summary (20 sec)

- Return to current view
- Recap the key features shown:
  - Grounded answers with verifiable citations
  - Four-method retrieval comparison
  - Evidence quality filtering
  - PDF source linking
  - Intent-aware query planning
- **Narration**: "The Evidence Workbench is a complete data science system — from document ingestion through retrieval comparison to verifiable grounded answers. It's designed for understanding how RAG systems work, not just consuming their output."
