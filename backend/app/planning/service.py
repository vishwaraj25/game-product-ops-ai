from __future__ import annotations

from dataclasses import dataclass

from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.service import AIReasoningService
from app.investigations.models import Investigation, InvestigationPlan, InvestigationPlanStep
from app.planning.exceptions import PlannerOutputError
from app.planning.schemas import StructuredInvestigationPlan


@dataclass(frozen=True)
class PlannerRequest:
    objective: str
    game_id: str = "project-eclipse"
    requested_by: str | None = None


@dataclass(frozen=True)
class PlannerResult:
    investigation: Investigation
    plan: InvestigationPlan


class InvestigationPlanner:
    def __init__(self, ai_reasoning: AIReasoningService) -> None:
        self.ai_reasoning = ai_reasoning

    def plan_new_investigation(self, db: Session, request: PlannerRequest) -> PlannerResult:
        investigation = Investigation(
            game_id=request.game_id,
            objective=request.objective,
            status="planning",
            requested_by=request.requested_by,
        )
        db.add(investigation)
        db.flush()

        try:
            plan = self.plan_existing_investigation(db, investigation)
        except PlannerOutputError:
            investigation.status = "planning_failed"
            db.commit()
            raise

        return PlannerResult(investigation=investigation, plan=plan)

    def plan_existing_investigation(
        self,
        db: Session,
        investigation: Investigation,
    ) -> InvestigationPlan:
        structured_plan = self._generate_plan(investigation.objective)
        trace = self.ai_reasoning.last_trace
        next_version = self._next_plan_version(db, investigation.id)

        plan = InvestigationPlan(
            investigation_id=investigation.id,
            objective=structured_plan.objective,
            objective_interpretation=structured_plan.objective_interpretation,
            product_domain=structured_plan.product_domain,
            hypotheses=[hypothesis.model_dump() for hypothesis in structured_plan.hypotheses],
            required_data_sources=list(structured_plan.required_data_sources),
            planned_tool_usage=[usage.model_dump() for usage in structured_plan.planned_tool_usage],
            success_criteria=list(structured_plan.success_criteria),
            status="planned",
            version=next_version,
            created_model=trace.model_name if trace else None,
            created_model_version=trace.model_version if trace else None,
        )
        db.add(plan)
        db.flush()

        for step in structured_plan.steps:
            db.add(
                InvestigationPlanStep(
                    plan_id=plan.id,
                    step_order=step.step_order,
                    step_type=step.step_type,
                    intended_tool=step.intended_tool,
                    input_scope=step.input_scope,
                    selection_rationale=step.selection_rationale,
                    status="planned",
                )
            )

        investigation.status = "planned"
        db.commit()
        db.refresh(investigation)
        db.refresh(plan)
        return plan

    def _generate_plan(self, objective: str) -> StructuredInvestigationPlan:
        try:
            raw_plan = self.ai_reasoning.plan(
                objective=objective,
                input_payload={
                    "available_sources": AVAILABLE_SOURCES,
                    "available_tools": AVAILABLE_TOOLS,
                    "planning_boundary": "Plan only. Do not execute tools, collect evidence, create findings, or recommend actions.",
                },
            )
            return StructuredInvestigationPlan.model_validate(raw_plan)
        except (PlannerOutputError, ValidationError, ValueError) as exc:
            raise PlannerOutputError("Unable to produce a valid investigation plan.") from exc

    @staticmethod
    def _next_plan_version(db: Session, investigation_id: int) -> int:
        current_version = db.scalar(
            select(func.max(InvestigationPlan.version)).where(
                InvestigationPlan.investigation_id == investigation_id
            )
        )
        return int(current_version or 0) + 1


AVAILABLE_SOURCES = [
    "gameplay_telemetry",
    "player_reviews",
    "patch_notes",
    "crash_reports",
    "liveops_events",
    "revenue_metrics",
    "store_purchases",
    "session_analytics",
]

AVAILABLE_TOOLS = [
    "getTelemetry",
    "searchReviews",
    "readPatchNotes",
    "getCrashMetrics",
    "getRevenueMetrics",
    "getLiveOpsEvents",
    "getStorePurchases",
    "getSessionAnalytics",
]

PLANNER_INSTRUCTIONS = """
Convert a Product Manager business objective into a structured investigation
plan. The plan must identify the product domain, candidate hypotheses, evidence
requirements, minimum required tools, ordered steps, and success criteria.

Planning boundary:
- never execute tools
- never collect evidence
- never analyze evidence
- never generate findings
- never generate recommendations
- never generate decision artifacts

Return structured data only.
"""
