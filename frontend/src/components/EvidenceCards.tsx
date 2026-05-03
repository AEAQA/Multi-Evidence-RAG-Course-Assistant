import type { EvidenceItem } from "../types";
import { formatScore, ScoreBar } from "./ScoreBar";

export function EvidenceCard({
  item,
  isActive,
  setRef
}: {
  item: EvidenceItem;
  isActive: boolean;
  setRef: (node: HTMLElement | null) => void;
}) {
  return (
    <article
      ref={setRef}
      className={isActive ? "evidence-card evidence-card-active" : "evidence-card"}
      data-testid={`evidence-card-${item.evidence_id}`}
    >
      <div className="evidence-topline">
        <strong>{item.evidence_id}</strong>
        <span>{item.method}</span>
        <span>{formatScore(item.score)}</span>
      </div>
      <p>{item.preview}</p>
      <div className="evidence-meta">
        <span>{item.source_file}</span>
        <span>page {item.page ?? "n/a"}</span>
        <span>{displayEvidenceType(item.type)}</span>
      </div>
      <small>{item.chunk_id}</small>
      <ScoreBar value={item.confidence ?? item.score} />
    </article>
  );
}

export function displayEvidenceType(type?: string | null): "Text evidence" | "Image evidence" {
  return type === "image" ? "Image evidence" : "Text evidence";
}
