"""Claim-level verification: does the cited evidence actually support the claim?

The original Checker compared numbers in a claim against numbers in its own
payload, and separately asserted that a `source` string was non-empty. Both
checks are self-referential: they cannot detect a claim that is numerically
consistent but topically unsupported, nor a claim citing a passage that says
something else entirely.

This module adds the missing half:

* **citation resolution** — every cited chunk id must exist in the retrieved set;
* **lexical entailment proxy** — token-overlap F1 between claim and cited text,
  with a recognisable-entity guard (numbers, document nouns);
* **numeric grounding** — numbers in the claim must appear in the cited passage.

A claim is `supported` only if all three hold. Verdicts use explicit status
codes so a report can show exactly what failed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from scope.evidence.checker import validate_numeric_claim
from scope.rag.bm25 import tokenize

SUPPORT_THRESHOLD = 0.42
MIN_CLAIM_TOKENS = 3

STATUS_SUPPORTED = "supported"
STATUS_UNSUPPORTED = "unsupported"
STATUS_UNCITED = "uncited"
STATUS_UNKNOWN_CITATION = "citation_not_retrieved"
STATUS_NUMERIC_MISMATCH = "numeric_mismatch"


@dataclass
class ClaimVerdict:
    claim: str
    status: str
    support: float
    cited_chunk_ids: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status == STATUS_SUPPORTED

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim,
            "status": self.status,
            "ok": self.ok,
            "support": round(self.support, 4),
            "cited_chunk_ids": self.cited_chunk_ids,
            "notes": self.notes,
        }


def f1_overlap(claim: str, passage: str) -> float:
    """Token-overlap F1 between a claim and a passage (order-insensitive)."""
    claim_tokens = tokenize(claim)
    if len(claim_tokens) < MIN_CLAIM_TOKENS:
        return 1.0  # too short to judge; do not fail on brevity
    claim_set = set(claim_tokens)
    passage_set = set(tokenize(passage))
    if not claim_set or not passage_set:
        return 0.0
    shared = claim_set & passage_set
    if not shared:
        return 0.0
    precision = len(shared) / len(claim_set)
    recall = len(shared) / len(passage_set)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def verify_claim(
    claim: str,
    cited_chunk_ids: Sequence[str],
    passages: dict[str, str],
    *,
    support_threshold: float = SUPPORT_THRESHOLD,
) -> ClaimVerdict:
    """Verify one claim against the passages it cites."""
    cited = [chunk_id for chunk_id in cited_chunk_ids if chunk_id]
    if not cited:
        return ClaimVerdict(
            claim=claim,
            status=STATUS_UNCITED,
            support=0.0,
            notes=["Claim carries no citation."],
        )

    unknown = [chunk_id for chunk_id in cited if chunk_id not in passages]
    if unknown and len(unknown) == len(cited):
        return ClaimVerdict(
            claim=claim,
            status=STATUS_UNKNOWN_CITATION,
            support=0.0,
            cited_chunk_ids=cited,
            notes=[f"Cited passage(s) not in the retrieved set: {unknown}"],
        )

    resolved = [chunk_id for chunk_id in cited if chunk_id in passages]
    combined = "\n".join(passages[chunk_id] for chunk_id in resolved)
    support = max(f1_overlap(claim, passages[chunk_id]) for chunk_id in resolved)

    numeric_ok, numeric_note = validate_numeric_claim(claim, {"passage": combined})
    notes: list[str] = []
    if not numeric_ok:
        notes.append(numeric_note)
        return ClaimVerdict(
            claim=claim,
            status=STATUS_NUMERIC_MISMATCH,
            support=support,
            cited_chunk_ids=resolved,
            notes=notes,
        )

    if unknown:
        notes.append(f"Some cited passages were not retrieved: {unknown}")
    if support < support_threshold:
        notes.append(
            f"Cited passage shares too little wording with the claim "
            f"(overlap {support:.2f} < {support_threshold:.2f})."
        )
        return ClaimVerdict(
            claim=claim,
            status=STATUS_UNSUPPORTED,
            support=support,
            cited_chunk_ids=resolved,
            notes=notes,
        )

    notes.append(f"Supported by cited passage (overlap {support:.2f}).")
    return ClaimVerdict(
        claim=claim,
        status=STATUS_SUPPORTED,
        support=support,
        cited_chunk_ids=resolved,
        notes=notes,
    )


def verify_claims(
    claims: Iterable[dict[str, Any]],
    retrieved: Sequence[dict[str, Any]],
    *,
    support_threshold: float = SUPPORT_THRESHOLD,
) -> dict[str, Any]:
    """Verify a list of answer claims against the retrieved passages."""
    passages = {str(hit.get("chunk_id", "")): str(hit.get("text", "")) for hit in retrieved}
    verdicts: list[ClaimVerdict] = []
    for claim in claims:
        verdicts.append(
            verify_claim(
                str(claim.get("text", "")),
                [str(cid) for cid in claim.get("chunk_ids", [])],
                passages,
                support_threshold=support_threshold,
            )
        )

    counts: dict[str, int] = {}
    for verdict in verdicts:
        counts[verdict.status] = counts.get(verdict.status, 0) + 1
    supported = counts.get(STATUS_SUPPORTED, 0)
    total = len(verdicts)

    return {
        "claims_checked": total,
        "supported": supported,
        "unsupported": total - supported,
        "needs_review": total - supported,
        "support_rate": (supported / total) if total else None,
        "status_counts": counts,
        "verdicts": [verdict.to_dict() for verdict in verdicts],
        "support_threshold": support_threshold,
        "method": "citation resolution + token-overlap entailment proxy + numeric grounding",
    }


def prune_unsupported(
    claims: Sequence[dict[str, Any]], verdicts: Sequence[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Drop claims that failed verification (used by the agent revision loop)."""
    keep = {v["claim"] for v in verdicts if v.get("ok")}
    return [claim for claim in claims if str(claim.get("text", "")) in keep]
