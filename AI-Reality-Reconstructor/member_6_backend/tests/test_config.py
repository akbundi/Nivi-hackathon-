from __future__ import annotations

import pytest
from sqlalchemy.engine import URL, make_url

from member_6_backend.config import _database_url


def test_postgres_url_preserves_and_escapes_special_character_password(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_HOST", "db")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "reality_reconstructor")
    monkeypatch.setenv("DB_USER", "reality_app")
    password = "local@:/#%$password"
    monkeypatch.setenv("DB_PASSWORD", password)

    url = _database_url()

    assert isinstance(url, URL)
    assert url.host == "db"
    assert url.username == "reality_app"
    assert url.password == password
    rendered = url.render_as_string(hide_password=False)
    assert "%40" in rendered and "%3A" in rendered and "%2F" in rendered
    assert make_url(rendered).password == password


def test_postgres_configuration_requires_password_without_echoing_it(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_HOST", "db")
    monkeypatch.setenv("DB_NAME", "reality_reconstructor")
    monkeypatch.setenv("DB_USER", "reality_app")
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    with pytest.raises(ValueError) as error:
        _database_url()

    assert "DB_PASSWORD" in str(error.value)
    assert "local_dev_only_change_me" not in str(error.value)
