import { useEffect, useMemo, useState } from "react";
import {
  deleteDocument,
  getDocuments,
  getEvaluationSummary,
  getStatus,
  runQuery,
  uploadDocuments
} from "./api/client";
import { ChatPanel } from "./components/ChatPanel";
import { EvidenceIntelligencePanel } from "./components/EvidenceIntelligencePanel";
import { KnowledgeBasePanel } from "./components/KnowledgeBasePanel";
import type {
  ChatMessage,
  DocumentRecord,
  EvaluationSummary,
  QueryResponse,
  ScopeMode,
  StatusResponse,
  UploadFailure
} from "./types";

export default function App() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [evaluationSummary, setEvaluationSummary] = useState<EvaluationSummary | null>(null);
  const [scopeMode, setScopeMode] = useState<ScopeMode>("combined");
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [latestResponse, setLatestResponse] = useState<QueryResponse | null>(null);
  const [activeEvidenceId, setActiveEvidenceId] = useState<string | null>(null);
  const [uploadFailures, setUploadFailures] = useState<UploadFailure[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isQuerying, setIsQuerying] = useState(false);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [topK, setTopK] = useState(5);

  useEffect(() => {
    void refreshWorkspace();
    void getEvaluationSummary()
      .then(setEvaluationSummary)
      .catch(() => setEvaluationSummary(null));
  }, []);

  const selectedForRequest = useMemo(() => {
    if (scopeMode === "sample") {
      return [];
    }
    return selectedDocIds;
  }, [scopeMode, selectedDocIds]);

  async function refreshWorkspace() {
    const [statusResult, documentResult] = await Promise.allSettled([
      getStatus(),
      getDocuments()
    ]);
    if (statusResult.status === "fulfilled") {
      setStatus(statusResult.value);
    }
    if (documentResult.status === "fulfilled") {
      setDocuments(documentResult.value.documents);
    }
  }

  async function handleUpload(files: File[]) {
    setIsUploading(true);
    setUploadFailures([]);
    try {
      const result = await uploadDocuments(files);
      setDocuments(result.documents);
      setUploadFailures(result.failed);
      const newIds = result.uploaded.map((item) => item.doc_id);
      if (newIds.length) {
        setScopeMode("uploaded");
        setSelectedDocIds((current) => [...new Set([...current, ...newIds])]);
      }
    } catch (error) {
      setUploadFailures([
        {
          filename: "upload",
          error: error instanceof Error ? error.message : "Upload failed"
        }
      ]);
    } finally {
      setIsUploading(false);
    }
  }

  async function handleDelete(docId: string) {
    const result = await deleteDocument(docId);
    setDocuments(result.documents);
    setSelectedDocIds((current) => current.filter((id) => id !== docId));
  }

  async function handleQuery(query: string) {
    setQueryError(null);
    setIsQuerying(true);
    setActiveEvidenceId(null);
    const userMessage: ChatMessage = {
      id: createId(),
      role: "user",
      text: query
    };
    setMessages((current) => [...current, userMessage]);
    try {
      const response = await runQuery({
        query,
        topK,
        mode: scopeMode,
        selectedDocIds: selectedForRequest
      });
      setLatestResponse(response);
      const assistantMessage: ChatMessage = {
        id: createId(),
        role: "assistant",
        text: response.answer.text,
        response
      };
      setMessages((current) => [...current, assistantMessage]);
    } catch (error) {
      setQueryError(error instanceof Error ? error.message : "Query failed");
    } finally {
      setIsQuerying(false);
    }
  }

  return (
    <div className="app-shell">
      <KnowledgeBasePanel
        documents={documents}
        status={status}
        scopeMode={scopeMode}
        selectedDocIds={selectedDocIds}
        uploadFailures={uploadFailures}
        isUploading={isUploading}
        onScopeModeChange={setScopeMode}
        onSelectedDocIdsChange={setSelectedDocIds}
        onUpload={handleUpload}
        onDelete={handleDelete}
        onRefresh={refreshWorkspace}
      />
      <ChatPanel
        messages={messages}
        activeEvidenceId={activeEvidenceId}
        isQuerying={isQuerying}
        queryError={queryError}
        topK={topK}
        onTopKChange={(value) => setTopK(Math.max(1, Math.min(10, value || 1)))}
        onSubmit={handleQuery}
        onCitationClick={setActiveEvidenceId}
      />
      <EvidenceIntelligencePanel
        response={latestResponse}
        evaluationSummary={evaluationSummary}
        activeEvidenceId={activeEvidenceId}
      />
    </div>
  );
}

function createId(): string {
  if (globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID();
  }
  return `msg-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
