import type { ChatMessage, QueryResponse } from "../types";
import type { FormEvent } from "react";
import { CitationText } from "./CitationText";

interface ChatPanelProps {
  messages: ChatMessage[];
  activeEvidenceId: string | null;
  isQuerying: boolean;
  queryError: string | null;
  topK: number;
  onTopKChange: (value: number) => void;
  onSubmit: (query: string) => void;
  onCitationClick: (evidenceId: string) => void;
}

export function ChatPanel({
  messages,
  activeEvidenceId,
  isQuerying,
  queryError,
  topK,
  onTopKChange,
  onSubmit,
  onCitationClick
}: ChatPanelProps) {
  return (
    <main className="panel chat-panel" aria-label="Chat">
      <header className="chat-header">
        <div>
          <p className="eyebrow">RAG Workbench</p>
          <h1>Grounded Study Chat</h1>
        </div>
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
      </header>

      <section className="message-scroll" aria-live="polite">
        {messages.length === 0 ? (
          <div className="chat-empty">
            <p className="eyebrow">Ready</p>
            <h2>Ask a question after choosing the corpus scope.</h2>
            <p>
              Answers are grounded in retrieved evidence and cite the final
              evidence cards inline.
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <article key={message.id} className={`message-bubble ${message.role}`}>
              <span className="message-role">{message.role === "user" ? "You" : "Assistant"}</span>
              {message.response ? (
                <AssistantAnswer
                  response={message.response}
                  activeEvidenceId={activeEvidenceId}
                  onCitationClick={onCitationClick}
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

  return (
    <form className="query-composer" onSubmit={handleSubmit}>
      <textarea
        name="query"
        aria-label="Study question"
        placeholder="Ask about retrieval, reranking, evaluation, or uploaded notes..."
        rows={2}
        disabled={disabled}
      />
      <button type="submit" disabled={disabled}>
        Send
      </button>
    </form>
  );
}
