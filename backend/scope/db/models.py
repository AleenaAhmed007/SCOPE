"""PostgreSQL-oriented ORM models for SCOPE metadata (Phases 03–11)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MLExperiment(Base):
    __tablename__ = "ml_experiments"

    experiment_id = Column(String(64), primary_key=True)
    phase = Column(String(32), nullable=False)
    task = Column(String(64), nullable=False)
    model_name = Column(String(64), nullable=False)
    metrics_json = Column(Text, nullable=True)
    artifact_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class ModelVersion(Base):
    __tablename__ = "model_versions"

    version_id = Column(String(64), primary_key=True)
    model_name = Column(String(128), nullable=False)
    task = Column(String(64), nullable=False)
    artifact_path = Column(String(512), nullable=False)
    feature_list_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class ModelMetric(Base):
    __tablename__ = "model_metrics"

    metric_id = Column(String(64), primary_key=True)
    version_id = Column(String(64), nullable=False)
    split_name = Column(String(32), nullable=False)
    metric_name = Column(String(64), nullable=False)
    metric_value = Column(Float, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    prediction_id = Column(String(64), primary_key=True)
    order_id = Column(String(64), nullable=True)
    model_name = Column(String(128), nullable=False)
    prediction_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class EvidenceRecord(Base):
    __tablename__ = "evidence_records"

    evidence_id = Column(String(64), primary_key=True)
    evidence_type = Column(String(64), nullable=False)
    source = Column(String(512), nullable=False)
    related_order_id = Column(String(64), nullable=True)
    related_vendor = Column(String(256), nullable=True)
    document_page = Column(String(64), nullable=True)
    model_version = Column(String(128), nullable=True)
    claim = Column(Text, nullable=False)
    payload_json = Column(Text, nullable=True)
    validation_status = Column(String(32), default="pending")
    validation_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    synthetic_source = Column(Boolean, default=False)


class ClaimRecord(Base):
    __tablename__ = "claims"

    claim_id = Column(String(64), primary_key=True)
    investigation_id = Column(String(64), nullable=True)
    claim_text = Column(Text, nullable=False)
    status = Column(String(32), default="pending")
    created_at = Column(DateTime, default=_utcnow)


class ClaimEvidence(Base):
    __tablename__ = "claim_evidence"

    link_id = Column(String(64), primary_key=True)
    claim_id = Column(String(64), nullable=False)
    evidence_id = Column(String(64), nullable=False)


class ValidationRun(Base):
    __tablename__ = "validation_runs"

    run_id = Column(String(64), primary_key=True)
    checked = Column(Integer, default=0)
    validated = Column(Integer, default=0)
    needs_review = Column(Integer, default=0)
    result_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    run_id = Column(String(64), primary_key=True)
    query = Column(Text, nullable=False)
    order_id = Column(String(64), nullable=True)
    status = Column(String(32), nullable=True)
    report_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class DocumentChunkMeta(Base):
    __tablename__ = "document_chunks"

    chunk_id = Column(String(128), primary_key=True)
    document_id = Column(String(128), nullable=False)
    file_name = Column(String(256), nullable=False)
    source = Column(String(512), nullable=False)
    page = Column(Integer, nullable=True)
    synthetic = Column(Boolean, default=False)
    text_preview = Column(Text, nullable=True)
