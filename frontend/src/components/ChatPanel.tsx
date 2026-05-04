import type { FormEvent, KeyboardEvent } from "react";
import type { ChatMessage, DocumentRecord, QueryResponse, ScopeMode, UploadFailure } from "../types";
import { CitationText } from "./CitationText";
import { MaterialsDrawer } from "./MaterialsDrawer";

interface ChatPanelProps {
  messages: ChatMessage[];
  activeEvidenceId: string | null;
  isQuerying: boolean;
  queryError: string | null;
  topK: number;
  scopeMode: ScopeMode;
  showMaterials: boolean;
  documents: DocumentRecord[];
  selectedDocIds: string[];
  uploadFailures: UploadFailure[];
  isUploading: boolean;
  showEvidence: boolean;
  onTopKChange: (value: number) => void;
  onSubmit: (query: string) => void;
  onCitationClick: (evidenceId: string, response: QueryResponse) => void;
  onScopeModeChange: (mode: ScopeMode) => void;
  onSelectedDocIdsChange: (ids: string[]) => void;
  onUpload: (files: File[]) => void;
  onDelete: (docId: string) => void;
  onRefresh: () => void;
  onToggleMaterials: () => void;
  onToggleEvidence: () => void;
}

const scopeLabels: Record<ScopeMode, string> = {
  combined: "All materials",
  uploaded: "Uploaded only",
  sample: "Sample only"
};

export function ChatPanel({
  messages,
  activeEvidenceId,
  isQuerying,
  queryError,
  topK,
  scopeMode,
  showMaterials,
  documents,
  selectedDocIds,
  uploadFailures,
  isUploading,
  showEvidence,
  onTopKChange,
  onSubmit,
  onCitationClick,
  onScopeModeChange,
  onSelectedDocIdsChange,
  onUpload,
  onDelete,
  onRefresh,
  onToggleMaterials,
  onToggleEvidence
}: ChatPanelProps) {
  const selectedDocCount = selectedDocIds.length
    ? `${selectedDocIds.length} selected`
    : "All uploaded";
  const scopeLabel = scopeMode === "sample"
    ? "Sample corpus"
    : `${scopeLabels[scopeMode]} (${selectedDocCount})`;

  return (
    <main className="panel chat-panel" aria-label="Chat">
      <header className="chat-header">
        <div>
          <p className="eyebrow">Study Chat</p>
          <h1>Ask a Question</h1>
        </div>
        <div className="chat-header-right">
          <span className="scope-pill" title="Current retrieval scope">
            {scopeLabel}
          </span>
          <label className="topk-control">
            Top-k
            <input
              aria-label="Top k"
              type="number"
              min={1}
              max={10}
              value={topK}
              onChange={(event) => onTopKChange(Number(event.currentTarget.value))}
            />
          </label>
        </div>
      </header>

      <section className="message-scroll" aria-live="polite">
        {messages.length === 0 ? (
          <div className="chat-empty">
            <p className="eyebrow">Ready</p>
            <h2>Ask a question about your study materials.</h2>
            <p>
              Upload course PDFs or notes, then ask questions. Answers are grounded
              in retrieved evidence with inline citations.
            </p>
            <p className="subtle">
              Current scope: <strong>{scopeLabel}</strong> -{" "}
              {documents.length > 0
                ? `${documents.length} document${documents.length > 1 ? "s" : ""} indexed`
                : "No documents uploaded. Use sample corpus or upload materials."}
            </p>
            <div className="starter-grid" aria-label="Suggested questions">
              <button type="button" onClick={() => onSubmit("Compare BM25, Dense retrieval, Fusion, and Reranker for this topic.")}>
                Compare retrieval methods
              </button>
              <button type="button" onClick={() => onSubmit("What evidence supports the key concept in my materials?")}>
                Find grounded evidence
              </button>
              <button type="button" onClick={() => onSubmit("Where do the uploaded notes discuss evaluation metrics?")}>
                Inspect evaluation metrics
              </button>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <article key={message.id} className={`message-bubble ${message.role}`}>
              <span className="message-role">{message.role === "user" ? "You" : "Assistant"}</span>
              {message.response ? (
                <AssistantAnswer
                  response={message.response}
                  activeEvidenceId={activeEvidenceId}
                  onCitationClick={(evidenceId) => onCitationClick(evidenceId, message.response as QueryResponse)}
                />
              ) : (
                <p>{message.text}</p>
              )}
            </article>
          ))
        )}
        {isQuerying ? <div className="typing-card">Retrieving evidence and generating answer...</div> : null}
        {queryError ? (
          <div className="notice warning" role="alert">
            {queryError}
          </div>
        ) : null}
      </section>

      {showMaterials ? (
        <MaterialsDrawer
          documents={documents}
          scopeMode={scopeMode}
          selectedDocIds={selectedDocIds}
          uploadFailures={uploadFailures}
          isUploading={isUploading}
          onScopeModeChange={onScopeModeChange}
          onSelectedDocIdsChange={onSelectedDocIdsChange}
          onUpload={onUpload}
          onDelete={onDelete}
          onRefresh={onRefresh}
          onClose={onToggleMaterials}
        />
      ) : null}

      <div className="input-actions">
        <button
          className="input-action-btn"
          type="button"
          onClick={onToggleMaterials}
        >
          {showMaterials ? "Close Materials" : "Manage Materials"}
        </button>
        {messages.length > 0 ? (
          <button
            className="input-action-btn"
            type="button"
            onClick={onToggleEvidence}
          >
            {showEvidence ? "Hide Evidence" : "Show Evidence"}
          </button>
        ) : null}
      </div>

      <QueryComposer disabled={isQuerying} onSubmit={onSubmit} />
    </main>
  );
}

function AssistantAnswer({
  response,
  activeEvidenceId,
  onCitationClick
}: {
  response: QueryResponse;
  activeEvidenceId: string | null;
  onCitationClick: (evidenceId: string) => void;
}) {
  return (
    <div className="assistant-answer">
      <p>
        <CitationText
          text={response.answer.text}
          citations={response.citations}
          evidence={response.final_evidence}
          activeEvidenceId={activeEvidenceId}
          onCitationClick={onCitationClick}
        />
      </p>
      <div className="answer-meta">
        <span>{response.answer.grounding_status}</span>
        <span>{response.final_evidence.length} evidence cards</span>
        <span>{Math.round(response.timing.total ?? 0)} ms</span>
      </div>
    </div>
  );
}

function QueryComposer({
  disabled,
  onSubmit
}: {
  disabled: boolean;
  onSubmit: (query: string) => void;
}) {
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const field = form.elements.namedItem("query") as HTMLTextAreaElement;
    const value = field.value.trim();
    if (!value) {
      return;
    }
    onSubmit(value);
    field.value = "";
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      const field = event.currentTarget;
      const value = field.value.trim();
      if (!value) {
        return;
      }
      onSubmit(value);
      field.value = "";
    }
  };

  return (
    <form className="query-composer" onSubmit={handleSubmit}>
      <textarea
        name="query"
        aria-label="Study question"
        placeholder="Ask about retrieval, reranking, evaluation, or uploaded notes..."
        rows={2}
        disabled={disabled}
        onKeyDown={handleKeyDown}
      />
      <button type="submit" disabled={disabled}>
        Send
      </button>
    </form>
  );
}
