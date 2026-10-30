"""Sensor data processor supporting CSV and JSON time-series readings with timestamp normalization."""

from __future__ import annotations

import csv
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("member_2_evidence.sensor")

SUPPORTED_SENSOR_EXTENSIONS = frozenset({".csv", ".json"})

TIMESTAMP_FIELD_CANDIDATES = (
    "timestamp",
    "time",
    "datetime",
    "date",
    "time_utc",
    "recorded_at",
    "ts",
    "clock",
    "event_time",
    "time_stamp",
)


def normalize_timestamp(raw_val: Any) -> str | None:
    """
    Normalize various timestamp formats into ISO 8601 string.
    Supports ISO formats, epoch seconds/milliseconds, and common date-time strings.
    """
    if raw_val is None:
        return None

    # Handle numeric epoch timestamp (e.g. 1761037200 or 1761037200000)
    if isinstance(raw_val, (int, float)):
        try:
            val = float(raw_val)
            if val > 1e11:  # Milliseconds
                val /= 1000.0
            return datetime.fromtimestamp(val, tz=timezone.utc).isoformat()
        except Exception:
            return None

    raw_str = str(raw_val).strip()
    if not raw_str:
        return None

    # Try numeric string epoch
    if re.fullmatch(r"^\d{9,13}(\.\d+)?$", raw_str):
        try:
            num = float(raw_str)
            if num > 1e11:
                num /= 1000.0
            return datetime.fromtimestamp(num, tz=timezone.utc).isoformat()
        except Exception:
            pass

    # Try fromisoformat (handles standard ISO 8601)
    iso_clean = raw_str.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(iso_clean).isoformat()
    except ValueError:
        pass

    # Try common explicit date formats
    date_formats = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y/%m/%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%d-%m-%Y %H:%M:%S",
        "%m/%d/%Y %I:%M:%S %p",
        "%Y-%m-%d",
        "%d-%m-%Y",
    )
    for fmt in date_formats:
        try:
            dt = datetime.strptime(raw_str, fmt)
            return dt.isoformat()
        except ValueError:
            continue

    return None


def _find_timestamp_key(record: dict[str, Any]) -> str | None:
    """Find the key representing a timestamp in a record dictionary."""
    lower_map = {k.lower().strip(): k for k in record.keys()}
    for candidate in TIMESTAMP_FIELD_CANDIDATES:
        if candidate in lower_map:
            return lower_map[candidate]
    return None


def _parse_numeric(val: Any) -> float | int | None:
    """Try to parse a value into float or int if numeric."""
    if isinstance(val, (int, float)):
        return val
    if isinstance(val, str):
        val_clean = val.strip()
        if re.fullmatch(r"^-?\d+$", val_clean):
            try:
                return int(val_clean)
            except ValueError:
                pass
        if re.fullmatch(r"^-?\d+(\.\d+)?([eE][-+]?\d+)?$", val_clean):
            try:
                return float(val_clean)
            except ValueError:
                pass
    return None


