from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.source_data.models import (
    CrashReport,
    LiveOpsEvent,
    PatchNote,
    PlayerReview,
    RevenueMetric,
    SessionAnalytic,
    StorePurchase,
    TelemetryMetric,
)
from app.tools.base import EvidenceCandidate, ToolResult


def scope_entities(input_scope: dict) -> dict:
    return input_scope.get("entities", {}) if isinstance(input_scope.get("entities"), dict) else {}


def preferred_modes(input_scope: dict) -> list[str]:
    modes = scope_entities(input_scope).get("modes", [])
    return [mode for mode in modes if mode != "battle_pass"]


def preferred_platforms(input_scope: dict) -> list[str]:
    return scope_entities(input_scope).get("platforms", [])


def time_window_for_output(input_scope: dict) -> dict:
    return input_scope.get("timeframe", {})


class ReadPatchNotesTool:
    name = "readPatchNotes"
    source_type = "patch_notes"

    def execute(self, db: Session, input_scope: dict) -> ToolResult:
        patches = db.scalars(select(PatchNote).order_by(PatchNote.release_date)).all()
        evidence = [
            EvidenceCandidate(
                source_type=self.source_type,
                source_id=patch.patch_version,
                title=f"Patch {patch.patch_version}: {patch.title}",
                summary=patch.summary,
                observed_value={
                    "systems_changed": patch.systems_changed,
                    "risk_flags": patch.risk_flags,
                },
                time_window={"release_date": patch.release_date.isoformat()},
                strength="high",
                confidence=0.95,
                metadata={"patch_version": patch.patch_version},
            )
            for patch in patches
        ]
        return ToolResult(summary={"patches_reviewed": len(patches)}, evidence=evidence)


class GetLiveOpsEventsTool:
    name = "getLiveOpsEvents"
    source_type = "liveops_events"

    def execute(self, db: Session, input_scope: dict) -> ToolResult:
        events = db.scalars(select(LiveOpsEvent).order_by(LiveOpsEvent.start_date)).all()
        evidence = [
            EvidenceCandidate(
                source_type=self.source_type,
                source_id=event.event_code,
                title=f"LiveOps event: {event.name}",
                summary=f"{event.name} ran from {event.start_date} to {event.end_date} in {event.featured_mode}.",
                observed_value={
                    "event_type": event.event_type,
                    "featured_mode": event.featured_mode,
                    "tuning": event.tuning,
                    "expected_player_impact": event.expected_player_impact,
                },
                time_window={"start_date": event.start_date.isoformat(), "end_date": event.end_date.isoformat()},
                strength="high",
                confidence=0.95,
                metadata={"event_code": event.event_code},
            )
            for event in events
        ]
        return ToolResult(summary={"events_reviewed": len(events)}, evidence=evidence)


class GetSessionAnalyticsTool:
    name = "getSessionAnalytics"
    source_type = "session_analytics"

    def execute(self, db: Session, input_scope: dict) -> ToolResult:
        mode_filter = preferred_modes(input_scope)
        platform_filter = preferred_platforms(input_scope)
        stmt = select(
            SessionAnalytic.game_mode,
            SessionAnalytic.platform,
            func.avg(SessionAnalytic.d1_retention),
            func.avg(SessionAnalytic.d7_retention),
            func.avg(SessionAnalytic.avg_queue_seconds),
            func.avg(SessionAnalytic.matchmaking_fail_rate),
            func.sum(SessionAnalytic.dau),
        ).group_by(SessionAnalytic.game_mode, SessionAnalytic.platform)
        if mode_filter:
            stmt = stmt.where(SessionAnalytic.game_mode.in_(mode_filter))
        if platform_filter:
            stmt = stmt.where(SessionAnalytic.platform.in_(platform_filter))
        rows = db.execute(stmt).all()
        evidence = [
            EvidenceCandidate(
                source_type=self.source_type,
                source_id=f"{row[0]}:{row[1]}",
                title=f"Session health for {row[0]} on {row[1]}",
                summary=(
                    f"Average D1 retention {row[2]:.2%}, D7 retention {row[3]:.2%}, "
                    f"queue {row[4]:.1f}s, matchmaking fail rate {row[5]:.2%}."
                ),
                observed_value={
                    "game_mode": row[0],
                    "platform": row[1],
                    "avg_d1_retention": round(float(row[2] or 0), 4),
                    "avg_d7_retention": round(float(row[3] or 0), 4),
                    "avg_queue_seconds": round(float(row[4] or 0), 2),
                    "avg_matchmaking_fail_rate": round(float(row[5] or 0), 4),
                    "total_dau": int(row[6] or 0),
                },
                time_window=time_window_for_output(input_scope),
                strength="high",
                confidence=0.9,
                metadata={"group_by": ["game_mode", "platform"]},
            )
            for row in rows
        ]
        return ToolResult(summary={"groups_returned": len(rows)}, evidence=evidence)


