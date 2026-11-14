"""Deterministic negative-path evaluation for claim-level evidence checking."""

from __future__ import annotations

import json
import re
import argparse
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scope.config.loader import get_project_root
from scope.evidence.claims import SUPPORT_THRESHOLD, f1_overlap, verify_claims
from scope.rag.bm25 import tokenize
from scope.rag.index import build_chunk_table
from scope.rag.bm25 import BM25Index


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


def evaluate_corpus_claim_checker(max_source_claims: int = 200) -> dict[str, Any]:
    """Evaluate extracted claims and controlled corruptions from indexed documents."""
    chunks = build_chunk_table()
    sources: list[tuple[str, dict[str, Any]]] = []
    seen: set[tuple[str, str]] = set()
    for chunk in chunks:
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", str(chunk.get("text", ""))):
            claim = re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", sentence).strip()
            key = (str(chunk.get("chunk_id", "")), claim)
            if claim.startswith(("|", "#", "```")) or len(tokenize(claim)) < 4 or key in seen:
                continue
            seen.add(key)
            sources.append((claim, chunk))
            if len(sources) >= max_source_claims:
                break
        if len(sources) >= max_source_claims:
            break

    cases: list[dict[str, Any]] = []
    number_pattern = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?")
    for i, (claim, source_chunk) in enumerate(sources):
        chunk_id = str(source_chunk["chunk_id"])
        source_hit = {"chunk_id": chunk_id, "text": str(source_chunk["text"])}
        cases.append({
            "case_id": f"corpus_supported_{i + 1}",
            "category": "corpus_supported",
            "expected_supported": True,
            "claim": {"text": claim, "chunk_ids": [chunk_id]},
            "hit": source_hit,
        })
        cases.append({
            "case_id": f"corpus_uncited_{i + 1}",
            "category": "corpus_uncited",
            "expected_supported": False,
            "claim": {"text": claim, "chunk_ids": []},
            "hit": source_hit,
        })
        cases.append({
            "case_id": f"corpus_unknown_citation_{i + 1}",
            "category": "corpus_unknown_citation",
            "expected_supported": False,
            "claim": {"text": claim, "chunk_ids": [f"not-retrieved::{i}"]},
            "hit": source_hit,
        })

        other = next(
            (
                candidate for candidate in chunks
                if candidate.get("document_id") != source_chunk.get("document_id")
                and f1_overlap(claim, str(candidate.get("text", ""))) < SUPPORT_THRESHOLD
            ),
            None,
        )
        if other is not None:
            cases.append({
                "case_id": f"corpus_unsupported_citation_{i + 1}",
                "category": "corpus_unsupported_citation",
                "expected_supported": False,
                "claim": {"text": claim, "chunk_ids": [str(other["chunk_id"])]},
                "hit": {"chunk_id": str(other["chunk_id"]), "text": str(other["text"])},
            })

        match = number_pattern.search(claim)
        if match:
            token = match.group(0)
            value = float(token)
            replacement_value = value + 1
            passage_text = str(source_chunk["text"])
            while number_pattern.search(passage_text) and any(
                float(found.group(0)) == replacement_value
                for found in number_pattern.finditer(passage_text)
            ):
                replacement_value += 1
            replacement = str(int(replacement_value)) if value.is_integer() else str(round(replacement_value, 3))
            corrupted = claim[: match.start()] + replacement + claim[match.end() :]
            cases.append({
                "case_id": f"corpus_wrong_number_{i + 1}",
                "category": "corpus_wrong_number",
                "expected_supported": False,
                "claim": {"text": corrupted, "chunk_ids": [chunk_id]},
                "hit": source_hit,
            })

    rows: list[dict[str, Any]] = []
    for case in cases:
        verdict = verify_claims([case["claim"]], [case["hit"]])["verdicts"][0]
        rows.append({
            "case_id": case["case_id"],
            "category": case["category"],
            "claim": case["claim"]["text"],
            "chunk_id": case["claim"]["chunk_ids"][0] if case["claim"]["chunk_ids"] else None,
            "expected_supported": case["expected_supported"],
            "predicted_supported": verdict["ok"],
            "status": verdict["status"],
            "support": verdict["support"],
        })

    positives = [row for row in rows if row["expected_supported"]]
    negatives = [row for row in rows if not row["expected_supported"]]
    false_positives = sum(row["predicted_supported"] for row in negatives)
    false_negatives = sum(not row["predicted_supported"] for row in positives)
    by_category: dict[str, Any] = {}
    for category in sorted({row["category"] for row in rows}):
        category_rows = [row for row in rows if row["category"] == category]
        by_category[category] = {
            "cases": len(category_rows),
            "correct": sum(row["predicted_supported"] == row["expected_supported"] for row in category_rows),
            "status_counts": dict(Counter(row["status"] for row in category_rows)),
        }
    return {
        "evaluation": "corpus-grounded claim checker corruption evaluation",
        "method": "Extracted sentences from the current indexed document corpus; tested their source citations and controlled uncited, unknown-citation, cross-document, and numeric corruptions with production verify_claims().",
        "source_documents": sorted({str(chunk["file_name"]) for chunk in chunks}),
        "n_source_claims": len(positives),
        "n_cases": len(rows),
        "n_supported": len(positives),
        "n_unsupported": len(negatives),
        "detection_rate": (len(negatives) - false_positives) / len(negatives) if negatives else None,
        "false_positive_rate": false_positives / len(negatives) if negatives else None,
        "supported_claim_false_rejection_rate": false_negatives / len(positives) if positives else None,
        "accuracy": sum(row["predicted_supported"] == row["expected_supported"] for row in rows) / len(rows) if rows else None,
        "by_category": by_category,
        "cases": rows,
        "limitation": "Claims are extractive and source passages come from the small synthetic project corpus. Corruptions are controlled, not human-authored semantic errors; results do not estimate free-form LLM claim accuracy.",
    }


