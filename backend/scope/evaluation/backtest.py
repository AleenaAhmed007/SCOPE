"""Walk-forward (unseen-quarter) backtests for SCOPE models.

Each quarter is predicted by models trained only on outcomes already delivered
before that quarter starts, so every score is on genuinely unseen data. This
complements the single chronological test split with many out-of-time checks.
"""

from __future__ import annotations

from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    average_precision_score,
    mean_absolute_error,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline

from scope.logging_config import setup_logging
from scope.models.common import (
    CalibratedClassifier,
    build_preprocessor,
    calibration_report,
    f1_optimal_threshold,
    fit_platt,
    load_shipments,
    project_paths,
    save_json,
)
from scope.models.forecasting.train_forecast import _candidates, _make_lag_frame

logger = setup_logging()

N_QUARTERS = 11
CALIBRATION_QUARTERS = 2


def _known_before(df: pd.DataFrame, ts: pd.Timestamp) -> pd.DataFrame:
    return df[(df["Scheduled_Delivery_Date_Parsed"] < ts) & (df["Delivered_To_Client_Date_Parsed"] < ts)]


def backtest_late_delivery(df: pd.DataFrame) -> dict[str, Any]:
    """Retrain + recalibrate before each quarter (the deployed drift procedure)."""
    bundle = joblib.load(project_paths()["models"] / "late_delivery_classifier" / "model.joblib")
    base = getattr(bundle["pipeline"], "base_pipeline", bundle["pipeline"])
    features = bundle["features"]
    lab = df[df["is_late"].notna() & df["split"].isin(["train", "val", "test"])].copy()
    lab["is_late"] = lab["is_late"].astype(int)
    lab["quarter"] = lab["Scheduled_Delivery_Date_Parsed"].dt.to_period("Q")
    rows = []
    for q in sorted(lab["quarter"].unique())[-N_QUARTERS:]:
        target = lab[lab["quarter"] == q]
        if len(target) < 50 or target["is_late"].nunique() < 2:
            continue
        q_start = q.start_time
        cal_start = (q - CALIBRATION_QUARTERS).start_time
        fit_rows = _known_before(lab, cal_start)
        cal_rows = _known_before(lab, q_start)
        cal_rows = cal_rows[cal_rows["Scheduled_Delivery_Date_Parsed"] >= cal_start]
        if len(cal_rows) < 100 or cal_rows["is_late"].nunique() < 2:
            continue
        model = clone(base).fit(fit_rows[features], fit_rows["is_late"])
        raw_cal = model.predict_proba(cal_rows[features])[:, 1]
        a, b = fit_platt(raw_cal, cal_rows["is_late"].to_numpy())
        calibrate = CalibratedClassifier(model, a, b).calibrate
        threshold = f1_optimal_threshold(cal_rows["is_late"].to_numpy(), calibrate(raw_cal))
        raw = model.predict_proba(target[features])[:, 1]
        proba = calibrate(raw)
        pred = (proba >= threshold).astype(int)
        y = target["is_late"]
        vendor = target["vendor_hist_late_rate"].fillna(fit_rows["is_late"].mean())
        cal = calibration_report(y, proba)
        rows.append(
            {
                "quarter": str(q),
                "n": int(len(target)),
                "actual_late_rate": float(y.mean()),
                "mean_predicted_raw": float(raw.mean()),
                "mean_predicted_calibrated": float(proba.mean()),
                "ece_raw": calibration_report(y, raw)["ece"],
                "ece_calibrated": cal["ece"],
                "brier_calibrated": cal["brier"],
                "brier_constant": cal["brier_constant_prevalence"],
                "roc_auc": float(roc_auc_score(y, proba)),
                "vendor_only_roc_auc": float(roc_auc_score(y, vendor)),
                "pr_auc": float(average_precision_score(y, proba)),
                "threshold": float(threshold),
                "flag_rate": float(pred.mean()),
                "precision": float(precision_score(y, pred, zero_division=0)),
                "recall": float(recall_score(y, pred, zero_division=0)),
            }
        )
    table = pd.DataFrame(rows)
    summary = {}
    if len(table):
        summary = {
            "n_quarters": int(len(table)),
            "mean_roc_auc": float(table["roc_auc"].mean()),
            "min_roc_auc": float(table["roc_auc"].min()),
            "mean_vendor_only_roc_auc": float(table["vendor_only_roc_auc"].mean()),
            "quarters_model_beats_vendor_only": int((table["roc_auc"] > table["vendor_only_roc_auc"]).sum()),
            "mean_ece_raw": float(table["ece_raw"].mean()),
            "mean_ece_calibrated": float(table["ece_calibrated"].mean()),
            "quarters_brier_beats_constant": int((table["brier_calibrated"] < table["brier_constant"]).sum()),
            "mean_precision": float(table["precision"].mean()),
            "mean_recall": float(table["recall"].mean()),
            "min_recall": float(table["recall"].min()),
        }
    return {
        "procedure": f"refit on outcomes known before calibration window; Platt + F1 threshold on previous {CALIBRATION_QUARTERS} quarters",
        "summary": summary,
        "quarters": rows,
    }


