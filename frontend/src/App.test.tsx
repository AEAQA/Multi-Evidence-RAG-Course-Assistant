import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";
import App from "./App";

const documentRecord = {
  doc_id: "doc-alpha",
  filename: "alpha_notes.txt",
  stored_path: "uploads/alpha_notes.txt",
  chunk_count: 3,
  type_counts: { text: 3 },
  created_at: "2026-05-03T00:00:00+00:00"
};

const queryResponse = {
  query: "What does reranking do?",
  answer: {
    text:
      "The materials indicate that reranking selects the final evidence chunks [E1]. They also state that fusion combines lexical and semantic rankings [E2].",
    style: "detailed",
    grounding_status: "grounded",
    retrieval_explanation:
      "Top reranked evidence chunks were selected for grounded answer generation."
  },
  citations: [
    {
      evidence_id: "E1",
      chunk_id: "chunk-1",
      doc_id: "doc-alpha",
      source_file: "alpha_notes.txt",
      page: 1
    },
    {
      evidence_id: "E2",
      chunk_id: "chunk-2",
      doc_id: "doc-alpha",
      source_file: "alpha_notes.txt",
      page: 2
    }
  ],
  final_evidence: [
    {
      evidence_id: "E1",
      chunk_id: "chunk-1",
      doc_id: "doc-alpha",
      source_file: "alpha_notes.txt",
      page: 1,
      type: "text",
      method: "reranked",
      score: 0.91,
      confidence: 0.91,
      preview: "Reranking selects the final evidence chunks."
    },
    {
      evidence_id: "E2",
      chunk_id: "chunk-2",
      doc_id: "doc-alpha",
      source_file: "alpha_notes.txt",
      page: 2,
      type: "table",
      method: "reranked",
      score: 0.74,
      confidence: 0.74,
      preview: "Fusion combines lexical and semantic rankings."
    }
  ],
  retrieval_trace: [
    { stage: "BM25", result_count: 3, top_score: 2.1, latency_ms: 3, confidence: 0.7 },
    { stage: "Dense", result_count: 3, top_score: 0.9, latency_ms: 4, confidence: 0.6 },
    { stage: "Fusion", result_count: 3, top_score: 0.04, latency_ms: 2, confidence: 0.8 },
    { stage: "Reranker", result_count: 3, top_score: 0.91, latency_ms: 5, confidence: 0.9 },
    { stage: "Final Evidence", result_count: 2, top_score: 0.91, latency_ms: 0, confidence: 0.9 }
  ],
  retrieval: {
    bm25: [
      {
        rank: 1,
        score: 2.1,
        method: "bm25",
        chunk_id: "chunk-1",
        doc_id: "doc-alpha",
        source_file: "alpha_notes.txt",
        page: 1,
        type: "text",
        preview: "BM25 found lexical evidence."
      },
      {
        rank: 2,
        score: 1.7,
        method: "bm25",
        chunk_id: "chunk-3",
        doc_id: "doc-alpha",
        source_file: "alpha_notes.txt",
        page: 3,
        type: "text",
        preview: "BM25 found another lexical candidate."
      }
    ],
    dense: [
      {
        rank: 1,
        score: 0.9,
        method: "dense",
        chunk_id: "chunk-2",
        doc_id: "doc-alpha",
        source_file: "alpha_notes.txt",
        page: 2,
        type: "table",
        preview: "Dense retrieval found semantic evidence."
      },
      {
        rank: 2,
        score: 0.71,
        method: "dense",
        chunk_id: "chunk-3",
        doc_id: "doc-alpha",
        source_file: "alpha_notes.txt",
        page: 3,
        type: "text",
        preview: "Dense retrieval found a nearby concept."
      }
    ],
    fusion: [
      {
        rank: 1,
        score: 0.04,
        method: "fusion",
        chunk_id: "chunk-2",
        doc_id: "doc-alpha",
        source_file: "alpha_notes.txt",
        page: 2,
        type: "table",
        preview: "Fusion merged method outputs."
      },
      {
        rank: 2,
        score: 0.03,
        method: "fusion",
        chunk_id: "chunk-1",
        doc_id: "doc-alpha",
        source_file: "alpha_notes.txt",
        page: 1,
        type: "text",
        preview: "Fusion retained lexical evidence."
      }
    ],
    reranked: [
      {
        rank: 1,
        score: 0.91,
        method: "reranked",
        chunk_id: "chunk-1",
        doc_id: "doc-alpha",
        source_file: "alpha_notes.txt",
        page: 1,
        type: "text",
        preview: "Reranker selected final evidence."
      },
      {
        rank: 2,
        score: 0.74,
        method: "reranked",
        chunk_id: "chunk-2",
        doc_id: "doc-alpha",
        source_file: "alpha_notes.txt",
        page: 2,
        type: "table",
        preview: "Reranker kept fusion evidence."
      }
    ]
  },
  timing: { bm25: 3, dense: 4, fusion: 2, reranker: 5, total: 32 },
  scope: { mode: "uploaded", chunk_count: 3, doc_count: 1 },
  diagnostics: [
    {
      method: "bm25",
      result_count: 1,
      top_score: 2.1,
      confidence_label: "high",
      recommendation: "Lexical match is strong."
    }
  ],
  provider_status: { by_component: {} },
  warnings: [],
  suggestions: ["Inspect cited evidence before trusting the answer."]
};

