from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Float, Index, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PatchNote(Base):
    __tablename__ = "patch_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[str] = mapped_column(String(64), index=True)
    patch_version: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(160))
    release_date: Mapped[date] = mapped_column(Date, index=True)
    summary: Mapped[str] = mapped_column(Text)
    systems_changed: Mapped[dict] = mapped_column(JSON)
    risk_flags: Mapped[dict] = mapped_column(JSON)


class LiveOpsEvent(Base):
    __tablename__ = "liveops_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[str] = mapped_column(String(64), index=True)
    event_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    featured_mode: Mapped[str] = mapped_column(String(64), index=True)
    start_date: Mapped[date] = mapped_column(Date, index=True)
    end_date: Mapped[date] = mapped_column(Date, index=True)
    reward_currency: Mapped[str] = mapped_column(String(64))
    tuning: Mapped[dict] = mapped_column(JSON)
    expected_player_impact: Mapped[dict] = mapped_column(JSON)


class TelemetryMetric(Base):
    __tablename__ = "telemetry_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[str] = mapped_column(String(64), index=True)
    metric_date: Mapped[date] = mapped_column(Date, index=True)
    platform: Mapped[str] = mapped_column(String(32), index=True)
    region: Mapped[str] = mapped_column(String(32), index=True)
    player_segment: Mapped[str] = mapped_column(String(64), index=True)
    game_mode: Mapped[str] = mapped_column(String(64), index=True)
    metric_name: Mapped[str] = mapped_column(String(96), index=True)
    metric_value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(32))
    patch_version: Mapped[str] = mapped_column(String(32), index=True)
    liveops_event_code: Mapped[str | None] = mapped_column(String(64), index=True)

    __table_args__ = (
        Index(
            "ix_telemetry_metric_lookup",
            "metric_date",
            "metric_name",
            "game_mode",
            "player_segment",
        ),
    )


class PlayerReview(Base):
    __tablename__ = "player_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[str] = mapped_column(String(64), index=True)
    review_date: Mapped[date] = mapped_column(Date, index=True)
    platform: Mapped[str] = mapped_column(String(32), index=True)
    rating: Mapped[int] = mapped_column(Integer, index=True)
    locale: Mapped[str] = mapped_column(String(16), index=True)
    player_segment: Mapped[str] = mapped_column(String(64), index=True)
    game_mode: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text)
    sentiment: Mapped[str] = mapped_column(String(32), index=True)
    topics: Mapped[list[str]] = mapped_column(JSON)
    patch_version: Mapped[str] = mapped_column(String(32), index=True)


class CrashReport(Base):
    __tablename__ = "crash_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[str] = mapped_column(String(64), index=True)
    crash_date: Mapped[date] = mapped_column(Date, index=True)
    platform: Mapped[str] = mapped_column(String(32), index=True)
    game_mode: Mapped[str] = mapped_column(String(64), index=True)
    app_version: Mapped[str] = mapped_column(String(32), index=True)
    crash_signature: Mapped[str] = mapped_column(String(160), index=True)
    affected_sessions: Mapped[int] = mapped_column(Integer)
    crash_free_sessions_pct: Mapped[float] = mapped_column(Float)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    device_tier: Mapped[str] = mapped_column(String(32), index=True)
    notes: Mapped[str] = mapped_column(Text)


class RevenueMetric(Base):
    __tablename__ = "revenue_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[str] = mapped_column(String(64), index=True)
    metric_date: Mapped[date] = mapped_column(Date, index=True)
    platform: Mapped[str] = mapped_column(String(32), index=True)
    region: Mapped[str] = mapped_column(String(32), index=True)
    player_segment: Mapped[str] = mapped_column(String(64), index=True)
    gross_revenue_usd: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    net_revenue_usd: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    arpdau_usd: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    payer_conversion_rate: Mapped[float] = mapped_column(Float)
    arppu_usd: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    payer_count: Mapped[int] = mapped_column(Integer)
    patch_version: Mapped[str] = mapped_column(String(32), index=True)
    liveops_event_code: Mapped[str | None] = mapped_column(String(64), index=True)


class SessionAnalytic(Base):
    __tablename__ = "session_analytics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[str] = mapped_column(String(64), index=True)
    session_date: Mapped[date] = mapped_column(Date, index=True)
    platform: Mapped[str] = mapped_column(String(32), index=True)
    region: Mapped[str] = mapped_column(String(32), index=True)
    player_segment: Mapped[str] = mapped_column(String(64), index=True)
    game_mode: Mapped[str] = mapped_column(String(64), index=True)
    dau: Mapped[int] = mapped_column(Integer)
    sessions: Mapped[int] = mapped_column(Integer)
    avg_session_minutes: Mapped[float] = mapped_column(Float)
    d1_retention: Mapped[float] = mapped_column(Float)
    d7_retention: Mapped[float] = mapped_column(Float)
    d30_retention: Mapped[float] = mapped_column(Float)
    churn_rate: Mapped[float] = mapped_column(Float)
    avg_queue_seconds: Mapped[float] = mapped_column(Float)
    matchmaking_fail_rate: Mapped[float] = mapped_column(Float)
    patch_version: Mapped[str] = mapped_column(String(32), index=True)
    liveops_event_code: Mapped[str | None] = mapped_column(String(64), index=True)

    __table_args__ = (
        Index(
            "ix_session_health_lookup",
            "session_date",
            "game_mode",
            "player_segment",
            "platform",
        ),
    )


class StorePurchase(Base):
    __tablename__ = "store_purchases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[str] = mapped_column(String(64), index=True)
    purchase_ts: Mapped[datetime] = mapped_column(DateTime, index=True)
    platform: Mapped[str] = mapped_column(String(32), index=True)
    region: Mapped[str] = mapped_column(String(32), index=True)
    player_segment: Mapped[str] = mapped_column(String(64), index=True)
    item_sku: Mapped[str] = mapped_column(String(64), index=True)
    item_name: Mapped[str] = mapped_column(String(160))
    item_category: Mapped[str] = mapped_column(String(64), index=True)
    price_usd: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    premium_currency_amount: Mapped[int] = mapped_column(Integer)
    premium_currency_name: Mapped[str] = mapped_column(String(64))
    patch_version: Mapped[str] = mapped_column(String(32), index=True)
    liveops_event_code: Mapped[str | None] = mapped_column(String(64), index=True)
