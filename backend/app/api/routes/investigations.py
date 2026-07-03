from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.session import get_db
from app.engine.full_workflow import FullInvestigationWorkflow
from app.investigations.models import (
    DecisionArtifact,
    Evidence,
    Finding,
    Investigation,
    InvestigationPlan,
    InvestigationPlanStep,
    Recommendation,
    ToolRun,
)
from app.source_data.models import PatchNote
from app.planning.factory import build_planner
from app.planning.service import PlannerRequest

router = APIRouter(prefix="/investigations", tags=["investigations"])


class RunInvestigationRequest(BaseModel):
    objective: str = Field(min_length=8)
    requested_by: str | None = None


class RunInvestigationResponse(BaseModel):
    investigation_id: int
    plan_id: int
    status: str
    objective: str
    product_domain: str | None
    counts: dict[str, int]
    findings: list[dict]
    recommendations: list[dict]
    executive_brief: dict


class StartInvestigationResponse(BaseModel):
    investigation_id: int
    plan_id: int
    status: str


@router.post("/start", response_model=StartInvestigationResponse)
def start_investigation(
    payload: RunInvestigationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> StartInvestigationResponse:
    ensure_source_data_exists(db)
    planner_result = build_planner().plan_new_investigation(
        db,
        PlannerRequest(objective=payload.objective, requested_by=payload.requested_by),
    )
    background_tasks.add_task(complete_investigation_background, planner_result.plan.id)

    return StartInvestigationResponse(
        investigation_id=planner_result.investigation.id,
        plan_id=planner_result.plan.id,
        status=planner_result.investigation.status,
    )


@router.get("/{investigation_id}/status")
def investigation_status(
    investigation_id: int,
    db: Session = Depends(get_db),
) -> dict:
    investigation = db.get(Investigation, investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    plan = db.scalar(
        select(InvestigationPlan)
        .where(InvestigationPlan.investigation_id == investigation.id)
        .order_by(InvestigationPlan.version.desc())
    )
    if plan is None:
        raise HTTPException(status_code=404, detail="Investigation plan not found")

    steps = db.scalars(
        select(InvestigationPlanStep)
        .where(InvestigationPlanStep.plan_id == plan.id)
        .order_by(InvestigationPlanStep.step_order)
    ).all()
    tool_runs = db.scalars(
        select(ToolRun)
        .where(ToolRun.investigation_id == investigation.id)
        .order_by(ToolRun.created_at, ToolRun.id)
    ).all()
    evidence_items = db.scalars(
        select(Evidence)
        .where(Evidence.investigation_id == investigation.id)
        .order_by(Evidence.created_at, Evidence.id)
    ).all()
    findings = db.scalars(
        select(Finding)
        .where(Finding.investigation_id == investigation.id)
        .order_by(Finding.created_at, Finding.id)
    ).all()
    recommendations = db.scalars(
        select(Recommendation)
        .where(Recommendation.investigation_id == investigation.id)
        .order_by(Recommendation.created_at, Recommendation.id)
    ).all()
    executive_brief = db.scalar(
        select(DecisionArtifact)
        .where(
            DecisionArtifact.investigation_id == investigation.id,
            DecisionArtifact.artifact_type == "executive_brief",
        )
        .order_by(DecisionArtifact.version.desc(), DecisionArtifact.id.desc())
    )

    return serialize_investigation_detail(
        investigation=investigation,
        plan=plan,
        steps=steps,
        tool_runs=tool_runs,
        evidence_items=evidence_items,
        findings=findings,
        recommendations=recommendations,
        executive_brief=executive_brief,
    )


@router.post("/run", response_model=RunInvestigationResponse)
def run_investigation(
    payload: RunInvestigationRequest,
    db: Session = Depends(get_db),
) -> RunInvestigationResponse:
    ensure_source_data_exists(db)
    result = FullInvestigationWorkflow().run(
        db,
        objective=payload.objective,
        requested_by=payload.requested_by,
    )

    return RunInvestigationResponse(
        investigation_id=result.investigation.id,
        plan_id=result.plan.id,
        status=result.investigation.status,
        objective=result.investigation.objective,
        product_domain=result.plan.product_domain,
        counts={
            "plan_steps": count_for(db, InvestigationPlanStep, InvestigationPlanStep.plan_id == result.plan.id),
            "tool_runs": count_for(db, ToolRun, ToolRun.investigation_id == result.investigation.id),
            "evidence": count_for(db, Evidence, Evidence.investigation_id == result.investigation.id),
            "findings": count_for(db, Finding, Finding.investigation_id == result.investigation.id),
            "recommendations": count_for(db, Recommendation, Recommendation.investigation_id == result.investigation.id),
            "artifacts": count_for(db, DecisionArtifact, DecisionArtifact.investigation_id == result.investigation.id),
        },
        findings=[
            {
                "title": finding.title,
                "summary": finding.summary,
                "confidence": finding.confidence,
                "severity": finding.severity,
                "evidence_count": len(finding.supporting_evidence_ids),
            }
            for finding in result.findings
        ],
        recommendations=[
            {
                "title": recommendation.title,
                "summary": recommendation.summary,
                "priority": recommendation.priority,
                "confidence": recommendation.confidence,
                "risk_level": recommendation.risk_level,
                "requires_approval": recommendation.requires_approval,
            }
            for recommendation in result.recommendations
        ],
        executive_brief=result.executive_brief.content,
    )


def complete_investigation_background(plan_id: int) -> None:
    db = SessionLocal()
    try:
        FullInvestigationWorkflow().complete_existing_plan(db, plan_id)
    finally:
        db.close()


def serialize_investigation_detail(
    *,
    investigation: Investigation,
    plan: InvestigationPlan,
    steps: list[InvestigationPlanStep],
    tool_runs: list[ToolRun],
    evidence_items: list[Evidence],
    findings: list[Finding],
    recommendations: list[Recommendation],
    executive_brief: DecisionArtifact | None,
) -> dict:
    evidence_by_id = {item.id: serialize_evidence(item) for item in evidence_items}
    tool_runs_by_step: dict[int, list[ToolRun]] = {}
    for tool_run in tool_runs:
        if tool_run.plan_step_id is not None:
            tool_runs_by_step.setdefault(tool_run.plan_step_id, []).append(tool_run)

    return {
        "investigation_id": investigation.id,
        "plan_id": plan.id,
        "status": investigation.status,
        "objective": investigation.objective,
        "product_domain": plan.product_domain,
        "counts": {
            "plan_steps": len(steps),
            "tool_runs": len(tool_runs),
            "evidence": len(evidence_items),
            "findings": len(findings),
            "recommendations": len(recommendations),
            "artifacts": 1 if executive_brief else 0,
        },
        "plan_steps": [
            {
                "id": step.id,
                "step_order": step.step_order,
                "step_type": step.step_type,
                "intended_tool": step.intended_tool,
                "input_scope": step.input_scope,
                "selection_rationale": step.selection_rationale,
                "status": step.status,
                "tool_runs": [serialize_tool_run(tool_run) for tool_run in tool_runs_by_step.get(step.id, [])],
            }
            for step in steps
        ],
        "tool_runs": [serialize_tool_run(tool_run) for tool_run in tool_runs],
        "evidence": list(evidence_by_id.values()),
        "findings": [
            {
                "id": finding.id,
                "title": finding.title,
                "summary": finding.summary,
                "confidence": finding.confidence,
                "severity": finding.severity,
                "evidence_count": len(finding.supporting_evidence_ids),
                "supporting_evidence_ids": finding.supporting_evidence_ids,
                "supporting_evidence": [
                    evidence_by_id[evidence_id]
                    for evidence_id in finding.supporting_evidence_ids
                    if evidence_id in evidence_by_id
                ],
            }
            for finding in findings
        ],
        "recommendations": [
            {
                "id": recommendation.id,
                "finding_id": recommendation.finding_id,
                "title": recommendation.title,
                "summary": recommendation.summary,
                "priority": recommendation.priority,
                "confidence": recommendation.confidence,
                "risk_level": recommendation.risk_level,
                "requires_approval": recommendation.requires_approval,
                "supporting_evidence_ids": recommendation.supporting_evidence_ids,
                "supporting_evidence": [
                    evidence_by_id[evidence_id]
                    for evidence_id in recommendation.supporting_evidence_ids
                    if evidence_id in evidence_by_id
                ],
            }
            for recommendation in recommendations
        ],
        "executive_brief": executive_brief.content if executive_brief else None,
    }


def serialize_tool_run(tool_run: ToolRun) -> dict:
    return {
        "id": tool_run.id,
        "plan_step_id": tool_run.plan_step_id,
        "tool_name": tool_run.tool_name,
        "status": tool_run.status,
        "input_payload": tool_run.input_payload,
        "output_summary": tool_run.output_summary,
        "error_message": tool_run.error_message,
        "started_at": tool_run.started_at.isoformat() if tool_run.started_at else None,
        "completed_at": tool_run.completed_at.isoformat() if tool_run.completed_at else None,
        "created_at": tool_run.created_at.isoformat(),
    }


def serialize_evidence(evidence: Evidence) -> dict:
    return {
        "id": evidence.id,
        "tool_run_id": evidence.tool_run_id,
        "source_type": evidence.source_type,
        "source_id": evidence.source_id,
        "title": evidence.title,
        "summary": evidence.summary,
        "observed_value": evidence.observed_value,
        "time_window": evidence.time_window,
        "strength": evidence.strength,
        "confidence": evidence.confidence,
        "metadata": evidence.evidence_metadata,
        "created_at": evidence.created_at.isoformat(),
    }


def ensure_source_data_exists(db: Session) -> None:
    existing_patches = db.scalar(select(func.count()).select_from(PatchNote))
    if existing_patches:
        return

    from app.seed.project_eclipse import (
        EVENT_DEFINITIONS,
        PATCH_DEFINITIONS,
        seed_crashes,
        seed_daily_metrics,
        seed_reviews,
        seed_store_purchases,
    )
    from app.source_data.models import LiveOpsEvent

    db.add_all(PatchNote(**patch) for patch in PATCH_DEFINITIONS)
    db.add_all(LiveOpsEvent(**event) for event in EVENT_DEFINITIONS)
    seed_daily_metrics(db)
    seed_reviews(db)
    seed_crashes(db)
    seed_store_purchases(db)
    db.commit()


def count_for(db: Session, model: type, condition) -> int:
    return int(db.scalar(select(func.count()).select_from(model).where(condition)) or 0)
