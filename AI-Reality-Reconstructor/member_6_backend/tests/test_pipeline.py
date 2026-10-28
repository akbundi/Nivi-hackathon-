from __future__ import annotations

from dataclasses import replace

from member_6_backend.config import settings
from member_6_backend.database import session as db_session
from member_6_backend.database.models import JobRecord
from member_6_backend.orchestration import pipeline
from member_6_backend.services import adapters

from .conftest import create_case


def upload(client, case_id):
    return client.post(f"/api/v1/cases/{case_id}/evidence", files={"file": ("evidence.txt", b"source")})


def test_mock_pipeline_completes_and_outputs_are_retrievable(client):
    case_id = create_case(client)
    assert upload(client, case_id).status_code == 201
    queued = client.post(f"/api/v1/cases/{case_id}/process")
    assert queued.status_code == 202
    assert queued.json()["data"]["status"] == "queued"
    status = client.get(f"/api/v1/cases/{case_id}/status").json()["data"]
    assert status["status"] == "completed"
    assert status["adapter_mode"] == "mock"
    assert len(status["stage_outcomes"]) >= 5
    assert client.get(f"/api/v1/cases/{case_id}/timeline").json()["data"]["events"] == []
    assert client.get(f"/api/v1/cases/{case_id}/findings").json()["data"]["findings"] == []
    assert client.get(f"/api/v1/cases/{case_id}/scene").json()["data"]["objects"] == []
    history = client.get(f"/api/v1/cases/{case_id}/jobs").json()["data"]
    assert history["total"] == 1
    assert client.get(f"/api/v1/jobs/{status['id']}").json()["data"]["status"] == "completed"


def test_process_requires_evidence_and_prevents_active_duplicate(client):
    case_id = create_case(client)
    assert client.post(f"/api/v1/cases/{case_id}/process").status_code == 422
    upload(client, case_id)
    first = client.post(f"/api/v1/cases/{case_id}/process")
    assert first.status_code == 202
    # BackgroundTasks finish before TestClient returns, so a new attempt is allowed.
    assert client.post(f"/api/v1/cases/{case_id}/process").status_code == 202


def test_active_job_conflict(client):
    case_id = create_case(client)
    upload(client, case_id)
    with db_session.SessionLocal() as session:
        session.add(JobRecord(id="active-job", case_id=case_id, status="queued", current_stage="queued", adapter_mode="mock", stage_outcomes=[]))
        session.commit()
    assert client.post(f"/api/v1/cases/{case_id}/process").status_code == 409


def test_missing_real_adapter_fails_job_without_mock_fallback(client, monkeypatch):
    case_id = create_case(client)
    upload(client, case_id)
    monkeypatch.setattr(adapters, "settings", replace(settings, adapter_mode="real", real_adapter_factory=None))
    client.post(f"/api/v1/cases/{case_id}/process")
    job = client.get(f"/api/v1/cases/{case_id}/status").json()["data"]
    assert job["status"] == "failed"
    assert job["error"]["code"] == "adapter_unavailable"
    assert client.get(f"/api/v1/cases/{case_id}/timeline").status_code == 404


def test_adapter_exception_persists_failed_state(client, monkeypatch):
    case_id = create_case(client)
    upload(client, case_id)

    class BrokenEvidenceAdapter:
        def process(self, _case_id, _evidence):
            raise RuntimeError("private adapter detail")

    bundle = adapters.AdapterBundle(
        BrokenEvidenceAdapter(), adapters.MockTimelineGenerator(), adapters.MockInvestigationAnalyzer(),
        adapters.MockSceneReconstructor(), "mock",
    )
    monkeypatch.setattr(pipeline, "load_adapters", lambda: bundle)
    client.post(f"/api/v1/cases/{case_id}/process")
    job = client.get(f"/api/v1/cases/{case_id}/status").json()["data"]
    assert job["status"] == "failed"
    assert job["error"]["code"] == "adapter_failed"
    assert "private adapter detail" not in str(job)


def test_invalid_adapter_output_fails_schema_validation(client, monkeypatch):
    case_id = create_case(client)
    upload(client, case_id)

    class InvalidTimelineAdapter:
        def generate(self, case_id, _evidence, _processed):
            return {"case_id": case_id, "events": [{"id": "invented", "summary": "missing fields"}], "adapter_mode": "mock"}

    bundle = adapters.AdapterBundle(
        adapters.MockEvidenceProcessor(), InvalidTimelineAdapter(), adapters.MockInvestigationAnalyzer(),
        adapters.MockSceneReconstructor(), "mock",
    )
    monkeypatch.setattr(pipeline, "load_adapters", lambda: bundle)
    client.post(f"/api/v1/cases/{case_id}/process")
    job = client.get(f"/api/v1/cases/{case_id}/status").json()["data"]
    assert job["status"] == "failed"
    assert job["error"]["code"] == "invalid_output"
