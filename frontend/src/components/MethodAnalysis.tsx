import { useMemo } from "react";
import type { Citation, QueryResponse, RetrievalRow } from "../types";
import { displayEvidenceType } from "./EvidenceCards";
import { formatScore, ScoreBar } from "./ScoreBar";

export const methodLabels = {
  bm25: "BM25",
  dense: "Dense",
  fusion: "Fusion",
  reranked: "Reranker"
} as const;

export type MethodKey = keyof typeof methodLabels;

export function MethodRows({ rows }: { rows: RetrievalRow[] }) {
  const maxScore = useMemo(
    () => Math.max(1, ...rows.map((row) => Math.abs(row.score))),
    [rows]
  );

  if (rows.length === 0) {
    return <div className="empty-card">No rows returned for this method.</div>;
  }

  return (
    <div className="method-list">
      {rows.map((row) => (
        <article className="method-row" key={`${row.method}-${row.chunk_id}-${row.rank}`}>
          <div className="method-row-head">
            <strong>#{row.rank}</strong>
            <span>{row.source_file}</span>
            <span>{formatScore(row.score)}</span>
          </div>
          <p>{row.preview}</p>
          <div className="evidence-meta compact">
            <span>{displayEvidenceType(row.type)}</span>
            <span>{row.chunk_id}</span>
          </div>
          <ScoreBar value={Math.abs(row.score) / maxScore} />
        </article>
      ))}
    </div>
  );
}

export function PerQueryAnalysis({ response }: { response: QueryResponse }) {
  const finalIds = new Set(response.final_evidence.map((item) => item.chunk_id));
  const finalCount = response.final_evidence.length;
  const citationStats = getCitationCoverage(response.answer.text, response.citations);
  const sourceGroups = countValues(response.final_evidence.map((item) => item.source_file));
  const typeGroups = countValues(
    response.final_evidence.map((item) => displayEvidenceType(item.type))
  );
  const latencyRows = getLatencyRows(response);
  const overlapRows = getOverlapRows(response);

  return (
    <div className="analysis-panel" role="region" aria-label="Per-query method analysis">
      <div className="analysis-header">
        <div>
          <h3>Per-query method analysis</h3>
          <p>Current-query diagnostics derived from returned retrieval traces.</p>
        </div>
        <span className="pill">{response.answer.grounding_status}</span>
      </div>

      {finalCount === 0 ? (
        <div className="notice warning">
          No final evidence available; method analysis can only inspect retrieved
          candidates for this question.
        </div>
      ) : null}

      <div className="analysis-grid">
        <article className="analysis-card">
          <h4>Final evidence coverage</h4>
          {(Object.keys(methodLabels) as MethodKey[]).map((method) => {
            const rows = response.retrieval[method];
            const hitCount = rows.filter((row) => finalIds.has(row.chunk_id)).length;
            const ratio = finalCount ? hitCount / finalCount : 0;
            return (
              <div className="analysis-row" key={method}>
                <span>{methodLabels[method]}</span>
                <strong>
                  {hitCount}/{finalCount}
                </strong>
                <ScoreBar value={ratio} />
              </div>
            );
          })}
        </article>

        <article className="analysis-card">
          <h4>Rank agreement</h4>
          {overlapRows.map((row) => (
            <div className="analysis-row" key={row.label}>
              <span>{row.label}</span>
              <strong>{Math.round(row.value * 100)}%</strong>
              <ScoreBar value={row.value} />
            </div>
          ))}
        </article>

        <article className="analysis-card">
          <h4>Latency by stage</h4>
          {latencyRows.map((row) => (
            <div className="analysis-row" key={row.label}>
              <span>{row.label}</span>
              <strong>{Math.round(row.ms)} ms</strong>
              <ScoreBar value={row.ratio} />
            </div>
          ))}
        </article>

        <article className="analysis-card">
          <h4>Citation coverage</h4>
          <div className="analysis-row">
            <span>Markers resolved</span>
            <strong>
              {citationStats.resolved}/{citationStats.total}
            </strong>
            <ScoreBar value={citationStats.total ? citationStats.resolved / citationStats.total : 0} />
          </div>
          <p className="analysis-note">
            {citationStats.unresolved.length
              ? `Unresolved: ${citationStats.unresolved.join(", ")}`
              : "Every answer marker maps to a returned evidence item."}
          </p>
        </article>

        <article className="analysis-card wide">
          <h4>Score distribution</h4>
          <div className="score-distribution">
            {(Object.keys(methodLabels) as MethodKey[]).map((method) => (
              <MethodScoreDistribution
                key={method}
                label={methodLabels[method]}
                rows={response.retrieval[method]}
              />
            ))}
          </div>
        </article>

        <article className="analysis-card">
          <h4>Source diversity</h4>
          <DiversityList title="Sources" groups={sourceGroups} />
          <DiversityList title="Types" groups={typeGroups} />
        </article>
      </div>
    </div>
  );
}

