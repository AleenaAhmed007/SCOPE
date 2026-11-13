"""Phase 10 — Evidence Ledger (SQLAlchemy; PostgreSQL preferred)."""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import select

from scope.db.models import EvidenceRecord
from scope.db.session import get_session, init_db


def add_evidence(
    evidence_type: str,
    source: str,
    claim: str,
    related_order_id: str | None = None,
    related_vendor: str | None = None,
    document_page: str | None = None,
    model_version: str | None = None,
    payload: dict[str, Any] | None = None,
    synthetic_source: bool = False,
) -> dict[str, Any]:
    init_db()
    session = get_session()
    try:
        eid = str(uuid.uuid4())
        rec = EvidenceRecord(
            evidence_id=eid,
            evidence_type=evidence_type,
            source=source,
            related_order_id=related_order_id,
            related_vendor=related_vendor,
            document_page=document_page,
            model_version=model_version,
            claim=claim,
            payload_json=json.dumps(payload or {}, default=str),
            validation_status="pending",
            synthetic_source=synthetic_source,
        )
        session.add(rec)
        session.commit()
        return record_to_dict(rec)
    finally:
        session.close()


def record_to_dict(rec: EvidenceRecord) -> dict[str, Any]:
    return {
        "evidence_id": rec.evidence_id,
        "evidence_type": rec.evidence_type,
        "source": rec.source,
        "related_order_id": rec.related_order_id,
        "related_vendor": rec.related_vendor,
        "document_page": rec.document_page,
        "model_version": rec.model_version,
        "claim": rec.claim,
        "payload": json.loads(rec.payload_json or "{}"),
        "validation_status": rec.validation_status,
        "validation_notes": rec.validation_notes,
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
        "synthetic_source": rec.synthetic_source,
    }


def list_evidence(limit: int = 100) -> list[dict[str, Any]]:
    init_db()
    session = get_session()
    try:
        rows = session.execute(select(EvidenceRecord).limit(limit)).scalars().all()
        return [record_to_dict(r) for r in rows]
    finally:
        session.close()


def update_validation(evidence_id: str, status: str, notes: str) -> dict[str, Any] | None:
    init_db()
    session = get_session()
    try:
        rec = session.get(EvidenceRecord, evidence_id)
        if not rec:
            return None
        rec.validation_status = status
        rec.validation_notes = notes
        session.commit()
        return record_to_dict(rec)
    finally:
        session.close()
