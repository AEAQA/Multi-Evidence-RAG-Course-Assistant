import { useEffect, useMemo, useRef, useState } from "react";
import type {
  Citation,
  EvaluationSummary,
  EvidenceItem,
  QueryResponse,
  RetrievalRow,
  RetrievalStage
} from "../types";

interface EvidenceIntelligencePanelProps {
  response: QueryResponse | null;
  evaluationSummary: EvaluationSummary | null;
  activeEvidenceId: string | null;
}

const methodLabels = {
  bm25: "BM25",
  dense: "Dense",
  fusion: "Fusion",
  reranked: "Reranker"
} as const;

type MethodKey = keyof typeof methodLabels;

export function EvidenceIntelligencePanel({
  response,
  evaluationSummary,
  activeEvidenceId
}: EvidenceIntelligencePanelProps) {
  const refs = useRef<Record<string, HTMLElement | null>>({});
  const [activeMethod, setActiveMethod] = useState<MethodKey>("reranked");
  const [showMethodAnalysis, setShowMethodAnalysis] = useState(false);

  useEffect(() => {
    if (!activeEvidenceId) {
      return;
    }
    refs.current[activeEvidenceId]?.scrollIntoView({
      block: "center",
      behavior: "smooth"
    });
  }, [activeEvidenceId]);

  useEffect(() => {
    setShowMethodAnalysis(false);
  }, [response?.query]);

  if (!response) {
    return (
      <aside className="panel right-panel" aria-label="Evidence Intelligence">
        <div className="panel-heading">
          <p className="eyebrow">Evidence Intelligence</p>
          <h1>Awaiting Query</h1>
          <p className="subtle">
            Evidence cards, method rankings, retrieval flow, and diagnostics appear here.
          </p>
        </div>
        <div className="empty-card tall">
          Run a grounded question to inspect BM25, Dense, Fusion, and Reranker outputs.
        </div>
      </aside>
    );
  }

  const activeRows = response.retrieval[activeMethod];

  return (
    <aside className="panel right-panel" aria-label="Evidence Intelligence">
      <div className="panel-heading">
        <p className="eyebrow">Evidence Intelligence</p>
        <h1>Trace</h1>
        <p className="subtle">{response.answer.retrieval_explanation}</p>
      </div>

      <section className="section-block">
        <div className="section-row">
          <h2>Cited Evidence</h2>
          <span className="pill">{response.final_evidence.length} final</span>
        </div>
        <div className="evidence-stack">
          {response.final_evidence.length === 0 ? (
            <div className="notice warning">Insufficient evidence for grounded citation.</div>
          ) : (
            response.final_evidence.map((item) => (
              <EvidenceCard
                key={item.evidence_id}
                item={item}
                isActive={activeEvidenceId === item.evidence_id}
                setRef={(node) => {
                  refs.current[item.evidence_id] = node;
                }}
              />
            ))
          )}
        </div>
      </section>

      <section className="section-block">
        <h2>Retrieval Flow</h2>
        <div className="flow-grid">
          {response.retrieval_trace.map((stage) => (
            <FlowCard key={stage.stage} stage={stage} />
          ))}
        </div>
      </section>

      <section className="section-block">
        <div className="section-row">
          <h2>Method Comparison</h2>
          <span className="pill">{activeRows.length} rows</span>
        </div>
        <div className="analysis-toggle">
          <p>
            Compare how this query moved through BM25, Dense, Fusion, and Reranker
            without rerunning retrieval.
          </p>
          <button
            className={showMethodAnalysis ? "ghost-button method-active" : "ghost-button"}
            type="button"
            onClick={() => setShowMethodAnalysis((current) => !current)}
          >
            {showMethodAnalysis ? "Hide analysis" : "Analyze methods"}
          </button>
        </div>
        {showMethodAnalysis ? <PerQueryAnalysis response={response} /> : null}
        <div className="method-tabs" role="tablist" aria-label="Retrieval methods">
          {(Object.keys(methodLabels) as MethodKey[]).map((method) => (
            <button
              key={method}
              role="tab"
              aria-selected={activeMethod === method}
              className={activeMethod === method ? "method-active" : ""}
              type="button"
              onClick={() => setActiveMethod(method)}
            >
              {methodLabels[method]}
            </button>
          ))}
        </div>
        <MethodRows rows={activeRows} />
      </section>

      <Diagnostics response={response} evaluationSummary={evaluationSummary} />
    </aside>
  );
}