function MethodScoreDistribution({
  label,
  rows
}: {
  label: string;
  rows: RetrievalRow[];
}) {
  const maxScore = Math.max(1, ...rows.map((row) => Math.abs(row.score)));
  return (
    <div className="distribution-group">
      <strong>{label}</strong>
      {rows.slice(0, 4).map((row) => (
        <div className="distribution-row" key={`${label}-${row.chunk_id}-${row.rank}`}>
          <span>#{row.rank}</span>
          <ScoreBar value={Math.abs(row.score) / maxScore} />
        </div>
      ))}
      {rows.length === 0 ? <span className="subtle">No rows</span> : null}
    </div>
  );
}

function DiversityList({
  title,
  groups
}: {
  title: string;
  groups: Array<[string, number]>;
}) {
  return (
    <div className="diversity-list">
      <span>{title}</span>
      {groups.length ? (
        groups.map(([name, count]) => (
          <strong key={`${title}-${name}`}>
            {name} {count}
          </strong>
        ))
      ) : (
        <strong>none</strong>
      )}
    </div>
  );
}

function getCitationCoverage(answerText: string, citations: Citation[]) {
  const markers = Array.from(new Set(answerText.match(/\[E\d+\]/g) ?? [])).map((marker) =>
    marker.slice(1, -1)
  );
  const citationIds = new Set(citations.map((citation) => citation.evidence_id).filter(Boolean));
  const unresolved = markers.filter((marker) => !citationIds.has(marker));

  return {
    total: markers.length,
    resolved: markers.length - unresolved.length,
    unresolved
  };
}

function getLatencyRows(response: QueryResponse) {
  const rows = [
    ["BM25", response.timing.bm25 ?? findStageLatency(response, "BM25")],
    ["Dense", response.timing.dense ?? findStageLatency(response, "Dense")],
    ["Fusion", response.timing.fusion ?? findStageLatency(response, "Fusion")],
    ["Reranker", response.timing.reranker ?? findStageLatency(response, "Reranker")],
    ["Total", response.timing.total ?? 0]
  ] as Array<[string, number]>;
  const max = Math.max(1, ...rows.map(([, ms]) => ms));

  return rows.map(([label, ms]) => ({
    label,
    ms,
    ratio: ms / max
  }));
}

function findStageLatency(response: QueryResponse, stageName: string): number {
  return response.retrieval_trace.find((stage) => stage.stage === stageName)?.latency_ms ?? 0;
}

function getOverlapRows(response: QueryResponse) {
  const pairs: Array<[MethodKey, MethodKey]> = [
    ["bm25", "dense"],
    ["bm25", "fusion"],
    ["dense", "fusion"],
    ["fusion", "reranked"]
  ];

  return pairs.map(([left, right]) => ({
    label: `${methodLabels[left]} vs ${methodLabels[right]}`,
    value: jaccard(
      response.retrieval[left].map((row) => row.chunk_id),
      response.retrieval[right].map((row) => row.chunk_id)
    )
  }));
}

function jaccard(left: string[], right: string[]): number {
  const leftSet = new Set(left);
  const rightSet = new Set(right);
  const union = new Set([...leftSet, ...rightSet]);
  if (union.size === 0) {
    return 0;
  }
  const intersection = [...leftSet].filter((id) => rightSet.has(id));
  return intersection.length / union.size;
}

function countValues(values: string[]): Array<[string, number]> {
  const counts = values.reduce<Record<string, number>>((acc, value) => {
    acc[value] = (acc[value] ?? 0) + 1;
    return acc;
  }, {});
  return Object.entries(counts).sort((left, right) => right[1] - left[1]);
}
