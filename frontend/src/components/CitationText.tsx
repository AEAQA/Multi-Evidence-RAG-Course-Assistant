import type { Citation, EvidenceItem } from "../types";

interface CitationTextProps {
  text: string;
  citations: Citation[];
  evidence: EvidenceItem[];
  activeEvidenceId?: string | null;
  onCitationClick: (evidenceId: string) => void;
}

const MARKER_PATTERN = /(\[(E\d+)\])/g;

export function CitationText({
  text,
  citations,
  evidence,
  activeEvidenceId,
  onCitationClick
}: CitationTextProps) {
  const resolvedIds = new Set<string>();
  for (const citation of citations) {
    if (citation.evidence_id) {
      resolvedIds.add(citation.evidence_id);
    }
  }
  for (const item of evidence) {
    resolvedIds.add(item.evidence_id);
  }

  const allMarkers = Array.from(
    new Set((text.match(/\[E\d+\]/g) ?? []).map((marker) => marker.slice(1, -1)))
  );
  const unresolved = allMarkers.filter((id) => !resolvedIds.has(id));

  const parts = text.split(MARKER_PATTERN);
  return (
    <>
      {parts.map((part, index) => {
        const markerMatch = part.match(/^\[(E\d+)\]$/);
        if (!markerMatch) {
          if (/^E\d+$/.test(part)) {
            return null;
          }
          return <span key={`${part}-${index}`}>{part}</span>;
        }
        const evidenceId = markerMatch[1];
        if (!resolvedIds.has(evidenceId)) {
          return (
            <span
              key={`${part}-${index}`}
              className="citation-anchor-unresolved"
              title={`Citation ${evidenceId} is not linked to returned evidence`}
            >
              [{evidenceId}]
            </span>
          );
        }
        return (
          <button
            className={
              activeEvidenceId === evidenceId
                ? "citation-anchor citation-anchor-active"
                : "citation-anchor"
            }
            key={`${part}-${index}`}
            type="button"
            onClick={() => onCitationClick(evidenceId)}
            aria-label={`Show evidence ${evidenceId}`}
          >
            [{evidenceId}]
          </button>
        );
      })}
      {unresolved.length > 0 ? (
        <div className="notice warning citation-warning">
          Unresolved citation{unresolved.length > 1 ? "s" : ""}:{" "}
          {unresolved.map((id) => `[${id}]`).join(", ")} - evidence may be missing.
        </div>
      ) : null}
    </>
  );
}