const insufficientResponse = {
  ...queryResponse,
  query: "unanswerable question",
  answer: {
    ...queryResponse.answer,
    text: "The selected materials do not provide enough evidence to answer.",
    grounding_status: "insufficient_evidence"
  },
  citations: [],
  final_evidence: [],
  warnings: ["No final evidence was selected."]
};

const secondQueryResponse = {
  ...queryResponse,
  query: "What does BM25 do?",
  answer: {
    ...queryResponse.answer,
    text: "BM25 finds evidence through lexical term matching [E1].",
    retrieval_explanation: "BM25 evidence was selected for this follow-up answer."
  },
  citations: [
    {
      evidence_id: "E1",
      chunk_id: "chunk-bm25",
      doc_id: "doc-alpha",
      source_file: "bm25_notes.txt",
      page: 4
    }
  ],
  final_evidence: [
    {
      evidence_id: "E1",
      chunk_id: "chunk-bm25",
      doc_id: "doc-alpha",
      source_file: "bm25_notes.txt",
      page: 4,
      type: "text",
      method: "reranked",
      score: 0.88,
      confidence: 0.88,
      preview: "BM25 ranks chunks using lexical term matching."
    }
  ],
  retrieval: {
    ...queryResponse.retrieval,
    reranked: [
      {
        rank: 1,
        score: 0.88,
        method: "reranked",
        chunk_id: "chunk-bm25",
        doc_id: "doc-alpha",
        source_file: "bm25_notes.txt",
        page: 4,
        type: "text",
        preview: "BM25 ranks chunks using lexical term matching."
      }
    ]
  },
  timing: {
    bm25: 3,
    dense: 4,
    fusion: 2,
    reranker: 5,
    retrieval_total: 14,
    generation: 48,
    total: 68
  }
};