def process_sensor_file(
    file_path: str | Path,
    case_id: str = "case-001",
) -> dict[str, Any]:
    """
    Process sensor time-series data from CSV or JSON.
    Normalizes timestamps to ISO 8601, extracts numeric metrics, computes summary
    statistics, and counts valid vs invalid records.
    """
    if not case_id or not str(case_id).strip():
        raise ValueError("A non-empty case_id is required.")

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Sensor file not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a regular file: {path}")

    if path.stat().st_size == 0:
        raise ValueError(f"Sensor file is empty (0 bytes): {path}")

    ext = path.suffix.lower()
    if ext not in SUPPORTED_SENSOR_EXTENSIONS:
        raise ValueError(f"Unsupported sensor file extension '{ext}'. Only CSV and JSON are supported.")

    raw_records: list[dict[str, Any]] = []

    if ext == ".csv":
        try:
            with open(path, "r", encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file)
                if reader.fieldnames is None:
                    raise ValueError(f"CSV file contains no headers or columns: {path.name}")
                raw_records = list(reader)
        except Exception as exc:
            raise ValueError(f"Failed to read CSV sensor data: {exc}") from exc

    elif ext == ".json":
        try:
            with open(path, "r", encoding="utf-8-sig") as file:
                content = json.load(file)
            if isinstance(content, list):
                raw_records = [item for item in content if isinstance(item, dict)]
            elif isinstance(content, dict):
                # Common nested keys
                for key in ("records", "readings", "data", "items", "measurements"):
                    if key in content and isinstance(content[key], list):
                        raw_records = [item for item in content[key] if isinstance(item, dict)]
                        break
                else:
                    raw_records = [content]
            else:
                raise ValueError("JSON must contain an object or a list of reading objects.")
        except Exception as exc:
            raise ValueError(f"Failed to parse JSON sensor data: {exc}") from exc

    normalized_records: list[dict[str, Any]] = []
    invalid_records: list[dict[str, Any]] = []
    numeric_series: dict[str, list[float]] = {}
    timestamps_collected: list[str] = []

    for index, raw_item in enumerate(raw_records, start=1):
        if not isinstance(raw_item, dict) or not raw_item:
            invalid_records.append({"row_index": index, "raw": raw_item, "reason": "Empty or non-dictionary record"})
            continue

        ts_key = _find_timestamp_key(raw_item)
        normalized_ts = None
        orig_ts = None

        if ts_key:
            orig_ts = raw_item[ts_key]
            normalized_ts = normalize_timestamp(orig_ts)

        record_data: dict[str, Any] = {}
        has_any_reading = False

        for k, v in raw_item.items():
            if k == ts_key:
                continue
            num = _parse_numeric(v)
            if num is not None:
                record_data[k] = num
                has_any_reading = True
                numeric_series.setdefault(k, []).append(float(num))
            else:
                record_data[k] = v

        if not has_any_reading and normalized_ts is None:
            invalid_records.append({
                "row_index": index,
                "raw": raw_item,
                "reason": "Record contains neither a valid timestamp nor measurement data",
            })
            continue

        item_entry = {
            "row_index": index,
            "timestamp": normalized_ts,
            "original_timestamp": orig_ts,
            "readings": record_data,
        }
        normalized_records.append(item_entry)
        if normalized_ts:
            timestamps_collected.append(normalized_ts)

    # Compute summary statistics for numeric channels
    summary_stats: dict[str, dict[str, Any]] = {}
    for channel, values in numeric_series.items():
        if values:
            summary_stats[channel] = {
                "count": len(values),
                "min": round(min(values), 3),
                "max": round(max(values), 3),
                "mean": round(sum(values) / len(values), 3),
            }

    primary_timestamp = timestamps_collected[0] if timestamps_collected else None

    evidence = {
        "id": str(uuid.uuid4()),
        "case_id": case_id,
        "type": "sensor",
        "timestamp": primary_timestamp,
        "source": str(path.resolve()),
        "confidence": None,
        "status": "OBSERVED",
        "data": {
            "filename": path.name,
            "format": ext.lstrip(".").upper(),
            "file_size_bytes": path.stat().st_size,
            "total_rows_read": len(raw_records),
            "valid_record_count": len(normalized_records),
            "invalid_record_count": len(invalid_records),
            "metric_channels": list(numeric_series.keys()),
            "summary_statistics": summary_stats,
            "time_range": {
                "start": timestamps_collected[0] if timestamps_collected else None,
                "end": timestamps_collected[-1] if timestamps_collected else None,
            },
            "records": normalized_records,
            "invalid_records": invalid_records,
        },
    }

    return evidence


def save_sensor_evidence(evidence: dict[str, Any], output_path: str | Path) -> None:
    """Save or append sensor evidence record into evidence JSON array."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    if output.exists():
        try:
            with open(output, "r", encoding="utf-8") as file:
                existing = json.load(file)
                records = existing if isinstance(existing, list) else [existing]
        except (json.JSONDecodeError, OSError):
            records = []

    records.append(evidence)

    with open(output, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=4, ensure_ascii=False)

    print(f"Sensor evidence saved to: {output.resolve()}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        f_path = sys.argv[1]
        c_id = sys.argv[2] if len(sys.argv) > 2 else "case-001"
    else:
        f_path = input("Enter sensor CSV/JSON file path: ").strip().strip('"')
        c_id = input("Enter case ID (or press Enter for case-001): ").strip() or "case-001"

    try:
        ev = process_sensor_file(f_path, c_id)
        project_root = Path(__file__).resolve().parents[2]
        shared_output = project_root / "real_outputs" / "evidence" / "evidence.json"
        save_sensor_evidence(ev, shared_output)
        print("\nExtracted evidence:")
        print(json.dumps(ev, indent=4, ensure_ascii=False))
    except Exception as error:
        print(f"Error: {error}")