class GetTelemetryTool:
    name = "getTelemetry"
    source_type = "gameplay_telemetry"

    def execute(self, db: Session, input_scope: dict) -> ToolResult:
        mode_filter = preferred_modes(input_scope)
        stmt = select(
            TelemetryMetric.metric_name,
            TelemetryMetric.game_mode,
            func.avg(TelemetryMetric.metric_value),
        ).group_by(TelemetryMetric.metric_name, TelemetryMetric.game_mode)
        if mode_filter:
            stmt = stmt.where(TelemetryMetric.game_mode.in_(mode_filter))
        rows = db.execute(stmt).all()
        evidence = [
            EvidenceCandidate(
                source_type=self.source_type,
                source_id=f"{row[1]}:{row[0]}",
                title=f"Telemetry metric {row[0]} for {row[1]}",
                summary=f"Average {row[0]} for {row[1]} is {float(row[2] or 0):.4f}.",
                observed_value={
                    "metric_name": row[0],
                    "game_mode": row[1],
                    "average_value": round(float(row[2] or 0), 4),
                },
                time_window=time_window_for_output(input_scope),
                strength="medium",
                confidence=0.84,
                metadata={"aggregation": "average"},
            )
            for row in rows[:24]
        ]
        return ToolResult(summary={"metrics_returned": len(evidence)}, evidence=evidence)


class SearchReviewsTool:
    name = "searchReviews"
    source_type = "player_reviews"

    def execute(self, db: Session, input_scope: dict) -> ToolResult:
        mode_filter = preferred_modes(input_scope)
        stmt = select(
            PlayerReview.sentiment,
            PlayerReview.game_mode,
            func.count(PlayerReview.id),
            func.avg(PlayerReview.rating),
        ).group_by(PlayerReview.sentiment, PlayerReview.game_mode)
        if mode_filter:
            stmt = stmt.where(PlayerReview.game_mode.in_(mode_filter))
        rows = db.execute(stmt).all()
        evidence = [
            EvidenceCandidate(
                source_type=self.source_type,
                source_id=f"{row[1]}:{row[0]}",
                title=f"Review sentiment for {row[1]}",
                summary=f"{row[2]} {row[0]} reviews for {row[1]} with average rating {float(row[3] or 0):.2f}.",
                observed_value={
                    "sentiment": row[0],
                    "game_mode": row[1],
                    "review_count": int(row[2] or 0),
                    "avg_rating": round(float(row[3] or 0), 2),
                },
                time_window=time_window_for_output(input_scope),
                strength="medium",
                confidence=0.82,
                metadata={"aggregation": "sentiment_by_mode"},
            )
            for row in rows
        ]
        return ToolResult(summary={"sentiment_groups": len(rows)}, evidence=evidence)


