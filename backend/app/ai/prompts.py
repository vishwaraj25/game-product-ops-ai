from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    version: str
    instructions: str


class PromptManager:
    def __init__(self) -> None:
        self._templates = {
            "investigation_planning": PromptTemplate(
                name="investigation_planning",
                version="0.1.0",
                instructions=(
                    "Convert a Product Manager business objective into a structured "
                    "investigation plan. Return structured output only. Do not execute "
                    "tools, collect evidence, create findings, recommend actions, or "
                    "generate artifacts."
                ),
            ),
            "evidence_correlation": PromptTemplate(
                name="evidence_correlation",
                version="0.1.0",
                instructions=(
                    "Group persisted evidence into correlated product themes. Only "
                    "reference evidence ids provided in the input. Do not create "
                    "findings, recommendations, or artifacts."
                ),
            ),
            "finding_generation": PromptTemplate(
                name="finding_generation",
                version="0.1.0",
                instructions=(
                    "Generate findings from correlated evidence clusters. Every "
                    "finding must reference existing evidence ids from the input. "
                    "Do not recommend actions or generate artifacts."
                ),
            ),
            "executive_brief": PromptTemplate(
                name="executive_brief",
                version="0.1.0",
                instructions=(
                    "Generate an executive brief from persisted findings and "
                    "recommendations. Do not invent evidence, findings, or "
                    "recommendations."
                ),
            ),
        }

    def get(self, name: str) -> PromptTemplate:
        return self._templates[name]
