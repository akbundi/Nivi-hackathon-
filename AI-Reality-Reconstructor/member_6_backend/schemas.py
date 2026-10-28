"""API and pipeline contracts owned by the backend until shared schemas exist."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CaseCreate(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10_000)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title must not be blank")
        return value


class CaseUpdate(StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10_000)

    @field_validator("title")
    @classmethod
    def updated_title_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError("title must not be blank")
        return value


class CaseOut(StrictModel):
    id: str
    title: str
    description: str
    created_at: datetime
    updated_at: datetime


class EvidenceOut(StrictModel):
    id: str
    case_id: str
    filename: str
    content_type: str
    size_bytes: int
    sha256: str
    metadata: dict[str, Any]
    created_at: datetime


class JobOut(StrictModel):
    id: str
    case_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    current_stage: str | None
    adapter_mode: str
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error: dict[str, str] | None = None
    stage_outcomes: list[dict[str, Any]]


class EvidenceProcessingRecord(StrictModel):
    evidence_id: str
    outcome: Literal["available"]
    provenance: list[str]


class EvidenceProcessingOutput(StrictModel):
    records: list[EvidenceProcessingRecord]
    adapter_mode: Literal["mock", "real"]


class TimelineEvent(StrictModel):
    id: str
    timestamp: datetime | None = None
    summary: str
    epistemic_status: Literal["OBSERVED", "INFERRED", "UNKNOWN"]
    source_evidence_ids: list[str]

    @model_validator(mode="after")
    def require_sources_for_claims(self):
        if self.epistemic_status != "UNKNOWN" and not self.source_evidence_ids:
            raise ValueError("OBSERVED and INFERRED events require source evidence")
        return self


class TimelineOutput(StrictModel):
    case_id: str
    events: list[TimelineEvent]
    adapter_mode: Literal["mock", "real"]


class Finding(StrictModel):
    id: str
    statement: str
    epistemic_status: Literal["OBSERVED", "INFERRED", "UNKNOWN"]
    source_evidence_ids: list[str]

    @model_validator(mode="after")
    def require_sources_for_claims(self):
        if self.epistemic_status != "UNKNOWN" and not self.source_evidence_ids:
            raise ValueError("OBSERVED and INFERRED findings require source evidence")
        return self


class InvestigationOutput(StrictModel):
    case_id: str
    findings: list[Finding]
    adapter_mode: Literal["mock", "real"]


class SceneObject(StrictModel):
    id: str
    label: str
    epistemic_status: Literal["OBSERVED", "INFERRED", "UNKNOWN"]
    source_evidence_ids: list[str]
    position: dict[str, float] | None = None

    @model_validator(mode="after")
    def require_sources_for_claims(self):
        if self.epistemic_status != "UNKNOWN" and not self.source_evidence_ids:
            raise ValueError("OBSERVED and INFERRED scene objects require source evidence")
        return self


class SceneOutput(StrictModel):
    case_id: str
    objects: list[SceneObject]
    adapter_mode: Literal["mock", "real"]


class PaginatedCases(StrictModel):
    items: list[CaseOut]
    page: int
    page_size: int
    total: int


class PaginatedEvidence(StrictModel):
    items: list[EvidenceOut]
    page: int
    page_size: int
    total: int


class PaginatedJobs(StrictModel):
    items: list[JobOut]
    page: int
    page_size: int
    total: int
