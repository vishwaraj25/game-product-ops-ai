from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
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

GAME_ID = "project-eclipse"
START_DATE = date(2026, 4, 15)
END_DATE = date(2026, 6, 14)

PLATFORMS = ("ios", "android", "pc")
REGIONS = ("na", "eu", "apac")
SEGMENTS = ("new", "engaged", "competitive", "spender", "lapsed_returning")
MODES = ("ranked", "casual", "rift_raid", "training")

PATCH_DEFINITIONS = [
    {
        "game_id": GAME_ID,
        "patch_version": "1.2.0",
        "title": "Aurora Arsenal",
        "release_date": date(2026, 5, 7),
        "summary": (
            "Introduced the Aurora Arsenal content drop with two weapons, "
            "economy tuning for upgrade materials, and stability improvements."
        ),
        "systems_changed": {
            "weapons": ["Helio Lance", "Volt Repeater"],
            "economy": {"upgrade_material_drop_rate": "+8%"},
            "stability": {"memory_pooling": "enabled on mobile"},
        },
        "risk_flags": {"economy_inflation": "medium", "matchmaking": "low"},
    },
    {
        "game_id": GAME_ID,
        "patch_version": "1.3.0",
        "title": "Ranked Integrity Update",
        "release_date": date(2026, 5, 28),
        "summary": (
            "Tightened ranked matchmaking bands, increased MMR confidence "
            "weighting, and added stricter party skill-delta validation."
        ),
        "systems_changed": {
            "matchmaking": {
                "mmr_band": "tightened from 420 to 260",
                "confidence_weight": "+18%",
                "party_skill_delta": "reduced from 600 to 380",
            },
            "ranked": {"placement_match_count": "5 to 7"},
        },
        "risk_flags": {
            "queue_time": "high",
            "ranked_retention": "high",
            "negative_reviews": "medium",
        },
    },
    {
        "game_id": GAME_ID,
        "patch_version": "1.3.1",
        "title": "Nebula Hotfix",
        "release_date": date(2026, 6, 9),
        "summary": (
            "Relaxed ranked search expansion after 90 seconds and fixed a "
            "mobile shader cache crash affecting Rift Raid rewards."
        ),
        "systems_changed": {
            "matchmaking": {"search_expansion_after_seconds": 90},
            "crash_fix": {"android_shader_cache": "patched"},
        },
        "risk_flags": {"queue_time": "medium", "mobile_stability": "low"},
    },
]

EVENT_DEFINITIONS = [
    {
        "game_id": GAME_ID,
        "event_code": "void-bloom",
        "name": "Void Bloom Festival",
        "event_type": "collection_event",
        "featured_mode": "casual",
        "start_date": date(2026, 5, 10),
        "end_date": date(2026, 5, 17),
        "reward_currency": "Bloom Shards",
        "tuning": {
            "daily_missions": 5,
            "cosmetic_bundle_discount_pct": 15,
            "bonus_xp_pct": 20,
        },
        "expected_player_impact": {
            "casual_sessions": "+10%",
            "cosmetic_revenue": "+12%",
        },
    },
    {
        "game_id": GAME_ID,
        "event_code": "nebula-siege",
        "name": "Nebula Siege Weekend",
        "event_type": "competitive_weekend",
        "featured_mode": "rift_raid",
        "start_date": date(2026, 6, 5),
        "end_date": date(2026, 6, 8),
        "reward_currency": "Nebula Cores",
        "tuning": {
            "raid_reward_multiplier": 2.0,
            "limited_bundle": "Nebula Commander Pack",
            "android_shader_variant": "experimental",
        },
        "expected_player_impact": {
            "rift_raid_sessions": "+28%",
            "store_revenue": "+18%",
            "android_crash_risk": "elevated",
        },
    },
]

REVIEW_TEMPLATES = {
    "matchmaking": [
        ("Ranked queues are painful", "Patch 1.3 made ranked take forever and the matches still feel uneven."),
        ("MMR change feels bad", "I spend more time waiting than playing ranked now."),
        ("Please revert ranked", "The tighter matchmaking sounds good, but my squad cannot find games at night."),
    ],
    "crash": [
        ("Nebula event crashes", "Rift Raid crashes after the reward screen on my Android phone."),
        ("Lost rewards twice", "The weekend event is fun, but the app closes before rewards are granted."),
        ("Android stability got worse", "Since Nebula Siege started, raids crash every few matches."),
    ],
    "positive": [
        ("Great event rewards", "Void Bloom had a good pace and the cosmetics were worth chasing."),
        ("Combat still feels sharp", "Project Eclipse has the best arena movement in the genre."),
        ("Nice arsenal update", "The Helio Lance is fun without feeling too strong."),
    ],
    "economy": [
        ("Bundles feel expensive", "The event bundles are tempting but the prices feel high after shorter sessions."),
        ("Progress slowed down", "I am earning fewer upgrade materials than expected from ranked."),
    ],
}


