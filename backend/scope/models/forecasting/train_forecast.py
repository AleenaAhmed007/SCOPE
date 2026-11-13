"""Phase 05 — Time-series forecasting for late rate and shipment volume."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

from scope.logging_config import setup_logging
from scope.models.common import project_paths, save_json, save_model_bundle

logger = setup_logging()


class LagOneRegressor:
    """Persistence baseline that predicts the last observed period."""

    def fit(self, X: pd.DataFrame, y: pd.Series, sample_weight=None) -> "LagOneRegressor":
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return X["lag_1"].to_numpy(dtype=float)


def _make_lag_frame(series: pd.Series, lags: list[int] = [1, 2, 3, 4]) -> pd.DataFrame:
    df = pd.DataFrame({"y": series.astype(float)})
    for lag in lags:
        df[f"lag_{lag}"] = df["y"].shift(lag)
    df["rolling_mean_4"] = df["y"].shift(1).rolling(4).mean()
    return df.dropna()


def _forecast_splits(ts: pd.DataFrame, value_col: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Use the same monthly lag frame and chronological split for train/eval."""
    ordered = ts.dropna(subset=[value_col]).sort_values("period_start").reset_index(drop=True)
    frame = _make_lag_frame(ordered[value_col])
    if value_col == "late_rate" and "shipment_count" in ordered:
        frame["sample_weight"] = ordered.loc[frame.index, "shipment_count"].astype(float).to_numpy()
    n_test = max(8, int(len(frame) * 0.2))
    development = frame.iloc[:-n_test]
    test = frame.iloc[-n_test:]
    n_val = max(8, int(len(development) * 0.2))
    train = development.iloc[:-n_val]
    val = development.iloc[-n_val:]
    return train, val, test


def _train_one(ts: pd.DataFrame, value_col: str, name: str) -> dict[str, Any]:
    train, val, test = _forecast_splits(ts, value_col)
    development = pd.concat([train, val])
    frame = pd.concat([train, val, test])
    feats = [c for c in frame.columns if c not in {"y", "sample_weight"}]
    weighted = "sample_weight" in frame
    train_weight = train["sample_weight"] if weighted else None
    val_weight = val["sample_weight"] if weighted else None
    test_weight = test["sample_weight"] if weighted else None
    candidates = {
        "naive_lag1": LagOneRegressor(),
        "persistence_linear": LinearRegression(),
        "gradient_boosting": GradientBoostingRegressor(random_state=42, n_estimators=100, max_depth=2, learning_rate=0.03, loss="huber"),
        "random_forest": RandomForestRegressor(n_estimators=300, min_samples_leaf=5, max_features=0.8, random_state=42, n_jobs=2),
        "extra_trees": ExtraTreesRegressor(n_estimators=300, min_samples_leaf=5, max_features=0.8, random_state=42, n_jobs=2),
        "mean_baseline": DummyRegressor(strategy="mean"),
    }
    lower, upper = (0.0, 1.0) if "rate" in name else (0.0, None)
    validation_mae = {}
    for candidate_name, candidate in candidates.items():
        candidate.fit(train[feats], train["y"], sample_weight=train_weight)
        val_pred = candidate.predict(val[feats])
        val_pred = np.clip(val_pred, lower, upper) if upper is not None else np.maximum(val_pred, lower)
        validation_mae[candidate_name] = float(
            mean_absolute_error(val["y"], val_pred, sample_weight=val_weight)
        )
    selected_name = min(validation_mae, key=validation_mae.get)
    model = candidates[selected_name]
    development_weight = development["sample_weight"] if weighted else None
    model.fit(development[feats], development["y"], sample_weight=development_weight)
    pred = model.predict(test[feats])
    pred = np.clip(pred, lower, upper) if upper is not None else np.maximum(pred, lower)
    naive_pred = test["lag_1"].to_numpy()
    development_mean = float(
        np.average(development["y"], weights=development_weight)
        if weighted else development["y"].mean()
    )
    mean_pred = np.full(len(test), development_mean)
    model_mae = float(mean_absolute_error(test["y"], pred, sample_weight=test_weight))
    naive_mae = float(mean_absolute_error(test["y"], naive_pred, sample_weight=test_weight))
    mean_mae = float(mean_absolute_error(test["y"], mean_pred, sample_weight=test_weight))
    metrics = {
        "mae": model_mae,
        "rmse": float(np.sqrt(mean_squared_error(test["y"], pred))),
        "selected_model": selected_name,
        "validation_mae": validation_mae,
        "validation_selected_mae": validation_mae[selected_name],
        "naive_lag1_test_mae": naive_mae,
        "mean_baseline_test_mae": mean_mae,
        "beats_naive_baseline_on_test": model_mae < naive_mae,
        "beats_mean_baseline_on_test": model_mae < mean_mae,
        "test_result_note": "Selected with validation data; test comparison is a final holdout diagnostic.",
        "metric_weighting": "shipment_count_weighted" if weighted else "unweighted",
        "n_train": len(development),
        "n_validation": len(val),
        "n_test": len(test),
        "last_actual": test["y"].tolist(),
        "last_pred": pred.tolist(),
    }
    bundle = {
        "pipeline": model,
        "features": feats,
        "target": value_col,
        "series_name": name,
        "prediction_bounds": [lower, upper],
        "selected_model": selected_name,
        "training_mean": development_mean,
        "metrics": metrics,
    }
    out = save_model_bundle(f"forecast_{name}", bundle)
    metrics["artifact_dir"] = str(out)
    return metrics


