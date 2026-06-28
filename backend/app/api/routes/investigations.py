from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

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
