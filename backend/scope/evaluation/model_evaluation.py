"""Evaluate saved SCOPE model bundles against their held-out data."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Support direct execution from an uninstalled checkout.
BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
    silhouette_score,
)

from scope.data.table_io import read_table
from scope.models.common import project_paths, save_json
from scope.models.forecasting.train_forecast import _forecast_splits


MODEL_ARTIFACTS = {
    "late_delivery": "late_delivery_classifier",
    "duration": "delivery_duration_regressor",
    "inventory": "inventory_stockout_classifier",
    "forecast_late_rate": "forecast_late_rate_monthly",
    "forecast_volume": "forecast_volume_quantity_monthly",
    "vendor_segmentation": "vendor_segmentation",
    "anomaly_unusual_profile": "anomaly_unusual_profile",
    "anomaly_retrospective": "anomaly_retrospective",
    "anomaly_vendor_kpi": "anomaly_vendor_kpi",
}


def _bundle(name: str) -> dict[str, Any]:
    path = project_paths()["models"] / MODEL_ARTIFACTS[name] / "model.joblib"
    if not path.exists():
        raise FileNotFoundError(f"Missing model artifact: {path}. Train the model first.")
    return joblib.load(path)


def _classification(bundle: dict[str, Any], target: str, inventory: bool = False) -> dict[str, Any]:
    df = read_table(project_paths()["processed"] / "shipments.csv")
    if inventory:
        df["below_reorder"] = (df["Inventory_Opening_Stock"] < df["Inventory_Reorder_Level"]).astype(int)
    test = df[(df["split"] == "test") & df[target].notna()].copy()
    test[target] = test[target].astype(int)
    features = bundle["features"]
    if test.empty:
        raise ValueError(f"No test rows with target {target!r}.")
    pipeline = bundle["pipeline"]
    proba = pipeline.predict_proba(test[features])[:, 1]
    pred = (proba >= float(bundle.get("threshold", 0.5))).astype(int)
    y = test[target]
    return {
        "n_test": len(test),
        "threshold": float(bundle.get("threshold", 0.5)),
        "accuracy": float(accuracy_score(y, pred)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, proba)) if y.nunique() > 1 else None,
        "pr_auc": float(average_precision_score(y, proba)) if y.nunique() > 1 else None,
        "confusion_matrix": confusion_matrix(y, pred).tolist(),
        "classification_report": classification_report(y, pred, output_dict=True, zero_division=0),
    }


def _evaluate(name: str) -> dict[str, Any]:
    paths = project_paths()
    bundle = _bundle(name)
    if name == "inventory":
        df = read_table(paths["processed"] / "shipments.csv")
        work = df[(df["split"] == "test") & df["Inventory_Stockout_Flag"].notna()].copy()
        y = work["Inventory_Stockout_Flag"].astype(int)
        rule = (work["Inventory_Opening_Stock"] - work["Line_Item_Quantity"] < 0).astype(int)
        metrics = _classification(bundle, "Inventory_Stockout_Flag")
        metrics.update({
            "n_test": len(work),
            "target_rule": "Inventory_Opening_Stock - Line_Item_Quantity < 0",
            "target_rule_agreement": float((rule == y).mean()) if len(work) else None,
            "interpretation": "Experimental ML proxy excludes both deterministic rule operands. The rule agreement is a data consistency check; inventory provenance is unverified.",
        })
    elif name == "late_delivery":
        metrics = _classification(bundle, "is_late")
    elif name == "duration":
        df = read_table(paths["processed"] / "shipments.csv")
        eligible = df[df["delivery_duration_days"].notna() & df["split"].isin(["train", "val", "test"])]
        cap = eligible.loc[eligible["split"] == "train", "delivery_duration_days"].quantile(0.99)
        test = eligible[(eligible["split"] == "test") & (eligible["delivery_duration_days"] <= cap)]
        y = test["delivery_duration_days"]
        pred = bundle["pipeline"].predict(test[bundle["features"]])
        metrics = {"n_test": len(test), "mae": float(mean_absolute_error(y, pred)),
                   "rmse": float(np.sqrt(mean_squared_error(y, pred))), "r2": float(r2_score(y, pred)),
                   "median_ae": float(np.median(np.abs(y.to_numpy() - pred))),
                   "mean_actual": float(y.mean()), "mean_pred": float(np.mean(pred))}
    elif name.startswith("forecast_"):
        col = "late_rate" if name == "forecast_late_rate" else "total_line_item_quantity"
        file = "delay_timeseries_monthly.csv" if col == "late_rate" else "volume_timeseries_monthly.csv"
        ts = read_table(paths["processed"] / file)
        _, _, test = _forecast_splits(ts, col)
        pred = bundle["pipeline"].predict(test[bundle["features"]])
        lower, upper = bundle.get("prediction_bounds", [None, None])
        if lower is not None or upper is not None:
            pred = np.clip(pred, lower, upper)
        naive = test["lag_1"].to_numpy(dtype=float)
        weight = test["sample_weight"].to_numpy(dtype=float) if "sample_weight" in test else None
        mean_pred = np.full(len(test), float(bundle.get("training_mean", test["y"].mean())))
        mae = lambda actual, forecast: float(mean_absolute_error(actual, forecast, sample_weight=weight))
        metrics = {"frequency": "monthly", "selected_model": bundle.get("selected_model"),
                   "n_test": len(test), "mae": mae(test["y"], pred),
                   "rmse": float(np.sqrt(mean_squared_error(test["y"], pred, sample_weight=weight))),
                   "metric_weighting": "shipment_count_weighted" if weight is not None else "unweighted",
                   "baselines": {
                       "naive_lag1": {"mae": mae(test["y"], naive)},
                       "development_mean": {"mae": mae(test["y"], mean_pred)},
                   },
                   "beats_naive_lag1": bool(mae(test["y"], pred) < mae(test["y"], naive)),
                   "beats_development_mean": bool(mae(test["y"], pred) < mae(test["y"], mean_pred)),
                   "selection_note": "Model selected using validation data; test baseline comparisons are final holdout diagnostics.",
                   "actual": test["y"].tolist(), "predicted": pred.tolist()}
    elif name == "vendor_segmentation":
        vendors = read_table(paths["processed"] / "vendor_features.csv")
        features = bundle["features"]
        vendors = vendors.dropna(subset=["late_rate"]).copy()
        for col in features:
            vendors[col] = vendors[col].fillna(vendors[col].median())
        pipe = bundle["pipeline"]
        dominant = vendors["shipment_count"] > float(bundle["dominant_threshold"])
        small = vendors["shipment_count"] < int(bundle["min_history"])
        profile_outlier = vendors["Vendor"].isin(bundle.get("profile_outlier_vendors", []))
        cluster_rows = vendors[~dominant & ~small & ~profile_outlier].copy()
        model_features = cluster_rows[features].copy()
        model_features[bundle["log_features"]] = np.log1p(model_features[bundle["log_features"]].clip(lower=0))
        scaled = pipe["scaler"].transform(model_features.to_numpy())
        labels = pipe["kmeans"].predict(scaled)
        sizes = pd.Series(labels).value_counts().sort_index()
        metrics = {"kmeans_k": int(pipe["kmeans"].n_clusters), "n_vendors": len(vendors), "n_clustered": len(cluster_rows),
                   "n_insufficient_history": int(small.sum()), "n_dominant_separated": int(dominant.sum()),
                   "n_profile_outliers_separated": int(profile_outlier.sum()),
                   "segment_sizes": {str(k): int(v) for k, v in sizes.items()},
                   "silhouette": float(silhouette_score(scaled, labels)) if len(set(labels)) > 1 and len(labels) > len(set(labels)) else None,
                   "inertia": float(pipe["kmeans"].inertia_),
                   "caveat": "Silhouette applies only to the modeled subset. Segments describe profiles, not vendor quality."}
    elif name == "anomaly_vendor_kpi":
        scored = read_table(paths["processed"] / "anomaly_scores_vendor_kpi.csv")
        test = scored[scored["split"] == "test"]
        flagged = test[test["is_anomaly"] == 1]
        unflagged = test[test["is_anomaly"] == 0]
        metrics = {
            "label": bundle.get("label"),
            "n_test_periods": len(test),
            "n_unusual": int(test["is_anomaly"].sum()),
            "anomaly_rate": float(test["is_anomaly"].mean()) if len(test) else None,
            "mean_late_rate_flagged": float(flagged["late_rate"].mean()) if len(flagged) else None,
            "mean_late_rate_unflagged": float(unflagged["late_rate"].mean()) if len(unflagged) else None,
            "n_deteriorating": int(test["is_deteriorating"].sum()) if "is_deteriorating" in test else None,
            "disruption_signal_rate": float(test["disruption_signal"].mean())
            if "disruption_signal" in test and len(test)
            else None,
            "injected_disruption_check": (bundle.get("metrics") or {}).get("injected_disruption_check"),
            "note": "Unsupervised supplier-period flags; detection rate comes from labelled synthetic injections.",
        }
    else:
        suffix = "unusual_profile" if name.endswith("unusual_profile") else "retrospective"
        scores_path = paths["processed"] / f"anomaly_scores_{suffix}.csv"
        scored = read_table(scores_path)
        test = scored[scored["split"] == "test"]
        metrics = {"label": "unusual_shipment_profile", "n_test": len(test), "n_unusual": int(test["is_anomaly"].sum()),
                   "anomaly_rate": float(test["is_anomaly"].mean()) if len(test) else None,
                   "mean_anomaly_score": float(test["anomaly_score"].mean()) if len(test) else None,
                   "note": "Unsupervised unusual-profile flags, not delay predictions. There are no ground-truth anomaly labels.",
                   "source_scores": str(scores_path)}
        if name.endswith("unusual_profile"):
            late_labels = read_table(paths["processed"] / "shipments.csv")[["ID", "is_late"]]
            diagnostic = test.merge(late_labels, on="ID", how="left").dropna(subset=["is_late"])
            flagged = diagnostic[diagnostic["is_anomaly"] == 1]
            unflagged = diagnostic[diagnostic["is_anomaly"] == 0]
            metrics["late_rate_diagnostic"] = {
                "flagged": float(flagged["is_late"].mean()) if len(flagged) else None,
                "unflagged": float(unflagged["is_late"].mean()) if len(unflagged) else None,
                "interpretation": "Descriptive association only; it is not anomaly-model accuracy or a delay-prediction metric.",
            }
    result = {"model": name, "artifact": MODEL_ARTIFACTS[name], "evaluated_at": datetime.now(timezone.utc).isoformat(), "test": metrics}
    out = paths["metrics"] / f"evaluation_{name}.json"
    save_json(out, result)
    result["report_path"] = str(out)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate saved SCOPE models using held-out data.")
    parser.add_argument("--model", choices=["all", *MODEL_ARTIFACTS], default="all")
    args = parser.parse_args()
    results, failures = evaluate_models(args.model)
    print(json.dumps({"evaluated": list(results), "failed": failures}, indent=2))
    if failures:
        raise SystemExit(1)


def evaluate_models(model: str = "all") -> tuple[dict[str, Any], dict[str, str]]:
    """Evaluate one saved model or all models and return results plus failures."""
    if model != "all" and model not in MODEL_ARTIFACTS:
        raise ValueError(f"Unknown model {model!r}. Choose from: {', '.join(MODEL_ARTIFACTS)}")
    names = MODEL_ARTIFACTS if model == "all" else [model]
    results = {}
    failures = {}
    for name in names:
        try:
            results[name] = _evaluate(name)
        except Exception as exc:
            failures[name] = str(exc)
    return results, failures


if __name__ == "__main__":
    main()
