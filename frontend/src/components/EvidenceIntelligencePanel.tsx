import { useEffect, useMemo, useRef, useState } from "react";
import type { MutableRefObject } from "react";
import type { QueryResponse } from "../types";
import { ErrorBoundary } from "./ErrorBoundary";
import { EvidenceCard } from "./EvidenceCards";
import {
  MethodRows,
  methodLabels,
  PerQueryAnalysis,
  type MethodKey
} from "./MethodAnalysis";
import { MethodHowItWorks } from "./MethodGuide";
import { RetrievalFlow } from "./RetrievalFlow";

interface EvidenceIntelligencePanelProps {
  response: QueryResponse | null;
  activeEvidenceId: string | null;
  onEvidenceSelect?: (evidenceId: string) => void;
}

export function EvidenceIntelligencePanel({
  response,
  activeEvidenceId,
  onEvidenceSelect
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
            Evidence cards, retrieval flow, and current-query diagnostics appear here.
          </p>
        </div>
        <div className="empty-card tall">
          Run a grounded question to inspect BM25, Dense, Fusion, and Reranker outputs.
        </div>
      </aside>
    );
  }

  return (
    <ErrorBoundary>
      <LoadedEvidencePanel
        response={response}
        activeEvidenceId={activeEvidenceId}
        refs={refs}
        activeMethod={activeMethod}
        setActiveMethod={setActiveMethod}
        showMethodAnalysis={showMethodAnalysis}
        setShowMethodAnalysis={setShowMethodAnalysis}
        onEvidenceSelect={onEvidenceSelect}
      />
    </ErrorBoundary>
  );
}

interface LoadedEvidencePanelProps {
  response: QueryResponse;
  activeEvidenceId: string | null;
  refs: MutableRefObject<Record<string, HTMLElement | null>>;
  activeMethod: MethodKey;
  setActiveMethod: (method: MethodKey) => void;
  showMethodAnalysis: boolean;
  setShowMethodAnalysis: (show: boolean) => void;
  onEvidenceSelect?: (evidenceId: string) => void;
}

function LoadedEvidencePanel({
  response,
  activeEvidenceId,
  refs,
  activeMethod,
  setActiveMethod,
  showMethodAnalysis,
  setShowMethodAnalysis,
  onEvidenceSelect
}: LoadedEvidencePanelProps) {

  const activeRows = response.retrieval?.[activeMethod] ?? [];

  const finalEvidenceIds = useMemo(
    () => new Set(response.final_evidence.map((item) => item.chunk_id)),
    [response]
  );

  const allRetrieval = useMemo(
    () => ({
      bm25: response.retrieval.bm25,
      dense: response.retrieval.dense,
      fusion: response.retrieval.fusion,
      reranked: response.retrieval.reranked
    }),
    [response]
  );

  return (
    <aside className="panel right-panel" aria-label="Evidence Intelligence">
      <div className="panel-heading">
        <p className="eyebrow">Evidence Intelligence</p>
        <h1>Evidence Trace</h1>
        <p className="evidence-context">For: {response.query}</p>
        <p className="subtle">{response.answer.retrieval_explanation}</p>
        {response.final_evidence.length > 0 ? (
          <div className="evidence-quick-nav">
            {response.final_evidence.map((item) => (
              <button
                key={item.evidence_id}
                type="button"
                className={`evidence-nav-btn ${activeEvidenceId === item.evidence_id ? "active" : ""}`}
                onClick={() => {
                  onEvidenceSelect?.(item.evidence_id);
                  refs.current[item.evidence_id]?.scrollIntoView({
                    block: "start",
                    behavior: "smooth"
                  });
                }}
              >
                {item.evidence_id}
              </button>
            ))}
          </div>
        ) : null}
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
        <RetrievalFlow
          stages={response.retrieval_trace}
          finalEvidenceIds={finalEvidenceIds}
          allRetrieval={allRetrieval}
        />
      </section>

      <section className="section-block collapsible-section">
        <details open>
          <summary className="section-summary">
            <h2>Method Comparison</h2>
            <span className="pill">{activeRows.length} rows</span>
          </summary>
          <MethodHowItWorks method={activeMethod} />
          <div className="analysis-toggle">
            <p>Inspect current-query coverage, overlap, latency, scores, and citations.</p>
            <button
              className={showMethodAnalysis ? "ghost-button method-active" : "ghost-button"}
              type="button"
              onClick={() => setShowMethodAnalysis(!showMethodAnalysis)}
            >
              {showMethodAnalysis ? "Hide analysis" : "Analyze methods"}
            </button>
          </div>
          {showMethodAnalysis ? <PerQueryAnalysis response={response} /> : null}
          <MethodTabs activeMethod={activeMethod} onMethodChange={setActiveMethod} />
          <MethodRows rows={activeRows} />
        </details>
      </section>

      <Diagnostics response={response} />
    </aside>
  );
}

function MethodTabs({
  activeMethod,
  onMethodChange
}: {
  activeMethod: MethodKey;
  onMethodChange: (method: MethodKey) => void;
}) {
  return (
    <div className="method-tabs" role="tablist" aria-label="Retrieval methods">
      {(Object.keys(methodLabels) as MethodKey[]).map((method) => (
        <button
          key={method}
          role="tab"
          aria-selected={activeMethod === method}
          className={activeMethod === method ? "method-active" : ""}
          type="button"
          onClick={() => onMethodChange(method)}
        >
          {methodLabels[method]}
        </button>
      ))}
    </div>
  );
}

function Diagnostics({ response }: { response: QueryResponse }) {
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
    </section>
  );
}
