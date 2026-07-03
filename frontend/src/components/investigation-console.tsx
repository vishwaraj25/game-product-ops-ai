"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { BackendHealth } from "@/components/backend-health";

type InvestigationPhase = "idle" | "running" | "complete";
type ApprovalDecision = "Awaiting PM approval" | "Approved" | "Rejected" | "Deeper investigation requested";

type ToolRun = {
  id: number;
  plan_step_id: number | null;
  tool_name: string;
  status: string;
  input_payload: Record<string, unknown>;
  output_summary: Record<string, unknown> | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
};

type EvidenceItem = {
  id: number;
  tool_run_id: number | null;
  source_type: string;
  source_id: string | null;
  title: string;
  summary: string;
  observed_value: Record<string, unknown> | null;
  time_window: Record<string, unknown> | null;
  strength: string;
  confidence: number | null;
  metadata: Record<string, unknown>;
  created_at: string;
};

type PlanStep = {
  id: number;
  step_order: number;
  step_type: string;
  intended_tool: string | null;
  input_scope: Record<string, unknown>;
  selection_rationale: string;
  status: string;
  tool_runs: ToolRun[];
};

type Finding = {
  id: number;
  title: string;
  summary: string;
  confidence: number;
  severity: string;
  evidence_count: number;
  supporting_evidence_ids: number[];
  supporting_evidence: EvidenceItem[];
};

type Recommendation = {
  id: number;
  finding_id: number | null;
  title: string;
  summary: string;
  priority: string;
  confidence: number;
  risk_level: string;
  requires_approval: boolean;
  supporting_evidence_ids: number[];
  supporting_evidence: EvidenceItem[];
};

type InvestigationStatus = {
  investigation_id: number;
  plan_id: number;
  status: string;
  objective: string;
  product_domain: string | null;
  counts: Record<string, number>;
  plan_steps: PlanStep[];
  tool_runs: ToolRun[];
  evidence: EvidenceItem[];
  findings: Finding[];
  recommendations: Recommendation[];
  executive_brief: {
    summary: string;
    objective_interpretation: string;
    approval_required: boolean;
  } | null;
};

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const exampleObjectives = [
  "Why are Ranked players leaving?",
  "Evaluate Patch 1.3",
  "Investigate declining Battle Pass revenue",
];

const terminalStatuses = new Set([
  "awaiting_approval",
  "execution_failed",
  "planning_failed",
]);

