"""Phase 04 — PO-to-client delivery duration regression."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, median_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor

from scope.db.experiments import log_experiment
from scope.logging_config import setup_logging
from scope.models.classification.train_late import CAT, NUM
from scope.models.common import (
    build_preprocessor,
    load_shipments,
    project_paths,
    save_json,
    save_model_bundle,
)

logger = setup_logging()


def _reg_metrics(y_true, y_pred) -> dict[str, Any]:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
        "median_ae": float(median_absolute_error(y_true, y_pred)),
        "mean_actual": float(np.mean(y_true)),
        "mean_pred": float(np.mean(y_pred)),
    }


def train_delivery_duration() -> dict[str, Any]:
    df = load_shipments()
    work = df[df["delivery_duration_days"].notna() & df["split"].isin(["train", "val", "test"])].copy()
    # Set the clipping boundary from the training period only to avoid test leakage.
    hi = work.loc[work["split"] == "train", "delivery_duration_days"].quantile(0.99)
    work = work[work["delivery_duration_days"] <= hi]

    features = [c for c in CAT + NUM if c in work.columns]
    cat = [c for c in CAT if c in features]
    num = [c for c in NUM if c in features]
    train = work[work["split"] == "train"]
    val = work[work["split"] == "val"]
    test = work[work["split"] == "test"]

    pre = build_preprocessor(num, cat)
    models = {
        "dummy_median": DummyRegressor(strategy="median"),
        "gradient_boosting": GradientBoostingRegressor(random_state=42),
        "xgboost": XGBRegressor(
            n_estimators=250,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=2,
        ),
        "random_forest": RandomForestRegressor(
            n_estimators=250,
            max_depth=12,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=2,
        ),
    }

    results: dict[str, Any] = {
        "target": "delivery_duration_days",
        "definition": "Delivered_To_Client_Date - PO_Sent_To_Vendor_Date (plausible only)",
        "note": "PO-to-client delivery duration — not generic supplier procurement lead time",
        "features": features,
        "n_train": len(train),
        "n_val": len(val),
        "n_test": len(test),
        "target_diagnostics": {
            "zero_day_rows_before_cap": int((df["delivery_duration_days"] == 0).sum()),
            "median_by_split": {
                split_name: float(part["delivery_duration_days"].median()) if len(part) else None
                for split_name, part in (("train", train), ("val", val), ("test", test))
            },
            "extreme_value_cap_from_train_p99": float(hi),
        },
        "models": {},
    }

    best_name, best_mae, best_pipe = None, float("inf"), None
    for name, reg in models.items():
        pipe = Pipeline([("pre", pre), ("model", reg)])
        pipe.fit(train[features], train["delivery_duration_days"])
        split_metrics = {}
        for split_name, part in [("val", val), ("test", test)]:
            if len(part) == 0:
                continue
            pred = pipe.predict(part[features])
            split_metrics[split_name] = _reg_metrics(part["delivery_duration_days"], pred)
        results["models"][name] = split_metrics
        mae = split_metrics.get("val", {}).get("mae", float("inf"))
        if mae < best_mae:
            best_mae, best_name, best_pipe = mae, name, pipe

    baseline_val_mae = results["models"]["dummy_median"].get("val", {}).get("mae")
    results["selected_model_beats_median_baseline_on_validation"] = bool(
        baseline_val_mae is not None and best_mae < baseline_val_mae - 1e-9
    )

    bundle = {
        "pipeline": best_pipe,
        "model_name": best_name,
        "features": features,
        "categorical": cat,
        "numeric": num,
        "target": "delivery_duration_days",
        "metrics": results,
    }
    out = save_model_bundle("delivery_duration_regressor", bundle)
    results["artifact_dir"] = str(out)
    results["best_model"] = best_name
    save_json(project_paths()["metrics"] / "delivery_duration_regression.json", results)
    try:
        results["db_ids"] = log_experiment(
            phase="04",
            task="delivery_duration_regression",
            model_name=str(best_name),
            metrics=results,
            artifact_path=str(out),
            features=features,
        )
    except Exception as exc:
        logger.warning("Could not persist experiment metadata: %s", exc)
    logger.info("Duration model saved %s best=%s mae=%.3f", out, best_name, best_mae)
    return results


if __name__ == "__main__":
    print(train_delivery_duration())
