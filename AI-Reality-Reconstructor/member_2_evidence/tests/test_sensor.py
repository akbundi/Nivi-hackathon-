"""Tests for sensor CSV/JSON data parsing, timestamp normalization, and statistics."""

from __future__ import annotations

from pathlib import Path
import pytest

from member_2_evidence.sensor.sensor_processor import (
    normalize_timestamp,
    process_sensor_file,
)


def test_sensor_csv_parsing(synthetic_sensor_csv: Path):
    record = process_sensor_file(synthetic_sensor_csv, case_id="case-401")

    assert record["case_id"] == "case-401"
    assert record["type"] == "sensor"
    assert record["status"] == "OBSERVED"

    data = record["data"]
    assert data["format"] == "CSV"
    assert data["total_rows_read"] == 3
    assert data["valid_record_count"] == 3
    assert data["invalid_record_count"] == 0

    assert "temperature" in data["metric_channels"]
    assert "humidity" in data["metric_channels"]

    temp_stats = data["summary_statistics"]["temperature"]
    assert temp_stats["count"] == 3
    assert temp_stats["min"] == 22.5
    assert temp_stats["max"] == 24.0
    assert pytest.approx(temp_stats["mean"], rel=1e-2) == 23.2

    assert record["timestamp"] == "2026-10-25T10:00:00"


def test_sensor_json_parsing(synthetic_sensor_json: Path):
    record = process_sensor_file(synthetic_sensor_json, case_id="case-402")

    assert record["type"] == "sensor"
    data = record["data"]
    assert data["format"] == "JSON"
    assert data["valid_record_count"] == 2
    assert "pressure_kpa" in data["metric_channels"]
    assert "vibration_hz" in data["metric_channels"]


def test_timestamp_normalization_formats():
    assert normalize_timestamp("2026-10-25T12:00:00Z") == "2026-10-25T12:00:00+00:00"
    assert normalize_timestamp("2026-10-25 14:30:00") == "2026-10-25T14:30:00"
    assert normalize_timestamp("25/10/2026 09:15:00") == "2026-10-25T09:15:00"
    assert normalize_timestamp(1761037200) is not None
    assert normalize_timestamp(None) is None
    assert normalize_timestamp("invalid-date") is None


def test_sensor_invalid_rows_handling(tmp_path: Path):
    bad_csv = tmp_path / "mixed.csv"
    bad_csv.write_text("timestamp,temperature\n2026-10-25T10:00:00,25.0\n,\n")
    record = process_sensor_file(bad_csv, case_id="case-403")

    assert record["data"]["valid_record_count"] == 1
    assert record["data"]["invalid_record_count"] >= 1