def seed_project_eclipse() -> None:
    with SessionLocal() as session:
        reset_source_data(session)
        session.add_all(PatchNote(**patch) for patch in PATCH_DEFINITIONS)
        session.add_all(LiveOpsEvent(**event) for event in EVENT_DEFINITIONS)
        seed_daily_metrics(session)
        seed_reviews(session)
        seed_crashes(session)
        seed_store_purchases(session)
        session.commit()


def reset_source_data(session: Session) -> None:
    for model in (
        StorePurchase,
        RevenueMetric,
        SessionAnalytic,
        CrashReport,
        PlayerReview,
        TelemetryMetric,
        LiveOpsEvent,
        PatchNote,
    ):
        session.execute(delete(model))
    session.commit()


def seed_daily_metrics(session: Session) -> None:
    rng = random.Random(1307)
    current = START_DATE
    while current <= END_DATE:
        patch = patch_for_day(current)
        event = event_for_day(current)
        weekday_factor = 1.12 if current.weekday() >= 4 else 1.0

        for platform in PLATFORMS:
            for region in REGIONS:
                for segment in SEGMENTS:
                    for mode in MODES:
                        base_dau = baseline_dau(platform, region, segment, mode)
                        trend = 1 + ((current - START_DATE).days * 0.0018)
                        event_factor = liveops_session_factor(event, mode)
                        ranked_penalty = ranked_patch_penalty(current, segment, mode)
                        crash_penalty = crash_experience_penalty(current, platform, mode)
                        noise = rng.uniform(0.94, 1.06)
                        dau = max(60, int(base_dau * trend * weekday_factor * event_factor * ranked_penalty * crash_penalty * noise))

                        queue_seconds = queue_time(current, segment, mode, rng)
                        fail_rate = matchmaking_fail_rate(current, mode, queue_seconds)
                        session_minutes = avg_session_minutes(mode, segment, queue_seconds, platform, current)
                        d1, d7, d30, churn = retention_values(mode, segment, current, queue_seconds, platform)
                        sessions = int(dau * sessions_per_user(mode, segment, current))

                        session.add(
                            SessionAnalytic(
                                game_id=GAME_ID,
                                session_date=current,
                                platform=platform,
                                region=region,
                                player_segment=segment,
                                game_mode=mode,
                                dau=dau,
                                sessions=sessions,
                                avg_session_minutes=round(session_minutes, 2),
                                d1_retention=round(d1, 4),
                                d7_retention=round(d7, 4),
                                d30_retention=round(d30, 4),
                                churn_rate=round(churn, 4),
                                avg_queue_seconds=round(queue_seconds, 2),
                                matchmaking_fail_rate=round(fail_rate, 4),
                                patch_version=patch,
                                liveops_event_code=event["event_code"] if event else None,
                            )
                        )

                        add_telemetry(session, current, platform, region, segment, mode, patch, event, dau, sessions, queue_seconds, fail_rate, d1, d7)

                seed_revenue_for_platform_region(session, current, platform, region, patch, event, rng)

        current += timedelta(days=1)


def add_telemetry(
    session: Session,
    current: date,
    platform: str,
    region: str,
    segment: str,
    mode: str,
    patch: str,
    event: dict | None,
    dau: int,
    sessions: int,
    queue_seconds: float,
    fail_rate: float,
    d1: float,
    d7: float,
) -> None:
    metrics = {
        "dau": (dau, "players"),
        "sessions": (sessions, "sessions"),
        "avg_queue_seconds": (queue_seconds, "seconds"),
        "matchmaking_fail_rate": (fail_rate, "rate"),
        "d1_retention": (d1, "rate"),
        "d7_retention": (d7, "rate"),
    }
    for name, (value, unit) in metrics.items():
        session.add(
            TelemetryMetric(
                game_id=GAME_ID,
                metric_date=current,
                platform=platform,
                region=region,
                player_segment=segment,
                game_mode=mode,
                metric_name=name,
                metric_value=round(float(value), 4),
                unit=unit,
                patch_version=patch,
                liveops_event_code=event["event_code"] if event else None,
            )
        )


