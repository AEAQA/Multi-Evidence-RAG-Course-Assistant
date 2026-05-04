import type { DocumentRecord, ScopeMode, UploadFailure } from "../types";

interface MaterialsDrawerProps {
  documents: DocumentRecord[];
  scopeMode: ScopeMode;
  selectedDocIds: string[];
  uploadFailures: UploadFailure[];
  isUploading: boolean;
  onScopeModeChange: (mode: ScopeMode) => void;
  onSelectedDocIdsChange: (ids: string[]) => void;
  onUpload: (files: File[]) => void;
  onDelete: (docId: string) => void;
  onRefresh: () => void;
  onClose: () => void;
}

const scopeLabels: Record<ScopeMode, string> = {
  combined: "Sample + Uploads",
  uploaded: "Uploaded only",
  sample: "Sample only"
};

export function MaterialsDrawer({
  documents,
  scopeMode,
  selectedDocIds,
  uploadFailures,
  isUploading,
  onScopeModeChange,
  onSelectedDocIdsChange,
  onUpload,
  onDelete,
  onRefresh,
  onClose
}: MaterialsDrawerProps) {
  const selected = new Set(selectedDocIds);
  const totalChunks = documents.reduce((sum, item) => sum + item.chunk_count, 0);

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
    <div className="materials-drawer" role="region" aria-label="Materials and scope">
      <div className="materials-drawer-header">
        <div>
          <p className="eyebrow">Materials</p>
          <h2>Knowledge Base</h2>
        </div>
        <div className="materials-drawer-actions">
          <button className="ghost-button" type="button" onClick={onRefresh}>
            Refresh
          </button>
          <button className="ghost-button" type="button" onClick={onClose}>
            Close
          </button>
        </div>
      </div>

      <div className="materials-drawer-body">
        <div className="materials-stats">
          <div className="materials-stat">
            <span className="metric-value">{documents.length}</span>
            <span className="metric-label">docs</span>
          </div>
          <div className="materials-stat">
            <span className="metric-value">{totalChunks}</span>
            <span className="metric-label">chunks</span>
          </div>
          <div className="materials-stat">
            <span className="metric-value">
              {selectedDocIds.length || "All"}
            </span>
            <span className="metric-label">selected</span>
          </div>
        </div>

        <div className="materials-scope-row">
          <span>Scope:</span>
          <div className="segmented-control inline" role="group" aria-label="Retrieval scope">
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
        </div>

        <div className="materials-upload">
          <label className="drop-zone compact">
            <span className="drop-title">{isUploading ? "Indexing..." : "Drop files or click to upload"}</span>
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
        </div>

        {documents.length > 0 ? (
          <div className="materials-doc-list">
            <div className="section-row">
              <h3>Uploaded Documents</h3>
              <div className="button-pair">
                <button
                  className="ghost-button"
                  type="button"
                  onClick={() => onSelectedDocIdsChange(documents.map((item) => item.doc_id))}
                >
                  Select All
                </button>
                <button
                  className="ghost-button"
                  type="button"
                  onClick={() => onSelectedDocIdsChange([])}
                >
                  Clear
                </button>
              </div>
            </div>
            <div className="compact-doc-list">
              {documents.map((document) => (
                <article
                  key={document.doc_id}
                  className={selected.has(document.doc_id) ? "doc-card doc-card-selected compact" : "doc-card compact"}
                >
                  <label className="doc-select">
                    <input
                      type="checkbox"
                      checked={selected.has(document.doc_id)}
                      onChange={() => toggleDoc(document.doc_id)}
                    />
                    <span>
                      <strong>{document.filename}</strong>
                      <small>{document.chunk_count} chunks - {formatTypeCounts(document.type_counts)}</small>
                    </span>
                  </label>
                  <button
                    className="danger-button compact"
                    type="button"
                    onClick={() => onDelete(document.doc_id)}
                    aria-label={`Delete ${document.filename}`}
                  >
                    Delete
                  </button>
                </article>
              ))}
            </div>
          </div>
        ) : (
          <div className="empty-card">No documents uploaded. Upload course PDFs or notes to get started.</div>
        )}
      </div>
    </div>
  );
}

function formatTypeCounts(typeCounts: Record<string, number>): string {
  const entries = Object.entries(typeCounts);
  if (!entries.length) {
    return "text 0";
  }
  return entries.map(([type, count]) => `${type} ${count}`).join(" / ");
}
