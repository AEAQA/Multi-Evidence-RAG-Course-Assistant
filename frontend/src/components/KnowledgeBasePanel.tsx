import type { DocumentRecord, ScopeMode, StatusResponse, UploadFailure } from "../types";

interface KnowledgeBasePanelProps {
  documents: DocumentRecord[];
  status: StatusResponse | null;
  scopeMode: ScopeMode;
  selectedDocIds: string[];
  uploadFailures: UploadFailure[];
  isUploading: boolean;
  onScopeModeChange: (mode: ScopeMode) => void;
  onSelectedDocIdsChange: (ids: string[]) => void;
  onUpload: (files: File[]) => void;
  onDelete: (docId: string) => void;
  onRefresh: () => void;
}

const scopeLabels: Record<ScopeMode, string> = {
  combined: "Sample + Uploads",
  uploaded: "Uploaded only",
  sample: "Sample only"
};

export function KnowledgeBasePanel({
  documents,
  status,
  scopeMode,
  selectedDocIds,
  uploadFailures,
  isUploading,
  onScopeModeChange,
  onSelectedDocIdsChange,
  onUpload,
  onDelete,
  onRefresh
}: KnowledgeBasePanelProps) {
  const selected = new Set(selectedDocIds);
  const totalChunks = documents.reduce((sum, item) => sum + item.chunk_count, 0);
  const providers = status?.provider_status?.by_component ?? {};

  function toggleDoc(docId: string) {
    const next = new Set(selected);
    if (next.has(docId)) {
      next.delete(docId);
    } else {
      next.add(docId);
    }
    onSelectedDocIdsChange([...next]);
  }

  return (
    <aside className="panel left-panel" aria-label="Knowledge Base">
      <div className="panel-heading">
        <p className="eyebrow">Knowledge Base</p>
        <h1>Materials</h1>
        <p className="subtle">
          Upload local study files and choose the retrieval scope before asking.
        </p>
      </div>

      <div className="status-grid">
        <div>
          <span className="metric-value">{documents.length}</span>
          <span className="metric-label">docs</span>
        </div>
        <div>
          <span className="metric-value">{totalChunks}</span>
          <span className="metric-label">chunks</span>
        </div>
        <div>
          <span className="metric-value">{status?.api?.streaming ? "SSE" : "JSON"}</span>
          <span className="metric-label">api</span>
        </div>
      </div>

      <section className="section-block">
        <div className="section-row">
          <h2>Retrieval Scope</h2>
          <button className="ghost-button" type="button" onClick={onRefresh}>
            Refresh
          </button>
        </div>
        <div className="segmented-control" role="group" aria-label="Retrieval scope">
          {(Object.keys(scopeLabels) as ScopeMode[]).map((mode) => (
            <button
              key={mode}
              type="button"
              className={scopeMode === mode ? "segment-active" : ""}
              onClick={() => onScopeModeChange(mode)}
            >
              {scopeLabels[mode]}
            </button>
          ))}
        </div>
      </section>

      <section className="section-block">
        <h2>Upload</h2>
        <label className="drop-zone">
          <span className="drop-title">{isUploading ? "Indexing..." : "Drop or select files"}</span>
          <span className="drop-caption">PDF, TXT, MD, MARKDOWN</span>
          <input
            aria-label="Upload study materials"
            type="file"
            multiple
            accept=".pdf,.txt,.md,.markdown"
            onChange={(event) => {
              const files = Array.from(event.currentTarget.files ?? []);
              if (files.length) {
                onUpload(files);
              }
              event.currentTarget.value = "";
            }}
          />
        </label>
        {uploadFailures.length > 0 ? (
          <div className="notice warning" role="status">
            {uploadFailures.map((failure) => (
              <p key={failure.filename}>
                {failure.filename}: {failure.error}
              </p>
            ))}
          </div>
        ) : null}
      </section>

      <section className="section-block document-section">
        <div className="section-row">
          <h2>Documents</h2>
          <div className="button-pair">
            <button
              className="ghost-button"
              type="button"
              onClick={() => onSelectedDocIdsChange(documents.map((item) => item.doc_id))}
              disabled={!documents.length}
            >
              All
            </button>
            <button
              className="ghost-button"
              type="button"
              onClick={() => onSelectedDocIdsChange([])}
              disabled={!documents.length}
            >
              Clear
            </button>
          </div>
        </div>

        <div className="document-list">
          {documents.length === 0 ? (
            <div className="empty-card">No uploaded documents yet.</div>
          ) : (
            documents.map((document) => (
              <article
                key={document.doc_id}
                className={selected.has(document.doc_id) ? "doc-card doc-card-selected" : "doc-card"}
              >
                <label className="doc-select">
                  <input
                    type="checkbox"
                    checked={selected.has(document.doc_id)}
                    onChange={() => toggleDoc(document.doc_id)}
                  />
                  <span>
                    <strong>{document.filename}</strong>
                    <small>{document.doc_id}</small>
                  </span>
                </label>
                <div className="doc-meta">
                  <span>{document.chunk_count} chunks</span>
                  <span>{formatTypeCounts(document.type_counts)}</span>
                  <span>RAG ready</span>
                </div>
                <button
                  className="danger-button"
                  type="button"
                  onClick={() => onDelete(document.doc_id)}
                  aria-label={`Delete ${document.filename}`}
                >
                  Delete
                </button>
              </article>
            ))
          )}
        </div>
      </section>

      <section className="section-block provider-strip">
        <h2>Provider State</h2>
        {Object.keys(providers).length === 0 ? (
          <span className="pill">local</span>
        ) : (
          Object.entries(providers).map(([name, provider]) => (
            <span className="pill" key={name}>
              {name}: {provider.state}
            </span>
          ))
        )}
      </section>
    </aside>
  );
}

function formatTypeCounts(typeCounts: Record<string, number>): string {
  const entries = Object.entries(typeCounts);
  if (!entries.length) {
    return "text 0";
  }
  return entries.map(([type, count]) => `${type} ${count}`).join(" / ");
}