describe("React product workbench", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.stubGlobal("fetch", vi.fn(mockFetch));
  });

  test("renders chat-first layout and offline-safe empty states", async () => {
    render(<App />);

    expect(screen.getByRole("main", { name: /chat/i })).toBeInTheDocument();
    expect(await screen.findByText(/Ask a question about your study materials/i)).toBeInTheDocument();
    expect(await screen.findByText(/1 document indexed/i)).toBeInTheDocument();
  });

  test("does not load or show the offline benchmark in the product UI", async () => {
    const fetchSpy = vi.mocked(fetch);
    render(<App />);

    const materialsBtn = await screen.findByRole("button", { name: "Manage Materials" });
    fireEvent.click(materialsBtn);
    await screen.findByText("alpha_notes.txt");

    expect(screen.queryByText(/Offline Benchmark/i)).not.toBeInTheDocument();
    expect(fetchSpy.mock.calls.some(([url]) => url === "/api/evaluation/summary")).toBe(false);
  });

  test("loads documents and shows chunk summary when materials drawer is open", async () => {
    render(<App />);

    const materialsBtn = await screen.findByRole("button", { name: "Manage Materials" });
    fireEvent.click(materialsBtn);
    expect(await screen.findByText("alpha_notes.txt")).toBeInTheDocument();
    expect(screen.getByText("3 chunks - text 3")).toBeInTheDocument();
  });

  test("reports unsupported upload failures without crashing", async () => {
    render(<App />);

    const materialsBtn = await screen.findByRole("button", { name: "Manage Materials" });
    fireEvent.click(materialsBtn);

    const input = await screen.findByLabelText(/upload study materials/i);
    fireEvent.change(input, {
      target: {
        files: [new File(["a,b"], "table.csv", { type: "text/csv" })]
      }
    });

    expect(await screen.findByText(/table.csv: Unsupported file type/i)).toBeInTheDocument();
  });

  test("sends selected uploaded scope and renders inline citation anchors", async () => {
    const user = userEvent.setup();
    const fetchSpy = vi.mocked(fetch);
    render(<App />);

    const materialsBtn = await screen.findByRole("button", { name: "Manage Materials" });
    fireEvent.click(materialsBtn);
    await screen.findByText("alpha_notes.txt");
    await user.click(screen.getByRole("button", { name: "Uploaded only" }));
    const checkbox = screen.getByRole("checkbox");
    await user.click(checkbox);
    await user.type(screen.getByLabelText(/study question/i), "What does reranking do?");
    await user.click(screen.getByRole("button", { name: "Send" }));

    await screen.findByRole("button", { name: "Show evidence E1" });
    const queryCall = fetchSpy.mock.calls.find(([url]) => url === "/api/query");
    expect(queryCall).toBeTruthy();
    expect(JSON.parse(String(queryCall?.[1]?.body))).toMatchObject({
      top_k: 3,
      scope: { mode: "uploaded", selected_doc_ids: ["doc-alpha"] }
    });
    expect(screen.getByRole("button", { name: "Show evidence E1" })).toBeInTheDocument();
  });

  test("clicking a citation highlights the matching evidence card", async () => {
    const user = userEvent.setup();
    render(<App />);

    const materialsBtn = await screen.findByRole("button", { name: "Manage Materials" });
    fireEvent.click(materialsBtn);
    await screen.findByText("alpha_notes.txt");
    await user.type(screen.getByLabelText(/study question/i), "What does reranking do?");
    await user.click(screen.getByRole("button", { name: "Send" }));
    await user.click(await screen.findByRole("button", { name: "Show evidence E1" }));

    expect(screen.getByTestId("evidence-card-E1")).toHaveClass("evidence-card-active");
  });

  test("clicking a citation in an older answer restores that turn's evidence", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.type(await screen.findByLabelText(/study question/i), "What does reranking do?");
    await user.click(screen.getByRole("button", { name: "Send" }));
    await screen.findByText("Reranking selects the final evidence chunks.");

    await user.type(screen.getByLabelText(/study question/i), "What does BM25 do?");
    await user.click(screen.getByRole("button", { name: "Send" }));
    expect(await screen.findAllByText("BM25 ranks chunks using lexical term matching.")).not.toHaveLength(0);

    const firstAnswer = screen.getByText(/The materials indicate that reranking/i).closest("article");
    expect(firstAnswer).toBeTruthy();
    await user.click(
      within(firstAnswer as HTMLElement).getByRole("button", { name: "Show evidence E1" })
    );

    expect(screen.getByText("Reranking selects the final evidence chunks.")).toBeInTheDocument();
    expect(screen.queryByText("BM25 ranks chunks using lexical term matching.")).not.toBeInTheDocument();
    expect(screen.getByTestId("evidence-card-E1")).toHaveClass("evidence-card-active");
  });

  test("renders retrieval flow, method tabs, diagnostics", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.type(await screen.findByLabelText(/study question/i), "What does reranking do?");
    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByRole("tab", { name: "BM25" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Dense" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Fusion" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Reranker" })).toBeInTheDocument();

    await user.click(screen.getByText("Diagnostics"));
    expect(screen.getByText(/Inspect cited evidence/i)).toBeInTheDocument();
    expect(within(screen.getByTestId("evidence-card-E2")).getByText("Table summary evidence")).toBeInTheDocument();
    expect(screen.queryByText("table")).not.toBeInTheDocument();
  });

  test("latency analysis separates generation from retrieval stages", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.type(await screen.findByLabelText(/study question/i), "What does reranking do?");
    await user.click(screen.getByRole("button", { name: "Send" }));
    await user.click(await screen.findByRole("button", { name: "Analyze methods" }));

    expect(screen.getByText("Generation")).toBeInTheDocument();
    expect(screen.getByText("Retrieval total")).toBeInTheDocument();
  });

  test("keeps detailed method analysis hidden until requested", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.type(await screen.findByLabelText(/study question/i), "What does reranking do?");
    await user.click(screen.getByRole("button", { name: "Send" }));

    await screen.findByRole("tab", { name: "BM25" });
    expect(screen.queryByRole("region", { name: /per-query method analysis/i })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Analyze methods" }));

    expect(screen.getByRole("region", { name: /per-query method analysis/i })).toBeInTheDocument();
    expect(screen.getByText("Final evidence coverage")).toBeInTheDocument();
    expect(screen.getByText("Rank agreement")).toBeInTheDocument();
    expect(screen.getByText("Latency by stage")).toBeInTheDocument();
    expect(screen.getByText("Score distribution")).toBeInTheDocument();
    expect(screen.getByText("Citation coverage")).toBeInTheDocument();
    expect(screen.getByText("Source diversity")).toBeInTheDocument();
    expect(screen.getByText("BM25 vs Dense")).toBeInTheDocument();
    expect(screen.getAllByText("2/2").length).toBeGreaterThan(0);
  });

  test("shows a safe method-analysis empty state for insufficient evidence", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.type(await screen.findByLabelText(/study question/i), "unanswerable question");
    await user.click(screen.getByRole("button", { name: "Send" }));
    await user.click(await screen.findByRole("button", { name: "Analyze methods" }));

    expect(screen.getByText(/No final evidence available/i)).toBeInTheDocument();
    expect(screen.getByText("Final evidence coverage")).toBeInTheDocument();
    expect(screen.getByText("Citation coverage")).toBeInTheDocument();
  });

  test("resizes right evidence panel with drag handle (ratio-based)", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.type(await screen.findByLabelText(/study question/i), "What does reranking do?");
    await user.click(screen.getByRole("button", { name: "Send" }));
    await screen.findByRole("tab", { name: "BM25" });

    const shell = await screen.findByTestId("app-shell");
    expect(shell.style.gridTemplateColumns).toContain("0.33fr");
    expect(shell.style.gridTemplateColumns).toContain("0.67fr");

    vi.spyOn(shell, "getBoundingClientRect").mockImplementation(() => ({
      x: 0, y: 0, top: 0, right: 1200, bottom: 800, left: 0,
      width: 1200, height: 800,
      toJSON: () => ({})
    }));

    fireEvent.mouseDown(screen.getByRole("separator", { name: /resize evidence panel/i }), {
      clientX: 1200 * 0.67
    });
    fireEvent.mouseMove(window, { clientX: 1200 * 0.50 });
    fireEvent.mouseUp(window);
    expect(shell.style.gridTemplateColumns).toContain("0.50fr");
  });
});

