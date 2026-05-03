import { useEffect, useMemo, useRef, useState } from "react";
import type {
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

  useEffect(() => {
    if (!activeEvidenceId) {
      return;
    }
    refs.current[activeEvidenceId]?.scrollIntoView({
      block: "center",
      behavior: "smooth"
    });
  }, [activeEvidenceId]);

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
        <summary>Evaluation metrics</summary>
        {evaluationSummary?.available ? (
          <EvaluationMetrics summary={evaluationSummary} />
        ) : (
          <div className="empty-card">No evaluation report loaded yet.</div>
        )}
      </details>
    </section>
  );
}

function EvaluationMetrics({ summary }: { summary: EvaluationSummary }) {
  return (
    <div className="metric-table">
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
