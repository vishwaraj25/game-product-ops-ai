"use client";

import { FormEvent, useMemo, useState } from "react";
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

type ToolRunView = {
  name: string;
  source: string;
  status: "completed" | "pending";
};

type EvidenceGroup = {
  source: string;
  label: string;
  count: number;
  emphasis: string;
};

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const suggestedObjectives = [
  "Why are Ranked players leaving?",
  "Evaluate Patch 1.3",
  "Analyze Android crash spike",
];

const timelineStages = [
  "Planning",
  "Tool Selection",
  "Evidence Collection",
  "Correlation",
  "Findings",
  "Recommendations",
  "Executive Brief",
  "Awaiting Approval",
];

const toolsByDomain: Record<string, ToolRunView[]> = {
  ranked_retention: [
    { name: "readPatchNotes", source: "Patch Notes", status: "completed" },
    { name: "getSessionAnalytics", source: "Session Analytics", status: "completed" },
    { name: "getTelemetry", source: "Telemetry", status: "completed" },
    { name: "searchReviews", source: "Reviews", status: "completed" },
    { name: "getRevenueMetrics", source: "Revenue", status: "completed" },
  ],
  patch_evaluation: [
    { name: "readPatchNotes", source: "Patch Notes", status: "completed" },
    { name: "getSessionAnalytics", source: "Session Analytics", status: "completed" },
    { name: "getTelemetry", source: "Telemetry", status: "completed" },
    { name: "searchReviews", source: "Reviews", status: "completed" },
    { name: "getCrashMetrics", source: "Crash Reports", status: "completed" },
    { name: "getRevenueMetrics", source: "Revenue", status: "completed" },
  ],
  stability: [
    { name: "readPatchNotes", source: "Patch Notes", status: "completed" },
    { name: "getLiveOpsEvents", source: "LiveOps", status: "completed" },
    { name: "getSessionAnalytics", source: "Session Analytics", status: "completed" },
    { name: "searchReviews", source: "Reviews", status: "completed" },
    { name: "getCrashMetrics", source: "Crash Reports", status: "completed" },
  ],
  monetization: [
    { name: "readPatchNotes", source: "Patch Notes", status: "completed" },
    { name: "getLiveOpsEvents", source: "LiveOps", status: "completed" },
    { name: "getSessionAnalytics", source: "Session Analytics", status: "completed" },
    { name: "getRevenueMetrics", source: "Revenue", status: "completed" },
    { name: "getStorePurchases", source: "Store Purchases", status: "completed" },
  ],
};

const defaultTools: ToolRunView[] = [
  { name: "readPatchNotes", source: "Patch Notes", status: "completed" },
  { name: "getSessionAnalytics", source: "Session Analytics", status: "completed" },
  { name: "getTelemetry", source: "Telemetry", status: "completed" },
  { name: "searchReviews", source: "Reviews", status: "completed" },
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
        <header className="header ops-header">
          <div>
            <p className="eyebrow">LiveOps Command Review</p>
            <h1>Project Eclipse Operations Console</h1>
            <p className="subtitle">
              Run an autonomous product investigation and review the completed
              pipeline as a decision packet for game PM approval.
            </p>
          </div>
          <span className="badge">Approval Gate Active</span>
        </header>

        <section className="run-panel">
          <form onSubmit={runInvestigation} className="objective-form">
            <label htmlFor="objective">Investigation objective</label>
            <div className="objective-row">
              <input
                id="objective"
                value={objective}
                onChange={(event) => setObjective(event.target.value)}
                minLength={8}
              />
              <button type="submit" disabled={isRunning}>
                {isRunning ? <span className="spinner-label">Running</span> : "Run Investigation"}
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
          <StatusCard label="Investigation" value={result?.status ?? "Ready"} />
          <StatusCard label="Domain" value={formatLabel(result?.product_domain ?? "Pending")} />
        </section>

        <InvestigationTimeline isRunning={isRunning} hasResult={Boolean(result)} />

        {result ? <InvestigationResultView result={result} /> : <EmptyState />}
      </div>
    </main>
  );
}

function StatusCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="panel status-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function InvestigationTimeline({
  isRunning,
  hasResult,
}: {
  isRunning: boolean;
  hasResult: boolean;
}) {
  return (
    <section className="timeline-panel" aria-label="Investigation timeline">
      {timelineStages.map((stage, index) => {
        const complete = hasResult;
        const active = isRunning && index < 3;
        return (
          <div
            className={`timeline-step ${complete ? "complete" : ""} ${active ? "active" : ""}`}
            key={stage}
          >
            <span>{index + 1}</span>
            <strong>{stage}</strong>
          </div>
        );
      })}
    </section>
  );
}