function EvidenceCard({
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
        <span>{item.type}</span>
      </div>
      <small>{item.chunk_id}</small>
      <ScoreBar value={item.confidence ?? item.score} />
    </article>
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

function MethodRows({ rows }: { rows: RetrievalRow[] }) {
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
          <ScoreBar value={Math.abs(row.score) / maxScore} />
        </article>
      ))}
    </div>
  );
}

function Diagnostics({
  response,
  evaluationSummary
}: {
  response: QueryResponse;
  evaluationSummary: EvaluationSummary | null;
}) {
  return (
    <section className="section-block diagnostics-block">
      <details>
        <summary>Diagnostics</summary>
        <div className="diagnostic-grid">
          <pre>{JSON.stringify(response.timing, null, 2)}</pre>
          <pre>{JSON.stringify(response.scope, null, 2)}</pre>
        </div>
        {response.warnings.length ? (
          <div className="notice warning">{response.warnings.join(" ")}</div>
        ) : null}
        {response.suggestions.length ? (
          <div className="notice">{response.suggestions.join(" ")}</div>
        ) : null}
      </details>
      <details>
        <summary>Offline Benchmark</summary>
        {evaluationSummary?.available ? (
          <EvaluationMetrics summary={evaluationSummary} />
        ) : (
          <div className="empty-card">No evaluation report loaded yet.</div>
        )}
      </details>
    </section>
  );
}

function PerQueryAnalysis({ response }: { response: QueryResponse }) {
  const finalIds = new Set(response.final_evidence.map((item) => item.chunk_id));
  const finalCount = response.final_evidence.length;
  const citationStats = getCitationCoverage(response.answer.text, response.citations);
  const sourceGroups = countValues(response.final_evidence.map((item) => item.source_file));
  const typeGroups = countValues(response.final_evidence.map((item) => item.type));
  const latencyRows = getLatencyRows(response);
  const overlapRows = getOverlapRows(response);

  return (
    <div className="analysis-panel" role="region" aria-label="Per-query method analysis">
      <div className="analysis-header">
        <div>
          <h3>Per-query method analysis</h3>
          <p>
            Proxy diagnostics for the current question only. Ground-truth Recall/MRR/NDCG
            remain in Offline Benchmark.
          </p>
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

function EvaluationMetrics({ summary }: { summary: EvaluationSummary }) {
  return (
    <div className="metric-table">
      <p className="benchmark-note">
        Fixed eval set benchmark, not the current query. Use it for reproducible
        Recall/MRR/NDCG comparison across methods.
      </p>
      {Object.entries(summary.summary_by_method).map(([method, metrics]) => (
        <article key={method}>
          <strong>{method}</strong>
          {Object.entries(metrics).map(([name, value]) => (
            <span key={name}>
              {name}: {Number(value).toFixed(3)}
            </span>
          ))}
          {summary.latency_by_method[method] != null ? (
            <span>latency: {Math.round(summary.latency_by_method[method])} ms</span>
          ) : null}
        </article>
      ))}
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

function ScoreBar({ value }: { value: number }) {
  const width = Math.max(3, Math.min(100, Number.isFinite(value) ? Math.abs(value) * 100 : 3));
  return (
    <div className="score-track" aria-hidden="true">
      <span style={{ width: `${width}%` }} />
    </div>
  );
}

function formatScore(value: number): string {
  if (!Number.isFinite(value)) {
    return "0.000";
  }
  return value.toFixed(3);
}
