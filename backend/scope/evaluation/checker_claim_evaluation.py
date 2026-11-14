"""Deterministic negative-path evaluation for claim-level evidence checking."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from scope.config.loader import get_project_root
from scope.evidence.claims import verify_claims


def _evaluation_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for i in range(10):
        text = f"The review window is {i + 1} business days."
        cases.append(
            {
                "case_id": f"supported_{i + 1}",
                "category": "supported",
                "expected_supported": True,
                "claim": {"text": text, "chunk_ids": [f"supported::{i}"]},
                "hit": {"chunk_id": f"supported::{i}", "text": text},
            }
        )

    unsupported_labels = [
        "guaranteed premium status",
        "automatic gold status",
        "unconditional priority approval",
        "certified preferred supplier status",
        "immediate contract renewal",
        "risk-free shipment status",
        "guaranteed service credit",
        "automatic penalty waiver",
        "approved exception status",
        "unlimited expedited service",
    ]
    for i, label in enumerate(unsupported_labels):
        cases.append(
            {
                "case_id": f"unsupported_{i + 1}",
                "category": "unsupported",
                "expected_supported": False,
                "claim": {
                    "text": f"The shipment qualifies for {label}.",
                    "chunk_ids": [f"unrelated::{i}"],
                },
                "hit": {
                    "chunk_id": f"unrelated::{i}",
                    "text": "Escalate delayed ocean shipments to procurement for review.",
                },
            }
        )

    for i in range(10):
        text = f"Supplier notice is required within {i + 1} days."
        cases.append(
            {
                "case_id": f"uncited_{i + 1}",
                "category": "uncited",
                "expected_supported": False,
                "claim": {"text": text, "chunk_ids": []},
                "hit": {"chunk_id": f"available::{i}", "text": text},
            }
        )

    for i in range(10):
        text = f"Temperature must remain below {i + 2} degrees."
        cases.append(
            {
                "case_id": f"unknown_citation_{i + 1}",
                "category": "unknown_citation",
                "expected_supported": False,
                "claim": {"text": text, "chunk_ids": [f"missing::{i}"]},
                "hit": {"chunk_id": f"available_temp::{i}", "text": text},
            }
        )

    for i in range(10):
        stated = 48 + i
        supported = stated + 24
        cases.append(
            {
                "case_id": f"wrong_number_{i + 1}",
                "category": "wrong_number",
                "expected_supported": False,
                "claim": {
                    "text": f"A delay must be reported within {stated} hours.",
                    "chunk_ids": [f"numeric::{i}"],
                },
                "hit": {
                    "chunk_id": f"numeric::{i}",
                    "text": f"A delay must be reported within {supported} hours.",
                },
            }
        )
    return cases


def evaluate_claim_checker() -> dict[str, Any]:
    """Run 50 labelled claim/passage cases through the production verifier."""
    cases = _evaluation_cases()
    rows: list[dict[str, Any]] = []
    for case in cases:
        result = verify_claims([case["claim"]], [case["hit"]])
        verdict = result["verdicts"][0]
        rows.append(
            {
                "case_id": case["case_id"],
                "category": case["category"],
                "expected_supported": case["expected_supported"],
                "predicted_supported": verdict["ok"],
                "status": verdict["status"],
                "support": verdict["support"],
                "notes": verdict["notes"],
            }
        )

    positives = [row for row in rows if row["expected_supported"]]
    negatives = [row for row in rows if not row["expected_supported"]]
    false_positives = sum(row["predicted_supported"] for row in negatives)
    false_negatives = sum(not row["predicted_supported"] for row in positives)
    by_category: dict[str, Any] = {}
    counts = Counter(row["category"] for row in rows)
    for category, total in counts.items():
        category_rows = [row for row in rows if row["category"] == category]
        by_category[category] = {
            "cases": total,
            "correct": sum(row["predicted_supported"] == row["expected_supported"] for row in category_rows),
            "rejected": sum(not row["predicted_supported"] for row in category_rows),
            "status_counts": dict(Counter(row["status"] for row in category_rows)),
        }

    return {
        "evaluation": "synthetic claim-level checker negative-path evaluation",
        "method": "Each labelled claim and its retrieved passage are evaluated with production verify_claims().",
        "n_cases": len(rows),
        "n_supported": len(positives),
        "n_unsupported": len(negatives),
        "detection_rate": (len(negatives) - false_positives) / len(negatives) if negatives else None,
        "false_positive_rate": false_positives / len(negatives) if negatives else None,
        "supported_claim_false_rejection_rate": false_negatives / len(positives) if positives else None,
        "accuracy": sum(row["predicted_supported"] == row["expected_supported"] for row in rows) / len(rows) if rows else None,
        "by_category": by_category,
        "cases": rows,
        "limitation": "Small deterministic synthetic fixture; these rates measure wiring and known failure modes, not real-world semantic accuracy.",
    }


def main() -> None:
    result = evaluate_claim_checker()
    output = get_project_root() / "reports" / "metrics" / "checker_claim_evaluation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    summary = {key: result[key] for key in ("n_cases", "n_supported", "n_unsupported", "detection_rate", "false_positive_rate", "supported_claim_false_rejection_rate", "accuracy")}
    print(json.dumps({"report": str(output), **summary}, indent=2))


if __name__ == "__main__":
    main()
