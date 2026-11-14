from __future__ import annotations

from scope.evaluation.checker_claim_evaluation import (
    evaluate_claim_checker,
    evaluate_corpus_claim_checker,
)
from scope.evidence.claims import verify_claim
from scope.rag.answer import Claim, GroundedAnswer
from scope.agents import workflow


def test_claim_checker_negative_path_evaluation() -> None:
    result = evaluate_claim_checker()
    assert result["n_cases"] == 50
    assert result["detection_rate"] == 1.0
    assert result["false_positive_rate"] == 0.0
    assert result["supported_claim_false_rejection_rate"] == 0.0
    assert set(result["by_category"]) == {
        "supported",
        "unsupported",
        "uncited",
        "unknown_citation",
        "wrong_number",
    }


def test_corpus_checker_evaluation_uses_real_indexed_document_passages() -> None:
    result = evaluate_corpus_claim_checker()
    assert result["n_source_claims"] > 50
    assert result["n_cases"] > 100
    assert "SYNTHETIC_shipping_sla.md" in result["source_documents"]
    assert result["by_category"]["corpus_wrong_number"]["cases"] > 0
    assert result["by_category"]["corpus_unknown_citation"]["correct"] == result["n_source_claims"]


def test_answer_displays_only_supported_claims_and_exposes_verdicts() -> None:
    answer = GroundedAnswer(
        query="What is the review period?",
        claims=[
            Claim("The review period is 30 days.", [1], ["policy::c1"]),
            Claim("The review period is 300 days.", [1], ["policy::c1"], generator="llm:test"),
        ],
        citations=[],
        retrieved=[
            {
                "chunk_id": "policy::c1",
                "text": "The review period is 30 days.",
            }
        ],
        grounded=True,
        generator="test",
    )

    result = answer.to_dict()
    assert result["grounded"] is False
    assert "30 days" in result["answer"]
    assert "300 days" not in result["answer"]
    assert [claim["verification"]["status"] for claim in result["claims"]] == [
        "supported",
        "numeric_mismatch",
    ]


def test_supported_sentence_is_not_penalized_by_long_passage() -> None:
    claim = "The review window is 30 days."
    verdict = verify_claim(
        claim,
        ["policy::c1"],
        {"policy::c1": f"Unrelated introductory wording. {claim} More unrelated text."},
    )
    assert verdict.status == "supported"


def test_mixed_known_and_unknown_citations_are_rejected() -> None:
    verdict = verify_claim(
        "The review window is 30 days.",
        ["policy::c1", "fabricated::c1"],
        {"policy::c1": "The review window is 30 days."},
    )
    assert verdict.status == "citation_not_retrieved"


def test_investigation_checker_downgrades_unsupported_claim(monkeypatch) -> None:
    persisted: list[tuple[str, str]] = []
    monkeypatch.setattr(
        workflow,
        "run_checker",
        lambda evidence_ids: {
            "checked": 1,
            "validated": 1,
            "needs_review": 0,
            "results": [{"evidence_id": "e1", "status": "validated", "notes": "ok"}],
        },
    )
    monkeypatch.setattr(
        workflow,
        "update_validation",
        lambda evidence_id, status, notes: persisted.append((evidence_id, status)),
    )

    result = workflow.checker_node(
        {
            "evidence_ids": ["e1"],
            "claim_evidence_ids": ["e1"],
            "document_findings": {
                "claims": [
                    {"text": "The shipment has guaranteed premium status.", "chunk_ids": ["policy::c1"]}
                ],
                "retrieved": [
                    {"chunk_id": "policy::c1", "text": "Escalate delayed ocean shipments to procurement."}
                ],
            },
        }
    )

    assert result["status"] == "needs_review"
    assert result["checker_result"]["claim_verification"]["needs_review"] == 1
    assert result["checker_result"]["results"][0]["status"] == "needs_review"
    assert persisted == [("e1", "needs_review")]
