import type { RetrievalStage } from "../types";

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

  const topStages = stages.filter((s) => s.stage !== "Final Evidence");
  const finalStage = stages.find((s) => s.stage === "Final Evidence");
  const contributedCount = Object.values(contributionByStage).filter((c) => c > 0).length;
  const finalCount = finalEvidenceIds?.size ?? finalStage?.result_count ?? 0;

  const summary = buildFlowSummary(contributedCount, finalCount);

  return (
    <div className="flow-section">
      <div className="flow-section-body">
        <div className="flow-grid">
          {stages.map((stage, index) => (
            <div key={stage.stage} className="flow-item">
              {index > 0 ? <span className="flow-arrow" aria-hidden="true">→</span> : null}
              <FlowCard
                stage={stage}
                isFinal={stage.stage === "Final Evidence"}
                contribution={contributionByStage[stage.stage]}
                finalEvidenceCount={finalEvidenceIds?.size}
              />
            </div>
          ))}
        </div>
        {summary ? <p className="flow-summary">{summary}</p> : null}
        <details className="flow-explainer">
          <summary>How to read this</summary>
          <p>
            BM25, Dense, Fusion, and Reranker each use different scoring
            algorithms. The bars above show <strong>match strength within each
            method</strong>, not scores that can be directly compared across
            methods. The flow moves left to right: BM25 and Dense search
            independently, Fusion blends their rankings, and Reranker selects
            the final evidence used to generate the answer.
          </p>
        </details>
      </div>
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
      <div className="flow-match-bar" aria-hidden="true">
        <span className="flow-match-fill" style={{ width: `${Math.max(4, (stage.confidence ?? 0) * 100)}%` }} />
      </div>
      <span className="flow-score-label" title="Scores are normalized within each retrieval method and should not be compared directly across BM25, Dense, Fusion, and Reranker.">
        Match strength
      </span>
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

function buildFlowSummary(contributedCount: number, finalCount: number): string | null {
  if (finalCount <= 0) return null;
  if (contributedCount >= 3) {
    return `Evidence was found across ${contributedCount} of the 4 retrieval stages. The Reranker selected ${finalCount} final evidence card${finalCount > 1 ? "s" : ""} for the answer.`;
  }
  if (contributedCount >= 2) {
    return `${contributedCount} retrieval stages contributed to the ${finalCount} final evidence card${finalCount > 1 ? "s" : ""}.`;
  }
  return `The Reranker selected ${finalCount} final evidence card${finalCount > 1 ? "s" : ""} from the fusion candidates.`;
}
