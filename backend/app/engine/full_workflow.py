from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.artifacts.executive_brief import ExecutiveBriefGenerator
from app.engine.state_machine import InvestigationExecutionStateMachine
from app.evidence.correlation import EvidenceCorrelator
from app.evidence.finding_service import FindingService
from app.investigations.models import DecisionArtifact, Finding, Investigation, InvestigationPlan, Recommendation
from app.planning.factory import build_planner
from app.planning.service import PlannerRequest
from app.recommendations.engine import RecommendationEngine
from app.tools.source_data_tools import build_default_tool_registry


@dataclass(frozen=True)
class FullInvestigationResult:
    investigation: Investigation
    plan: InvestigationPlan
    findings: list[Finding]
    recommendations: list[Recommendation]
    executive_brief: DecisionArtifact


class FullInvestigationWorkflow:
    def run(
        self,
        db: Session,
        objective: str,
        game_id: str = "project-eclipse",
        requested_by: str | None = None,
    ) -> FullInvestigationResult:
        planner_result = build_planner().plan_new_investigation(
            db,
            PlannerRequest(objective=objective, game_id=game_id, requested_by=requested_by),
        )

        executor = InvestigationExecutionStateMachine(build_default_tool_registry())
        executor.execute_plan(db, planner_result.plan.id)

        plan = db.get(InvestigationPlan, planner_result.plan.id)
        if plan is None:
            raise RuntimeError("Investigation plan disappeared during execution.")

        clusters = EvidenceCorrelator().correlate(db, plan)
        findings = FindingService().create_findings(db, plan, clusters)
        recommendations = RecommendationEngine().create_recommendations(db, plan.investigation_id, findings)
        executive_brief = ExecutiveBriefGenerator().create_executive_brief(db, plan, findings, recommendations)

        investigation = db.get(Investigation, plan.investigation_id)
        if investigation is None:
            raise RuntimeError("Investigation disappeared during artifact generation.")
        investigation.status = "awaiting_approval"
        db.commit()

        db.refresh(investigation)
        db.refresh(plan)
        db.refresh(executive_brief)
        for finding in findings:
            db.refresh(finding)
        for recommendation in recommendations:
            db.refresh(recommendation)

        return FullInvestigationResult(
            investigation=investigation,
            plan=plan,
            findings=findings,
            recommendations=recommendations,
            executive_brief=executive_brief,
        )
