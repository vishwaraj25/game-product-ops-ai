from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError

from app.llm.base import StructuredLLM, StructuredModel
from app.planning.exceptions import PlannerOutputError


class LocalStructuredPlanningModel(StructuredLLM):
    provider_name = "local"
    model_name = "structured-planning-rules"
    model_version = "0.1.0"

    def generate_structured(
        self,
        *,
        task: str,
        instructions: str,
        input_payload: dict[str, Any],
        output_schema: type[StructuredModel],
    ) -> StructuredModel:
        objective = str(input_payload.get("objective", "")).strip()
        if not objective:
            raise PlannerOutputError("Planner input requires an objective.")

        output = build_structured_plan(objective)
        try:
            return output_schema.model_validate(output)
        except ValidationError as exc:
            raise PlannerOutputError("Planner produced malformed structured output.") from exc


def build_structured_plan(objective: str) -> dict[str, Any]:
    normalized = objective.lower()
    domain = infer_domain(normalized)
    timeframe = infer_timeframe(normalized)
    entities = infer_entities(normalized)
    hypotheses = build_hypotheses(domain, normalized)
    required_sources = minimum_sources_for_domain(domain, hypotheses)
    tool_usage = build_tool_usage(required_sources, domain, timeframe, entities)
    steps = build_steps(tool_usage, domain, timeframe, entities)

    return {
        "objective": objective,
        "objective_interpretation": interpret_objective(objective, domain, timeframe, entities),
        "product_domain": domain,
        "hypotheses": hypotheses,
        "required_data_sources": required_sources,
        "planned_tool_usage": tool_usage,
        "steps": steps,
        "success_criteria": success_criteria_for_domain(domain),
    }


def infer_domain(normalized: str) -> str:
    domain_scores = {
        "retention": score(normalized, ("retention", "leaving", "churn", "players leaving", "drop", "decline")),
        "ranked_matchmaking": score(normalized, ("ranked", "mmr", "matchmaking", "queue", "competitive")),
        "patch_evaluation": score(normalized, ("patch", "update", "hotfix", "release", "1.3")),
        "monetization": score(normalized, ("revenue", "battle pass", "store", "purchase", "payer", "conversion", "bundle")),
        "stability": score(normalized, ("crash", "android", "stability", "freeze", "disconnect")),
        "liveops": score(normalized, ("liveops", "event", "weekend", "festival", "siege")),
    }
    if domain_scores["ranked_matchmaking"] and domain_scores["retention"]:
        return "ranked_retention"
    return max(domain_scores, key=domain_scores.get) if max(domain_scores.values()) > 0 else "product_health"


def infer_timeframe(normalized: str) -> dict[str, str]:
    if "1.3" in normalized or "patch" in normalized:
        return {"anchor": "patch_1_3", "comparison": "pre_vs_post_release"}
    if "weekend" in normalized:
        return {"anchor": "recent_weekend", "comparison": "event_window_vs_prior_week"}
    if "declin" in normalized or "drop" in normalized or "leaving" in normalized:
        return {"anchor": "recent_decline", "comparison": "baseline_vs_recent_period"}
    return {"anchor": "objective_window", "comparison": "baseline_vs_investigation_window"}


def infer_entities(normalized: str) -> dict[str, list[str]]:
    modes = []
    if "ranked" in normalized:
        modes.append("ranked")
    if "battle pass" in normalized:
        modes.append("battle_pass")
    platforms = ["android"] if "android" in normalized else []
    patches = ["1.3"] if "1.3" in normalized or "patch" in normalized else []
    return {"modes": modes, "platforms": platforms, "patches": patches}


