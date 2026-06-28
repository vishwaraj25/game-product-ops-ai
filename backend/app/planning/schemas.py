from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


SourceType = Literal[
    "gameplay_telemetry",
    "player_reviews",
    "patch_notes",
    "crash_reports",
    "liveops_events",
    "revenue_metrics",
    "store_purchases",
    "session_analytics",
]

ToolName = Literal[
    "getTelemetry",
    "searchReviews",
    "readPatchNotes",
    "getCrashMetrics",
    "getRevenueMetrics",
    "getLiveOpsEvents",
    "getStorePurchases",
    "getSessionAnalytics",
]

StepType = Literal[
    "interpret_objective",
    "inspect_change_history",
    "collect_metric_context",
    "collect_sentiment_context",
    "collect_stability_context",
    "collect_monetization_context",
    "collect_liveops_context",
    "cross_source_validation",
]


class PlannerHypothesis(BaseModel):
    title: str = Field(min_length=8, max_length=180)
    rationale: str = Field(min_length=12)
    evidence_required: list[SourceType] = Field(min_length=1)


class PlannedToolUsage(BaseModel):
    tool_name: ToolName
    purpose: str = Field(min_length=12)
    input_scope: dict


class PlannerStep(BaseModel):
    step_order: int = Field(ge=1)
    step_type: StepType
    intended_tool: ToolName | None
    input_scope: dict
    selection_rationale: str = Field(min_length=20)


class StructuredInvestigationPlan(BaseModel):
    objective: str = Field(min_length=8)
    objective_interpretation: str = Field(min_length=20)
    product_domain: str = Field(min_length=3, max_length=64)
    hypotheses: list[PlannerHypothesis] = Field(min_length=2)
    required_data_sources: list[SourceType] = Field(min_length=2)
    planned_tool_usage: list[PlannedToolUsage] = Field(min_length=1)
    steps: list[PlannerStep] = Field(min_length=3)
    success_criteria: list[str] = Field(min_length=2)

    @field_validator("product_domain")
    @classmethod
    def normalize_product_domain(cls, value: str) -> str:
        return value.strip().lower().replace(" ", "_")

    @model_validator(mode="after")
    def validate_step_order_and_tools(self) -> "StructuredInvestigationPlan":
        orders = [step.step_order for step in self.steps]
        expected = list(range(1, len(orders) + 1))
        if orders != expected:
            raise ValueError("Planner steps must be ordered contiguously from 1.")

        planned_tools = {usage.tool_name for usage in self.planned_tool_usage}
        step_tools = {step.intended_tool for step in self.steps if step.intended_tool}
        missing = step_tools - planned_tools
        if missing:
            raise ValueError(f"Step tools missing from planned_tool_usage: {sorted(missing)}")

        required_sources = set(self.required_data_sources)
        hypothesis_sources = {
            source for hypothesis in self.hypotheses for source in hypothesis.evidence_required
        }
        if not hypothesis_sources.issubset(required_sources):
            missing_sources = hypothesis_sources - required_sources
            raise ValueError(f"Hypothesis evidence missing from required_data_sources: {sorted(missing_sources)}")

        return self