def _suitability(ts: pd.DataFrame, value_col: str, name: str) -> dict[str, Any]:
    s = ts.dropna(subset=[value_col]).sort_values("period_start")
    n = len(s)
    gaps = int(s["period_start"].diff().dt.days.gt(45).sum()) if n else 0
    recommend_lstm = n >= 120 and gaps < n * 0.1
    return {
        "series": name,
        "n_periods": n,
        "min_period": str(s["period_start"].min()) if n else None,
        "max_period": str(s["period_start"].max()) if n else None,
        "approx_gap_flags": gaps,
        "mean": float(s[value_col].mean()) if n else None,
        "std": float(s[value_col].std()) if n else None,
        "lstm_recommended": recommend_lstm,
        "rationale": (
            "Monthly sample length and regularity support trying a neural model"
            if recommend_lstm
            else "Monthly history is too short or irregular; prefer classical baselines."
        ),
    }


def _baseline_naive(ts: pd.DataFrame, value_col: str) -> dict[str, Any]:
    _, _, test = _forecast_splits(ts, value_col)
    if len(test) < 1:
        return {"status": "insufficient_data"}
    weight = test["sample_weight"] if "sample_weight" in test else None
    actual = test["y"]
    pred = test["lag_1"]
    return {
        "model": "naive_lag1",
        "mae": float(mean_absolute_error(actual, pred, sample_weight=weight)),
        "rmse": float(np.sqrt(mean_squared_error(actual, pred, sample_weight=weight))),
        "n_test": len(test),
        "metric_weighting": "shipment_count_weighted" if weight is not None else "unweighted",
    }


def train_forecasts() -> dict[str, Any]:
    paths = project_paths()
    delay = pd.read_parquet(paths["processed"] / "delay_timeseries_monthly.parquet")
    volume = pd.read_parquet(paths["processed"] / "volume_timeseries_monthly.parquet")

    suitability = {
        "late_rate_monthly": _suitability(delay, "late_rate", "late_rate_monthly"),
        "volume_monthly": _suitability(
            volume, "total_line_item_quantity", "volume_quantity_monthly"
        ),
    }
    # Keep neural models out unless monthly history and validation gain justify them.
    results = {
        "note": (
            "Volume series is shipment/order quantity proxy, not verified warehouse demand."
        ),
        "suitability": suitability,
        "baselines": {
            "late_rate_naive": _baseline_naive(delay, "late_rate"),
            "volume_naive": _baseline_naive(volume, "total_line_item_quantity"),
        },
        "frequency": "monthly",
        "late_rate_monthly": _train_one(delay, "late_rate", "late_rate_monthly"),
        "volume_monthly": _train_one(
            volume, "total_line_item_quantity", "volume_quantity_monthly"
        ),
        "lstm": {
            "trained": False,
            "reason": "Classical monthly lag models are compared with explicit baselines; no neural model is justified without a demonstrated validation gain.",
        },
    }
    save_json(paths["metrics"] / "forecasting.json", results)
    save_json(paths["metrics"] / "forecast_suitability.json", suitability)
    logger.info("Forecast models trained")
    return results


if __name__ == "__main__":
    print(train_forecasts())
