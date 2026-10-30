"""Validation script for multimodal evidence records and outputs."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = [
    "id",
    "case_id",
    "type",
    "timestamp",
    "source",
    "confidence",
    "status",
    "data",
]

ALLOWED_STATUSES = {"OBSERVED", "INFERRED", "UNKNOWN"}
ALLOWED_TYPES = {"image", "video", "video_frame", "document", "sensor"}


def validate_record(record: dict[str, Any], index: int = 1) -> list[str]:
    """Validate a single evidence record against the canonical schema."""
    errors: list[str] = []

    if not isinstance(record, dict):
        return [f"Record {index}: item must be a JSON object"]

    missing = [field for field in REQUIRED_FIELDS if field not in record]
    if missing:
        errors.append(f"Record {index}: missing required fields {missing}")

    # Case ID check
    case_id = record.get("case_id")
    if not case_id or not str(case_id).strip():
        errors.append(f"Record {index}: case_id must be a non-empty string")

    # Status check
    status = record.get("status")
    if status not in ALLOWED_STATUSES:
        errors.append(f"Record {index}: invalid status '{status}'; allowed: {sorted(ALLOWED_STATUSES)}")

    # Type check
    ev_type = record.get("type")
    if ev_type not in ALLOWED_TYPES:
        errors.append(f"Record {index}: invalid evidence type '{ev_type}'; allowed: {sorted(ALLOWED_TYPES)}")

    # Timestamp check (if present, must be valid ISO format)
    timestamp = record.get("timestamp")
    if timestamp is not None:
        try:
            # Handle ISO 8601 validation
            iso_str = str(timestamp).replace("Z", "+00:00")
            datetime.fromisoformat(iso_str)
        except ValueError:
            errors.append(f"Record {index}: timestamp '{timestamp}' is not valid ISO 8601")

    # Data payload check
    data = record.get("data")
    if not isinstance(data, dict):
        errors.append(f"Record {index}: 'data' must be a dictionary object")

    return errors


def validate_evidence_file(file_path: str | Path) -> tuple[bool, list[str], int]:
    """
    Validate all records in an evidence JSON file.
    Returns (is_valid, errors_list, record_count).
    """
    path = Path(file_path)
    if not path.is_file():
        return False, [f"Evidence file not found: {path}"], 0

    try:
        with open(path, "r", encoding="utf-8") as file:
            records = json.load(file)
    except Exception as exc:
        return False, [f"Failed to read or parse JSON: {exc}"], 0

    if not isinstance(records, list):
        return False, ["Evidence file must contain a JSON array/list of records."], 0

    all_errors: list[str] = []
    for idx, rec in enumerate(records, start=1):
        rec_errors = validate_record(rec, idx)
        all_errors.extend(rec_errors)

    return len(all_errors) == 0, all_errors, len(records)


def find_default_evidence_file() -> Path:
    """Locate the active real_outputs/evidence/evidence.json file."""
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / "real_outputs" / "evidence" / "evidence.json",
        here.parent / "AI-Reality-Reconstructor" / "real_outputs" / "evidence" / "evidence.json",
        here / "real_outputs" / "evidence" / "evidence.json",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return candidates[0]


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
    else:
        target = find_default_evidence_file()

    print(f"Validating evidence file: {target}")
    valid, errors, count = validate_evidence_file(target)

    if not valid:
        print("\nValidation failed:")
        for err in errors:
            print("-", err)
        sys.exit(1)
    else:
        print("Validation passed!")
        print(f"Total evidence records: {count}")
        print("All records conform to required schema and contracts.")
        sys.exit(0)