class GetCrashMetricsTool:
    name = "getCrashMetrics"
    source_type = "crash_reports"

    def execute(self, db: Session, input_scope: dict) -> ToolResult:
        platform_filter = preferred_platforms(input_scope)
        stmt = select(
            CrashReport.platform,
            CrashReport.game_mode,
            CrashReport.crash_signature,
            func.sum(CrashReport.affected_sessions),
            func.min(CrashReport.crash_free_sessions_pct),
        ).group_by(CrashReport.platform, CrashReport.game_mode, CrashReport.crash_signature)
        if platform_filter:
            stmt = stmt.where(CrashReport.platform.in_(platform_filter))
        rows = db.execute(stmt).all()
        evidence = [
            EvidenceCandidate(
                source_type=self.source_type,
                source_id=f"{row[0]}:{row[1]}:{row[2]}",
                title=f"Crash signature {row[2]} on {row[0]}",
                summary=f"{row[3]} affected sessions in {row[1]}, minimum crash-free sessions {row[4]:.3f}%.",
                observed_value={
                    "platform": row[0],
                    "game_mode": row[1],
                    "crash_signature": row[2],
                    "affected_sessions": int(row[3] or 0),
                    "min_crash_free_sessions_pct": round(float(row[4] or 0), 3),
                },
                time_window=time_window_for_output(input_scope),
                strength="high",
                confidence=0.92,
                metadata={"aggregation": "signature_by_platform_mode"},
            )
            for row in rows
        ]
        return ToolResult(summary={"crash_groups": len(rows)}, evidence=evidence)


class GetRevenueMetricsTool:
    name = "getRevenueMetrics"
    source_type = "revenue_metrics"

    def execute(self, db: Session, input_scope: dict) -> ToolResult:
        stmt = select(
            RevenueMetric.player_segment,
            func.sum(RevenueMetric.gross_revenue_usd),
            func.avg(RevenueMetric.payer_conversion_rate),
            func.avg(RevenueMetric.arpdau_usd),
            func.sum(RevenueMetric.payer_count),
        ).group_by(RevenueMetric.player_segment)
        rows = db.execute(stmt).all()
        evidence = [
            EvidenceCandidate(
                source_type=self.source_type,
                source_id=row[0],
                title=f"Revenue health for {row[0]} players",
                summary=f"Gross revenue ${float(row[1] or 0):.2f}, conversion {float(row[2] or 0):.2%}, ARPDAU ${float(row[3] or 0):.4f}.",
                observed_value={
                    "player_segment": row[0],
                    "gross_revenue_usd": round(float(row[1] or 0), 2),
                    "payer_conversion_rate": round(float(row[2] or 0), 4),
                    "arpdau_usd": round(float(row[3] or 0), 4),
                    "payer_count": int(row[4] or 0),
                },
                time_window=time_window_for_output(input_scope),
                strength="high",
                confidence=0.9,
                metadata={"aggregation": "revenue_by_segment"},
            )
            for row in rows
        ]
        return ToolResult(summary={"segments_returned": len(rows)}, evidence=evidence)


class GetStorePurchasesTool:
    name = "getStorePurchases"
    source_type = "store_purchases"

    def execute(self, db: Session, input_scope: dict) -> ToolResult:
        stmt = select(
            StorePurchase.item_category,
            StorePurchase.item_name,
            func.count(StorePurchase.id),
            func.sum(StorePurchase.price_usd),
        ).group_by(StorePurchase.item_category, StorePurchase.item_name)
        rows = db.execute(stmt).all()
        evidence = [
            EvidenceCandidate(
                source_type=self.source_type,
                source_id=f"{row[0]}:{row[1]}",
                title=f"Store purchases: {row[1]}",
                summary=f"{row[2]} purchases in {row[0]} totaling ${float(row[3] or 0):.2f}.",
                observed_value={
                    "item_category": row[0],
                    "item_name": row[1],
                    "purchase_count": int(row[2] or 0),
                    "gross_sales_usd": round(float(row[3] or 0), 2),
                },
                time_window=time_window_for_output(input_scope),
                strength="medium",
                confidence=0.86,
                metadata={"aggregation": "purchase_count_by_item"},
            )
            for row in rows
        ]
        return ToolResult(summary={"items_returned": len(rows)}, evidence=evidence)


def build_default_tool_registry():
    from app.tools.registry import ToolRegistry

    return ToolRegistry(
        [
            ReadPatchNotesTool(),
            GetLiveOpsEventsTool(),
            GetSessionAnalyticsTool(),
            GetTelemetryTool(),
            SearchReviewsTool(),
            GetCrashMetricsTool(),
            GetRevenueMetricsTool(),
            GetStorePurchasesTool(),
        ]
    )
