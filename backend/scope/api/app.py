"""Phase 12 — FastAPI application integrating ML, RAG, evidence, and agents."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from scope.agents.workflow import run_investigation
from scope.config.loader import get_project_root
from scope.db.session import init_db, resolve_database_url
from scope.evidence.ledger import list_evidence
from scope.models.common import load_shipments, project_paths
from scope.rag.index import answer_with_citations, build_rag_index

app = FastAPI(title="SCOPE API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LateDeliveryRequest(BaseModel):
    order_id: int | None = None
    features: dict[str, Any] | None = None


class InvestigationRequest(BaseModel):
    query: str = Field(..., min_length=3)
    order_id: int | None = None


class RagQuery(BaseModel):
    query: str
    top_k: int = 5


def _bundle(name: str):
    path = project_paths()["models"] / name / "model.joblib"
    if not path.exists():
        raise HTTPException(404, f"Model not found: {name}")
    return joblib.load(path)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/system/status")
def system_status() -> dict[str, Any]:
    root = get_project_root()
    models_dir = project_paths()["models"]
    model_names = [p.name for p in models_dir.iterdir()] if models_dir.exists() else []
    return {
        "status": "ok",
        "project_root": str(root),
        "models_available": model_names,
        "database_url_scheme": resolve_database_url().split("://", 1)[0],
        "database_note": "PostgreSQL only; startup fails if the configured server is unavailable",
    }


@app.get("/api/v1/dashboard")
def dashboard() -> dict[str, Any]:
    df = load_shipments()
    late = df["is_late"].dropna()
    dur = df["delivery_duration_days"].dropna()
    anom_path = project_paths()["processed"] / "anomaly_scores_unusual_profile.parquet"
    anomaly_count = 0
    if anom_path.exists():
        anomaly_count = int(pd.read_parquet(anom_path)["is_anomaly"].sum())
    inv_dir = get_project_root() / "reports" / "investigations"
    recent = sorted(inv_dir.glob("*.json"))[-5:] if inv_dir.exists() else []
    return {
        "total_orders": int(len(df)),
        "total_vendors": int(df["Vendor"].nunique()),
        "late_delivery_pct": float(late.mean() * 100) if len(late) else None,
        "avg_delivery_duration": float(dur.mean()) if len(dur) else None,
        "unusual_profile_count": anomaly_count,
        "anomaly_count": anomaly_count,
        "recent_investigations": [p.name for p in recent],
        "risk_distribution": {
            "on_time": int((late == 0).sum()),
            "late": int((late == 1).sum()),
        },
    }


@app.get("/api/v1/orders")
def list_orders(limit: int = 50, offset: int = 0) -> dict[str, Any]:
    df = load_shipments()
    cols = [
        "ID",
        "Vendor",
        "Country",
        "Shipment_Mode",
        "Product_Group",
        "is_late",
        "delay_days",
        "Line_Item_Quantity",
    ]
    cols = [c for c in cols if c in df.columns]
    slice_df = df[cols].iloc[offset : offset + limit]
    return {"total": len(df), "items": slice_df.to_dict(orient="records")}


@app.get("/api/v1/orders/{order_id}")
def get_order(order_id: int) -> dict[str, Any]:
    df = load_shipments()
    row = df[df["ID"] == order_id]
    if row.empty:
        raise HTTPException(404, "Order not found")
    return row.iloc[0].where(pd.notnull(row.iloc[0]), None).to_dict()


@app.get("/api/v1/vendors")
def list_vendors(limit: int = 100) -> dict[str, Any]:
    path = project_paths()["processed"] / "vendor_features.parquet"
    df = pd.read_parquet(path).head(limit)
    return {"items": df.to_dict(orient="records")}


@app.get("/api/v1/vendors/segments")
def vendor_segments() -> dict[str, Any]:
    path = project_paths()["processed"] / "vendor_segments.parquet"
    if not path.exists():
        raise HTTPException(404, "Vendor segments not trained yet")
    df = pd.read_parquet(path)
    return {"items": df.to_dict(orient="records")}


@app.get("/api/v1/vendors/{vendor_name}")
def get_vendor(vendor_name: str) -> dict[str, Any]:
    path = project_paths()["processed"] / "vendor_features.parquet"
    df = pd.read_parquet(path)
    row = df[df["Vendor"] == vendor_name]
    if row.empty:
        raise HTTPException(404, "Vendor not found")
    return row.iloc[0].to_dict()


@app.post("/api/v1/predictions/late-delivery")
def predict_late(req: LateDeliveryRequest) -> dict[str, Any]:
    bundle = _bundle("late_delivery_classifier")
    df = load_shipments()
    if req.order_id is not None:
        row = df[df["ID"] == req.order_id]
        if row.empty:
            raise HTTPException(404, "Order not found")
        X = row[bundle["features"]]
        order_id = req.order_id
    else:
        raise HTTPException(400, "order_id required")
    proba = float(bundle["pipeline"].predict_proba(X)[0, 1])
    return {
        "order_id": order_id,
        "late_probability": proba,
        "late_prediction": int(proba >= bundle.get("threshold", 0.5)),
        "model": bundle.get("model_name"),
    }


@app.post("/api/v1/predictions/delivery-duration")
def predict_duration(req: LateDeliveryRequest) -> dict[str, Any]:
    bundle = _bundle("delivery_duration_regressor")
    df = load_shipments()
    if req.order_id is None:
        raise HTTPException(400, "order_id required")
    row = df[df["ID"] == req.order_id]
    if row.empty:
        raise HTTPException(404, "Order not found")
    pred = float(bundle["pipeline"].predict(row[bundle["features"]])[0])
    low_confidence = not bool(
        (bundle.get("metrics") or {}).get("selected_model_beats_median_baseline_on_validation", False)
    )
    return {
        "order_id": req.order_id,
        "predicted_duration_days": pred,
        "model": bundle.get("model_name"),
        "prediction_basis": bundle.get("prediction_basis", "ml_model"),
        "low_confidence": low_confidence,
    }


@app.post("/api/v1/predictions/inventory-stockout")
def predict_inventory_stockout(req: LateDeliveryRequest) -> dict[str, Any]:
    bundle = _bundle("inventory_stockout_classifier")
    if req.order_id is None:
        raise HTTPException(400, "order_id required")
    df = load_shipments()
    row = df[df["ID"] == req.order_id]
    if row.empty:
        raise HTTPException(404, "Order not found")
    probability = float(bundle["pipeline"].predict_proba(row[bundle["features"]])[0, 1])
    low_confidence = not bool(
        (bundle.get("metrics") or {}).get("selected_model_beats_prevalence_baseline", False)
    )
    return {
        "order_id": req.order_id,
        "stockout_probability": probability,
        "stockout_prediction": int(probability >= bundle.get("threshold", 0.5)),
        "model": bundle.get("model_name"),
        "prediction_basis": bundle.get("prediction_basis"),
        "low_confidence": low_confidence,
    }


@app.get("/api/v1/predictions/anomaly/{order_id}")
def get_anomaly(order_id: int) -> dict[str, Any]:
    path = project_paths()["processed"] / "anomaly_scores_unusual_profile.parquet"
    if not path.exists():
        raise HTTPException(404, "Anomaly scores missing")
    df = pd.read_parquet(path)
    row = df[df["ID"] == order_id]
    if row.empty:
        raise HTTPException(404, "Order not found")
    return row.iloc[0].to_dict()


@app.get("/api/v1/explainability/shap/summary")
def shap_summary() -> dict[str, Any]:
    path = project_paths()["metrics"] / "shap_explainability.json"
    if not path.exists():
        raise HTTPException(404, "SHAP report missing")
    import json

    return json.loads(path.read_text(encoding="utf-8"))


@app.post("/api/v1/rag/query")
def rag_query(body: RagQuery) -> dict[str, Any]:
    return answer_with_citations(body.query, top_k=body.top_k)


@app.post("/api/v1/rag/reindex")
def rag_reindex() -> dict[str, Any]:
    return build_rag_index()


@app.post("/api/v1/rag/upload")
async def rag_upload(file: UploadFile = File(...)) -> dict[str, Any]:
    root = get_project_root()
    dest_dir = root / "data" / "documents" / "uploads"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / file.filename
    content = await file.read()
    dest.write_bytes(content)
    # Reindex including uploads (build_rag_index currently uses synthetic+docs; append upload text)
    text = content.decode("utf-8", errors="ignore")
    note = dest.with_suffix(dest.suffix + ".md") if dest.suffix.lower() != ".md" else dest
    if dest.suffix.lower() != ".md":
        note.write_text(
            f"# Uploaded document\n\nSource file: {file.filename}\n\n{text[:20000]}",
            encoding="utf-8",
        )
    meta = build_rag_index()
    return {"saved": str(dest), "reindex": meta}


@app.post("/api/v1/investigations/run")
def investigations_run(body: InvestigationRequest) -> dict[str, Any]:
    result = run_investigation(body.query, order_id=body.order_id)
    return {
        "status": result.get("status"),
        "order_id": result.get("order_id"),
        "plan": result.get("plan"),
        "ml_findings": result.get("ml_findings"),
        "document_findings": {
            "answer": (result.get("document_findings") or {}).get("answer"),
            "claims": (result.get("document_findings") or {}).get("claims"),
            "claim_verification": (result.get("checker_result") or {}).get("claim_verification"),
            "citations": (result.get("document_findings") or {}).get("citations"),
        },
        "evidence_ids": result.get("evidence_ids"),
        "checker_result": result.get("checker_result"),
        "report": result.get("report"),
    }


@app.get("/api/v1/evidence")
def evidence_list(limit: int = 100) -> dict[str, Any]:
    return {"items": list_evidence(limit=limit)}


def create_app() -> FastAPI:
    return app
