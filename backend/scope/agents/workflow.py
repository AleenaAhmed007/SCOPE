"""Phase 11 — Agentic investigation workflow (LangGraph if available, else deterministic graph)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, TypedDict

import joblib
import pandas as pd

from scope.config.loader import get_project_root
from scope.data.table_io import read_table
from scope.evidence.claims import verify_claims
from scope.evidence.checker import run_checker
from scope.evidence.ledger import add_evidence, update_validation
from scope.logging_config import setup_logging
from scope.models.common import load_shipments, project_paths
from scope.rag.index import answer_with_citations

logger = setup_logging()


class InvestigationState(TypedDict, total=False):
    query: str
    order_id: int | None
    plan: list[str]
    needs_data: bool
    needs_documents: bool
    ml_findings: dict[str, Any]
    document_findings: dict[str, Any]
    evidence_ids: list[str]
    active_evidence_ids: list[str]
    claim_evidence_ids: list[str]
    excluded_claims: list[dict[str, Any]]
    revision_history: list[dict[str, Any]]
    revision_count: int
    checker_result: dict[str, Any]
    report: str
    status: str


def planner(state: InvestigationState) -> InvestigationState:
    import re

    query = state.get("query", "").lower()
    has_order_id = state.get("order_id") is not None or bool(re.search(r"\b(?:order|shipment)\s*#?\s*\d+\b", query))
    document_terms = ("policy", "policies", "contract", "clause", "agreement", "sla", "document", "terms")
    analytic_terms = ("predict", "prediction", "risk", "late", "delay", "duration", "forecast", "anomaly", "shipment")
    wants_documents = any(term in query for term in document_terms)
    wants_analysis = has_order_id or any(term in query for term in analytic_terms)
    # Route a document-only question to retrieval; otherwise run data analysis,
    # and add document research when the question asks for policy/contract support.
    needs_data = wants_analysis or not wants_documents
    needs_documents = wants_documents or not needs_data

    plan: list[str] = []
    if needs_data:
        plan.extend(["Resolve shipment context", "Run relevant shipment risk models"])
    if needs_documents:
        plan.append("Retrieve policy/document evidence")
    plan.extend(["Record evidence", "Run claim Checker"])
    return {
        **state,
        "needs_data": needs_data,
        "needs_documents": needs_documents,
        "plan": plan,
        "revision_count": 0,
        "revision_history": [],
        "excluded_claims": [],
        "status": "planned",
    }


def route_after_planner(state: InvestigationState) -> str:
    return "data" if state.get("needs_data", True) else "documents"


def route_after_data(state: InvestigationState) -> str:
    return "documents" if state.get("needs_documents", True) else "evidence"


def route_after_checker(state: InvestigationState) -> str:
    if state.get("status") == "needs_review" and state.get("revision_count", 0) < 1:
        return "revise"
    return "report"


def _load_bundle(name: str):
    path = project_paths()["models"] / name / "model.joblib"
    if not path.exists():
        return None
    return joblib.load(path)


def data_analyst(state: InvestigationState) -> InvestigationState:
    df = load_shipments()
    order_id = state.get("order_id")
    if order_id is None:
        # try parse from query
        import re

        m = re.search(r"\b(\d{1,6})\b", state.get("query", ""))
        order_id = int(m.group(1)) if m else int(df.iloc[0]["ID"])

    row = df[df["ID"] == order_id]
    findings: dict[str, Any] = {"order_id": order_id, "found": not row.empty}
    if row.empty:
        return {**state, "order_id": order_id, "ml_findings": findings, "status": "order_not_found"}

    record = row.iloc[0]
    findings["vendor"] = record["Vendor"]
    findings["country"] = record["Country"]
    findings["shipment_mode"] = record.get("Shipment_Mode")
    findings["actual_is_late"] = None if pd.isna(record.get("is_late")) else int(record["is_late"])

    late_bundle = _load_bundle("late_delivery_classifier")
    dur_bundle = _load_bundle("delivery_duration_regressor")
    anom_path = project_paths()["processed"] / "anomaly_scores_unusual_profile.csv"

    if late_bundle:
        feats = late_bundle["features"]
        X = row[feats]
        proba = float(late_bundle["pipeline"].predict_proba(X)[0, 1])
        findings["late_probability"] = proba
        findings["late_prediction"] = int(proba >= late_bundle.get("threshold", 0.5))
        findings["late_model"] = late_bundle.get("model_name")

    if dur_bundle:
        feats = dur_bundle["features"]
        pred = float(dur_bundle["pipeline"].predict(row[feats])[0])
        findings["predicted_duration_days"] = pred
        findings["duration_model"] = dur_bundle.get("model_name")
        findings["duration_basis"] = dur_bundle.get("prediction_basis", "ml_model")
        findings["duration_low_confidence"] = not bool(
            (dur_bundle.get("metrics") or {}).get("selected_model_beats_median_baseline_on_validation", False)
        )

    if anom_path.exists():
        anom = read_table(anom_path)
        arow = anom[anom["ID"] == order_id]
        if not arow.empty:
            findings["anomaly_score"] = float(arow.iloc[0]["anomaly_score"])
            findings["is_anomaly"] = int(arow.iloc[0]["is_anomaly"])
            findings["anomaly_type"] = "unusual_shipment_profile"

    return {**state, "order_id": order_id, "ml_findings": findings, "status": "ml_complete"}


def document_researcher(state: InvestigationState) -> InvestigationState:
    query = state.get("query") or "late delivery vendor escalation policy"
    ml = state.get("ml_findings") or {}
    context = " ".join(
        str(ml[key]) for key in ("vendor", "country", "shipment_mode") if ml.get(key)
    )
    enriched = f"{query}. {context}".strip()
    docs = answer_with_citations(enriched, top_k=4)
    return {**state, "document_findings": docs, "status": "docs_complete"}


def evidence_writer(state: InvestigationState) -> InvestigationState:
    ml = state.get("ml_findings") or {}
    docs = state.get("document_findings") or {}
    eids = []

    if "late_probability" in ml:
        e = add_evidence(
            evidence_type="ml_prediction",
            source="late_delivery_classifier",
            claim=(
                f"Order {ml.get('order_id')} late probability "
                f"{ml['late_probability']:.3f} (pred={ml.get('late_prediction')})"
            ),
            related_order_id=str(ml.get("order_id")),
            related_vendor=str(ml.get("vendor")),
            model_version=str(ml.get("late_model")),
            payload=ml,
        )
        eids.append(e["evidence_id"])

    citations = {int(c.get("index", 0)): c for c in docs.get("citations") or []}
    passages = {str(hit.get("chunk_id", "")): hit for hit in docs.get("retrieved") or []}
    claim_eids: list[str] = []
    for claim in docs.get("claims") or []:
        claim_text = str(claim.get("text", ""))
        cited_chunks = [str(cid) for cid in claim.get("chunk_ids", [])]
        cited_hits = [passages[cid] for cid in cited_chunks if cid in passages]
        cited_indices = [int(i) for i in claim.get("citation_indices", [])]
        cited = [citations[i] for i in cited_indices if i in citations]
        primary = cited[0] if cited else {}
        payload = {
            "claim": claim_text,
            "cited_chunk_ids": cited_chunks,
            "passages": [str(hit.get("text", "")) for hit in cited_hits],
            "citation_sources": cited,
        }
        e = add_evidence(
            evidence_type="document",
            source=str(primary.get("source", "")),
            claim=claim_text,
            related_order_id=str(ml.get("order_id")),
            related_vendor=str(ml.get("vendor")),
            document_page=str(primary.get("page")) if primary else None,
            payload=payload,
            synthetic_source=any(bool(c.get("synthetic")) for c in cited),
        )
        eids.append(e["evidence_id"])
        claim_eids.append(e["evidence_id"])

    return {
        **state,
        "evidence_ids": eids,
        "active_evidence_ids": list(eids),
        "claim_evidence_ids": claim_eids,
        "status": "evidence_recorded",
    }


def report_writer(state: InvestigationState) -> InvestigationState:
    ml = state.get("ml_findings") or {}
    docs = state.get("document_findings") or {}
    plan = state.get("plan") or []
    report = {
        "title": "SCOPE Investigation Report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "query": state.get("query"),
        "plan": plan,
        "order_id": state.get("order_id"),
        "predictions": {
            "late_probability": ml.get("late_probability"),
            "late_prediction": ml.get("late_prediction"),
            "predicted_duration_days": ml.get("predicted_duration_days"),
            "unusual_shipment_profile": {
                "score": ml.get("anomaly_score"),
                "is_anomaly": ml.get("is_anomaly"),
                "label": ml.get("anomaly_type"),
            },
        },
        "observations": {
            "vendor": ml.get("vendor"),
            "country": ml.get("country"),
            "shipment_mode": ml.get("shipment_mode"),
            "actual_is_late_if_known": ml.get("actual_is_late"),
        },
        "document_answer": docs.get("answer"),
        "citations": docs.get("citations"),
        "evidence_ids": state.get("evidence_ids"),
        "checker_result": state.get("checker_result"),
        "validation_status": state.get("status"),
        "excluded_claims": state.get("excluded_claims", []),
        "revision_history": state.get("revision_history", []),
        "assumptions": [
            "ML outputs are probabilistic estimates, not certain outcomes.",
            "Synthetic documents are non-authoritative; official extracts apply only within their stated jurisdiction.",
            "Inventory-augmented fields are not treated as system-of-record here.",
        ],
    }
    text = json.dumps(report, indent=2)
    out = get_project_root() / "reports" / "investigations"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"investigation_{state.get('order_id')}.json"
    path.write_text(text, encoding="utf-8")
    return {**state, "report": text, "status": state.get("status", "report_written")}


def checker_node(state: InvestigationState) -> InvestigationState:
    evidence_ids = state.get("active_evidence_ids", state.get("evidence_ids", []))
    result = run_checker(evidence_ids)
    docs = state.get("document_findings") or {}
    claim_verification = verify_claims(docs.get("claims") or [], docs.get("retrieved") or [])

    # Persist failed claim-level verdicts on the matching evidence records.
    claim_evidence_ids = state.get("claim_evidence_ids", [])
    for evidence_id, verdict in zip(
        claim_evidence_ids, claim_verification["verdicts"]
    ):
        if not verdict["ok"]:
            update_validation(evidence_id, "needs_review", "; ".join(verdict["notes"]))
            for item in result["results"]:
                if item["evidence_id"] == evidence_id:
                    item["status"] = "needs_review"
                    item["notes"] = "; ".join(verdict["notes"])

    result["claim_verification"] = claim_verification
    result["needs_review"] = sum(item["status"] != "validated" for item in result["results"])
    result["validated"] = result["checked"] - result["needs_review"]
    status = (
        "validated"
        if result.get("needs_review", 0) == 0
        and claim_verification.get("needs_review", 0) == 0
        else "needs_review"
    )
    return {**state, "checker_result": result, "status": status}


def revise_after_checker(state: InvestigationState) -> InvestigationState:
    """Remove failed document claims, retain an audit trail, then recheck once."""
    docs = dict(state.get("document_findings") or {})
    claims = list(docs.get("claims") or [])
    verdicts = (state.get("checker_result") or {}).get("claim_verification", {}).get("verdicts", [])
    claim_ids = state.get("claim_evidence_ids", [])
    keep: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = list(state.get("excluded_claims", []))
    kept_ids: list[str] = []
    excluded_ids: set[str] = set()
    for index, claim in enumerate(claims):
        verdict = verdicts[index] if index < len(verdicts) else {"ok": False, "status": "missing_verdict", "notes": ["No Checker verdict was returned."]}
        evidence_id = claim_ids[index] if index < len(claim_ids) else None
        if verdict.get("ok"):
            keep.append(claim)
            if evidence_id:
                kept_ids.append(evidence_id)
        else:
            excluded.append({"claim": claim.get("text", ""), "verdict": verdict, "evidence_id": evidence_id})
            if evidence_id:
                excluded_ids.add(evidence_id)

    docs["claims"] = keep
    docs["grounded"] = bool(keep)
    docs["answer"] = "\n".join(
        f"- {claim.get('text', '')} {''.join(f'[{i}]' for i in claim.get('citation_indices', []))}".rstrip()
        for claim in keep
    ) or "Insufficient grounded evidence was found in the document index."
    evidence_ids = state.get("evidence_ids", [])
    active_ids = [eid for eid in evidence_ids if eid not in excluded_ids]
    history = list(state.get("revision_history", []))
    history.append({
        "attempt": state.get("revision_count", 0) + 1,
        "action": "Removed claims rejected by the Checker; preserved them as needs_review evidence.",
        "removed_claims": len(excluded_ids),
        "remaining_claims": len(keep),
    })
    return {
        **state,
        "document_findings": docs,
        "active_evidence_ids": active_ids,
        "claim_evidence_ids": kept_ids,
        "excluded_claims": excluded,
        "revision_history": history,
        "revision_count": state.get("revision_count", 0) + 1,
        "status": "revised",
    }


def _run_deterministic(state: InvestigationState) -> InvestigationState:
    state = planner(state)
    if state.get("needs_data"):
        state = data_analyst(state)
    if state.get("needs_documents"):
        state = document_researcher(state)
    state = evidence_writer(state)
    state = checker_node(state)
    if route_after_checker(state) == "revise":
        state = revise_after_checker(state)
        state = checker_node(state)
    state = report_writer(state)
    return state


def run_investigation(query: str, order_id: int | None = None) -> InvestigationState:
    state: InvestigationState = {"query": query, "order_id": order_id, "status": "started"}

    try:
        from typing import Annotated

        from langgraph.graph import END, START, StateGraph
        from operator import or_

        class GraphState(TypedDict, total=False):
            query: str
            order_id: int | None
            plan: list[str]
            needs_data: bool
            needs_documents: bool
            ml_findings: dict[str, Any]
            document_findings: dict[str, Any]
            evidence_ids: list[str]
            active_evidence_ids: list[str]
            claim_evidence_ids: list[str]
            excluded_claims: list[dict[str, Any]]
            revision_history: list[dict[str, Any]]
            revision_count: int
            checker_result: dict[str, Any]
            report: str
            status: str

        graph = StateGraph(GraphState)
        graph.add_node("planner", planner)
        graph.add_node("data_analyst", data_analyst)
        graph.add_node("document_researcher", document_researcher)
        graph.add_node("evidence_writer", evidence_writer)
        graph.add_node("report_writer", report_writer)
        graph.add_node("checker", checker_node)
        graph.add_edge(START, "planner")
        graph.add_conditional_edges(
            "planner",
            route_after_planner,
            {"data": "data_analyst", "documents": "document_researcher"},
        )
        graph.add_conditional_edges(
            "data_analyst",
            route_after_data,
            {"documents": "document_researcher", "evidence": "evidence_writer"},
        )
        graph.add_edge("document_researcher", "evidence_writer")
        graph.add_edge("evidence_writer", "checker")
        graph.add_conditional_edges(
            "checker",
            route_after_checker,
            {"revise": "claim_revision", "report": "report_writer"},
        )
        graph.add_node("claim_revision", revise_after_checker)
        graph.add_edge("claim_revision", "checker")
        graph.add_edge("report_writer", END)
        app = graph.compile()
        final = app.invoke(state)
        if not final.get("ml_findings") and not final.get("document_findings"):
            raise RuntimeError("LangGraph returned incomplete state")
        logger.info("LangGraph investigation complete: %s", final.get("status"))
        return final  # type: ignore[return-value]
    except Exception as exc:
        logger.warning("LangGraph path failed (%s); using deterministic workflow", exc)
        return _run_deterministic(state)


if __name__ == "__main__":
    result = run_investigation("Investigate late delivery risk for order", order_id=1)
    print(result.get("status"), result.get("ml_findings"))
