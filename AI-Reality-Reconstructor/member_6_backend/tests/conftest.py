from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from member_6_backend.database.models import Base
from member_6_backend.database import session as db_session
from member_6_backend.main import app
from member_6_backend.orchestration import pipeline
from member_6_backend.storage.local import storage


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)
    factory = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(db_session, "engine", test_engine)
    monkeypatch.setattr(db_session, "SessionLocal", factory)
    monkeypatch.setattr(pipeline, "SessionLocal", factory)
    monkeypatch.setattr(storage, "root", tmp_path.resolve())
    with TestClient(app) as test_client:
        yield test_client
    test_engine.dispose()


def create_case(client, title="Example"):
    response = client.post("/api/v1/cases", json={"title": title, "description": "test"})
    assert response.status_code == 201
    return response.json()["data"]["id"]