export function InvestigationConsole() {
  const [objective, setObjective] = useState("");
  const [submittedObjective, setSubmittedObjective] = useState("");
  const [phase, setPhase] = useState<InvestigationPhase>("idle");
  const [investigationId, setInvestigationId] = useState<number | null>(null);
  const [status, setStatus] = useState<InvestigationStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [approvalDecision, setApprovalDecision] =
    useState<ApprovalDecision>("Awaiting PM approval");

  useEffect(() => {
    if (phase !== "running" || investigationId === null) {
      return;
    }

    const activeInvestigationId = investigationId;
    let isMounted = true;
    let timer: number | undefined;

    async function pollStatus() {
      try {
        const nextStatus = await fetchInvestigationStatus(activeInvestigationId);
        if (!isMounted) {
          return;
        }

        setStatus(nextStatus);
        if (terminalStatuses.has(nextStatus.status)) {
          setPhase("complete");
          return;
        }

        timer = window.setTimeout(pollStatus, 500);
      } catch (caught) {
        if (!isMounted) {
          return;
        }
        setError(caught instanceof Error ? caught.message : "Unable to refresh investigation");
        timer = window.setTimeout(pollStatus, 1000);
      }
    }

    pollStatus();

    return () => {
      isMounted = false;
      if (timer) {
        window.clearTimeout(timer);
      }
    };
  }, [investigationId, phase]);

  async function startInvestigation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedObjective = objective.trim();
    if (trimmedObjective.length < 8) {
      return;
    }

    setError(null);
    setStatus(null);
    setApprovalDecision("Awaiting PM approval");
    setSubmittedObjective(trimmedObjective);
    setPhase("running");

    try {
      const response = await fetch(`${apiBaseUrl}/investigations/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ objective: trimmedObjective, requested_by: "mvp-ui" }),
      });

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const data = (await response.json()) as { investigation_id: number };
      setInvestigationId(data.investigation_id);
    } catch (caught) {
      setPhase("idle");
      setError(caught instanceof Error ? caught.message : "Unable to start investigation");
    }
  }

  if (phase === "idle") {
    return (
      <main className="shell idle-shell">
        <section className="idle-intake" aria-label="Start investigation">
          <p className="eyebrow">Product Ops AI</p>
          <h1>What should we investigate?</h1>
          <form onSubmit={startInvestigation} className="objective-form">
            <label htmlFor="objective">Investigation Objective</label>
            <div className="objective-row">
              <input
                id="objective"
                value={objective}
                onChange={(event) => setObjective(event.target.value)}
                minLength={8}
                placeholder="Example: Why are Ranked players leaving?"
              />
              <button type="submit" disabled={objective.trim().length < 8}>
                Start Investigation
              </button>
            </div>
          </form>
          <div className="objective-chips" aria-label="Example objectives">
            {exampleObjectives.map((example) => (
              <button type="button" key={example} onClick={() => setObjective(example)}>
                {example}
              </button>
            ))}
          </div>
          {error ? <p className="error">{error}</p> : null}
        </section>
      </main>
    );
  }

  return (
    <main className="shell">
      <div className="workspace">
        <ObjectiveHeader objective={submittedObjective} />

        {phase === "running" ? (
          <RunningInvestigation status={status} />
        ) : status ? (
          <CompleteInvestigation
            approvalDecision={approvalDecision}
            setApprovalDecision={setApprovalDecision}
            status={status}
          />
        ) : null}

        <SystemDetailsDrawer status={status} />
      </div>
    </main>
  );
}

function ObjectiveHeader({ objective }: { objective: string }) {
  return (
    <header className="collapsed-objective">
      <div>
        <p className="eyebrow">Product Ops AI</p>
        <strong>{objective}</strong>
      </div>
      <span>Investigation packet</span>
    </header>
  );
}

function RunningInvestigation({ status }: { status: InvestigationStatus | null }) {
  const steps = status?.plan_steps ?? [];
  const activeStep = steps.find((step) => step.status === "running") ?? steps.find((step) => step.status === "planned") ?? null;
  const completedSteps = steps.filter((step) => step.status === "completed");
  const futureSteps = steps.filter((step) => step.status === "planned" && step.id !== activeStep?.id);

  return (
    <section className="running-stage" aria-label="Investigation in progress">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Workflow</p>
          <h1>Investigation Timeline</h1>
        </div>
        <span className="live-pill active">Live backend state</span>
      </div>

      <div className="step-trail" aria-label="Completed steps">
        {completedSteps.map((step) => (
          <span className="completed-pill" key={step.id}>
            <span aria-hidden="true">✓</span>
            {stepLabel(step)}
          </span>
        ))}
      </div>

      <ActiveStepCard step={activeStep} status={status} />

      {futureSteps.length > 0 ? (
        <div className="future-steps" aria-label="Queued steps">
          {futureSteps.map((step) => (
            <span key={step.id}>{stepLabel(step)}</span>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function ActiveStepCard({
  step,
  status,
}: {
  step: PlanStep | null;
  status: InvestigationStatus | null;
}) {
  if (!status) {
    return (
      <article className="active-step-card">
        <span className="activity-status large" />
        <div>
          <h2>Planning investigation</h2>
          <p>Creating the investigation plan and selecting source data.</p>
        </div>
      </article>
    );
  }

  if (!step) {
    return (
      <article className="active-step-card">
        <span className="activity-status large" />
        <div>
          <h2>Finalizing investigation packet</h2>
          <p>{formatStatus(status.status)}</p>
        </div>
      </article>
    );
  }

  const toolRun = step.tool_runs[step.tool_runs.length - 1];
  return (
    <article className="active-step-card">
      <span className="activity-status large" />
      <div>
        <h2>{stepLabel(step)}</h2>
        <p>{stepStatusDescription(step, toolRun)}</p>
        <div className="active-step-meta">
          <span>{formatStatus(step.status)}</span>
          {step.intended_tool ? <span>{step.intended_tool}</span> : null}
          <span>{formatScope(step.input_scope)}</span>
        </div>
      </div>
    </article>
  );
}

function CompleteInvestigation({
  approvalDecision,
  setApprovalDecision,
  status,
}: {
  approvalDecision: ApprovalDecision;
  setApprovalDecision: (decision: ApprovalDecision) => void;
  status: InvestigationStatus;
}) {
  const completedSteps = status.plan_steps.filter((step) => step.status === "completed").length;
  const totalSteps = status.plan_steps.length;

  return (
    <section className="complete-stage" aria-label="Completed investigation">
      <div className="breadcrumb-strip">
        <strong>
          {completedSteps}/{totalSteps} steps complete
        </strong>
        <span>{formatStatus(status.status)}</span>
      </div>

      <EvidenceBoard evidence={status.evidence} toolRuns={status.tool_runs} />
      <FindingsPanel findings={status.findings} />
      <RecommendationsPanel recommendations={status.recommendations} />
      <ExecutiveBrief status={status} />
      <ApprovalPanel
        approvalDecision={approvalDecision}
        setApprovalDecision={setApprovalDecision}
      />
    </section>
  );
}

function EvidenceBoard({
  evidence,
  toolRuns,
}: {
  evidence: EvidenceItem[];
  toolRuns: ToolRun[];
}) {
  const toolRunById = useMemo(
    () => new Map(toolRuns.map((toolRun) => [toolRun.id, toolRun])),
    [toolRuns],
  );
  const grouped = useMemo(() => groupEvidenceBySource(evidence), [evidence]);

  return (
    <section className="panel deliverable-panel">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Evidence First</p>
          <h2>Evidence Board</h2>
        </div>
        <span className="count-pill">{evidence.length} records</span>
      </div>
      <div className="evidence-columns">
        {grouped.map(([source, items]) => (
          <article className="evidence-group" key={source}>
            <h3>{formatLabel(source)}</h3>
            <div className="stack">
              {items.map((item) => (
                <EvidenceDisclosure
                  evidence={item}
                  key={item.id}
                  toolRun={item.tool_run_id ? toolRunById.get(item.tool_run_id) : undefined}
                />
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function EvidenceDisclosure({
  evidence,
  toolRun,
}: {
  evidence: EvidenceItem;
  toolRun?: ToolRun;
}) {
  return (
    <details className="evidence-disclosure">
      <summary>
        <span>{evidence.title}</span>
        <b>{confidenceLabel(evidence.confidence)}</b>
      </summary>
      <p>{evidence.summary}</p>
      <dl>
        <div>
          <dt>Tool</dt>
          <dd>{toolRun?.tool_name ?? "Unknown"}</dd>
        </div>
        <div>
          <dt>Source ID</dt>
          <dd>{evidence.source_id ?? "n/a"}</dd>
        </div>
        <div>
          <dt>Raw output</dt>
          <dd>
            <pre>{JSON.stringify(rawEvidencePayload(evidence, toolRun), null, 2)}</pre>
          </dd>
        </div>
      </dl>
    </details>
  );
}

function FindingsPanel({ findings }: { findings: Finding[] }) {
  return (
    <section className="panel deliverable-panel">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Claims</p>
          <h2>Findings</h2>
        </div>
        <span className="count-pill">{findings.length}</span>
      </div>
      <div className="stack">
        {findings.map((finding) => (
          <ClaimCard
            claim={finding.title}
            confidence={finding.confidence}
            evidence={finding.supporting_evidence}
            key={finding.id}
            meta={finding.severity}
            summary={finding.summary}
          />
        ))}
      </div>
    </section>
  );
}

function RecommendationsPanel({ recommendations }: { recommendations: Recommendation[] }) {
  return (
    <section className="panel deliverable-panel">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Actions</p>
          <h2>Recommendations</h2>
        </div>
        <span className="count-pill">{recommendations.length}</span>
      </div>
      <div className="stack">
        {recommendations.map((recommendation) => (
          <ClaimCard
            claim={recommendation.title}
            confidence={recommendation.confidence}
            evidence={recommendation.supporting_evidence}
            key={recommendation.id}
            meta={`${recommendation.priority} priority · ${recommendation.risk_level} risk`}
            summary={recommendation.summary}
          />
        ))}
      </div>
    </section>
  );
}

function ClaimCard({
  claim,
  confidence,
  evidence,
  meta,
  summary,
}: {
  claim: string;
  confidence: number;
  evidence: EvidenceItem[];
  meta: string;
  summary: string;
}) {
  return (
    <article className="claim-card">
      <div className="claim-card-header">
        <div>
          <span className="claim-meta">{meta}</span>
          <h3>{claim}</h3>
        </div>
        <ConfidenceMeter confidence={confidence} />
      </div>
      <p>{summary}</p>
      <div className="supporting-lines">
        {evidence.map((item) => (
          <details className="supporting-line" key={item.id}>
            <summary>{item.title}</summary>
            <p>{item.summary}</p>
            <pre>{JSON.stringify(rawEvidencePayload(item), null, 2)}</pre>
          </details>
        ))}
      </div>
    </article>
  );
}

function ConfidenceMeter({ confidence }: { confidence: number }) {
  const percent = Math.round(confidence * 100);
  return (
    <div className="confidence-meter" aria-label={`${percent}% confidence`}>
      <span>{percent}%</span>
      <div>
        <b style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}

function ExecutiveBrief({ status }: { status: InvestigationStatus }) {
  const brief = status.executive_brief;
  return (
    <section className="executive-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Executive Brief</p>
          <h2>{status.objective}</h2>
        </div>
        <span className="approval-pill awaiting">
          {brief?.approval_required ? "Approval required" : "Approval optional"}
        </span>
      </div>
      <p className="brief-summary">{brief?.summary ?? "Executive brief is not available."}</p>
      <div className="brief-grid">
        <BriefField
          label="Objective"
          value={brief?.objective_interpretation ?? status.objective}
        />
        <BriefField label="Domain" value={formatLabel(status.product_domain ?? "Pending")} />
        <BriefField label="Evidence" value={`${status.evidence.length} traceable records`} />
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

function ApprovalPanel({
  approvalDecision,
  setApprovalDecision,
}: {
  approvalDecision: ApprovalDecision;
  setApprovalDecision: (decision: ApprovalDecision) => void;
}) {
  return (
    <section className="approval-panel">
      <div>
        <p className="eyebrow">Decision Gate</p>
        <h2>Approval Actions</h2>
      </div>
      <div className="approval-actions" aria-label="Approval actions">
        <button
          className={approvalDecision === "Approved" ? "selected approve" : "approve"}
          type="button"
          onClick={() => setApprovalDecision("Approved")}
        >
          Approve
        </button>
        <button
          className={approvalDecision === "Rejected" ? "selected reject" : "reject"}
          type="button"
          onClick={() => setApprovalDecision("Rejected")}
        >
          Reject
        </button>
        <button
          className={approvalDecision === "Deeper investigation requested" ? "selected request" : "request"}
          type="button"
          onClick={() => setApprovalDecision("Deeper investigation requested")}
        >
          Request Deeper Investigation
        </button>
      </div>
    </section>
  );
}

function SystemDetailsDrawer({ status }: { status: InvestigationStatus | null }) {
  return (
    <details className="system-drawer">
      <summary>System details</summary>
      <div className="system-grid">
        <BackendHealth />
        <div className="panel status-card tone-blue">
          <span>Investigation</span>
          <strong>{status?.status ? formatStatus(status.status) : "Waiting"}</strong>
        </div>
        <div className="panel status-card tone-amber">
          <span>Domain</span>
          <strong>{formatLabel(status?.product_domain ?? "Pending")}</strong>
        </div>
      </div>
    </details>
  );
}

async function fetchInvestigationStatus(investigationId: number) {
  const response = await fetch(`${apiBaseUrl}/investigations/${investigationId}/status`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Backend returned ${response.status}`);
  }
  return (await response.json()) as InvestigationStatus;
}

