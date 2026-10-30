"""Validation CLI and module for multimodal evidence records and outputs."""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("member_2_evidence.validate")

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

_CACHED_SCHEMA: dict[str, Any] | None = None


def find_schema_file() -> Path | None:
    """Locate evidence.schema.json across standard repository locations."""
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / "shared" / "schemas" / "evidence.schema.json",
        here.parents[1] / "AI-Reality-Reconstructor" / "shared" / "schemas" / "evidence.schema.json",
        here / "shared" / "schemas" / "evidence.schema.json",
    ]
    for c in candidates:
        if c.is_file() and c.stat().st_size > 0:
            return c
    return None


def get_json_schema() -> dict[str, Any] | None:
    """Load JSON Schema from file if available."""
    global _CACHED_SCHEMA
    if _CACHED_SCHEMA is not None:
        return _CACHED_SCHEMA

    schema_file = find_schema_file()
    if schema_file:
        try:
            with open(schema_file, "r", encoding="utf-8") as f:
                _CACHED_SCHEMA = json.load(f)
                return _CACHED_SCHEMA
        except Exception as exc:
            logger.debug("Failed to load schema file %s: %s", schema_file, exc)
    return None


def validate_record(record: dict[str, Any], index: int = 1) -> list[str]:
    """Validate a single evidence record against requirements and evidence.schema.json."""
    errors: list[str] = []

    if not isinstance(record, dict):
        return [f"Record {index}: item must be a JSON object"]

    # 1. Required keys
    missing = [field for field in REQUIRED_FIELDS if field not in record]
    if missing:
        errors.append(f"Record {index}: missing required fields {missing}")

    # 2. Case ID check
    case_id = record.get("case_id")
    if not case_id or not str(case_id).strip():
        errors.append(f"Record {index}: case_id must be a non-empty string")

    # 3. Status tag check
    status = record.get("status")
    if status not in ALLOWED_STATUSES:
        errors.append(f"Record {index}: invalid status '{status}'; allowed: {sorted(ALLOWED_STATUSES)}")

    # 4. Modality type check
    ev_type = record.get("type")
    if ev_type not in ALLOWED_TYPES:
        errors.append(f"Record {index}: invalid evidence type '{ev_type}'; allowed: {sorted(ALLOWED_TYPES)}")

    # 5. Timestamp check (ISO-8601 validation if present)
    timestamp = record.get("timestamp")
    if timestamp is not None:
        try:
            iso_str = str(timestamp).replace("Z", "+00:00")
            datetime.fromisoformat(iso_str)
        except ValueError:
            errors.append(f"Record {index}: timestamp '{timestamp}' is not valid ISO-8601")

    # 6. Confidence range check (must be null or float between 0.0 and 1.0)
    confidence = record.get("confidence")
    if confidence is not None:
        if not isinstance(confidence, (int, float)):
            errors.append(f"Record {index}: confidence must be a number or null; got {type(confidence).__name__}")
        elif not (0.0 <= float(confidence) <= 1.0):
            errors.append(f"Record {index}: confidence {confidence} is outside allowed range [0.0, 1.0]")

    # 7. Data payload check
    data = record.get("data")
    if not isinstance(data, dict):
        errors.append(f"Record {index}: 'data' must be a dictionary object")

    # 8. Formal JSON Schema validation if jsonschema package is available
    schema = get_json_schema()
    if schema:
        try:
            import jsonschema

            validator = jsonschema.Draft7Validator(schema)
            for err in validator.iter_errors(record):
                errors.append(f"Record {index} schema error: {err.message}")
        except ImportError:
            pass

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
        if path.stat().st_size == 0:
            records = []
        else:
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
        here.parents[1] / "real_outputs" / "evidence" / "evidence.json",
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

    print(f"Validating evidence file against schema: {target}")
    valid, errors, count = validate_evidence_file(target)

    if not valid:
        print("\n[FAILED] Schema validation failed with errors:")
        for err in errors:
            print("-", err)
        sys.exit(1)
    else:
        print("\n[PASSED] Schema validation succeeded!")
        print(f"Total evidence records validated: {count}")
        print("All records conform strictly to required keys, ISO-8601 timestamps, confidence bounds, and status tags.")
        sys.exit(0)
