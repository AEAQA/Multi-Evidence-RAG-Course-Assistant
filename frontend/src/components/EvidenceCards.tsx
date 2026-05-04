import { useState } from "react";
import type { EvidenceItem } from "../types";

export function EvidenceCard({
  item,
  isActive,
  setRef
}: {
  item: EvidenceItem;
  isActive: boolean;
  setRef: (node: HTMLElement | null) => void;
}) {
  const [imageError, setImageError] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const previewText = item.table_summary || item.preview || "";
  const shouldCollapse = previewText.length > 280;
  const visiblePreview = shouldCollapse && !isExpanded
    ? sentenceBoundaryExcerpt(previewText, 280)
    : previewText;

  return (
    <article
      ref={setRef}
      className={isActive ? "evidence-card evidence-card-active" : "evidence-card"}
      data-testid={`evidence-card-${item.evidence_id}`}
    >
      <div className="evidence-topline">
        <strong>{item.evidence_id}</strong>
        <span className="method-badge">{item.method}</span>
        <span className="support-pill">{item.support_label ?? confidenceLabel(item.confidence ?? item.score)}</span>
      </div>

      {item.type === "image" && item.image_url && !imageError ? (
        <div className="evidence-thumb">
          <img
            src={item.image_url}
            alt={`Evidence ${item.evidence_id} image`}
            onError={() => setImageError(true)}
            loading="lazy"
          />
        </div>
      ) : null}

      {item.type === "image" && (!item.image_url || imageError) ? (
        <p className="evidence-fallback">
          {item.preview
            ? `Image evidence: ${item.preview}`
            : `Image evidence (preview unavailable)`}
        </p>
      ) : null}

      {item.type === "table" && item.table_summary ? (
        <>
          <p className="evidence-table-summary">
            <span className="table-badge">Table summary</span> {visiblePreview}
          </p>
        </>
      ) : null}

      {(item.type !== "image" || !item.image_url || imageError) && !(item.type === "table" && item.table_summary) && visiblePreview ? (
        <p>{visiblePreview}</p>
      ) : null}

      {shouldCollapse ? (
        <button
          className="detail-toggle"
          type="button"
          onClick={() => setIsExpanded((prev) => !prev)}
        >
          {isExpanded ? "Show less" : "Show more"}
        </button>
      ) : null}

      <div className="evidence-meta">
        <span>{item.source_file}</span>
        <span>page {item.page ?? "n/a"}</span>
        {item.source_url && item.page ? (
          <a href={item.source_url} target="_blank" rel="noopener noreferrer" className="open-page-link">
            Open page
          </a>
        ) : null}
        <span>{displayEvidenceType(item.type)}</span>
        {item.sub_question_id ? <span>{item.sub_question_id}</span> : null}
      </div>

      <button
        className="detail-toggle"
        type="button"
        onClick={() => setShowDetails((prev) => !prev)}
      >
        {showDetails ? "Hide developer details" : "Developer details"}
      </button>
      {showDetails ? (
        <div className="developer-details">
          <pre>
            {JSON.stringify(
              {
                chunk_id: item.chunk_id,
                doc_id: item.doc_id,
                score: item.score,
                confidence: item.confidence,
                support_label: item.support_label,
                sub_question_id: item.sub_question_id,
                method: item.method
              },
              null,
              2
            )}
          </pre>
        </div>
      ) : null}
    </article>
  );
}

export function displayEvidenceType(type?: string | null): string {
  if (type === "image") return "Image evidence";
  if (type === "table") return "Table evidence";
  return "Text evidence";
}

function confidenceLabel(value: number): string {
  if (value >= 0.75) return "supported";
  if (value >= 0.35) return "partial";
  if (value > 0) return "low";
  return "none";
}

function sentenceBoundaryExcerpt(text: string, maxChars: number): string {
  const normalized = String(text || "").split(/\s+/).filter(Boolean).join(" ");
  if (normalized.length <= maxChars) {
    return normalized;
  }
  const slice = normalized.slice(0, maxChars + 1);
  const boundary = Math.max(
    slice.lastIndexOf(". "),
    slice.lastIndexOf("? "),
    slice.lastIndexOf("! "),
    slice.lastIndexOf("; ")
  );
  if (boundary > 120) {
    return `${slice.slice(0, boundary + 1).trim()}...`;
  }
  return `${normalized.slice(0, maxChars).trim()}...`;
}