def evaluate_contractnli_checker(archive_path: str | Path) -> dict[str, Any]:
    """Evaluate the production claim verifier against ContractNLI's human labels.

    The official test split provides document-level Entailment, Contradiction,
    and NotMentioned annotations with evidence sentence spans. For neutral cases,
    a BM25 top sentence simulates retrieved-but-non-gold evidence.
    """
    archive = Path(archive_path)
    with zipfile.ZipFile(archive) as zipped:
        matches = [name for name in zipped.namelist() if name.endswith("/test.json")]
        if not matches:
            raise ValueError("ContractNLI archive does not contain test.json")
        dataset = json.loads(zipped.read(matches[0]))

    labels = dataset["labels"]
    rows: list[dict[str, Any]] = []
    for doc in dataset["documents"]:
        annotations = doc["annotation_sets"][0]["annotations"]
        source_spans = doc["spans"]
        text = str(doc.get("text", ""))
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if len(tokenize(part)) >= 3]
        sentence_index = BM25Index.build(sentences) if sentences else None
        for hypothesis_id, annotation in annotations.items():
            hypothesis = labels[hypothesis_id]["hypothesis"]
            gold = annotation["choice"]
            cited_texts: list[str] = []
            evidence_source = "annotated_evidence"
            if annotation.get("spans"):
                for span_id in annotation["spans"]:
                    start, end = source_spans[span_id]
                    cited_texts.append(text[int(start) : int(end)].strip())
            elif sentence_index is not None:
                evidence_source = "bm25_top_sentence_for_neutral"
                scores = sentence_index.scores(hypothesis)
                if len(scores):
                    best = max(range(len(scores)), key=lambda index: scores[index])
                    if scores[best] > 0:
                        cited_texts.append(sentences[best])
            evidence = "\n".join(value for value in cited_texts if value)
            chunk_id = f"contractnli::{doc['id']}"
            verdict = verify_claims(
                [{"text": hypothesis, "chunk_ids": [chunk_id]}] if evidence else
                [{"text": hypothesis, "chunk_ids": [f"missing::{doc['id']}"]}],
                [{"chunk_id": chunk_id, "text": evidence}] if evidence else [],
            )["verdicts"][0]
            rows.append({
                "document_id": str(doc["id"]),
                "hypothesis_id": hypothesis_id,
                "gold_label": gold,
                "expected_supported": gold == "Entailment",
                "predicted_supported": verdict["ok"],
                "checker_status": verdict["status"],
                "evidence_source": evidence_source,
            })

    positives = [row for row in rows if row["expected_supported"]]
    negatives = [row for row in rows if not row["expected_supported"]]
    fp = sum(row["predicted_supported"] for row in negatives)
    fn = sum(not row["predicted_supported"] for row in positives)
    label_counts = Counter(row["gold_label"] for row in rows)
    per_label = {}
    for label in sorted(label_counts):
        group = [row for row in rows if row["gold_label"] == label]
        per_label[label] = {
            "cases": len(group),
            "accepted_as_supported": sum(row["predicted_supported"] for row in group),
            "rejected": sum(not row["predicted_supported"] for row in group),
            "checker_status_counts": dict(Counter(row["checker_status"] for row in group)),
        }
    return {
        "evaluation": "ContractNLI human-annotated test split",
        "dataset": "ContractNLI: Koreeda and Manning (Findings of EMNLP 2021)",
        "dataset_source": "https://stanfordnlp.github.io/contract-nli/",
        "dataset_paper": "https://aclanthology.org/2021.findings-emnlp.164/",
        "license": "CC BY 4.0; retain dataset attribution when distributing derived data",
        "gold_label_method": "Published human annotations: Entailment is supported; Contradiction and NotMentioned are not supported.",
        "neutral_evidence_method": "BM25 top sentence from the same NDA simulates non-gold retrieved evidence.",
        "n_documents": len(dataset["documents"]),
        "n_claims": len(rows),
        "label_counts": dict(label_counts),
        "n_supported": len(positives),
        "n_not_supported": len(negatives),
        "detection_rate": (len(negatives) - fp) / len(negatives) if negatives else None,
        "false_positive_rate": fp / len(negatives) if negatives else None,
        "supported_claim_false_rejection_rate": fn / len(positives) if positives else None,
        "accuracy": sum(row["predicted_supported"] == row["expected_supported"] for row in rows) / len(rows) if rows else None,
        "per_gold_label": per_label,
        "results": rows,
        "limitation": "This legal NLI benchmark contains NDAs, not shipping policies. Neutral cases use a BM25 top sentence as retrieved evidence; the benchmark labels the whole contract, not retrieval relevance. Do not interpret these metrics as universal semantic accuracy.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate claim checking against synthetic corruption cases and optionally ContractNLI.")
    parser.add_argument("--contractnli-zip", type=Path, help="Path to the CC BY 4.0 ContractNLI archive")
    args = parser.parse_args()
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "corpus_grounded": evaluate_corpus_claim_checker(),
        "hand_authored_control_cases": evaluate_claim_checker(),
    }
    if args.contractnli_zip:
        result["human_annotated_contractnli"] = evaluate_contractnli_checker(args.contractnli_zip)
    output = get_project_root() / "reports" / "metrics" / "checker_claim_evaluation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    summary = result.get("human_annotated_contractnli") or result["corpus_grounded"]
    if "n_claims" in summary:
        summary = {
            key: summary.get(key)
            for key in (
                "n_documents", "n_claims", "n_supported", "n_not_supported",
                "detection_rate", "false_positive_rate",
                "supported_claim_false_rejection_rate", "accuracy",
            )
        }
    else:
        summary = {
            key: summary.get(key)
            for key in (
                "n_cases", "n_source_claims", "n_unsupported",
                "detection_rate", "false_positive_rate",
                "supported_claim_false_rejection_rate", "accuracy",
            )
        }
    print(json.dumps({"report": str(output), **summary}, indent=2))


if __name__ == "__main__":
    main()