def build_hypotheses(domain: str, normalized: str) -> list[dict[str, Any]]:
    library = {
        "ranked_retention": [
            ("Ranked matchmaking friction increased", "Queue times or matchmaking failures may be causing ranked players to leave.", ["session_analytics", "gameplay_telemetry"]),
            ("Patch-driven MMR tuning changed player experience", "A recent patch may have changed ranked quality or access.", ["patch_notes", "session_analytics"]),
            ("Player sentiment shifted around ranked fairness", "Reviews may show complaints about MMR, parties, or queue quality.", ["player_reviews"]),
        ],
        "ranked_matchmaking": [
            ("Matchmaking constraints are too narrow", "Tight skill bands may be increasing queue time and failed matches.", ["session_analytics", "gameplay_telemetry"]),
            ("Competitive segment is disproportionately affected", "Ranked-focused players may see more friction than casual segments.", ["session_analytics"]),
            ("Recent release changed ranked behavior", "Patch notes may identify MMR or party validation changes.", ["patch_notes"]),
        ],
        "patch_evaluation": [
            ("The patch changed core product health metrics", "A release should be assessed across retention, sessions, revenue, and stability.", ["patch_notes", "session_analytics", "revenue_metrics"]),
            ("Patch changes created player-facing friction", "Reviews and telemetry may show negative reactions to changed systems.", ["player_reviews", "gameplay_telemetry"]),
            ("Patch introduced stability or performance risk", "Crash data may show a new issue after release.", ["crash_reports"]),
        ],
        "monetization": [
            ("Purchase intent declined", "Revenue softness may come from fewer payers or weaker conversion.", ["revenue_metrics", "store_purchases"]),
            ("Engagement decline reduced monetization surface area", "Lower sessions or retention can reduce store exposure.", ["session_analytics", "revenue_metrics"]),
            ("Offer/event fit underperformed", "LiveOps or store content may not match player demand.", ["liveops_events", "store_purchases"]),
        ],
        "stability": [
            ("A platform-specific crash regression occurred", "Crash volume may be concentrated on a platform, mode, or app version.", ["crash_reports"]),
            ("Crash spike is tied to an event or mode", "LiveOps activity may have amplified an unstable path.", ["liveops_events", "session_analytics", "crash_reports"]),
            ("Player sentiment reflects stability pain", "Reviews may mention crashes, lost rewards, or freezes.", ["player_reviews"]),
        ],
        "liveops": [
            ("Event participation differed from expectations", "Sessions and DAU should be checked against the event design.", ["liveops_events", "session_analytics"]),
            ("Event rewards or offers changed monetization", "Revenue and purchase data should show whether event offers worked.", ["revenue_metrics", "store_purchases"]),
            ("Event created operational risk", "Crash and sentiment data may reveal stability or reward problems.", ["crash_reports", "player_reviews"]),
        ],
        "retention": [
            ("Core engagement declined", "Session frequency or duration may have dropped before retention moved.", ["session_analytics", "gameplay_telemetry"]),
            ("A release or event changed player behavior", "Patch and LiveOps context may explain the timing.", ["patch_notes", "liveops_events"]),
            ("Players are reporting a specific pain point", "Reviews may reveal the user-facing reason behind churn.", ["player_reviews"]),
        ],
        "product_health": [
            ("A product metric changed materially", "Telemetry and session analytics can locate the affected metric.", ["gameplay_telemetry", "session_analytics"]),
            ("The change is connected to a release or event", "Patch and LiveOps records can explain timing.", ["patch_notes", "liveops_events"]),
            ("Player sentiment confirms or contradicts the metric signal", "Reviews provide qualitative validation.", ["player_reviews"]),
        ],
    }
    entries = library.get(domain, library["product_health"])
    return [
        {"title": title, "rationale": rationale, "evidence_required": evidence}
        for title, rationale, evidence in entries
    ]


def minimum_sources_for_domain(domain: str, hypotheses: list[dict[str, Any]]) -> list[str]:
    ordered_minimums = {
        "ranked_retention": ["patch_notes", "session_analytics", "gameplay_telemetry", "player_reviews", "revenue_metrics"],
        "ranked_matchmaking": ["patch_notes", "session_analytics", "gameplay_telemetry", "player_reviews"],
        "patch_evaluation": ["patch_notes", "session_analytics", "gameplay_telemetry", "player_reviews", "crash_reports", "revenue_metrics"],
        "monetization": ["revenue_metrics", "store_purchases", "session_analytics", "liveops_events", "patch_notes"],
        "stability": ["crash_reports", "session_analytics", "player_reviews", "patch_notes", "liveops_events"],
        "liveops": ["liveops_events", "session_analytics", "revenue_metrics", "store_purchases", "crash_reports", "player_reviews"],
        "retention": ["session_analytics", "gameplay_telemetry", "player_reviews", "patch_notes", "liveops_events"],
        "product_health": ["gameplay_telemetry", "session_analytics", "player_reviews", "patch_notes"],
    }
    source_set = set(ordered_minimums.get(domain, ordered_minimums["product_health"]))
    for hypothesis in hypotheses:
        source_set.update(hypothesis["evidence_required"])
    canonical_order = [
        "patch_notes",
        "liveops_events",
        "session_analytics",
        "gameplay_telemetry",
        "player_reviews",
        "crash_reports",
        "revenue_metrics",
        "store_purchases",
    ]
    return [source for source in canonical_order if source in source_set]


