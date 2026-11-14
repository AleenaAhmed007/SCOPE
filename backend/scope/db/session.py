"""PostgreSQL-only SQLAlchemy session factory."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from scope.logging_config import setup_logging

logger = setup_logging()

# Load the repository-root .env for local development. Existing process
# environment variables keep precedence over values from the file.
load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=False)

DEFAULT_POSTGRES_URL = "postgresql+psycopg://scope:scope@127.0.0.1:5432/scope"


def _require_postgres_url(url: str) -> str:
    """Validate and normalize a PostgreSQL connection URL."""
    try:
        parsed = make_url(url)
    except Exception as exc:
        raise ValueError("Invalid SCOPE_DATABASE_URL; expected a PostgreSQL URL.") from exc

    if parsed.drivername == "postgresql":
        parsed = parsed.set(drivername="postgresql+psycopg")
    elif not parsed.drivername.startswith("postgresql+"):
        raise ValueError(
            "PostgreSQL is required. SQLite and other database backends are not supported."
        )
    return parsed.render_as_string(hide_password=False)


def resolve_database_url(url: str | None = None) -> str:
    """Resolve the explicit URL, environment URL, or PostgreSQL default only."""
    configured = (
        url
        or os.getenv("SCOPE_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or DEFAULT_POSTGRES_URL
    )
    return _require_postgres_url(configured)


def get_engine(url: str | None = None) -> Engine:
    db_url = resolve_database_url(url)
    return create_engine(db_url, future=True, pool_pre_ping=True)


def get_session(url: str | None = None) -> Session:
    engine = get_engine(url)
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)()


def init_db(url: str | None = None) -> str:
    """Initialize application tables on PostgreSQL or fail without fallback."""
    from scope.db import models  # noqa: F401 - register ORM mappers
    from scope.db.models import Base

    db_url = resolve_database_url(url)
    engine = get_engine(db_url)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        Base.metadata.create_all(engine)
    except Exception as exc:
        safe_host = make_url(db_url).host or "configured PostgreSQL host"
        raise RuntimeError(
            f"PostgreSQL at {safe_host} is required but unavailable. Start PostgreSQL and "
            "verify SCOPE_DATABASE_URL; SCOPE does not fall back to another database."
        ) from exc

    logger.info("PostgreSQL initialised: %s", make_url(db_url).host or "local server")
    return db_url
