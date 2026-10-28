"""Evidence validation and response serialization."""

import re
from ..database.models import EvidenceRecord
from ..schemas import EvidenceOut


def safe_display_filename(filename: str) -> str:
    # Normalize both POSIX and Windows separators before taking the leaf name.
    leaf = filename.replace("\\", "/").split("/")[-1]
    leaf = re.sub(r"[\x00-\x1f\x7f]", "", leaf).strip().strip(".")
    if not leaf or leaf in {".", ".."}:
        return "upload"
    return leaf[:255]


def parse_metadata(raw: str | None) -> dict:
    if raw is None or raw == "":
        return {}
    import json
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Metadata must be a JSON object")
    return value


def to_evidence_out(record: EvidenceRecord) -> dict:
    return EvidenceOut(
        id=record.id, case_id=record.case_id, filename=record.filename,
        content_type=record.content_type, size_bytes=record.size_bytes,
        sha256=record.sha256, metadata=record.metadata_json or {}, created_at=record.created_at,
    ).model_dump(mode="json")