def seed_revenue_for_platform_region(
    session: Session,
    current: date,
    platform: str,
    region: str,
    patch: str,
    event: dict | None,
    rng: random.Random,
) -> None:
    for segment in SEGMENTS:
        base_payers = {
            "new": 42,
            "engaged": 140,
            "competitive": 118,
            "spender": 360,
            "lapsed_returning": 32,
        }[segment]
        platform_factor = {"ios": 1.22, "android": 0.92, "pc": 1.05}[platform]
        region_factor = {"na": 1.18, "eu": 1.0, "apac": 0.9}[region]
        event_factor = 1.0
        if event and event["event_code"] == "void-bloom":
            event_factor = 1.12 if segment in {"engaged", "spender"} else 1.04
        if event and event["event_code"] == "nebula-siege":
            event_factor = 1.18 if segment in {"competitive", "spender"} else 1.06
        if current >= date(2026, 5, 30) and segment == "competitive":
            event_factor *= 0.92
        if date(2026, 6, 5) <= current <= date(2026, 6, 8) and platform == "android":
            event_factor *= 0.88

        payer_count = int(base_payers * platform_factor * region_factor * event_factor * rng.uniform(0.94, 1.07))
        arppu = Decimal(str(round({"spender": 24.5, "competitive": 14.8, "engaged": 10.2, "new": 5.8, "lapsed_returning": 6.4}[segment] * rng.uniform(0.96, 1.05), 2)))
        gross = Decimal(payer_count) * arppu
        dau_estimate = max(payer_count * 24, 1)

        session.add(
            RevenueMetric(
                game_id=GAME_ID,
                metric_date=current,
                platform=platform,
                region=region,
                player_segment=segment,
                gross_revenue_usd=gross.quantize(Decimal("0.01")),
                net_revenue_usd=(gross * Decimal("0.70")).quantize(Decimal("0.01")),
                arpdau_usd=(gross / Decimal(dau_estimate)).quantize(Decimal("0.0001")),
                payer_conversion_rate=round(payer_count / dau_estimate, 4),
                arppu_usd=arppu,
                payer_count=payer_count,
                patch_version=patch,
                liveops_event_code=event["event_code"] if event else None,
            )
        )


def seed_reviews(session: Session) -> None:
    rng = random.Random(404)
    current = START_DATE
    while current <= END_DATE:
        patch = patch_for_day(current)
        daily_volume = 6
        review_mix = ["positive"] * 4 + ["economy"]
        if current >= date(2026, 5, 29):
            daily_volume += 5
            review_mix += ["matchmaking"] * 7
        if date(2026, 6, 5) <= current <= date(2026, 6, 9):
            daily_volume += 6
            review_mix += ["crash"] * 8

        for _ in range(daily_volume):
            topic = rng.choice(review_mix)
            title, body = rng.choice(REVIEW_TEMPLATES[topic])
            rating = rating_for_review_topic(topic, rng)
            session.add(
                PlayerReview(
                    game_id=GAME_ID,
                    review_date=current,
                    platform=rng.choice(PLATFORMS),
                    rating=rating,
                    locale=rng.choice(("en-US", "en-GB", "de-DE", "fr-FR", "ja-JP")),
                    player_segment=rng.choice(SEGMENTS),
                    game_mode="ranked" if topic == "matchmaking" else ("rift_raid" if topic == "crash" else rng.choice(MODES)),
                    title=title,
                    body=body,
                    sentiment="positive" if rating >= 4 else ("neutral" if rating == 3 else "negative"),
                    topics=[topic, "ranked" if topic == "matchmaking" else "liveops" if topic == "crash" else "economy"],
                    patch_version=patch,
                )
            )
        current += timedelta(days=1)


