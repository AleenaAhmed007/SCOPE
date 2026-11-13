"""Phase 10 — Checker: validate claims against evidence and numeric payloads."""

from __future__ import annotations

import re
from typing import Any

import json
import uuid

from scope.db.models import ValidationRun
from scope.db.session import get_session, init_db
from scope.evidence.ledger import list_evidence, update_validation


def validate_numeric_claim(claim: str, payload: dict[str, Any]) -> tuple[bool, str]:
    """Check that numbers mentioned in the claim appear in payload (loose validation)."""
    numbers = re.findall(r"-?\d+\.?\d*", claim)
    if not numbers:
        return True, "No numeric claims to verify"
    payload_str = str(payload)
    missing = [n for n in numbers if n not in payload_str]
    if missing:
        return False, f"Numeric values not found in payload: {missing}"
    return True, "Numeric values found in evidence payload"


def validate_citation(evidence: dict[str, Any]) -> tuple[bool, str]:
    if evidence.get("evidence_type") == "document" and not evidence.get("source"):
        return False, "Document evidence missing source"
    if evidence.get("synthetic_source"):
        return True, "Synthetic source labeled correctly — treat as non-authoritative"
    return True, "Source present"


def run_checker(evidence_ids: list[str] | None = None) -> dict[str, Any]:
    items = list_evidence(limit=500)
    if evidence_ids:
        items = [e for e in items if e["evidence_id"] in evidence_ids]

    results = []
    unsupported = 0
    for e in items:
        ok_num, note_num = validate_numeric_claim(e["claim"], e.get("payload") or {})
        ok_cite, note_cite = validate_citation(e)
        ok = ok_num and ok_cite
        status = "validated" if ok else "needs_review"
        notes = f"{note_num}; {note_cite}"
        update_validation(e["evidence_id"], status, notes)
        if not ok:
            unsupported += 1
        results.append(
            {
                "evidence_id": e["evidence_id"],
                "status": status,
                "notes": notes,
            }
        )
    summary = {
        "checked": len(results),
        "needs_review": unsupported,
        "validated": len(results) - unsupported,
        "results": results,
    }
    init_db()
    session = get_session()
    try:
        session.add(
            ValidationRun(
                run_id=str(uuid.uuid4()),
                checked=summary["checked"],
                validated=summary["validated"],
                needs_review=summary["needs_review"],
                result_json=json.dumps(summary, default=str),
            )
        )
        session.commit()
    finally:
        session.close()
    return summary
