import type { RetrievalStage } from "../types";
import { ScoreBar } from "./ScoreBar";

export function RetrievalFlow({ stages }: { stages: RetrievalStage[] }) {
  return (
    <div className="flow-grid">
      {stages.map((stage) => (
        <FlowCard key={stage.stage} stage={stage} />
      ))}
    </div>
  );
}

function FlowCard({ stage }: { stage: RetrievalStage }) {
  return (
    <article className="flow-card">
      <strong>{stage.stage}</strong>
      <span>{stage.result_count} hits</span>
      <span>{Math.round(stage.latency_ms ?? 0)} ms</span>
      <ScoreBar value={stage.confidence ?? stage.top_score ?? 0} />
    </article>
  );
}
