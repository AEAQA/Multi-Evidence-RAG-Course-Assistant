export type ScopeMode = "sample" | "uploaded" | "combined";

export type TypeCounts = Record<string, number>;

export interface DocumentRecord {
  doc_id: string;
  filename: string;
  stored_path?: string;
  chunk_count: number;
  type_counts: TypeCounts;
  created_at?: string;
  chunk_cache_path?: string;
}

export interface DocumentsResponse {
  documents: DocumentRecord[];
  total_chunks: number;
}

export interface UploadFailure {
  filename: string;
  error: string;
}

export interface UploadResponse extends DocumentsResponse {
  uploaded: DocumentRecord[];
  failed: UploadFailure[];
  warnings: string[];
}

export interface ProviderComponent {
  component: string;
  provider: string;
  model: string;
  state: string;
  detail?: string;
}

export interface StatusResponse {
  status: string;
  provider_status?: {
    by_component?: Record<string, ProviderComponent>;
  };
  runtime?: Record<string, string>;
  document_count: number;
  total_chunks: number;
  api?: {
    streaming: boolean;
    react_product_ui_ready: boolean;
  };
}

export interface QueryScope {
  mode: ScopeMode;
  selected_doc_ids: string[];
}

export interface AnswerPayload {
  text: string;
  style: string;
  grounding_status: "grounded" | "insufficient_evidence";
  retrieval_explanation?: string;
}

export interface Citation {
  evidence_id?: string | null;
  chunk_id: string;
  doc_id?: string | null;
  source_file: string;
  page?: number | null;
}

export interface EvidenceItem {
  evidence_id: string;
  chunk_id: string;
  doc_id: string;
  source_file: string;
  page?: number | null;
  type: string;
  method: string;
  score: number;
  confidence?: number;
  preview: string;
  image_url?: string | null;
  table_summary?: string | null;
}

export interface RetrievalStage {
  stage: string;
  result_count: number;
  top_score?: number | null;
  latency_ms?: number | null;
  confidence?: number | null;
}

export interface RetrievalRow {
  rank: number;
  score: number;
  method: string;
  chunk_id: string;
  doc_id: string;
  source_file: string;
  page?: number | null;
  type: string;
  preview: string;
}

export interface MethodDiagnostic {
  method: string;
  result_count: number;
  top_score?: number | null;
  confidence_label?: string;
  recommendation?: string;
}

export interface QueryResponse {
  query: string;
  answer: AnswerPayload;
  citations: Citation[];
  final_evidence: EvidenceItem[];
  retrieval_trace: RetrievalStage[];
  retrieval: {
    bm25: RetrievalRow[];
    dense: RetrievalRow[];
    fusion: RetrievalRow[];
    reranked: RetrievalRow[];
  };
  timing: Record<string, number>;
  scope: Record<string, unknown>;
  diagnostics: MethodDiagnostic[];
  provider_status?: StatusResponse["provider_status"];
  warnings: string[];
  suggestions: string[];
}

export interface EvaluationSummary {
  available: boolean;
  summary_by_method: Record<string, Record<string, number>>;
  latency_by_method: Record<string, number>;
  report_paths: Record<string, string>;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  response?: QueryResponse;
}
