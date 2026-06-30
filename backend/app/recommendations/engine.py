from __future__ import annotations

from sqlalchemy.orm import Session

from app.investigations.models import Finding, Recommendation


class RecommendationEngine:
    def create_recommendations(
        self,
        db: Session,
        investigation_id: int,
        findings: list[Finding],
    ) -> list[Recommendation]:
        self._validate_findings_are_persisted(findings)
        recommendations: list[Recommendation] = []
        for finding in findings:
            recommendation = Recommendation(
                investigation_id=investigation_id,
                finding_id=finding.id,
                title=self._title_for_finding(finding),
                summary=self._summary_for_finding(finding),
                recommendation_type=self._type_for_finding(finding),
                priority=self._priority_for_finding(finding),
                confidence=max(0.0, min(0.95, finding.confidence - 0.03)),
                risk_level=self._risk_for_finding(finding),
                supporting_evidence_ids=finding.supporting_evidence_ids,
                expected_impact=self._impact_for_finding(finding),
                status="proposed",
                requires_approval=True,
            )
            db.add(recommendation)
            recommendations.append(recommendation)
        db.flush()
        self._validate_recommendations_reference_findings(recommendations, {finding.id for finding in findings})
        return recommendations

    @staticmethod
    def _validate_findings_are_persisted(findings: list[Finding]) -> None:
        for finding in findings:
            if finding.id is None:
                raise ValueError("Recommendation cannot reference an unpersisted finding.")

    @staticmethod
    def _validate_recommendations_reference_findings(
        recommendations: list[Recommendation],
        finding_ids: set[int | None],
    ) -> None:
        persisted_finding_ids = {finding_id for finding_id in finding_ids if finding_id is not None}
        for recommendation in recommendations:
            if recommendation.finding_id not in persisted_finding_ids:
                raise ValueError("Recommendation referenced a finding that does not exist.")

    @staticmethod
    def _title_for_finding(finding: Finding) -> str:
        if finding.finding_type == "ranked_matchmaking_friction":
            return "Review ranked matchmaking constraints"
        if finding.finding_type == "stability_regression":
            return "Prioritize platform stability fix"
        if finding.finding_type == "monetization_shift":
            return "Audit monetization impact by segment"
        if finding.finding_type == "liveops_context":
            return "Compare event design against player response"
        if finding.finding_type == "release_context":
            return "Review release changes against product health"
        return "Continue focused product health investigation"

    @staticmethod
    def _summary_for_finding(finding: Finding) -> str:
        return (
            f"Use the supporting evidence from '{finding.title}' to decide the next "
            "product action. Human approval is required before any product change."
        )

    @staticmethod
    def _type_for_finding(finding: Finding) -> str:
        mapping = {
            "ranked_matchmaking_friction": "systems_tuning",
            "stability_regression": "stability_fix",
            "monetization_shift": "monetization_review",
            "liveops_context": "liveops_review",
            "release_context": "release_review",
        }
        return mapping.get(finding.finding_type, "investigation_follow_up")

    @staticmethod
    def _priority_for_finding(finding: Finding) -> str:
        return "high" if finding.severity == "high" else "medium"

    @staticmethod
    def _risk_for_finding(finding: Finding) -> str:
        if finding.finding_type in {"ranked_matchmaking_friction", "stability_regression"}:
            return "medium"
        return "low"

    @staticmethod
    def _impact_for_finding(finding: Finding) -> dict:
        return {
            "confidence": finding.confidence,
            "expected_product_area": finding.finding_type,
            "evidence_count": len(finding.supporting_evidence_ids),
        }
