"""Phase 13 — Evaluation summary and final defence report."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scope.config.loader import get_project_root
from scope.logging_config import setup_logging

logger = setup_logging()


def _load(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _best_late_model(late: dict[str, Any], artifact_meta: dict[str, Any]) -> str | None:
    """Resolve the report's selected model from the saved bundle first."""
    artifact_model = artifact_meta.get("model_name")
    if artifact_model in (late.get("models") or {}):
        return artifact_model
    best = late.get("best_model")
    if best in (late.get("models") or {}):
        return best
    candidates = {
        name: block.get("val", {}).get("f1")
        for name, block in (late.get("models") or {}).items()
        if isinstance(block, dict) and block.get("val", {}).get("f1") is not None
    }
    return max(candidates, key=candidates.get) if candidates else None


def build_final_evaluation() -> dict[str, Any]:
    root = get_project_root()
    metrics = root / "reports" / "metrics"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "late_delivery": _load(metrics / "late_delivery_classification.json"),
        "duration": _load(metrics / "delivery_duration_regression.json"),
        "forecasting": _load(metrics / "forecasting.json"),
        "vendor_segmentation": _load(metrics / "vendor_segmentation.json"),
        "anomaly": _load(metrics / "anomaly_detection.json"),
        "inventory": _load(metrics / "inventory_experiment.json"),
        "shap": _load(metrics / "shap_explainability.json"),
        "rag_retrieval": _load(metrics / "rag_retrieval_evaluation.json"),
        "walk_forward_backtest": _load(metrics / "walk_forward_backtest.json"),
        "model_evaluations": {
            name: _load(metrics / f"evaluation_{name}.json")
            for name in (
                "late_delivery",
                "duration",
                "inventory",
                "forecast_late_rate",
                "forecast_volume",
                "vendor_segmentation",
                "anomaly_unusual_profile",
                "anomaly_retrospective",
                "anomaly_vendor_kpi",
            )
        },
        "preprocessing": _load(root / "reports" / "preprocessing_metadata.json"),
        "phase_run": _load(root / "reports" / "phase_run_summary.json"),
    }

    # Defence narrative — metrics may be nested under models[best].test
    late = payload.get("late_delivery") or {}
    late_models = late.get("models") or {}
    artifact_meta = _load(root / "reports" / "models" / "late_delivery_classifier" / "metadata.json") or {}
    best = _best_late_model(late, artifact_meta)
    test = (late_models.get(best) or {}).get("test") or {}

    duration = payload.get("duration") or {}
    forecast = payload.get("forecasting") or {}
    shap = payload.get("shap") or {}
    inventory = payload.get("inventory") or {}
    inventory_test = (payload.get("model_evaluations", {}).get("inventory") or {}).get("test") or {}
    inventory_best = inventory.get("best_model")
    inventory_validation = ((inventory.get("models") or {}).get(inventory_best) or {}).get("validation") or {}
    inventory_baseline = inventory.get("validation_baseline") or {}
    rag_retrieval = payload.get("rag_retrieval") or {}
    vendor_baseline = ((late.get("baselines") or {}).get("vendor_history_only") or {}).get("test") or {}
    forecast_evaluations = payload.get("model_evaluations") or {}
    monthly_late = (forecast_evaluations.get("forecast_late_rate") or {}).get("test") or {}
    monthly_volume = (forecast_evaluations.get("forecast_volume") or {}).get("test") or {}
    segmentation = (forecast_evaluations.get("vendor_segmentation") or {}).get("test") or {}
    unusual_profile = (forecast_evaluations.get("anomaly_unusual_profile") or {}).get("test") or {}

    md = f"""# SCOPE Final Evaluation and Defence Report

Generated: `{payload['generated_at']}`

## System summary

SCOPE integrates:
- Chronological preprocessing and leakage-aware features (Phase 02)
- Late-delivery classification (Phase 03)
- Delivery-duration regression (Phase 04)
- Monthly forecasting with baseline comparison (Phase 05)
- Vendor segmentation and anomaly detection (Phase 06)
- Inventory target rule audit (Phase 07)
- SHAP explainability (Phase 08)
- Hybrid RAG with synthetic-document labeling (Phase 09)
- Evidence ledger + Checker (Phase 10)
- Agentic investigation workflow (Phase 11)
- FastAPI + React frontend (Phase 12)

## Primary ML result — late delivery

- Best model: **{best}**
- Test recall: **{test.get('recall')}**
- Test precision: **{test.get('precision')}**
- Test F1: **{test.get('f1')}**
- Test ROC-AUC: **{test.get('roc_auc')}**
- Test PR-AUC: **{test.get('pr_auc')}**
- Test positive prevalence: **{(late.get('class_balance_test') or {}).get('positive_rate')}**
- Positive prevalence by split: **{ {name: block.get('positive_rate') for name, block in (late.get('class_balance_by_split') or {}).items()} }**
- Post-2010 training sensitivity test ROC-AUC: **{(late.get('post_2010_training_sensitivity') or {}).get('test', {}).get('roc_auc')}**
- Vendor-history-only baseline ROC-AUC: **{vendor_baseline.get('roc_auc')}**
- Rolling-origin ROC-AUC: **{(late.get('rolling_origin_cv') or {}).get('roc_auc_mean')} ± {(late.get('rolling_origin_cv') or {}).get('roc_auc_std')}**

## Supporting results

- Duration best model: **{duration.get('best_model')}**
- Duration median baseline validation MAE: **{((duration.get('models') or {}).get('dummy_median') or {}).get('val', {}).get('mae')}**
- Duration test MAE / R²: **{((duration.get('models') or {}).get(duration.get('best_model')) or {}).get('test', {}).get('mae')} / {((duration.get('models') or {}).get(duration.get('best_model')) or {}).get('test', {}).get('r2')}**
- Forecasting frequency: **{forecast.get('frequency')}**; results include naive and mean baselines.
- Monthly late-rate model MAE: **{monthly_late.get('mae')}**; beats naive: **{monthly_late.get('beats_naive_lag1')}**, beats mean: **{monthly_late.get('beats_development_mean')}**.
- Monthly volume model MAE: **{monthly_volume.get('mae')}**; beats naive: **{monthly_volume.get('beats_naive_lag1')}**, beats mean: **{monthly_volume.get('beats_development_mean')}**.
- Inventory proxy model: **{inventory_best}**; validation PR-AUC **{inventory_validation.get('pr_auc')}** vs prevalence baseline **{inventory_baseline.get('pr_auc')}**; test ROC-AUC / PR-AUC: **{inventory_test.get('roc_auc')} / {inventory_test.get('pr_auc')}**. It excludes the two operands of the deterministic target rule and is experimental against unverified augmented fields.
- Inventory rule agreement on test rows: **{inventory_test.get('target_rule_agreement')}** (consistency check, not model accuracy).
- RAG retrieval wiring sanity MRR: **{rag_retrieval.get('mrr')}** over {rag_retrieval.get('n_queries')} hand-authored synthetic queries; this is not a retrieval-quality claim.
- Vendor segmentation: **k={segmentation.get('kmeans_k')}, silhouette={segmentation.get('silhouette')}**, with small-history and profile-outlier vendors separated.
- Unusual shipment profile flags: **{unusual_profile.get('n_unusual')} / {unusual_profile.get('n_test')}** test shipments; flagged late-rate diagnostic **{(unusual_profile.get('late_rate_diagnostic') or {}).get('flagged')}** (descriptive only).
- SHAP status: **{shap.get('status')}**

## Important limitations

1. Inventory fields are **unverified augmented data**. The proxy classifier does not use the two fields that define its label; its scores are not operationally validated, and rule agreement is only a consistency check.
2. Synthetic RAG documents are **not official contracts/policies**.
3. Anomaly scores describe unusual shipment profiles and are not delay predictors; retrospective analysis is forensic only.
4. Prefer PostgreSQL via `docker compose up -d postgres` and `SCOPE_DATABASE_URL=postgresql+psycopg://scope:scope@127.0.0.1:5432/scope`. SQLite is only an automatic fallback when Postgres is down — do not claim Postgres compliance while on SQLite.
5. RAG uses hybrid TF-IDF + keyword RRF (upgradeable to dense embeddings + FAISS/pgvector).
6. RAG retrieval sanity queries are synthetic and too small to estimate production relevance.
7. Anomaly scores are investigative signals, not fraud probabilities or labeled accuracy.
8. Delivery-duration predictions should be treated as low-confidence unless the selected model beats the median baseline on validation data.
9. Late-delivery prevalence changes across train, validation, and test; rolling-origin CV shows substantial temporal variation.

## Reproducibility

```bash
py -3.13 -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
pip install -e .
docker compose up -d postgres
$env:SCOPE_DATABASE_URL='postgresql+psycopg://scope:scope@127.0.0.1:5432/scope'
python -m scope.data.preprocessing
python scripts/run_all_phases.py
uvicorn scope.api.app:app --reload --port 8000
cd frontend && npm install && npm run dev
pytest -q
```

## Defence talking points

- Prediction moment is documented: scheduled delivery known, outcome unknown.
- Chronological splits reduce temporal leakage.
- Checker validates numeric claims and citation presence.
- Agents coordinate ML + RAG + evidence rather than free-form hallucination.
- Forecasts use monthly lag models selected against naive and mean baselines.
"""
    out_md = root / "reports" / "final_defence_report.md"
    out_json = root / "reports" / "final_evaluation.json"
    out_md.write_text(md, encoding="utf-8")
    out_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    logger.info("Final evaluation written to %s", out_md)
    return {"report": str(out_md), "json": str(out_json)}
