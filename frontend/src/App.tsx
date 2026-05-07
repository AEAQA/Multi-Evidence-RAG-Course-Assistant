import { useEffect, useMemo, useRef, useState } from "react";
import type { MouseEvent as ReactMouseEvent } from "react";
import {
  deleteDocument,
  getDocuments,
  getStatus,
  runQuery,
  uploadDocuments
} from "./api/client";
import { ChatPanel } from "./components/ChatPanel";
import { EvidenceIntelligencePanel } from "./components/EvidenceIntelligencePanel";
import type {
  ChatMessage,
  DocumentRecord,
  QueryResponse,
  ScopeMode,
  StatusResponse,
  UploadFailure
} from "./types";

const RATIO_DEFAULT = 0.33;
const RATIO_MIN = 0.25;
const RATIO_MAX = 0.50;

export default function App() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [scopeMode, setScopeMode] = useState<ScopeMode>("combined");
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [latestResponse, setLatestResponse] = useState<QueryResponse | null>(null);
  const [visibleEvidenceResponse, setVisibleEvidenceResponse] = useState<QueryResponse | null>(null);
  const [activeEvidenceId, setActiveEvidenceId] = useState<string | null>(null);
  const [uploadFailures, setUploadFailures] = useState<UploadFailure[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isQuerying, setIsQuerying] = useState(false);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [topK, setTopK] = useState(5);
  const [evidenceRatio, setEvidenceRatio] = useState(RATIO_DEFAULT);
  const [showMaterials, setShowMaterials] = useState(false);
  const [showEvidence, setShowEvidence] = useState(false);
  const resizeRef = useRef<ResizeState | null>(null);
  const shellRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    void refreshWorkspace();
  }, []);

  useEffect(() => {
    function handleMove(event: MouseEvent) {
      const resize = resizeRef.current;
      if (!resize || !shellRef.current) {
        return;
      }
      const rect = shellRef.current.getBoundingClientRect();
      const totalWidth = rect.width;
      if (totalWidth <= 0) {
        return;
      }
      const deltaRatio = (event.clientX - resize.startX) / totalWidth;
      const newRatio = clamp(resize.startRatio - deltaRatio, RATIO_MIN, RATIO_MAX);
      setEvidenceRatio(newRatio);
    }

    function handleUp() {
      if (!resizeRef.current) {
        return;
      }
      resizeRef.current = null;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    }

    window.addEventListener("mousemove", handleMove);
    window.addEventListener("mouseup", handleUp);
    return () => {
      window.removeEventListener("mousemove", handleMove);
      window.removeEventListener("mouseup", handleUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
  }, []);

  const selectedForRequest = useMemo(() => {
    if (scopeMode === "sample") {
      return [];
    }
    return selectedDocIds;
  }, [scopeMode, selectedDocIds]);

  const totalChunks = useMemo(
    () => documents.reduce((sum, item) => sum + item.chunk_count, 0),
    [documents]
  );

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
      setVisibleEvidenceResponse(response);
      setShowEvidence(shouldShowEvidencePanel(response));
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

  function handleCitationClick(evidenceId: string, response: QueryResponse) {
    setVisibleEvidenceResponse(response);
    setActiveEvidenceId(evidenceId);
    setShowEvidence(true);
  }

  function startResize(event: ReactMouseEvent<HTMLButtonElement>) {
    resizeRef.current = {
      startX: event.clientX,
      startRatio: evidenceRatio
    };
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  }

  const chatCol = showEvidence ? `minmax(0, ${(1 - evidenceRatio).toFixed(2)}fr)` : "1fr";
  const evidenceCol = showEvidence ? `${evidenceRatio.toFixed(2)}fr` : "0px";
  const resizeCol = showEvidence ? "8px" : "0px";
  const gridTemplateColumns = `${chatCol} ${resizeCol} ${evidenceCol}`;

  return (
    <div className="app-root">
      <header className="top-bar">
        <div className="brand-mark" aria-hidden="true">RA</div>
        <div>
          <p className="eyebrow">RAG Study Assistant</p>
          <h1>Evidence Workbench</h1>
        </div>
        <div className="top-bar-status">
          <span>{scopeLabels[scopeMode]}</span>
          <span>{documents.length} docs</span>
          <span>{totalChunks} chunks</span>
          <span>{status?.runtime?.APP_MODE ?? "local"}</span>
        </div>
      </header>
      <div
        className="app-shell"
        data-testid="app-shell"
        ref={shellRef}
        style={{ gridTemplateColumns }}
      >
        <ChatPanel
          messages={messages}
          activeEvidenceId={activeEvidenceId}
          isQuerying={isQuerying}
          queryError={queryError}
          topK={topK}
          scopeMode={scopeMode}
          onTopKChange={(value) => setTopK(Math.max(1, Math.min(10, value || 1)))}
          onSubmit={handleQuery}
          onCitationClick={handleCitationClick}
          showMaterials={showMaterials}
          documents={documents}
          selectedDocIds={selectedDocIds}
          uploadFailures={uploadFailures}
          isUploading={isUploading}
          onScopeModeChange={setScopeMode}
          onSelectedDocIdsChange={setSelectedDocIds}
          onUpload={handleUpload}
          onDelete={handleDelete}
          onRefresh={refreshWorkspace}
          onToggleMaterials={() => setShowMaterials((prev) => !prev)}
          showEvidence={showEvidence}
          onToggleEvidence={() => setShowEvidence((prev) => !prev)}
        />
        {showEvidence ? (
          <ResizeHandle
            label="Resize evidence panel"
            onMouseDown={(event) => startResize(event)}
          />
        ) : null}
        {showEvidence ? (
          <EvidenceIntelligencePanel
            response={visibleEvidenceResponse ?? latestResponse}
            activeEvidenceId={activeEvidenceId}
            onEvidenceSelect={setActiveEvidenceId}
          />
        ) : null}
      </div>
    </div>
  );
}

function shouldShowEvidencePanel(response: QueryResponse): boolean {
  if (response.evidence_panel_mode === "show") {
    return true;
  }
  if (response.evidence_panel_mode === "hide") {
    return false;
  }
  return response.final_evidence.length > 0 || response.retrieval_trace.length > 0;
}

const scopeLabels: Record<ScopeMode, string> = {
  combined: "Sample + Uploads",
  uploaded: "Uploaded only",
  sample: "Sample only"
};

interface ResizeState {
  startX: number;
  startRatio: number;
}

function ResizeHandle({
  label,
  onMouseDown
}: {
  label: string;
  onMouseDown: (event: ReactMouseEvent<HTMLButtonElement>) => void;
}) {
  return (
    <button
      className="resize-handle"
      type="button"
      role="separator"
      aria-label={label}
      aria-orientation="vertical"
      onMouseDown={onMouseDown}
    />
  );
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function createId(): string {
  if (globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID();
  }
  return `msg-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
