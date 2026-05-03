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
import { KnowledgeBasePanel } from "./components/KnowledgeBasePanel";
import type {
  ChatMessage,
  DocumentRecord,
  QueryResponse,
  ScopeMode,
  StatusResponse,
  UploadFailure
} from "./types";

const LEFT_PANEL = { default: 300, min: 240, max: 460 };
const RIGHT_PANEL = { default: 390, min: 320, max: 560 };

export default function App() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [status, setStatus] = useState<StatusResponse | null>(null);
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
  const [leftWidth, setLeftWidth] = useState(LEFT_PANEL.default);
  const [rightWidth, setRightWidth] = useState(RIGHT_PANEL.default);
  const resizeRef = useRef<ResizeState | null>(null);

  useEffect(() => {
    void refreshWorkspace();
  }, []);

  useEffect(() => {
    function handleMove(event: MouseEvent) {
      const resize = resizeRef.current;
      if (!resize) {
        return;
      }
      const delta = event.clientX - resize.startX;
      if (resize.panel === "left") {
        setLeftWidth(clamp(resize.startWidth + delta, LEFT_PANEL.min, LEFT_PANEL.max));
      } else {
        setRightWidth(clamp(resize.startWidth - delta, RIGHT_PANEL.min, RIGHT_PANEL.max));
      }
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

  function startResize(panel: "left" | "right", event: ReactMouseEvent<HTMLButtonElement>) {
    resizeRef.current = {
      panel,
      startX: event.clientX,
      startWidth: panel === "left" ? leftWidth : rightWidth
    };
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  }

  const gridTemplateColumns = `${leftWidth}px 8px minmax(420px, 1fr) 8px ${rightWidth}px`;

  return (
    <div className="app-root">
      <header className="top-bar">
        <div className="brand-mark" aria-hidden="true">RA</div>
        <div>
          <p className="eyebrow">RAG Study Assistant</p>
          <h1>Evidence Workbench</h1>
        </div>
        <div className="top-bar-status">
          <span>{status?.runtime?.APP_MODE ?? "local"}</span>
          <span>{status?.api?.streaming ? "SSE" : "JSON API"}</span>
        </div>
      </header>
      <div
        className="app-shell"
        data-testid="app-shell"
        style={{ gridTemplateColumns }}
      >
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
      <ResizeHandle
        label="Resize knowledge base panel"
        onMouseDown={(event) => startResize("left", event)}
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
      <ResizeHandle
        label="Resize evidence panel"
        onMouseDown={(event) => startResize("right", event)}
      />
      <EvidenceIntelligencePanel
        response={latestResponse}
        activeEvidenceId={activeEvidenceId}
      />
      </div>
    </div>
  );
}

interface ResizeState {
  panel: "left" | "right";
  startX: number;
  startWidth: number;
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
