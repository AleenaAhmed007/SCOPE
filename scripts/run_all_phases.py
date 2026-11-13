"""Run SCOPE phases 02–13 pipelines sequentially."""

from __future__ import annotations

import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

# Allow running this file directly from a checkout without requiring `pip install -e .`.
ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from scope.config.loader import get_project_root
from scope.logging_config import setup_logging

logger = setup_logging()


def main() -> None:
    root = get_project_root()
    results: dict = {"started_at": datetime.now(timezone.utc).isoformat(), "phases": {}}

    steps = [
        ("02_preprocessing", "scope.data.preprocessing", "run_preprocessing"),
        ("03_late_classification", "scope.models.classification.train_late", "train_late_delivery"),
        ("04_duration_regression", "scope.models.regression.train_duration", "train_delivery_duration"),
        ("05_forecasting", "scope.models.forecasting.train_forecast", "train_forecasts"),
        ("06a_vendor_segments", "scope.models.clustering.train_vendor_segments", "train_vendor_segmentation"),
        ("06b_anomaly", "scope.models.anomaly.train_anomaly", "train_anomaly_models"),
        ("07_inventory", "scope.models.classification.train_inventory", "train_inventory_experiment"),
        ("08_shap", "scope.models.explainability.shap_explain", "run_shap_explainability"),
        ("09_rag", "scope.rag.index", "build_rag_index"),
        ("10_evidence_init", "scope.evidence.ledger", "init_db"),
        ("11_sample_investigation", "scope.agents.workflow", "run_investigation"),
        ("12_model_evaluation", "scope.evaluation.model_evaluation", "evaluate_models"),
        ("13_evaluation", "scope.evaluation.final_report", "build_final_evaluation"),
    ]

    for name, module_name, fn_name in steps:
        logger.info("=== Running %s ===", name)
        try:
            mod = __import__(module_name, fromlist=[fn_name])
            fn = getattr(mod, fn_name)
            if name == "11_sample_investigation":
                out = fn("Investigate late delivery risk and policy obligations", order_id=1)
            elif name == "10_evidence_init":
                fn()
                out = {"status": "ok"}
            elif name == "12_model_evaluation":
                evaluated, failures = fn("all")
                out = {"evaluated": list(evaluated), "failed": failures}
                if failures:
                    raise RuntimeError(f"Model evaluation failed: {failures}")
            else:
                out = fn()
            results["phases"][name] = {"status": "ok", "result": out}
        except Exception as exc:
            logger.error("%s failed: %s", name, exc)
            results["phases"][name] = {
                "status": "failed",
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }

    results["finished_at"] = datetime.now(timezone.utc).isoformat()
    out_path = root / "reports" / "phase_run_summary.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: v.get("status") for k, v in results["phases"].items()}, indent=2))
    print("Wrote", out_path)
    if any(phase.get("status") == "failed" for phase in results["phases"].values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
