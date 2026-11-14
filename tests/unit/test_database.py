"""Database configuration must never resolve to a non-PostgreSQL backend."""

from __future__ import annotations

import pytest

from scope.db import session as db_session
from scope.db.session import DEFAULT_POSTGRES_URL, resolve_database_url


def test_default_database_is_postgresql() -> None:
    assert resolve_database_url() == DEFAULT_POSTGRES_URL


def test_plain_postgresql_url_uses_psycopg_driver() -> None:
    assert resolve_database_url("postgresql://user:pass@localhost:5432/scope") == (
        "postgresql+psycopg://user:pass@localhost:5432/scope"
    )


@pytest.mark.parametrize("url", ["sqlite:///local.db", "mysql://user:pass@localhost/db"])
def test_non_postgresql_urls_are_rejected(url: str) -> None:
    with pytest.raises(ValueError, match="PostgreSQL is required"):
        resolve_database_url(url)


def test_sqlite_environment_url_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SCOPE_DATABASE_URL", "sqlite:///local.db")
    with pytest.raises(ValueError, match="PostgreSQL is required"):
        resolve_database_url()


def test_database_url_environment_alias_is_supported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SCOPE_DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/scope")
    assert resolve_database_url() == "postgresql+psycopg://user:pass@localhost:5432/scope"


def test_postgresql_connection_failure_does_not_fall_back(monkeypatch: pytest.MonkeyPatch) -> None:
    class UnavailableEngine:
        def connect(self):
            raise OSError("connection refused")

    monkeypatch.setattr(db_session, "get_engine", lambda _url=None: UnavailableEngine())
    with pytest.raises(RuntimeError, match="does not fall back to another database"):
        db_session.init_db(DEFAULT_POSTGRES_URL)
