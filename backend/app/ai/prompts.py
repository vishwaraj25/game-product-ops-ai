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
            )
        }

    def get(self, name: str) -> PromptTemplate:
        return self._templates[name]
