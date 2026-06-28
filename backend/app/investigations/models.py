from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[str] = mapped_column(String(64), index=True)
    objective: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(64), index=True, default="created")
    priority: Mapped[str] = mapped_column(String(32), index=True, default="normal")
    requested_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    plans: Mapped[list["InvestigationPlan"]] = relationship(
        back_populates="investigation",
        cascade="all, delete-orphan",
    )
    tool_runs: Mapped[list["ToolRun"]] = relationship(
        back_populates="investigation",
        cascade="all, delete-orphan",
    )
    evidence_items: Mapped[list["Evidence"]] = relationship(
        back_populates="investigation",
        cascade="all, delete-orphan",
    )
    findings: Mapped[list["Finding"]] = relationship(
        back_populates="investigation",
        cascade="all, delete-orphan",
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="investigation",
        cascade="all, delete-orphan",
    )
    decision_artifacts: Mapped[list["DecisionArtifact"]] = relationship(
        back_populates="investigation",
        cascade="all, delete-orphan",
    )
    approvals: Mapped[list["Approval"]] = relationship(
        back_populates="investigation",
        cascade="all, delete-orphan",
    )


class InvestigationPlan(Base):
    __tablename__ = "investigation_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"), index=True)
    objective: Mapped[str] = mapped_column(Text)
    objective_interpretation: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_domain: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    hypotheses: Mapped[list] = mapped_column(JSON)
    required_data_sources: Mapped[list] = mapped_column(JSON)
    planned_tool_usage: Mapped[list] = mapped_column(JSON)
    success_criteria: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(64), index=True, default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_model_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    investigation: Mapped[Investigation] = relationship(back_populates="plans")
    steps: Mapped[list["InvestigationPlanStep"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="InvestigationPlanStep.step_order",
    )

    __table_args__ = (
        Index("ix_investigation_plan_version", "investigation_id", "version", unique=True),
    )


class InvestigationPlanStep(Base):
    __tablename__ = "investigation_plan_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("investigation_plans.id", ondelete="CASCADE"), index=True)
    step_order: Mapped[int] = mapped_column(Integer)
    step_type: Mapped[str] = mapped_column(String(64), index=True)
    intended_tool: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    input_scope: Mapped[dict] = mapped_column(JSON)
    selection_rationale: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(64), index=True, default="planned")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    plan: Mapped[InvestigationPlan] = relationship(back_populates="steps")
    tool_runs: Mapped[list["ToolRun"]] = relationship(back_populates="plan_step")

    __table_args__ = (
        Index("ix_plan_step_order", "plan_id", "step_order", unique=True),
    )


class ToolRun(Base):
    __tablename__ = "tool_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"), index=True)
    plan_step_id: Mapped[int | None] = mapped_column(ForeignKey("investigation_plan_steps.id", ondelete="SET NULL"), nullable=True, index=True)
    tool_name: Mapped[str] = mapped_column(String(120), index=True)
    status: Mapped[str] = mapped_column(String(64), index=True, default="pending")
    input_payload: Mapped[dict] = mapped_column(JSON)
    output_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    investigation: Mapped[Investigation] = relationship(back_populates="tool_runs")
    plan_step: Mapped[InvestigationPlanStep | None] = relationship(back_populates="tool_runs")
    evidence_items: Mapped[list["Evidence"]] = relationship(back_populates="tool_run")


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"), index=True)
    tool_run_id: Mapped[int | None] = mapped_column(ForeignKey("tool_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    source_type: Mapped[str] = mapped_column(String(64), index=True)
    source_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text)
    observed_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    time_window: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    strength: Mapped[str] = mapped_column(String(32), index=True, default="medium")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence_metadata: Mapped[dict] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    investigation: Mapped[Investigation] = relationship(back_populates="evidence_items")
    tool_run: Mapped[ToolRun | None] = relationship(back_populates="evidence_items")


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text)
    finding_type: Mapped[str] = mapped_column(String(64), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    supporting_evidence_ids: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(64), index=True, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    investigation: Mapped[Investigation] = relationship(back_populates="findings")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="finding")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"), index=True)
    finding_id: Mapped[int | None] = mapped_column(ForeignKey("findings.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text)
    recommendation_type: Mapped[str] = mapped_column(String(64), index=True)
    priority: Mapped[str] = mapped_column(String(32), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String(32), index=True)
    supporting_evidence_ids: Mapped[list] = mapped_column(JSON)
    expected_impact: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(64), index=True, default="proposed")
    requires_approval: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    investigation: Mapped[Investigation] = relationship(back_populates="recommendations")
    finding: Mapped[Finding | None] = relationship(back_populates="recommendations")


class DecisionArtifact(Base):
    __tablename__ = "decision_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"), index=True)
    artifact_type: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(64), index=True, default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    investigation: Mapped[Investigation] = relationship(back_populates="decision_artifacts")


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"), index=True)
    decision: Mapped[str] = mapped_column(String(64), index=True)
    approver: Mapped[str] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_recommendation_ids: Mapped[list] = mapped_column(JSON)
    rejected_recommendation_ids: Mapped[list] = mapped_column(JSON)
    requested_follow_up: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    investigation: Mapped[Investigation] = relationship(back_populates="approvals")
