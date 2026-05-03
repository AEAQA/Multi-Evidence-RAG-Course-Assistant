import type {
  DocumentsResponse,
  EvaluationSummary,
  QueryResponse,
  ScopeMode,
  StatusResponse,
  UploadResponse
} from "../types";

async function requestJson<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  const response = await fetch(input, init);
  if (!response.ok) {
    const message = await response.text().catch(() => "");
    throw new Error(message || `Request failed with ${response.status}`);
  }
  return (await response.json()) as T;
}

export function getStatus(): Promise<StatusResponse> {
  return requestJson<StatusResponse>("/api/status");
}

export function getDocuments(): Promise<DocumentsResponse> {
  return requestJson<DocumentsResponse>("/api/documents");
}

export function uploadDocuments(files: File[]): Promise<UploadResponse> {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }
  return requestJson<UploadResponse>("/api/documents/upload", {
    method: "POST",
    body: formData
  });
}

export function deleteDocument(docId: string): Promise<DocumentsResponse> {
  return requestJson<DocumentsResponse>(`/api/documents/${encodeURIComponent(docId)}`, {
    method: "DELETE"
  });
}

export function runQuery(args: {
  query: string;
  topK: number;
  mode: ScopeMode;
  selectedDocIds: string[];
}): Promise<QueryResponse> {
  return requestJson<QueryResponse>("/api/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: args.query,
      top_k: args.topK,
      scope: {
        mode: args.mode,
        selected_doc_ids: args.selectedDocIds
      }
    })
  });
}

export function getEvaluationSummary(): Promise<EvaluationSummary> {
  return requestJson<EvaluationSummary>("/api/evaluation/summary");
}