def seed_crashes(session: Session) -> None:
    rng = random.Random(509)
    current = START_DATE
    while current <= END_DATE:
        patch = patch_for_day(current)
        for platform in PLATFORMS:
            base = {"ios": 58, "android": 92, "pc": 44}[platform]
            affected = int(base * rng.uniform(0.75, 1.25))
            signature = "network_timeout_reconnect_loop"
            severity = "medium"
            device_tier = "mixed"
            notes = "Background reconnect loop after packet loss."

            if date(2026, 6, 5) <= current <= date(2026, 6, 8) and platform == "android":
                affected = int(affected * 4.6)
                signature = "android_shader_cache_reward_screen"
                severity = "critical"
                device_tier = "mid"
                notes = "Crash after Rift Raid reward presentation during Nebula Siege."
            elif current >= date(2026, 6, 9) and platform == "android":
                affected = int(affected * 0.72)
                signature = "android_shader_cache_reward_screen"
                severity = "low"
                device_tier = "mid"
                notes = "Residual reports after 1.3.1 shader cache hotfix."

            session.add(
                CrashReport(
                    game_id=GAME_ID,
                    crash_date=current,
                    platform=platform,
                    game_mode="rift_raid" if "shader" in signature else "ranked",
                    app_version=patch,
                    crash_signature=signature,
                    affected_sessions=affected,
                    crash_free_sessions_pct=round(max(96.2, 99.82 - affected / 1000), 3),
                    severity=severity,
                    device_tier=device_tier,
                    notes=notes,
                )
            )
        current += timedelta(days=1)


def seed_store_purchases(session: Session) -> None:
    rng = random.Random(901)
    current = START_DATE
    catalog = [
        ("eclipse-pass-s5", "Eclipse Pass Season 5", "battle_pass", Decimal("9.99"), 0),
        ("void-bloom-cache", "Void Bloom Cache", "cosmetic_bundle", Decimal("14.99"), 1200),
        ("nebula-commander", "Nebula Commander Pack", "event_bundle", Decimal("19.99"), 1800),
        ("lumen-500", "500 Lumen", "premium_currency", Decimal("4.99"), 500),
        ("lumen-2200", "2200 Lumen", "premium_currency", Decimal("19.99"), 2200),
    ]

    while current <= END_DATE:
        patch = patch_for_day(current)
        event = event_for_day(current)
        purchase_count = 44
        if event and event["event_code"] == "void-bloom":
            purchase_count += 24
        if event and event["event_code"] == "nebula-siege":
            purchase_count += 34
        if current >= date(2026, 5, 30):
            purchase_count -= 7

        for i in range(max(12, purchase_count)):
            if event and event["event_code"] == "nebula-siege" and rng.random() < 0.45:
                item = catalog[2]
            elif event and event["event_code"] == "void-bloom" and rng.random() < 0.42:
                item = catalog[1]
            else:
                item = rng.choice(catalog)

            platform = rng.choice(PLATFORMS)
            if event and event["event_code"] == "nebula-siege" and platform == "android":
                if rng.random() < 0.28:
                    continue

            session.add(
                StorePurchase(
                    game_id=GAME_ID,
                    purchase_ts=datetime.combine(current, time(hour=rng.randrange(8, 24), minute=rng.randrange(0, 60), second=rng.randrange(0, 60))),
                    platform=platform,
                    region=rng.choice(REGIONS),
                    player_segment=rng.choices(SEGMENTS, weights=[1, 4, 4, 8, 1], k=1)[0],
                    item_sku=item[0],
                    item_name=item[1],
                    item_category=item[2],
                    price_usd=item[3],
                    premium_currency_amount=item[4],
                    premium_currency_name="Lumen",
                    patch_version=patch,
                    liveops_event_code=event["event_code"] if event else None,
                )
            )
        current += timedelta(days=1)


def patch_for_day(current: date) -> str:
    if current >= date(2026, 6, 9):
        return "1.3.1"
    if current >= date(2026, 5, 28):
        return "1.3.0"
    if current >= date(2026, 5, 7):
        return "1.2.0"
    return "1.1.4"


def event_for_day(current: date) -> dict | None:
    for event in EVENT_DEFINITIONS:
        if event["start_date"] <= current <= event["end_date"]:
            return event
    return None


def baseline_dau(platform: str, region: str, segment: str, mode: str) -> int:
    mode_base = {"ranked": 1650, "casual": 2300, "rift_raid": 980, "training": 420}[mode]
    platform_factor = {"ios": 1.0, "android": 1.14, "pc": 0.82}[platform]
    region_factor = {"na": 1.1, "eu": 0.96, "apac": 1.18}[region]
    segment_factor = {"new": 0.9, "engaged": 1.35, "competitive": 1.0, "spender": 0.38, "lapsed_returning": 0.22}[segment]
    return int(mode_base * platform_factor * region_factor * segment_factor)


