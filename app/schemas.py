from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


SCHEMA_VERSION = "1.0"
EpistemicStatus = Literal["observed", "reported", "inferred", "unknown"]


class Contract(BaseModel):
    schema_version: str = SCHEMA_VERSION


class CaseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value


class CaseOut(Contract):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    description: str | None
    created_at: datetime


class ObservationOut(Contract):
    id: str
    evidence_id: str
    text: str
    epistemic_status: EpistemicStatus
    created_at: datetime


class EvidenceOut(Contract):
    id: str
    case_id: str
    original_filename: str
    media_type: str
    size_bytes: int
    sha256: str
    uploaded_at: datetime
    processing_status: str
    file_url: str
    observations: list[ObservationOut] = Field(default_factory=list)


class EvidenceListOut(Contract):
    items: list[EvidenceOut]


class TimelineEventOut(Contract):
    model_config = ConfigDict(from_attributes=True)
    id: str
    case_id: str
    evidence_id: str
    label: str
    occurred_at: datetime
    time_basis: Literal["upload_time"]
    epistemic_status: EpistemicStatus


class TimelineOut(Contract):
    items: list[TimelineEventOut]


class FindingOut(Contract):
    id: str
    finding_type: Literal["information_gap", "potential_contradiction", "hypothesis", "follow_up_question"]
    text: str
    epistemic_status: EpistemicStatus
    evidence_ids: list[str] = Field(default_factory=list)


class FindingsOut(Contract):
    items: list[FindingOut]


class HealthOut(Contract):
    status: Literal["ok"]
