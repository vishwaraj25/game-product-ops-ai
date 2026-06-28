from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.investigations.models import Evidence, InvestigationPlan


@dataclass(frozen=True)
class EvidenceCluster:
    theme: str
    summary: str
    evidence_ids: list[int]
    source_types: list[str]
    strength: str
    confidence: float


class EvidenceCorrelator:
    def correlate(self, db: Session, plan: InvestigationPlan) -> list[EvidenceCluster]:
        evidence_items = db.scalars(
            select(Evidence)
            .where(Evidence.investigation_id == plan.investigation_id)
            .order_by(Evidence.source_type, Evidence.id)
        ).all()

        grouped: dict[str, list[Evidence]] = defaultdict(list)
        for evidence in evidence_items:
            grouped[self._theme_for_evidence(plan.product_domain or "product_health", evidence)].append(evidence)

        clusters = []
        for theme, items in grouped.items():
            source_types = sorted({item.source_type for item in items})
            avg_confidence = sum(item.confidence or 0.75 for item in items) / max(len(items), 1)
            clusters.append(
                EvidenceCluster(
                    theme=theme,
                    summary=self._cluster_summary(theme, items, source_types),
                    evidence_ids=[item.id for item in items],
                    source_types=source_types,
                    strength="high" if len(source_types) >= 2 else "medium",
                    confidence=round(min(0.95, avg_confidence + (0.05 if len(source_types) >= 2 else 0)), 2),
                )
            )
        return sorted(clusters, key=lambda cluster: (cluster.strength != "high", -cluster.confidence, cluster.theme))

    @staticmethod
    def _theme_for_evidence(product_domain: str, evidence: Evidence) -> str:
        title = evidence.title.lower()
        summary = evidence.summary.lower()
        source_type = evidence.source_type
        text = f"{title} {summary}"

        if "queue" in text or "matchmaking" in text or product_domain in {"ranked_retention", "ranked_matchmaking"} and source_type in {"session_analytics", "gameplay_telemetry", "player_reviews", "patch_notes"}:
            return "ranked_matchmaking_friction"
        if "crash" in text or "android" in text or source_type == "crash_reports":
            return "stability_regression"
        if source_type in {"revenue_metrics", "store_purchases"} or "revenue" in text or "purchase" in text:
            return "monetization_shift"
        if source_type == "liveops_events" or "event" in text:
            return "liveops_context"
        if source_type == "patch_notes" or "patch" in text:
            return "release_context"
        return "product_health_signal"

    @staticmethod
    def _cluster_summary(theme: str, items: list[Evidence], source_types: list[str]) -> str:
        readable_theme = theme.replace("_", " ")
        return (
            f"{len(items)} evidence items from {', '.join(source_types)} support "
            f"the {readable_theme} signal."
        )
