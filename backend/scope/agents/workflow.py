"""Phase 11 — Agentic investigation workflow (LangGraph if available, else deterministic graph)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, TypedDict

import joblib
import pandas as pd

from scope.config.loader import get_project_root
from scope.evidence.checker import run_checker
from scope.evidence.ledger import add_evidence
from scope.logging_config import setup_logging
from scope.models.common import load_shipments, project_paths
from scope.rag.index import answer_with_citations

logger = setup_logging()


class InvestigationState(TypedDict, total=False):
    query: str
    order_id: int | None
    plan: list[str]
    ml_findings: dict[str, Any]
    document_findings: dict[str, Any]
    evidence_ids: list[str]
    checker_result: dict[str, Any]
    report: str
    status: str


def planner(state: InvestigationState) -> InvestigationState:
    order_id = state.get("order_id")
    plan = [
        "Resolve order/shipment context",
        "Run late-delivery prediction",
        "Estimate delivery duration",
        "Check unusual shipment profile score",
        "Retrieve policy/document evidence",
        "Write evidence-grounded report",
        "Run Checker validation",
    ]
    if order_id is None:
        plan.insert(0, "Infer order ID from query if present")
    return {**state, "plan": plan, "status": "planned"}


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
    anom_path = project_paths()["processed"] / "anomaly_scores_unusual_profile.parquet"

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
        anom = pd.read_parquet(anom_path)
        arow = anom[anom["ID"] == order_id]
        if not arow.empty:
            findings["anomaly_score"] = float(arow.iloc[0]["anomaly_score"])
            findings["is_anomaly"] = int(arow.iloc[0]["is_anomaly"])
            findings["anomaly_type"] = "unusual_shipment_profile"

    return {**state, "order_id": order_id, "ml_findings": findings, "status": "ml_complete"}


def document_researcher(state: InvestigationState) -> InvestigationState:
    query = state.get("query") or "late delivery vendor escalation policy"
    ml = state.get("ml_findings") or {}
    enriched = (
        f"{query}. Vendor {ml.get('vendor')} country {ml.get('country')} "
        f"shipment mode {ml.get('shipment_mode')} late risk"
    )
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

    for cite in docs.get("citations") or []:
        e = add_evidence(
            evidence_type="document",
            source=cite.get("source", ""),
            claim=f"Retrieved support from {cite.get('file_name')} page/chunk {cite.get('page')}",
            related_order_id=str(ml.get("order_id")),
            related_vendor=str(ml.get("vendor")),
            document_page=str(cite.get("page")),
            payload=cite,
            synthetic_source=bool(cite.get("synthetic")),
        )
        eids.append(e["evidence_id"])

    return {**state, "evidence_ids": eids, "status": "evidence_recorded"}


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
        "assumptions": [
            "ML outputs are probabilistic estimates, not certain outcomes.",
            "Synthetic documents are non-authoritative development fixtures.",
            "Inventory-augmented fields are not treated as system-of-record here.",
        ],
    }
    text = json.dumps(report, indent=2)
    out = get_project_root() / "reports" / "investigations"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"investigation_{state.get('order_id')}.json"
    path.write_text(text, encoding="utf-8")
    return {**state, "report": text, "status": "report_written"}


def checker_node(state: InvestigationState) -> InvestigationState:
    result = run_checker(state.get("evidence_ids"))
    status = "validated" if result.get("needs_review", 0) == 0 else "needs_review"
    return {**state, "checker_result": result, "status": status}


def _run_deterministic(state: InvestigationState) -> InvestigationState:
    for fn in [
        planner,
        data_analyst,
        document_researcher,
        evidence_writer,
        report_writer,
        checker_node,
    ]:
        state = fn(state)
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
            ml_findings: dict[str, Any]
            document_findings: dict[str, Any]
            evidence_ids: list[str]
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
        graph.add_edge("planner", "data_analyst")
        graph.add_edge("data_analyst", "document_researcher")
        graph.add_edge("document_researcher", "evidence_writer")
        graph.add_edge("evidence_writer", "report_writer")
        graph.add_edge("report_writer", "checker")
        graph.add_edge("checker", END)
        app = graph.compile()
        final = app.invoke(state)
        if not final.get("ml_findings"):
            raise RuntimeError("LangGraph returned incomplete state")
        logger.info("LangGraph investigation complete: %s", final.get("status"))
        return final  # type: ignore[return-value]
    except Exception as exc:
        logger.warning("LangGraph path failed (%s); using deterministic workflow", exc)
        return _run_deterministic(state)


if __name__ == "__main__":
    result = run_investigation("Investigate late delivery risk for order", order_id=1)
    print(result.get("status"), result.get("ml_findings"))
