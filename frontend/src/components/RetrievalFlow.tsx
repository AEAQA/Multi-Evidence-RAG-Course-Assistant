import type { RetrievalStage } from "../types";
import { ScoreBar } from "./ScoreBar";

interface RetrievalFlowProps {
  stages: RetrievalStage[];
  finalEvidenceIds?: Set<string>;
  allRetrieval?: Record<string, Array<{ chunk_id: string }>>;
}

export function RetrievalFlow({ stages, finalEvidenceIds, allRetrieval }: RetrievalFlowProps) {
  const contributionByStage: Record<string, number> = {};
  if (finalEvidenceIds && allRetrieval) {
    for (const [method, rows] of Object.entries(allRetrieval)) {
      const stageName = methodToStageName(method);
      contributionByStage[stageName] = rows.filter((row) => finalEvidenceIds.has(row.chunk_id)).length;
    }
  }

  return (
    <div className="flow-grid">
      {stages.map((stage, index) => (
        <div key={stage.stage} className="flow-item">
          {index > 0 ? <span className="flow-arrow" aria-hidden="true">-&gt;</span> : null}
          <FlowCard
            stage={stage}
            isFinal={stage.stage === "Final Evidence"}
            contribution={contributionByStage[stage.stage]}
            finalEvidenceCount={finalEvidenceIds?.size}
          />
        </div>
      ))}
    </div>
  );
}

function FlowCard({
  stage,
  isFinal,
  contribution,
  finalEvidenceCount
}: {
  stage: RetrievalStage;
  isFinal: boolean;
  contribution?: number;
  finalEvidenceCount?: number;
}) {
  return (
    <article className={`flow-card ${isFinal ? "flow-card-final" : ""}`}>
      <strong>
        {stage.stage}
        {isFinal ? <span className="flow-badge-final">Final</span> : null}
      </strong>
      <div className="flow-stats">
        <span>{stage.result_count} hits</span>
        <span>{Math.round(stage.latency_ms ?? 0)} ms</span>
      </div>
      {contribution !== undefined && finalEvidenceCount !== undefined && finalEvidenceCount > 0 ? (
        <span className="flow-contribution">
          Contributed {contribution}/{finalEvidenceCount} final
        </span>
      ) : null}
      <ScoreBar value={stage.confidence ?? stage.top_score ?? 0} />
      <span className="flow-score-label">relative score within method</span>
    </article>
  );
}

function methodToStageName(method: string): string {
  if (method === "bm25") return "BM25";
  if (method === "dense") return "Dense";
  if (method === "fusion") return "Fusion";
  if (method === "reranked") return "Reranker";
  return method;
}