def backtest_duration(df: pd.DataFrame) -> dict[str, Any]:
    bundle = joblib.load(project_paths()["models"] / "delivery_duration_regressor" / "model.joblib")
    d = df[df["delivery_duration_days"].notna() & df["split"].isin(["train", "val", "test"])].copy()
    d["quarter"] = d["Scheduled_Delivery_Date_Parsed"].dt.to_period("Q")
    rows = []
    for q in sorted(d["quarter"].unique())[-8:]:
        target = d[d["quarter"] == q]
        fit_rows = _known_before(d, q.start_time)
        if len(target) < 50 or len(fit_rows) < 500:
            continue
        fit_rows = fit_rows[fit_rows["delivery_duration_days"] <= fit_rows["delivery_duration_days"].quantile(0.99)]
        model = Pipeline(
            [
                ("pre", build_preprocessor(bundle["numeric"], bundle["categorical"])),
                ("model", RandomForestRegressor(n_estimators=250, max_depth=12, min_samples_leaf=5, random_state=42, n_jobs=2)),
            ]
        ).fit(fit_rows[bundle["features"]], fit_rows["delivery_duration_days"])
        y = target["delivery_duration_days"]
        rows.append(
            {
                "quarter": str(q),
                "n": int(len(target)),
                "ml_mae": float(mean_absolute_error(y, model.predict(target[bundle["features"]]))),
                "median_baseline_mae": float(mean_absolute_error(y, np.full(len(y), fit_rows["delivery_duration_days"].median()))),
            }
        )
    wins = sum(r["ml_mae"] < r["median_baseline_mae"] for r in rows)
    return {
        "quarters": rows,
        "ml_beats_median_quarters": int(wins),
        "n_quarters": len(rows),
        "deployed_prediction_basis": bundle.get("prediction_basis"),
        "conclusion": "ML adds value" if rows and wins > len(rows) / 2 else "No reliable ML signal; serve historical median, flagged as baseline.",
    }


def backtest_forecasts() -> dict[str, Any]:
    paths = project_paths()
    out = {}
    for file, col in (
        ("delay_timeseries_monthly.parquet", "late_rate"),
        ("volume_timeseries_monthly.parquet", "total_line_item_quantity"),
    ):
        ts = pd.read_parquet(paths["processed"] / file).dropna(subset=[col]).sort_values("period_start").reset_index(drop=True)
        frame = _make_lag_frame(ts[col])
        feats = [c for c in frame.columns if c != "y"]
        errors: dict[str, list[float]] = {}
        for origin in range(len(frame) - 24, len(frame) - 1, 2):
            fit_part, nxt = frame.iloc[:origin], frame.iloc[origin : origin + 1]
            for name, model in _candidates().items():
                try:
                    pred = float(model.fit(fit_part[feats], fit_part["y"]).predict(nxt[feats])[0])
                except Exception:  # noqa: BLE001
                    continue
                errors.setdefault(name, []).append(abs(pred - float(nxt["y"].iloc[0])))
        n = max(len(v) for v in errors.values())
        mae = {k: float(np.mean(v)) for k, v in errors.items() if len(v) == n}
        bundle_name = "forecast_late_rate_monthly" if col == "late_rate" else "forecast_volume_quantity_monthly"
        deployed = joblib.load(paths["models"] / bundle_name / "model.joblib").get("selected_model")
        out[col] = {
            "n_origins": n,
            "mae": mae,
            "best": min(mae, key=mae.get),
            "deployed_model": deployed,
            "deployed_rank": sorted(mae, key=mae.get).index(deployed) + 1 if deployed in mae else None,
        }
    return out


def run_backtests() -> dict[str, Any]:
    df = load_shipments()
    results = {
        "late_delivery": backtest_late_delivery(df),
        "duration": backtest_duration(df),
        "forecasting": backtest_forecasts(),
    }
    save_json(project_paths()["metrics"] / "walk_forward_backtest.json", results)
    logger.info("Walk-forward backtests complete")
    return results


if __name__ == "__main__":
    import json

    print(json.dumps(run_backtests(), indent=2, default=str))
