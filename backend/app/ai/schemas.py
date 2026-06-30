from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class CorrelatedEvidenceCluster(BaseModel):
    theme: str = Field(min_length=3, max_length=80)
    summary: str = Field(min_length=20)
    evidence_ids: list[int] = Field(min_length=1)
    source_types: list[str] = Field(min_length=1)
    strength: str = Field(pattern="^(low|medium|high)$")
    confidence: float = Field(ge=0, le=1)


class CorrelationOutput(BaseModel):
    clusters: list[CorrelatedEvidenceCluster] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_evidence_ids(self) -> "CorrelationOutput":
        for cluster in self.clusters:
            if len(cluster.evidence_ids) != len(set(cluster.evidence_ids)):
                raise ValueError("Cluster evidence_ids must be unique.")
        return self


class FindingOutputItem(BaseModel):
    title: str = Field(min_length=8, max_length=200)
    summary: str = Field(min_length=20)
    finding_type: str = Field(min_length=3, max_length=80)
    confidence: float = Field(ge=0, le=1)
    severity: str = Field(pattern="^(low|medium|high)$")
    supporting_evidence_ids: list[int] = Field(min_length=1)


class FindingGenerationOutput(BaseModel):
    findings: list[FindingOutputItem] = Field(min_length=1)


class ExecutiveBriefFinding(BaseModel):
    title: str
    summary: str
    confidence: float = Field(ge=0, le=1)
    severity: str
    supporting_evidence_ids: list[int]


class ExecutiveBriefRecommendation(BaseModel):
    title: str
    summary: str
    priority: str
    confidence: float = Field(ge=0, le=1)
    risk_level: str
    requires_approval: bool


class ExecutiveBriefOutput(BaseModel):
    summary: str = Field(min_length=20)
    top_findings: list[ExecutiveBriefFinding]
    recommendations: list[ExecutiveBriefRecommendation]
    approval_required: bool
