from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.ai.exceptions import ProviderNotConfiguredError, StructuredOutputValidationError

StructuredOutput = TypeVar("StructuredOutput", bound=BaseModel)


class BaseProvider(ABC):
    provider_name: str
    model_name: str
    model_version: str

    @abstractmethod
    def generate_structured(
        self,
        *,
        prompt_name: str,
        prompt_version: str,
        instructions: str,
        input_payload: dict[str, Any],
        output_schema: type[StructuredOutput],
    ) -> StructuredOutput:
        """Return output validated against the provided schema."""

    def validate_output(
        self,
        output: Any,
        output_schema: type[StructuredOutput],
    ) -> StructuredOutput:
        try:
            return output_schema.model_validate(output)
        except ValidationError as exc:
            raise StructuredOutputValidationError("Provider returned malformed structured output.") from exc


class DeterministicProvider(BaseProvider):
    provider_name = "deterministic"
    model_name = "deterministic-mvp-reasoner"
    model_version = "0.1.0"

    def generate_structured(
        self,
        *,
        prompt_name: str,
        prompt_version: str,
        instructions: str,
        input_payload: dict[str, Any],
        output_schema: type[StructuredOutput],
    ) -> StructuredOutput:
        if prompt_name == "investigation_planning":
            from app.llm.local_planning_model import build_structured_plan

            objective = str(input_payload.get("objective", "")).strip()
            return self.validate_output(build_structured_plan(objective), output_schema)
        if prompt_name == "evidence_correlation":
            return self.validate_output(build_deterministic_correlation(input_payload), output_schema)
        if prompt_name == "finding_generation":
            return self.validate_output(build_deterministic_findings(input_payload), output_schema)
        if prompt_name == "executive_brief":
            return self.validate_output(build_deterministic_executive_brief(input_payload), output_schema)

        raise ProviderNotConfiguredError(f"Deterministic provider has no prompt handler for {prompt_name}.")


class ClaudeProvider(BaseProvider):
    provider_name = "claude"
    model_name = "placeholder"
    model_version = "not_configured"

    def generate_structured(
        self,
        *,
        prompt_name: str,
        prompt_version: str,
        instructions: str,
        input_payload: dict[str, Any],
        output_schema: type[StructuredOutput],
    ) -> StructuredOutput:
        raise ProviderNotConfiguredError("ClaudeProvider is a placeholder. Real API integration is out of scope for Sprint 7.")


class OpenAIProvider(BaseProvider):
    provider_name = "openai"
    model_name = "placeholder"
    model_version = "not_configured"

    def generate_structured(
        self,
        *,
        prompt_name: str,
        prompt_version: str,
        instructions: str,
        input_payload: dict[str, Any],
        output_schema: type[StructuredOutput],
    ) -> StructuredOutput:
        raise ProviderNotConfiguredError("OpenAIProvider is a placeholder. Real API integration is out of scope for Sprint 7.")


def build_deterministic_correlation(input_payload: dict[str, Any]) -> dict[str, Any]:
    product_domain = str(input_payload.get("product_domain") or "product_health")
    evidence_items = list(input_payload.get("evidence") or [])
    grouped: dict[str, list[dict[str, Any]]] = {}
    for evidence in evidence_items:
        grouped.setdefault(_theme_for_evidence(product_domain, evidence), []).append(evidence)

    clusters = []
    for theme, items in grouped.items():
        source_types = sorted({str(item.get("source_type")) for item in items})
        avg_confidence = sum(float(item.get("confidence") or 0.75) for item in items) / max(len(items), 1)
        clusters.append(
            {
                "theme": theme,
                "summary": (
                    f"{len(items)} evidence items from {', '.join(source_types)} support "
                    f"the {theme.replace('_', ' ')} signal."
                ),
                "evidence_ids": [int(item["id"]) for item in items],
                "source_types": source_types,
                "strength": "high" if len(source_types) >= 2 else "medium",
                "confidence": round(min(0.95, avg_confidence + (0.05 if len(source_types) >= 2 else 0)), 2),
            }
        )
    clusters.sort(key=lambda cluster: (cluster["strength"] != "high", -cluster["confidence"], cluster["theme"]))
    return {"clusters": clusters}


def build_deterministic_findings(input_payload: dict[str, Any]) -> dict[str, Any]:
    objective = str(input_payload.get("objective") or "")
    findings = []
    for cluster in list(input_payload.get("clusters") or [])[:4]:
        confidence = float(cluster.get("confidence") or 0.75)
        findings.append(
            {
                "title": _title_for_cluster(str(cluster.get("theme") or "product_health_signal")),
                "summary": (
                    f"For objective '{objective}', correlated evidence indicates: "
                    f"{cluster.get('summary')} Confidence is {confidence:.0%}."
                ),
                "finding_type": str(cluster.get("theme") or "product_health_signal"),
                "confidence": confidence,
                "severity": "high" if confidence >= 0.9 and cluster.get("strength") == "high" else "medium" if confidence >= 0.8 else "low",
                "supporting_evidence_ids": list(cluster.get("evidence_ids") or []),
            }
        )
    return {"findings": findings}


def build_deterministic_executive_brief(input_payload: dict[str, Any]) -> dict[str, Any]:
    findings = list(input_payload.get("findings") or [])
    recommendations = list(input_payload.get("recommendations") or [])
    if findings:
        strongest = max(findings, key=lambda finding: float(finding.get("confidence") or 0))
        summary = (
            f"The strongest signal is '{strongest.get('title')}' with "
            f"{float(strongest.get('confidence') or 0):.0%} confidence. Recommendations require PM approval."
        )
    else:
        summary = "The investigation completed, but no findings were generated."
    return {
        "summary": summary,
        "top_findings": findings,
        "recommendations": recommendations,
        "approval_required": True,
    }


def _theme_for_evidence(product_domain: str, evidence: dict[str, Any]) -> str:
    title = str(evidence.get("title") or "").lower()
    summary = str(evidence.get("summary") or "").lower()
    source_type = str(evidence.get("source_type") or "")
    text = f"{title} {summary}"
    if (
        "queue" in text
        or "matchmaking" in text
        or product_domain in {"ranked_retention", "ranked_matchmaking"}
        and source_type in {"session_analytics", "gameplay_telemetry", "player_reviews", "patch_notes"}
    ):
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


def _title_for_cluster(theme: str) -> str:
    titles = {
        "ranked_matchmaking_friction": "Ranked matchmaking friction is a likely driver",
        "stability_regression": "Stability regression is visible in source data",
        "monetization_shift": "Monetization movement is visible across revenue sources",
        "liveops_context": "LiveOps timing provides important context",
        "release_context": "Release changes align with the investigation window",
        "product_health_signal": "Product health signals require attention",
    }
    return titles.get(theme, theme.replace("_", " ").title())
