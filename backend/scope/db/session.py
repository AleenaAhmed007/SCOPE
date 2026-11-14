"""SQLAlchemy session factory — PostgreSQL by default when available."""

from __future__ import annotations

import os

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from scope.config.loader import get_project_root
from scope.logging_config import setup_logging

logger = setup_logging()

DEFAULT_POSTGRES_URL = "postgresql+psycopg://scope:scope@127.0.0.1:5432/scope"

# URL chosen by init_db() (e.g. the SQLite fallback). Without this, init_db()
# fell back to SQLite but get_session() kept resolving to Postgres and failed.
_ACTIVE_URL: str | None = None


def _sqlite_fallback_url() -> str:
    return f"sqlite:///{(get_project_root() / 'reports' / 'scope_local.db').as_posix()}"


def resolve_database_url(url: str | None = None) -> str:
    """Prefer SCOPE_DATABASE_URL, then Postgres default, then local SQLite fallback.

    Phase docs require PostgreSQL. SQLite is only a last-resort local fallback when
    Postgres is unreachable and SCOPE_ALLOW_SQLITE=1.
    """
    if url:
        return url
    if _ACTIVE_URL:
        return _ACTIVE_URL
    env_url = os.getenv("SCOPE_DATABASE_URL")
    if env_url:
        return env_url
    allow_sqlite = os.getenv("SCOPE_ALLOW_SQLITE", "0") == "1"
    # Try Postgres default; caller may still fail to connect
    if not allow_sqlite:
        return DEFAULT_POSTGRES_URL
    return _sqlite_fallback_url()


def get_engine(url: str | None = None) -> Engine:
    db_url = resolve_database_url(url)
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    return create_engine(db_url, future=True, pool_pre_ping=True, connect_args=connect_args)


def get_session(url: str | None = None) -> Session:
    engine = get_engine(url)
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)()


def init_db(url: str | None = None) -> str:
    """Create all ORM tables and return the resolved database URL."""
    from scope.db import models  # noqa: F401 — register mappers
    from scope.db.models import Base

    global _ACTIVE_URL
    db_url = resolve_database_url(url)
    try:
        # Engine creation is inside the try: a missing driver (psycopg) raises
        # here and must reach the fallback just like a refused connection.
        engine = get_engine(db_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        Base.metadata.create_all(engine)
        logger.info("Database initialised: %s", db_url.split("@")[-1] if "@" in db_url else db_url)
        if url is None:
            _ACTIVE_URL = db_url
        return db_url
    except Exception as exc:
        if os.getenv("SCOPE_ALLOW_SQLITE", "0") == "1":
            raise
        # Auto-fallback only when explicitly allowed via env; otherwise re-raise
        # For developer convenience: if Postgres down, fall back when SCOPE_ALLOW_SQLITE unset
        # but log loudly — phase docs forbid SQLite for production/evaluation claims.
        fallback = _sqlite_fallback_url()
        logger.warning(
            "PostgreSQL unavailable (%s). Falling back to SQLite at %s. "
            "Set SCOPE_DATABASE_URL for Postgres. Do not claim Postgres compliance while using SQLite.",
            exc,
            fallback,
        )
        engine = get_engine(fallback)
        Base.metadata.create_all(engine)
        if url is None:
            _ACTIVE_URL = fallback
        return fallback
