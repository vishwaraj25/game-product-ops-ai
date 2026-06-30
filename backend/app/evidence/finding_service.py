from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.exceptions import AIReasoningError
from app.ai.factory import build_ai_reasoning_service
from app.evidence.correlation import EvidenceCluster
from app.investigations.models import Evidence, Finding, InvestigationPlan


class FindingService:
    def create_findings(
        self,
        db: Session,
        plan: InvestigationPlan,
        clusters: list[EvidenceCluster],
    ) -> list[Finding]:
        persisted_evidence_ids = set(
            db.scalars(
                select(Evidence.id).where(Evidence.investigation_id == plan.investigation_id)
            ).all()
        )
        try:
            return self._create_ai_findings(db, plan, clusters, persisted_evidence_ids)
        except (AIReasoningError, ValueError):
            return self._create_deterministic_findings(db, plan, clusters, persisted_evidence_ids)

    def _create_ai_findings(
        self,
        db: Session,
        plan: InvestigationPlan,
        clusters: list[EvidenceCluster],
        persisted_evidence_ids: set[int],
    ) -> list[Finding]:
        output = build_ai_reasoning_service().generate_findings(
            input_payload={
                "objective": plan.objective,
                "objective_interpretation": plan.objective_interpretation,
                "product_domain": plan.product_domain,
                "clusters": [cluster.__dict__ for cluster in clusters],
            }
        )
        finding_specs = [
            {
                "title": item.title,
                "summary": item.summary,
                "finding_type": item.finding_type,
                "confidence": item.confidence,
                "severity": item.severity,
                "supporting_evidence_ids": list(item.supporting_evidence_ids),
            }
            for item in output.findings
        ]
        self._validate_finding_specs(finding_specs, persisted_evidence_ids)
        return self._persist_findings(db, plan, finding_specs)

    def _create_deterministic_findings(
        self,
        db: Session,
        plan: InvestigationPlan,
        clusters: list[EvidenceCluster],
        persisted_evidence_ids: set[int],
    ) -> list[Finding]:
        finding_specs = [
            {
                "title": self._title_for_cluster(cluster),
                "summary": self._summary_for_cluster(plan, cluster),
                "finding_type": cluster.theme,
                "confidence": cluster.confidence,
                "severity": self._severity_for_cluster(cluster),
                "supporting_evidence_ids": cluster.evidence_ids,
            }
            for cluster in clusters[:4]
        ]
        self._validate_finding_specs(finding_specs, persisted_evidence_ids)
        return self._persist_findings(db, plan, finding_specs)

    @staticmethod
    def _persist_findings(
        db: Session,
        plan: InvestigationPlan,
        finding_specs: list[dict],
    ) -> list[Finding]:
        findings: list[Finding] = []
        for spec in finding_specs:
            finding = Finding(
                investigation_id=plan.investigation_id,
                title=spec["title"],
                summary=spec["summary"],
                finding_type=spec["finding_type"],
                confidence=spec["confidence"],
                severity=spec["severity"],
                supporting_evidence_ids=spec["supporting_evidence_ids"],
                status="derived",
            )
            db.add(finding)
            findings.append(finding)
        db.flush()
        return findings

    @staticmethod
    def _validate_finding_specs(
        finding_specs: list[dict],
        persisted_evidence_ids: set[int],
    ) -> None:
        if not finding_specs:
            raise ValueError("Finding generation produced no findings.")
        for spec in finding_specs:
            evidence_ids = set(spec["supporting_evidence_ids"])
            if not evidence_ids:
                raise ValueError("Finding has no supporting evidence.")
            if not evidence_ids.issubset(persisted_evidence_ids):
                raise ValueError("Finding referenced evidence that does not exist.")

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
