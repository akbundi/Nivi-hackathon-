"""Case service serialization helpers."""

from ..database.models import CaseRecord
from ..schemas import CaseOut


def to_case_out(record: CaseRecord) -> dict:
    return CaseOut(id=record.id, title=record.title, description=record.description, created_at=record.created_at, updated_at=record.updated_at).model_dump(mode="json")
