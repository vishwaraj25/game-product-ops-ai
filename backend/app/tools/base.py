from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from sqlalchemy.orm import Session


@dataclass(frozen=True)
class EvidenceCandidate:
    source_type: str
    source_id: str | None
    title: str
    summary: str
    observed_value: dict | None = None
    time_window: dict | None = None
    strength: str = "medium"
    confidence: float | None = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ToolResult:
    summary: dict
    evidence: list[EvidenceCandidate]


class InvestigationTool(Protocol):
    name: str
    source_type: str

    def execute(self, db: Session, input_scope: dict) -> ToolResult:
        """Run a source-data query and return structured evidence candidates."""
