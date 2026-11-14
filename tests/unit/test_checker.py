"""Checker numeric validation: precision-aware matching against evidence payloads."""

from __future__ import annotations

from scope.evidence.checker import validate_numeric_claim


def test_rounded_value_is_supported() -> None:
    ok, _ = validate_numeric_claim(
        "Order 1 late probability 0.005 (pred=0)",
        {"order_id": 1, "late_probability": 0.004736, "late_prediction": 0},
    )
    assert ok


def test_digit_substring_is_not_support() -> None:
    # Old substring check accepted "0.5" because "0.55" contains it.
    ok, note = validate_numeric_claim("Late rate 0.5", {"late_rate": 0.55})
    assert not ok
    assert "0.5" in note


def test_changed_number_is_unsupported() -> None:
    ok, _ = validate_numeric_claim("Predicted duration 120.0 days", {"predicted_duration_days": 105.0})
    assert not ok


def test_nested_payload_and_identifiers() -> None:
    payload = {"ml": {"scores": [0.12, 0.34]}, "evidence_id": "6e549a1d-f941"}
    assert validate_numeric_claim("Scores 0.12 and 0.34 for 6e549a1d-f941", payload)[0]


def test_claim_without_numbers() -> None:
    assert validate_numeric_claim("Vendor has an escalation clause", {})[0]
