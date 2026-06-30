from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.exceptions import AIReasoningError
from app.ai.factory import build_ai_reasoning_service
from app.investigations.models import DecisionArtifact, Finding, InvestigationPlan, Recommendation


class ExecutiveBriefGenerator:
    def create_executive_brief(
        self,
        db: Session,
        plan: InvestigationPlan,
        findings: list[Finding],
        recommendations: list[Recommendation],
    ) -> DecisionArtifact:
        try:
            content = self._ai_content(plan, findings, recommendations)
        except (AIReasoningError, ValueError):
            content = self._deterministic_content(plan, findings, recommendations)

        artifact = DecisionArtifact(
            investigation_id=plan.investigation_id,
            artifact_type="executive_brief",
            title=f"Executive Brief: {plan.objective}",
            content=content,
            status="ready_for_review",
            version=1,
        )
        db.add(artifact)
        db.flush()
        return artifact

    def _ai_content(
        self,
        plan: InvestigationPlan,
        findings: list[Finding],
        recommendations: list[Recommendation],
    ) -> dict:
        finding_payload = self._finding_payload(findings)
        recommendation_payload = self._recommendation_payload(recommendations)
        output = build_ai_reasoning_service().generate_executive_brief(
            input_payload={
                "objective": plan.objective,
                "objective_interpretation": plan.objective_interpretation,
                "product_domain": plan.product_domain,
                "findings": finding_payload,
                "recommendations": recommendation_payload,
            }
        )
        content = {
            "objective": plan.objective,
            "objective_interpretation": plan.objective_interpretation,
            "product_domain": plan.product_domain,
            "summary": output.summary,
            "top_findings": [item.model_dump() for item in output.top_findings],
            "recommendations": [item.model_dump() for item in output.recommendations],
            "approval_required": output.approval_required,
        }
        self._validate_content(content, findings, recommendations)
        return content

    def _deterministic_content(
        self,
        plan: InvestigationPlan,
        findings: list[Finding],
        recommendations: list[Recommendation],
    ) -> dict:
        content = {
            "objective": plan.objective,
            "objective_interpretation": plan.objective_interpretation,
            "product_domain": plan.product_domain,
            "summary": self._summary(findings),
            "top_findings": self._finding_payload(findings),
            "recommendations": self._recommendation_payload(recommendations),
            "approval_required": True,
        }
        self._validate_content(content, findings, recommendations)
        return content

    @staticmethod
    def _finding_payload(findings: list[Finding]) -> list[dict]:
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
        return top_findings

    @staticmethod
    def _recommendation_payload(recommendations: list[Recommendation]) -> list[dict]:
        return [
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

    @staticmethod
    def _validate_content(
        content: dict,
        findings: list[Finding],
        recommendations: list[Recommendation],
    ) -> None:
        persisted_evidence_ids = {
            evidence_id
            for finding in findings
            for evidence_id in finding.supporting_evidence_ids
        }
        persisted_finding_titles = {finding.title for finding in findings}
        persisted_recommendation_titles = {recommendation.title for recommendation in recommendations}

        for finding in content.get("top_findings", []):
            if finding.get("title") not in persisted_finding_titles:
                raise ValueError("Executive brief referenced a finding that does not exist.")
            evidence_ids = set(finding.get("supporting_evidence_ids") or [])
            if not evidence_ids or not evidence_ids.issubset(persisted_evidence_ids):
                raise ValueError("Executive brief finding is not traceable to persisted evidence.")

        for recommendation in content.get("recommendations", []):
            if recommendation.get("title") not in persisted_recommendation_titles:
                raise ValueError("Executive brief referenced a recommendation that does not exist.")

    @staticmethod
    def _summary(findings: list[Finding]) -> str:
        if not findings:
            return "The investigation completed, but no findings were generated."
        strongest = max(findings, key=lambda finding: finding.confidence)
        return (
            f"The strongest signal is '{strongest.title}' with "
            f"{strongest.confidence:.0%} confidence. Recommendations require PM approval."
        )