def build_tool_usage(
    sources: list[str],
    domain: str,
    timeframe: dict[str, str],
    entities: dict[str, list[str]],
) -> list[dict[str, Any]]:
    tool_by_source = {
        "patch_notes": ("readPatchNotes", "Review release changes relevant to the objective."),
        "liveops_events": ("getLiveOpsEvents", "Identify active events or offers that may explain timing."),
        "session_analytics": ("getSessionAnalytics", "Inspect engagement, retention, queue, and session health."),
        "gameplay_telemetry": ("getTelemetry", "Collect gameplay metric context for the affected domain."),
        "player_reviews": ("searchReviews", "Check player sentiment and recurring complaint topics."),
        "crash_reports": ("getCrashMetrics", "Inspect platform, mode, and version stability patterns."),
        "revenue_metrics": ("getRevenueMetrics", "Measure revenue, payer conversion, ARPDAU, and ARPPU movement."),
        "store_purchases": ("getStorePurchases", "Inspect purchase mix and item-level monetization behavior."),
    }
    usage = []
    for source in sources:
        tool_name, purpose = tool_by_source[source]
        usage.append(
            {
                "tool_name": tool_name,
                "purpose": purpose,
                "input_scope": {
                    "product_domain": domain,
                    "timeframe": timeframe,
                    "entities": entities,
                    "source_type": source,
                },
            }
        )
    return usage


def build_steps(
    tool_usage: list[dict[str, Any]],
    domain: str,
    timeframe: dict[str, str],
    entities: dict[str, list[str]],
) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = [
        {
            "step_order": 1,
            "step_type": "interpret_objective",
            "intended_tool": None,
            "input_scope": {"product_domain": domain, "timeframe": timeframe, "entities": entities},
            "selection_rationale": "Clarify the product domain, affected scope, and comparison window before selecting evidence sources.",
        }
    ]

    step_type_by_tool = {
        "readPatchNotes": "inspect_change_history",
        "getLiveOpsEvents": "collect_liveops_context",
        "getSessionAnalytics": "collect_metric_context",
        "getTelemetry": "collect_metric_context",
        "searchReviews": "collect_sentiment_context",
        "getCrashMetrics": "collect_stability_context",
        "getRevenueMetrics": "collect_monetization_context",
        "getStorePurchases": "collect_monetization_context",
    }
    for usage in tool_usage:
        steps.append(
            {
                "step_order": len(steps) + 1,
                "step_type": step_type_by_tool[usage["tool_name"]],
                "intended_tool": usage["tool_name"],
                "input_scope": usage["input_scope"],
                "selection_rationale": f"{usage['tool_name']} is the minimum source needed to {usage['purpose'].lower()}",
            }
        )

    steps.append(
        {
            "step_order": len(steps) + 1,
            "step_type": "cross_source_validation",
            "intended_tool": None,
            "input_scope": {"product_domain": domain, "timeframe": timeframe, "entities": entities},
            "selection_rationale": "Reserve a planning step for future comparison across sources before any findings or recommendations are generated.",
        }
    )
    return steps


def interpret_objective(
    objective: str,
    domain: str,
    timeframe: dict[str, str],
    entities: dict[str, list[str]],
) -> str:
    entity_bits = []
    if entities["modes"]:
        entity_bits.append(f"modes={','.join(entities['modes'])}")
    if entities["platforms"]:
        entity_bits.append(f"platforms={','.join(entities['platforms'])}")
    if entities["patches"]:
        entity_bits.append(f"patches={','.join(entities['patches'])}")
    entity_text = f" Scope hints: {'; '.join(entity_bits)}." if entity_bits else ""
    return (
        f"Interpret '{objective}' as a {domain.replace('_', ' ')} investigation. "
        f"Compare {timeframe['comparison']} around {timeframe['anchor']}.{entity_text}"
    )


def success_criteria_for_domain(domain: str) -> list[str]:
    shared = [
        "Plan identifies the smallest set of source systems needed to validate or reject each hypothesis.",
        "Every planned step has a rationale and an explicit input scope.",
        "No evidence, findings, recommendations, or artifacts are generated during planning.",
    ]
    domain_specific = {
        "ranked_retention": "Plan can validate whether ranked friction explains player departure.",
        "ranked_matchmaking": "Plan can compare matchmaking health before and after the suspected change.",
        "patch_evaluation": "Plan covers product health before and after the release window.",
        "monetization": "Plan can distinguish payer conversion, purchase mix, and engagement-driven revenue effects.",
        "stability": "Plan can isolate crash impact by platform, mode, version, and timing.",
        "liveops": "Plan can compare event expectations against engagement, stability, sentiment, and revenue signals.",
        "retention": "Plan can identify whether engagement, sentiment, release, or event context explains retention movement.",
        "product_health": "Plan can triangulate quantitative metrics with qualitative player sentiment and change history.",
    }
    return [domain_specific.get(domain, domain_specific["product_health"]), *shared]


def score(normalized: str, keywords: tuple[str, ...]) -> int:
    return sum(1 for keyword in keywords if keyword in normalized)
