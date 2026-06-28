from __future__ import annotations

from sqlalchemy.orm import Session

from app.evidence.correlation import EvidenceCluster
from app.investigations.models import Finding, InvestigationPlan


class FindingService:
    def create_findings(
        self,
        db: Session,
        plan: InvestigationPlan,
        clusters: list[EvidenceCluster],
    ) -> list[Finding]:
        findings: list[Finding] = []
        for cluster in clusters[:4]:
            finding = Finding(
                investigation_id=plan.investigation_id,
                title=self._title_for_cluster(cluster),
                summary=self._summary_for_cluster(plan, cluster),
                finding_type=cluster.theme,
                confidence=cluster.confidence,
                severity=self._severity_for_cluster(cluster),
                supporting_evidence_ids=cluster.evidence_ids,
                status="derived",
            )
            db.add(finding)
            findings.append(finding)
        db.flush()
        return findings

    @staticmethod
    def _title_for_cluster(cluster: EvidenceCluster) -> str:
        titles = {
            "ranked_matchmaking_friction": "Ranked matchmaking friction is a likely driver",
            "stability_regression": "Stability regression is visible in source data",
            "monetization_shift": "Monetization movement is visible across revenue sources",
            "liveops_context": "LiveOps timing provides important context",
            "release_context": "Release changes align with the investigation window",
            "product_health_signal": "Product health signals require attention",
        }
        return titles.get(cluster.theme, cluster.theme.replace("_", " ").title())

    @staticmethod
    def _summary_for_cluster(plan: InvestigationPlan, cluster: EvidenceCluster) -> str:
        return (
            f"For objective '{plan.objective}', correlated evidence indicates: "
            f"{cluster.summary} Confidence is {cluster.confidence:.0%}."
        )

    @staticmethod
    def _severity_for_cluster(cluster: EvidenceCluster) -> str:
        if cluster.confidence >= 0.9 and cluster.strength == "high":
            return "high"
        if cluster.confidence >= 0.8:
            return "medium"
        return "low"
