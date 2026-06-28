"""create investigation domain tables

Revision ID: 20260628_0002
Revises: 20260628_0001
Create Date: 2026-06-28 00:02:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260628_0002"
down_revision: Union[str, None] = "20260628_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "investigations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.String(length=64), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False),
        sa.Column("requested_by", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_investigations_created_at"), "investigations", ["created_at"])
    op.create_index(op.f("ix_investigations_game_id"), "investigations", ["game_id"])
    op.create_index(op.f("ix_investigations_priority"), "investigations", ["priority"])
    op.create_index(op.f("ix_investigations_status"), "investigations", ["status"])

    op.create_table(
        "investigation_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("investigation_id", sa.Integer(), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("objective_interpretation", sa.Text(), nullable=True),
        sa.Column("hypotheses", sa.JSON(), nullable=False),
        sa.Column("required_data_sources", sa.JSON(), nullable=False),
        sa.Column("planned_tool_usage", sa.JSON(), nullable=False),
        sa.Column("success_criteria", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_model", sa.String(length=120), nullable=True),
        sa.Column("created_model_version", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["investigation_id"], ["investigations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_investigation_plan_version", "investigation_plans", ["investigation_id", "version"], unique=True)
    op.create_index(op.f("ix_investigation_plans_created_at"), "investigation_plans", ["created_at"])
    op.create_index(op.f("ix_investigation_plans_investigation_id"), "investigation_plans", ["investigation_id"])
    op.create_index(op.f("ix_investigation_plans_status"), "investigation_plans", ["status"])

    op.create_table(
        "investigation_plan_steps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("step_type", sa.String(length=64), nullable=False),
        sa.Column("intended_tool", sa.String(length=120), nullable=True),
        sa.Column("input_scope", sa.JSON(), nullable=False),
        sa.Column("selection_rationale", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["investigation_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_plan_step_order", "investigation_plan_steps", ["plan_id", "step_order"], unique=True)
    op.create_index(op.f("ix_investigation_plan_steps_intended_tool"), "investigation_plan_steps", ["intended_tool"])
    op.create_index(op.f("ix_investigation_plan_steps_plan_id"), "investigation_plan_steps", ["plan_id"])
    op.create_index(op.f("ix_investigation_plan_steps_status"), "investigation_plan_steps", ["status"])
    op.create_index(op.f("ix_investigation_plan_steps_step_type"), "investigation_plan_steps", ["step_type"])

    op.create_table(
        "findings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("investigation_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("finding_type", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("supporting_evidence_ids", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["investigation_id"], ["investigations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_findings_created_at"), "findings", ["created_at"])
    op.create_index(op.f("ix_findings_finding_type"), "findings", ["finding_type"])
    op.create_index(op.f("ix_findings_investigation_id"), "findings", ["investigation_id"])
    op.create_index(op.f("ix_findings_severity"), "findings", ["severity"])
    op.create_index(op.f("ix_findings_status"), "findings", ["status"])

    op.create_table(
        "decision_artifacts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("investigation_id", sa.Integer(), nullable=False),
        sa.Column("artifact_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["investigation_id"], ["investigations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_decision_artifacts_artifact_type"), "decision_artifacts", ["artifact_type"])
    op.create_index(op.f("ix_decision_artifacts_created_at"), "decision_artifacts", ["created_at"])
    op.create_index(op.f("ix_decision_artifacts_investigation_id"), "decision_artifacts", ["investigation_id"])
    op.create_index(op.f("ix_decision_artifacts_status"), "decision_artifacts", ["status"])

    op.create_table(
        "approvals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("investigation_id", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(length=64), nullable=False),
        sa.Column("approver", sa.String(length=120), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("approved_recommendation_ids", sa.JSON(), nullable=False),
        sa.Column("rejected_recommendation_ids", sa.JSON(), nullable=False),
        sa.Column("requested_follow_up", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["investigation_id"], ["investigations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_approvals_created_at"), "approvals", ["created_at"])
    op.create_index(op.f("ix_approvals_decision"), "approvals", ["decision"])
    op.create_index(op.f("ix_approvals_investigation_id"), "approvals", ["investigation_id"])

    op.create_table(
        "tool_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("investigation_id", sa.Integer(), nullable=False),
        sa.Column("plan_step_id", sa.Integer(), nullable=True),
        sa.Column("tool_name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("input_payload", sa.JSON(), nullable=False),
        sa.Column("output_summary", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["investigation_id"], ["investigations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_step_id"], ["investigation_plan_steps.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tool_runs_created_at"), "tool_runs", ["created_at"])
    op.create_index(op.f("ix_tool_runs_investigation_id"), "tool_runs", ["investigation_id"])
    op.create_index(op.f("ix_tool_runs_plan_step_id"), "tool_runs", ["plan_step_id"])
    op.create_index(op.f("ix_tool_runs_status"), "tool_runs", ["status"])
    op.create_index(op.f("ix_tool_runs_tool_name"), "tool_runs", ["tool_name"])

    op.create_table(
        "evidence",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("investigation_id", sa.Integer(), nullable=False),
        sa.Column("tool_run_id", sa.Integer(), nullable=True),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=120), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("observed_value", sa.JSON(), nullable=True),
        sa.Column("time_window", sa.JSON(), nullable=True),
        sa.Column("strength", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["investigation_id"], ["investigations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tool_run_id"], ["tool_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evidence_created_at"), "evidence", ["created_at"])
    op.create_index(op.f("ix_evidence_confidence"), "evidence", ["confidence"])
    op.create_index(op.f("ix_evidence_investigation_id"), "evidence", ["investigation_id"])
    op.create_index(op.f("ix_evidence_source_id"), "evidence", ["source_id"])
    op.create_index(op.f("ix_evidence_source_type"), "evidence", ["source_type"])
    op.create_index(op.f("ix_evidence_strength"), "evidence", ["strength"])
    op.create_index(op.f("ix_evidence_tool_run_id"), "evidence", ["tool_run_id"])

    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("investigation_id", sa.Integer(), nullable=False),
        sa.Column("finding_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("recommendation_type", sa.String(length=64), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=32), nullable=False),
        sa.Column("supporting_evidence_ids", sa.JSON(), nullable=False),
        sa.Column("expected_impact", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("requires_approval", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["finding_id"], ["findings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["investigation_id"], ["investigations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recommendations_created_at"), "recommendations", ["created_at"])
    op.create_index(op.f("ix_recommendations_finding_id"), "recommendations", ["finding_id"])
    op.create_index(op.f("ix_recommendations_investigation_id"), "recommendations", ["investigation_id"])
    op.create_index(op.f("ix_recommendations_priority"), "recommendations", ["priority"])
    op.create_index(op.f("ix_recommendations_recommendation_type"), "recommendations", ["recommendation_type"])
    op.create_index(op.f("ix_recommendations_risk_level"), "recommendations", ["risk_level"])
    op.create_index(op.f("ix_recommendations_status"), "recommendations", ["status"])


def downgrade() -> None:
    op.drop_table("recommendations")
    op.drop_table("evidence")
    op.drop_table("tool_runs")
    op.drop_table("approvals")
    op.drop_table("decision_artifacts")
    op.drop_table("findings")
    op.drop_table("investigation_plan_steps")
    op.drop_table("investigation_plans")
    op.drop_table("investigations")