function groupEvidenceBySource(evidence: EvidenceItem[]) {
  const grouped = new Map<string, EvidenceItem[]>();
  for (const item of evidence) {
    const source = item.source_type || "unknown";
    grouped.set(source, [...(grouped.get(source) ?? []), item]);
  }
  return Array.from(grouped.entries());
}

function stepLabel(step: PlanStep) {
  return step.intended_tool ?? formatLabel(step.step_type);
}

function stepStatusDescription(step: PlanStep, toolRun?: ToolRun) {
  if (toolRun?.status === "running") {
    return `${toolRun.tool_name} is querying ${formatLabel(step.step_type)} with ${formatScope(step.input_scope)}.`;
  }
  if (step.status === "planned") {
    return `Queued to use ${step.intended_tool ?? "selected source"} for ${formatScope(step.input_scope)}.`;
  }
  if (toolRun?.status === "failed") {
    return toolRun.error_message ?? "Tool execution failed.";
  }
  return step.selection_rationale;
}

function formatScope(scope: Record<string, unknown>) {
  const days = scope.lookback_days ?? scope.window_days;
  const segment = scope.segment ?? scope.mode ?? scope.platform;
  if (days && segment) {
    return `${String(days)}d window · ${String(segment)}`;
  }
  if (days) {
    return `${String(days)}d window`;
  }
  if (segment) {
    return String(segment);
  }
  return "selected scope";
}

function rawEvidencePayload(evidence: EvidenceItem, toolRun?: ToolRun) {
  return {
    evidence: {
      id: evidence.id,
      source_type: evidence.source_type,
      source_id: evidence.source_id,
      observed_value: evidence.observed_value,
      time_window: evidence.time_window,
      metadata: evidence.metadata,
    },
    tool_output_summary: toolRun?.output_summary,
  };
}

function confidenceLabel(confidence: number | null) {
  if (confidence === null) {
    return "n/a";
  }
  return `${Math.round(confidence * 100)}%`;
}

function formatStatus(value: string) {
  return formatLabel(value);
}

function formatLabel(value: string) {
  return value.replaceAll("_", " ");
}