function InvestigationResultView({ result }: { result: InvestigationResult }) {
  const primaryFinding = result.findings[0];
  const primaryRecommendation = result.recommendations[0];
  const tools = useMemo(
    () => toolsForResult(result).slice(0, result.counts.tool_runs ?? undefined),
    [result],
  );
  const evidenceGroups = useMemo(() => evidenceForResult(result, tools), [result, tools]);

  return (
    <section className="results">
      <ExecutiveSummaryCard
        result={result}
        primaryFinding={primaryFinding}
        primaryRecommendation={primaryRecommendation}
      />

      <div className="ops-grid">
        <ToolExecutionPanel tools={tools} />
        <EvidenceBoard groups={evidenceGroups} total={result.counts.evidence ?? 0} />
      </div>

      <div className="two-column">
        <SignalPanel title="Findings" items={result.findings} kind="finding" />
        <SignalPanel title="Recommendations" items={result.recommendations} kind="recommendation" />
      </div>
    </section>
  );
}

function ExecutiveSummaryCard({
  result,
  primaryFinding,
  primaryRecommendation,
}: {
  result: InvestigationResult;
  primaryFinding?: InvestigationResult["findings"][number];
  primaryRecommendation?: InvestigationResult["recommendations"][number];
}) {
  return (
    <section className="executive-card">
      <div className="executive-card-header">
        <div>
          <p className="eyebrow">Executive Brief</p>
          <h2>{result.objective}</h2>
        </div>
        <span className="approval-pill">
          {result.executive_brief.approval_required ? "Awaiting Approval" : "Approved"}
        </span>
      </div>

      <p className="brief-summary">{result.executive_brief.summary}</p>

      <div className="brief-grid">
        <BriefField label="Primary Finding" value={primaryFinding?.title ?? "No finding available"} />
        <BriefField
          label="Confidence"
          value={primaryFinding ? `${Math.round(primaryFinding.confidence * 100)}%` : "Pending"}
        />
        <BriefField
          label="Supporting Evidence"
          value={`${primaryFinding?.evidence_count ?? result.counts.evidence ?? 0} evidence items`}
        />
        <BriefField
          label="Recommendation"
          value={primaryRecommendation?.title ?? "No recommendation available"}
        />
      </div>
    </section>
  );
}

function BriefField({ label, value }: { label: string; value: string }) {
  return (
    <div className="brief-field">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ToolExecutionPanel({ tools }: { tools: ToolRunView[] }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Tool Execution</h2>
        <span>{tools.length} completed</span>
      </div>
      <div className="tool-list">
        {tools.map((tool) => (
          <article className="tool-row" key={tool.name}>
            <div>
              <strong>{tool.name}</strong>
              <span>{tool.source}</span>
            </div>
            <em>{tool.status}</em>
          </article>
        ))}
      </div>
    </section>
  );
}

function EvidenceBoard({ groups, total }: { groups: EvidenceGroup[]; total: number }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Evidence Board</h2>
        <span>{total} items</span>
      </div>
      <div className="evidence-board">
        {groups.map((group) => (
          <article className="evidence-source" key={group.source}>
            <div>
              <strong>{group.label}</strong>
              <span>{group.emphasis}</span>
            </div>
            <b>{group.count}</b>
          </article>
        ))}
      </div>
    </section>
  );
}

function SignalPanel({
  title,
  items,
  kind,
}: {
  title: string;
  items: InvestigationResult["findings"] | InvestigationResult["recommendations"];
  kind: "finding" | "recommendation";
}) {
  return (
    <div className="panel">
      <div className="panel-heading">
        <h2>{title}</h2>
        <span>{items.length}</span>
      </div>
      <div className="stack">
        {items.map((item) => (
          <article key={item.title} className="item">
            <h3>{item.title}</h3>
            <p>{item.summary}</p>
            <span>
              {kind === "finding"
                ? `${Math.round(("confidence" in item ? item.confidence : 0) * 100)}% confidence`
                : `${"priority" in item ? item.priority : "medium"} priority`}
            </span>
          </article>
        ))}
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <section className="empty-state">
      <strong>Ready for investigation</strong>
      <p>
        The console will populate with a completed pipeline, tool execution,
        evidence board, findings, recommendations, and executive brief.
      </p>
    </section>
  );
}

function toolsForResult(result: InvestigationResult): ToolRunView[] {
  return toolsByDomain[result.product_domain ?? ""] ?? defaultTools;
}

function evidenceForResult(result: InvestigationResult, tools: ToolRunView[]): EvidenceGroup[] {
  const total = result.counts.evidence ?? 0;
  const base = tools.map((tool) => ({
    source: tool.source,
    label: tool.source,
    count: 0,
    emphasis: evidenceEmphasis(tool.source),
  }));
  if (!base.length) {
    return [];
  }

  const even = Math.floor(total / base.length);
  let remainder = total % base.length;
  return base.map((group) => {
    const count = even + (remainder > 0 ? 1 : 0);
    remainder -= 1;
    return { ...group, count };
  });
}

function evidenceEmphasis(source: string) {
  const emphasis: Record<string, string> = {
    Telemetry: "metric movement",
    Reviews: "player sentiment",
    "Patch Notes": "release context",
    Revenue: "payer health",
    "Session Analytics": "retention and queues",
    "Crash Reports": "stability signal",
    LiveOps: "event timing",
    "Store Purchases": "purchase mix",
  };
  return emphasis[source] ?? "source signal";
}

function formatLabel(value: string) {
  return value.replaceAll("_", " ");
}
