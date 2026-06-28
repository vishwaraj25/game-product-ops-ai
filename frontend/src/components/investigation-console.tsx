"use client";

import { FormEvent, useState } from "react";
import { BackendHealth } from "@/components/backend-health";

type InvestigationResult = {
  investigation_id: number;
  plan_id: number;
  status: string;
  objective: string;
  product_domain: string | null;
  counts: Record<string, number>;
  findings: Array<{
    title: string;
    summary: string;
    confidence: number;
    severity: string;
    evidence_count: number;
  }>;
  recommendations: Array<{
    title: string;
    summary: string;
    priority: string;
    confidence: number;
    risk_level: string;
    requires_approval: boolean;
  }>;
  executive_brief: {
    summary: string;
    objective_interpretation: string;
    approval_required: boolean;
  };
};

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const suggestedObjectives = [
  "Why are Ranked players leaving?",
  "Evaluate Patch 1.3",
  "Analyze Android crash spike",
];

export function InvestigationConsole() {
  const [objective, setObjective] = useState(suggestedObjectives[0]);
  const [result, setResult] = useState<InvestigationResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runInvestigation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsRunning(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/investigations/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ objective, requested_by: "mvp-ui" }),
      });

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      setResult((await response.json()) as InvestigationResult);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Investigation failed");
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <main className="shell">
      <div className="workspace">
        <header className="header">
          <div>
            <p className="eyebrow">Version 1 MVP</p>
            <h1>Game Product Ops AI</h1>
            <p className="subtitle">
              Submit a product objective and let the system plan, collect
              evidence, correlate signals, create findings, and prepare a brief
              for PM review.
            </p>
          </div>
          <span className="badge">Human Approval Required</span>
        </header>

        <section className="run-panel">
          <form onSubmit={runInvestigation} className="objective-form">
            <label htmlFor="objective">Business objective</label>
            <div className="objective-row">
              <input
                id="objective"
                value={objective}
                onChange={(event) => setObjective(event.target.value)}
                minLength={8}
              />
              <button type="submit" disabled={isRunning}>
                {isRunning ? "Running..." : "Run Investigation"}
              </button>
            </div>
          </form>
          <div className="suggestions" aria-label="Suggested objectives">
            {suggestedObjectives.map((item) => (
              <button
                type="button"
                key={item}
                onClick={() => setObjective(item)}
                disabled={isRunning}
              >
                {item}
              </button>
            ))}
          </div>
          {error ? <p className="error">{error}</p> : null}
        </section>

        <section className="status-grid" aria-label="System status">
          <BackendHealth />
          <StatusCard label="Workflow" value={result?.status ?? "Ready"} />
          <StatusCard label="Domain" value={result?.product_domain ?? "Pending"} />
        </section>

        {result ? <InvestigationResultView result={result} /> : null}
      </div>
    </main>
  );
}

function StatusCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="panel">
      <h2>{label}</h2>
      <p>
        <strong className="status-ok">{value}</strong>
      </p>
    </div>
  );
}

function InvestigationResultView({ result }: { result: InvestigationResult }) {
  return (
    <section className="results">
      <div className="panel wide">
        <h2>Executive Brief</h2>
        <p>{result.executive_brief.summary}</p>
        <p className="small">{result.executive_brief.objective_interpretation}</p>
      </div>

      <div className="metric-strip">
        {Object.entries(result.counts).map(([label, value]) => (
          <div className="metric" key={label}>
            <span>{label.replace("_", " ")}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>

      <div className="two-column">
        <div className="panel">
          <h2>Findings</h2>
          <div className="stack">
            {result.findings.map((finding) => (
              <article key={finding.title} className="item">
                <h3>{finding.title}</h3>
                <p>{finding.summary}</p>
                <span>
                  {Math.round(finding.confidence * 100)}% confidence ·{" "}
                  {finding.evidence_count} evidence items
                </span>
              </article>
            ))}
          </div>
        </div>

        <div className="panel">
          <h2>Recommendations</h2>
          <div className="stack">
            {result.recommendations.map((recommendation) => (
              <article key={recommendation.title} className="item">
                <h3>{recommendation.title}</h3>
                <p>{recommendation.summary}</p>
                <span>
                  {recommendation.priority} priority ·{" "}
                  {Math.round(recommendation.confidence * 100)}% confidence
                </span>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
