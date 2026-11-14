"""Phase 10 — Checker: validate claims against evidence and numeric payloads."""

from __future__ import annotations

import re
from typing import Any

import json
import uuid

from scope.db.models import ValidationRun
from scope.db.session import get_session, init_db
from scope.evidence.ledger import list_evidence, update_validation


_NUMBER = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w.]*\d)")


def _payload_numbers(value: Any) -> list[float]:
    """All numeric values in a (nested) payload, including numeric strings."""
    if isinstance(value, bool):
        return [float(value)]
    if isinstance(value, (int, float)):
        return [float(value)]
    if isinstance(value, dict):
        return [n for v in value.values() for n in _payload_numbers(v)]
    if isinstance(value, (list, tuple, set)):
        return [n for v in value for n in _payload_numbers(v)]
    if isinstance(value, str):
        out = []
        for token in _NUMBER.findall(value):
            try:
                out.append(float(token))
            except ValueError:
                pass
        return out
    try:  # numpy scalars
        return [float(value)]
    except (TypeError, ValueError):
        return []


def validate_numeric_claim(claim: str, payload: dict[str, Any]) -> tuple[bool, str]:
    """Check every number in the claim against the payload's numeric values.

    A claimed number is supported when some payload value rounds to it at the
    precision the claim states (``0.005`` matches ``0.004736``; ``0.5`` does
    not match ``0.55``). The previous substring check rejected correctly
    rounded values and accepted any digit sequence found anywhere.
    """
    tokens = _NUMBER.findall(claim)
    if not tokens:
        return True, "No numeric claims to verify"
    values = _payload_numbers(payload)
    missing = []
    for token in tokens:
        claimed = float(token)
        decimals = len(token.split(".")[1]) if "." in token else 0
        half_unit = 0.5 * 10 ** (-decimals)
        supported = any(
            abs(v - claimed) < half_unit or f"{v:.{decimals}f}" == f"{claimed:.{decimals}f}"
            for v in values
        )
        if not supported:
            missing.append(token)
    if missing:
        return False, f"Numeric values not supported by payload: {missing}"
    return True, "All numeric values match the evidence payload (at stated precision)"


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