def liveops_session_factor(event: dict | None, mode: str) -> float:
    if not event:
        return 1.0
    if event["event_code"] == "void-bloom" and mode == "casual":
        return 1.12
    if event["event_code"] == "nebula-siege" and mode == "rift_raid":
        return 1.3
    return 1.03


def ranked_patch_penalty(current: date, segment: str, mode: str) -> float:
    if mode != "ranked" or current < date(2026, 5, 29):
        return 1.0
    penalty = {"new": 0.9, "engaged": 0.86, "competitive": 0.78, "spender": 0.88, "lapsed_returning": 0.82}[segment]
    if current >= date(2026, 6, 9):
        penalty += 0.07
    return penalty


def crash_experience_penalty(current: date, platform: str, mode: str) -> float:
    if platform == "android" and mode == "rift_raid" and date(2026, 6, 5) <= current <= date(2026, 6, 8):
        return 0.84
    return 1.0


def queue_time(current: date, segment: str, mode: str, rng: random.Random) -> float:
    base = {"ranked": 62, "casual": 18, "rift_raid": 28, "training": 0}[mode]
    if mode == "ranked" and current >= date(2026, 5, 29):
        base += {"new": 34, "engaged": 58, "competitive": 94, "spender": 44, "lapsed_returning": 66}[segment]
    if mode == "ranked" and current >= date(2026, 6, 9):
        base -= 28
    return max(0, base + rng.uniform(-6, 9))


def matchmaking_fail_rate(current: date, mode: str, queue_seconds: float) -> float:
    if mode == "training":
        return 0
    return min(0.22, 0.012 + max(0, queue_seconds - 45) * 0.0013)


def avg_session_minutes(mode: str, segment: str, queue_seconds: float, platform: str, current: date) -> float:
    base = {"ranked": 31, "casual": 22, "rift_raid": 28, "training": 9}[mode]
    base += {"new": -4, "engaged": 2, "competitive": 5, "spender": 3, "lapsed_returning": -2}[segment]
    base -= max(0, queue_seconds - 80) * 0.045
    if platform == "android" and mode == "rift_raid" and date(2026, 6, 5) <= current <= date(2026, 6, 8):
        base -= 4.8
    return max(5, base)


def retention_values(mode: str, segment: str, current: date, queue_seconds: float, platform: str) -> tuple[float, float, float, float]:
    base_d1 = {"new": 0.37, "engaged": 0.53, "competitive": 0.58, "spender": 0.62, "lapsed_returning": 0.29}[segment]
    mode_bonus = {"ranked": 0.02, "casual": 0.0, "rift_raid": 0.01, "training": -0.04}[mode]
    queue_drag = max(0, queue_seconds - 75) * 0.0016
    crash_drag = 0.045 if platform == "android" and mode == "rift_raid" and date(2026, 6, 5) <= current <= date(2026, 6, 8) else 0
    d1 = max(0.12, base_d1 + mode_bonus - queue_drag - crash_drag)
    d7 = max(0.07, d1 - 0.17 - queue_drag * 0.5)
    d30 = max(0.03, d7 - 0.12)
    churn = min(0.58, 1 - d1 + queue_drag + crash_drag)
    return d1, d7, d30, churn


def sessions_per_user(mode: str, segment: str, current: date) -> float:
    value = {"ranked": 2.4, "casual": 1.8, "rift_raid": 2.0, "training": 1.1}[mode]
    value += {"new": -0.2, "engaged": 0.25, "competitive": 0.45, "spender": 0.2, "lapsed_returning": -0.15}[segment]
    if mode == "ranked" and current >= date(2026, 5, 29):
        value -= 0.25
    return max(1.0, value)


def rating_for_review_topic(topic: str, rng: random.Random) -> int:
    if topic in {"matchmaking", "crash"}:
        return rng.choices([1, 2, 3], weights=[6, 3, 1], k=1)[0]
    if topic == "economy":
        return rng.choices([2, 3, 4], weights=[3, 4, 1], k=1)[0]
    return rng.choices([4, 5], weights=[3, 5], k=1)[0]


if __name__ == "__main__":
    seed_project_eclipse()
    print("Seeded Project Eclipse synthetic LiveOps data.")
