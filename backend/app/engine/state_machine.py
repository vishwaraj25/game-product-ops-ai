from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engine.exceptions import InvestigationPlanNotExecutable
from app.investigations.models import Evidence, Investigation, InvestigationPlan, InvestigationPlanStep, ToolRun
from app.tools.base import EvidenceCandidate
from app.tools.registry import ToolRegistry, UnknownToolError


@dataclass(frozen=True)
class ExecutionResult:
    investigation_id: int
    plan_id: int
    tool_runs_created: int
    evidence_created: int
    status: str


class InvestigationExecutionStateMachine:
    def __init__(self, tool_registry: ToolRegistry) -> None:
        self.tool_registry = tool_registry

    def execute_plan(self, db: Session, plan_id: int) -> ExecutionResult:
        plan = db.get(InvestigationPlan, plan_id)
        if not plan:
            raise InvestigationPlanNotExecutable(f"InvestigationPlan not found: {plan_id}")

        investigation = db.get(Investigation, plan.investigation_id)
        if not investigation:
            raise InvestigationPlanNotExecutable(f"Investigation not found for plan: {plan_id}")

        steps = db.scalars(
            select(InvestigationPlanStep)
            .where(InvestigationPlanStep.plan_id == plan.id)
            .order_by(InvestigationPlanStep.step_order)
        ).all()
        executable_steps = [step for step in steps if step.intended_tool]
        if not executable_steps:
            raise InvestigationPlanNotExecutable(f"Plan has no executable tool steps: {plan_id}")

        plan.status = "executing"
        investigation.status = "collecting_evidence"
        db.flush()

        tool_runs_created = 0
        evidence_created = 0
        failed = False

        for step in executable_steps:
            tool_run = self._create_tool_run(investigation.id, step)
            db.add(tool_run)
            db.flush()
            tool_runs_created += 1

            try:
                tool = self.tool_registry.get(step.intended_tool or "")
                result = tool.execute(db, step.input_scope)
                tool_run.status = "completed"
                tool_run.output_summary = result.summary
                tool_run.completed_at = datetime.utcnow()
                step.status = "completed"

                for candidate in result.evidence:
                    db.add(self._create_evidence(investigation.id, tool_run.id, candidate))
                    evidence_created += 1
            except UnknownToolError as exc:
                failed = True
                tool_run.status = "failed"
                tool_run.error_message = str(exc)
                tool_run.completed_at = datetime.utcnow()
                step.status = "failed"
                break
            except Exception as exc:
                failed = True
                tool_run.status = "failed"
                tool_run.error_message = f"{type(exc).__name__}: {exc}"
                tool_run.completed_at = datetime.utcnow()
                step.status = "failed"
                break

        if failed:
            plan.status = "execution_failed"
            investigation.status = "execution_failed"
        else:
            plan.status = "evidence_collected"
            investigation.status = "evidence_collected"

        db.commit()
        return ExecutionResult(
            investigation_id=investigation.id,
            plan_id=plan.id,
            tool_runs_created=tool_runs_created,
            evidence_created=evidence_created,
            status=investigation.status,
        )

    @staticmethod
    def _create_tool_run(investigation_id: int, step: InvestigationPlanStep) -> ToolRun:
        return ToolRun(
            investigation_id=investigation_id,
            plan_step_id=step.id,
            tool_name=step.intended_tool or "",
            status="running",
            input_payload=step.input_scope,
            started_at=datetime.utcnow(),
        )

    @staticmethod
    def _create_evidence(
        investigation_id: int,
        tool_run_id: int,
        candidate: EvidenceCandidate,
    ) -> Evidence:
        return Evidence(
            investigation_id=investigation_id,
            tool_run_id=tool_run_id,
            source_type=candidate.source_type,
            source_id=candidate.source_id,
            title=candidate.title,
            summary=candidate.summary,
            observed_value=candidate.observed_value,
            time_window=candidate.time_window,
            strength=candidate.strength,
            confidence=candidate.confidence,
            evidence_metadata=candidate.metadata,
        )