async function mockFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const url = String(input);
  if (url === "/api/status") {
    return jsonResponse({
      status: "ok",
      provider_status: { by_component: { llm: { state: "mock", provider: "mock", model: "mock-llm" } } },
      runtime: { APP_MODE: "local" },
      document_count: 1,
      total_chunks: 3,
      api: { streaming: false, react_product_ui_ready: true }
    });
  }
  if (url === "/api/documents") {
    return jsonResponse({ documents: [documentRecord], total_chunks: 3 });
  }
  if (url === "/api/documents/upload") {
    return jsonResponse({
      uploaded: [],
      failed: [{ filename: "table.csv", error: "Unsupported file type" }],
      warnings: [],
      documents: [documentRecord],
      total_chunks: 3
    });
  }
  if (url === "/api/query") {
    const body = init?.body ? JSON.parse(String(init.body)) : {};
    if (String(body.query).includes("unanswerable")) {
      return jsonResponse(insufficientResponse);
    }
    if (String(body.query).includes("BM25")) {
      return jsonResponse(secondQueryResponse);
    }
    return jsonResponse(queryResponse);
  }
  if (url.startsWith("/api/documents/") && init?.method === "DELETE") {
    return jsonResponse({ documents: [], total_chunks: 0 });
  }
  return new Response("Not found", { status: 404 });
}

function jsonResponse(payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" }
  });
}
