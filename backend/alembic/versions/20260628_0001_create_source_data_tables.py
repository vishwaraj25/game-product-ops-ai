"""create source data tables

Revision ID: 20260628_0001
Revises: None
Create Date: 2026-06-28 00:01:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260628_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patch_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.String(length=64), nullable=False),
        sa.Column("patch_version", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("release_date", sa.Date(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("systems_changed", sa.JSON(), nullable=False),
        sa.Column("risk_flags", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_patch_notes_game_id"), "patch_notes", ["game_id"])
    op.create_index(op.f("ix_patch_notes_patch_version"), "patch_notes", ["patch_version"], unique=True)
    op.create_index(op.f("ix_patch_notes_release_date"), "patch_notes", ["release_date"])

    op.create_table(
        "liveops_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.String(length=64), nullable=False),
        sa.Column("event_code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("featured_mode", sa.String(length=64), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("reward_currency", sa.String(length=64), nullable=False),
        sa.Column("tuning", sa.JSON(), nullable=False),
        sa.Column("expected_player_impact", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_liveops_events_end_date"), "liveops_events", ["end_date"])
    op.create_index(op.f("ix_liveops_events_event_code"), "liveops_events", ["event_code"], unique=True)
    op.create_index(op.f("ix_liveops_events_event_type"), "liveops_events", ["event_type"])
    op.create_index(op.f("ix_liveops_events_featured_mode"), "liveops_events", ["featured_mode"])
    op.create_index(op.f("ix_liveops_events_game_id"), "liveops_events", ["game_id"])
    op.create_index(op.f("ix_liveops_events_start_date"), "liveops_events", ["start_date"])

    op.create_table(
        "telemetry_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.String(length=64), nullable=False),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("region", sa.String(length=32), nullable=False),
        sa.Column("player_segment", sa.String(length=64), nullable=False),
        sa.Column("game_mode", sa.String(length=64), nullable=False),
        sa.Column("metric_name", sa.String(length=96), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("patch_version", sa.String(length=32), nullable=False),
        sa.Column("liveops_event_code", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_telemetry_metric_lookup", "telemetry_metrics", ["metric_date", "metric_name", "game_mode", "player_segment"])
    op.create_index(op.f("ix_telemetry_metrics_game_id"), "telemetry_metrics", ["game_id"])
    op.create_index(op.f("ix_telemetry_metrics_game_mode"), "telemetry_metrics", ["game_mode"])
    op.create_index(op.f("ix_telemetry_metrics_liveops_event_code"), "telemetry_metrics", ["liveops_event_code"])
    op.create_index(op.f("ix_telemetry_metrics_metric_date"), "telemetry_metrics", ["metric_date"])
    op.create_index(op.f("ix_telemetry_metrics_metric_name"), "telemetry_metrics", ["metric_name"])
    op.create_index(op.f("ix_telemetry_metrics_patch_version"), "telemetry_metrics", ["patch_version"])
    op.create_index(op.f("ix_telemetry_metrics_platform"), "telemetry_metrics", ["platform"])
    op.create_index(op.f("ix_telemetry_metrics_player_segment"), "telemetry_metrics", ["player_segment"])
    op.create_index(op.f("ix_telemetry_metrics_region"), "telemetry_metrics", ["region"])

    op.create_table(
        "player_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.String(length=64), nullable=False),
        sa.Column("review_date", sa.Date(), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("locale", sa.String(length=16), nullable=False),
        sa.Column("player_segment", sa.String(length=64), nullable=False),
        sa.Column("game_mode", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("sentiment", sa.String(length=32), nullable=False),
        sa.Column("topics", sa.JSON(), nullable=False),
        sa.Column("patch_version", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_player_reviews_game_id"), "player_reviews", ["game_id"])
    op.create_index(op.f("ix_player_reviews_game_mode"), "player_reviews", ["game_mode"])
    op.create_index(op.f("ix_player_reviews_locale"), "player_reviews", ["locale"])
    op.create_index(op.f("ix_player_reviews_patch_version"), "player_reviews", ["patch_version"])
    op.create_index(op.f("ix_player_reviews_platform"), "player_reviews", ["platform"])
    op.create_index(op.f("ix_player_reviews_player_segment"), "player_reviews", ["player_segment"])
    op.create_index(op.f("ix_player_reviews_rating"), "player_reviews", ["rating"])
    op.create_index(op.f("ix_player_reviews_review_date"), "player_reviews", ["review_date"])
    op.create_index(op.f("ix_player_reviews_sentiment"), "player_reviews", ["sentiment"])

    op.create_table(
        "crash_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.String(length=64), nullable=False),
        sa.Column("crash_date", sa.Date(), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("game_mode", sa.String(length=64), nullable=False),
        sa.Column("app_version", sa.String(length=32), nullable=False),
        sa.Column("crash_signature", sa.String(length=160), nullable=False),
        sa.Column("affected_sessions", sa.Integer(), nullable=False),
        sa.Column("crash_free_sessions_pct", sa.Float(), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("device_tier", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_crash_reports_app_version"), "crash_reports", ["app_version"])
    op.create_index(op.f("ix_crash_reports_crash_date"), "crash_reports", ["crash_date"])
    op.create_index(op.f("ix_crash_reports_crash_signature"), "crash_reports", ["crash_signature"])
    op.create_index(op.f("ix_crash_reports_device_tier"), "crash_reports", ["device_tier"])
    op.create_index(op.f("ix_crash_reports_game_id"), "crash_reports", ["game_id"])
    op.create_index(op.f("ix_crash_reports_game_mode"), "crash_reports", ["game_mode"])
    op.create_index(op.f("ix_crash_reports_platform"), "crash_reports", ["platform"])
    op.create_index(op.f("ix_crash_reports_severity"), "crash_reports", ["severity"])

    op.create_table(
        "revenue_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.String(length=64), nullable=False),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("region", sa.String(length=32), nullable=False),
        sa.Column("player_segment", sa.String(length=64), nullable=False),
        sa.Column("gross_revenue_usd", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("net_revenue_usd", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("arpdau_usd", sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column("payer_conversion_rate", sa.Float(), nullable=False),
        sa.Column("arppu_usd", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("payer_count", sa.Integer(), nullable=False),
        sa.Column("patch_version", sa.String(length=32), nullable=False),
        sa.Column("liveops_event_code", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_revenue_metrics_game_id"), "revenue_metrics", ["game_id"])
    op.create_index(op.f("ix_revenue_metrics_liveops_event_code"), "revenue_metrics", ["liveops_event_code"])
    op.create_index(op.f("ix_revenue_metrics_metric_date"), "revenue_metrics", ["metric_date"])
    op.create_index(op.f("ix_revenue_metrics_patch_version"), "revenue_metrics", ["patch_version"])
    op.create_index(op.f("ix_revenue_metrics_platform"), "revenue_metrics", ["platform"])
    op.create_index(op.f("ix_revenue_metrics_player_segment"), "revenue_metrics", ["player_segment"])
    op.create_index(op.f("ix_revenue_metrics_region"), "revenue_metrics", ["region"])

    op.create_table(
        "session_analytics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.String(length=64), nullable=False),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("region", sa.String(length=32), nullable=False),
        sa.Column("player_segment", sa.String(length=64), nullable=False),
        sa.Column("game_mode", sa.String(length=64), nullable=False),
        sa.Column("dau", sa.Integer(), nullable=False),
        sa.Column("sessions", sa.Integer(), nullable=False),
        sa.Column("avg_session_minutes", sa.Float(), nullable=False),
        sa.Column("d1_retention", sa.Float(), nullable=False),
        sa.Column("d7_retention", sa.Float(), nullable=False),
        sa.Column("d30_retention", sa.Float(), nullable=False),
        sa.Column("churn_rate", sa.Float(), nullable=False),
        sa.Column("avg_queue_seconds", sa.Float(), nullable=False),
        sa.Column("matchmaking_fail_rate", sa.Float(), nullable=False),
        sa.Column("patch_version", sa.String(length=32), nullable=False),
        sa.Column("liveops_event_code", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_session_health_lookup", "session_analytics", ["session_date", "game_mode", "player_segment", "platform"])
    op.create_index(op.f("ix_session_analytics_game_id"), "session_analytics", ["game_id"])
    op.create_index(op.f("ix_session_analytics_game_mode"), "session_analytics", ["game_mode"])
    op.create_index(op.f("ix_session_analytics_liveops_event_code"), "session_analytics", ["liveops_event_code"])
    op.create_index(op.f("ix_session_analytics_patch_version"), "session_analytics", ["patch_version"])
    op.create_index(op.f("ix_session_analytics_platform"), "session_analytics", ["platform"])
    op.create_index(op.f("ix_session_analytics_player_segment"), "session_analytics", ["player_segment"])
    op.create_index(op.f("ix_session_analytics_region"), "session_analytics", ["region"])
    op.create_index(op.f("ix_session_analytics_session_date"), "session_analytics", ["session_date"])

    op.create_table(
        "store_purchases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.String(length=64), nullable=False),
        sa.Column("purchase_ts", sa.DateTime(), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("region", sa.String(length=32), nullable=False),
        sa.Column("player_segment", sa.String(length=64), nullable=False),
        sa.Column("item_sku", sa.String(length=64), nullable=False),
        sa.Column("item_name", sa.String(length=160), nullable=False),
        sa.Column("item_category", sa.String(length=64), nullable=False),
        sa.Column("price_usd", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("premium_currency_amount", sa.Integer(), nullable=False),
        sa.Column("premium_currency_name", sa.String(length=64), nullable=False),
        sa.Column("patch_version", sa.String(length=32), nullable=False),
        sa.Column("liveops_event_code", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_store_purchases_game_id"), "store_purchases", ["game_id"])
    op.create_index(op.f("ix_store_purchases_item_category"), "store_purchases", ["item_category"])
    op.create_index(op.f("ix_store_purchases_item_sku"), "store_purchases", ["item_sku"])
    op.create_index(op.f("ix_store_purchases_liveops_event_code"), "store_purchases", ["liveops_event_code"])
    op.create_index(op.f("ix_store_purchases_patch_version"), "store_purchases", ["patch_version"])
    op.create_index(op.f("ix_store_purchases_platform"), "store_purchases", ["platform"])
    op.create_index(op.f("ix_store_purchases_player_segment"), "store_purchases", ["player_segment"])
    op.create_index(op.f("ix_store_purchases_purchase_ts"), "store_purchases", ["purchase_ts"])
    op.create_index(op.f("ix_store_purchases_region"), "store_purchases", ["region"])


def downgrade() -> None:
    op.drop_table("store_purchases")
    op.drop_table("session_analytics")
    op.drop_table("revenue_metrics")
    op.drop_table("crash_reports")
    op.drop_table("player_reviews")
    op.drop_table("telemetry_metrics")
    op.drop_table("liveops_events")
    op.drop_table("patch_notes")
