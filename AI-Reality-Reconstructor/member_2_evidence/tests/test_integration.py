"""Integration tests verifying dispatcher routing, schema validation, and Member 6 pipeline adapter."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import pytest

from member_2_evidence.processors.dispatcher import dispatch_process, identify_evidence_type
from member_2_evidence.processors.adapter import RealEvidenceProcessor, create_adapter_bundle
from member_2_evidence.validate_evidence import validate_evidence_file, validate_record


@dataclass(frozen=True)
class MockEvidenceInput:
    id: str
    filename: str
    content_type: str
    sha256: str
    storage_path: Path
    metadata: dict[str, Any]


def test_dispatcher_modalities(
    synthetic_image_no_exif: Path,
    synthetic_video: Path,
    synthetic_text_pdf: Path,
    synthetic_sensor_csv: Path,
    tmp_path: Path,
):
    shared_out = tmp_path / "evidence.json"

    # 1. Image
    assert identify_evidence_type(synthetic_image_no_exif) == "image"
    img_rec = dispatch_process(synthetic_image_no_exif, case_id="case-int", shared_output_path=shared_out)
    assert img_rec["type"] == "image"

    # 2. Video
    assert identify_evidence_type(synthetic_video) == "video"
    vid_rec, f_recs = dispatch_process(synthetic_video, case_id="case-int", shared_output_path=shared_out)
    assert vid_rec["type"] == "video"
    assert len(f_recs) > 0

    # 3. Document
    assert identify_evidence_type(synthetic_text_pdf) == "document"
    doc_rec = dispatch_process(synthetic_text_pdf, case_id="case-int", shared_output_path=shared_out)
    assert doc_rec["type"] == "document"

    # 4. Sensor
    assert identify_evidence_type(synthetic_sensor_csv) == "sensor"
    sen_rec = dispatch_process(synthetic_sensor_csv, case_id="case-int", shared_output_path=shared_out)
    assert sen_rec["type"] == "sensor"

    # Check shared evidence file validity
    is_valid, errors, total = validate_evidence_file(shared_out)
    assert is_valid, f"Validation errors: {errors}"
    assert total >= 4


def test_real_evidence_processor_adapter(
    synthetic_image_no_exif: Path,
    synthetic_sensor_csv: Path,
    tmp_path: Path,
):
    inputs = [
        MockEvidenceInput(
            id="ev-img-001",
            filename="test_img.png",
            content_type="image/png",
            sha256="abc1234",
            storage_path=synthetic_image_no_exif,
            metadata={},
        ),
        MockEvidenceInput(
            id="ev-sen-002",
            filename="sensor.csv",
            content_type="text/csv",
            sha256="def5678",
            storage_path=synthetic_sensor_csv,
            metadata={},
        ),
    ]

    out_file = tmp_path / "adapter_evidence.json"
    adapter = RealEvidenceProcessor(output_path=out_file)
    result = adapter.process(case_id="case-adapt-1", evidence=inputs)

    assert result.adapter_mode == "real"
    assert len(result.records) == 2
    rec_ids = {r.evidence_id for r in result.records}
    assert rec_ids == {"ev-img-001", "ev-sen-002"}
    assert all(r.outcome == "available" for r in result.records)


def test_member_6_backend_pipeline_with_real_adapter(tmp_path: Path, monkeypatch):
    """Test full integration with Member 6 backend pipeline in real adapter mode."""
    try:
        from member_6_backend.config import settings
        from member_6_backend.database.models import Base, CaseRecord, EvidenceRecord, JobRecord
        from member_6_backend.database.session import initialize_database
        from member_6_backend.orchestration import pipeline
        from member_6_backend.services import adapters
        from member_6_backend.storage.local import storage
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
    except ImportError:
        pytest.skip("member_6_backend not in python path for pipeline test")

    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)
    factory = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)

    from member_6_backend.database import session as db_session
    monkeypatch.setattr(db_session, "engine", test_engine)
    monkeypatch.setattr(db_session, "SessionLocal", factory)
    monkeypatch.setattr(pipeline, "SessionLocal", factory)
    monkeypatch.setattr(storage, "root", (tmp_path / "evidence_store").resolve())

    # Store a synthetic evidence file in storage
    test_file = tmp_path / "test.csv"
    test_file.write_text("timestamp,temperature\n2026-10-25T10:00:00,21.5\n")
    storage_key = storage.put(test_file.read_bytes())

    case_id = "test-pipeline-case"
    job_id = "test-job-001"
    ev_id = "test-ev-001"

    with factory() as session:
        session.add(CaseRecord(id=case_id, title="Test Pipeline Case"))
        session.add(
            EvidenceRecord(
                id=ev_id,
                case_id=case_id,
                filename="test.csv",
                content_type="text/csv",
                size_bytes=len(test_file.read_bytes()),
                sha256="dummy_sha256",
                storage_key=storage_key,
                metadata_json={},
            )
        )
        session.add(
            JobRecord(
                id=job_id,
                case_id=case_id,
                status="queued",
                current_stage="queued",
                adapter_mode="real",
                stage_outcomes=[],
            )
        )
        session.commit()

    # Configure real adapter bundle
    real_bundle = create_adapter_bundle()
    monkeypatch.setattr(pipeline, "load_adapters", lambda: real_bundle)

    # Run the Member 6 pipeline
    pipeline.run_case_pipeline(case_id, job_id)

    # Verify job completed successfully
    with factory() as session:
        job = session.get(JobRecord, job_id)
        assert job is not None
        assert job.status == "completed"
        assert job.adapter_mode == "real"
        assert job.error_code is None
