from __future__ import annotations

from sqlalchemy.orm import Session

from app.investigations.models import DecisionArtifact, Finding, InvestigationPlan, Recommendation


class ExecutiveBriefGenerator:
    def create_executive_brief(
        self,
        db: Session,
        plan: InvestigationPlan,
        findings: list[Finding],
        recommendations: list[Recommendation],
    ) -> DecisionArtifact:
        top_findings = [
            {
                "title": finding.title,
                "summary": finding.summary,
                "confidence": finding.confidence,
                "severity": finding.severity,
                "supporting_evidence_ids": finding.supporting_evidence_ids,
            }
            for finding in findings
        ]
        proposed_actions = [
            {
                "title": recommendation.title,
                "summary": recommendation.summary,
                "priority": recommendation.priority,
                "confidence": recommendation.confidence,
                "risk_level": recommendation.risk_level,
                "requires_approval": recommendation.requires_approval,
            }
            for recommendation in recommendations
        ]
        artifact = DecisionArtifact(
            investigation_id=plan.investigation_id,
            artifact_type="executive_brief",
            title=f"Executive Brief: {plan.objective}",
            content={
                "objective": plan.objective,
                "objective_interpretation": plan.objective_interpretation,
                "product_domain": plan.product_domain,
                "summary": self._summary(findings),
                "top_findings": top_findings,
                "recommendations": proposed_actions,
                "approval_required": True,
            },
            status="ready_for_review",
            version=1,
        )
        db.add(artifact)
        db.flush()
        return artifact

    @staticmethod
    def _summary(findings: list[Finding]) -> str:
        if not findings:
            return "The investigation completed, but no findings were generated."
        strongest = max(findings, key=lambda finding: finding.confidence)
        return (
            f"The strongest signal is '{strongest.title}' with "
            f"{strongest.confidence:.0%} confidence. Recommendations require PM approval."
        )
