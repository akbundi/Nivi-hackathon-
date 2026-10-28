from __future__ import annotations

from dataclasses import replace

from member_6_backend import config
from member_6_backend.storage.local import storage

from .conftest import create_case


def test_health_and_case_crud_and_pagination(client):
    assert client.get("/api/v1/health/live").json()["data"]["status"] == "ok"
    assert client.get("/api/v1/health/ready").status_code == 200
    first_id = create_case(client, "Alpha case")
    second_id = create_case(client, "Beta case")
    listing = client.get("/api/v1/cases?page=1&page_size=1&search=Alpha").json()["data"]
    assert listing["total"] == 1
    assert listing["items"][0]["id"] == first_id
    assert client.get(f"/api/v1/cases/{first_id}").status_code == 200
    updated = client.patch(f"/api/v1/cases/{first_id}", json={"title": "Renamed"})
    assert updated.json()["data"]["title"] == "Renamed"
    assert client.delete(f"/api/v1/cases/{second_id}").status_code == 204
    assert client.get(f"/api/v1/cases/{second_id}").status_code == 404


def test_evidence_upload_list_metadata_and_original_file(client):
    case_id = create_case(client)
    response = client.post(
        f"/api/v1/cases/{case_id}/evidence",
        files={"file": ("..\\source.txt", b"untouched evidence", "text/plain")},
        data={"metadata": '{"source":"camera card"}'},
    )
    assert response.status_code == 201
    evidence = response.json()["data"]
    assert evidence["filename"] == "source.txt"
    assert evidence["metadata"] == {"source": "camera card"}
    assert client.get(f"/api/v1/evidence/{evidence['id']}").status_code == 200
    listing = client.get(f"/api/v1/cases/{case_id}/evidence?content_type=text/plain").json()["data"]
    assert listing["total"] == 1
    downloaded = client.get(f"/api/v1/evidence/{evidence['id']}/file")
    assert downloaded.content == b"untouched evidence"
    assert client.get("/api/v1/evidence/not-a-real-id/file").status_code == 404


def test_upload_rejects_unsupported_type_and_invalid_metadata(client):
    case_id = create_case(client)
    bad_type = client.post(f"/api/v1/cases/{case_id}/evidence", files={"file": ("payload.exe", b"x")})
    assert bad_type.status_code == 415
    bad_metadata = client.post(
        f"/api/v1/cases/{case_id}/evidence",
        files={"file": ("payload.txt", b"x")},
        data={"metadata": "[]"},
    )
    assert bad_metadata.status_code == 422


def test_upload_enforces_configured_file_size(client, monkeypatch):
    case_id = create_case(client)
    monkeypatch.setattr(config, "settings", replace(config.settings, max_upload_bytes=3))
    response = client.post(f"/api/v1/cases/{case_id}/evidence", files={"file": ("payload.txt", b"four")})
    assert response.status_code == 413


def test_missing_case_and_pagination_validation(client):
    assert client.get("/api/v1/cases/missing").status_code == 404
    assert client.post("/api/v1/cases/missing/evidence", files={"file": ("x.txt", b"x")}).status_code == 404
    assert client.get("/api/v1/cases?page_size=1000").status_code == 422


def test_storage_failure_does_not_leave_metadata(client, monkeypatch):
    case_id = create_case(client)

    def fail_put(_data):
        raise OSError("disk error")

    monkeypatch.setattr(storage, "put", fail_put)
    response = client.post(f"/api/v1/cases/{case_id}/evidence", files={"file": ("evidence.txt", b"data")})
    assert response.status_code == 500
    assert client.get(f"/api/v1/cases/{case_id}/evidence").json()["data"]["total"] == 0
