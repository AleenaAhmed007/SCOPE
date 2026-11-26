"""Phase 05 — Time-series forecasting for late rate and shipment volume.

Per the proposal, a classical ARIMA model is a candidate alongside lag-feature
regressors and naive/mean baselines; the model is chosen on validation MAE.
Shipment volume is additionally forecast per product category.
"""

from __future__ import annotations

import re
import warnings
from itertools import product
from typing import Any

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

from scope.data.table_io import read_table
from scope.features.volume_features import build_volume_timeseries
from scope.logging_config import setup_logging
from scope.models.common import load_shipments, project_paths, save_json, save_model_bundle

logger = setup_logging()


class LagOneRegressor:
    """Persistence baseline that predicts the last observed period."""

    def fit(self, X: pd.DataFrame, y: pd.Series, sample_weight=None) -> "LagOneRegressor":
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return X["lag_1"].to_numpy(dtype=float)


class ARIMAForecaster:
    """(S)ARIMA one-step-ahead forecaster with an sklearn-style fit/predict API.

    ``fit`` picks the order by AIC on the training series. ``predict(X)`` returns
    rolling one-step-ahead forecasts for consecutive periods that directly follow
    the fitted history. After each forecast, the realised value of that period
    (the next row's ``lag_1``) is appended to the state without refitting, so no
    information from the forecast period itself is used.
    """

    def __init__(self, seasonal_period: int = 12) -> None:
        self.seasonal_period = seasonal_period

    def fit(self, X: pd.DataFrame, y: pd.Series, sample_weight=None) -> "ARIMAForecaster":
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        y_arr = np.asarray(y, dtype=float)
        seasonal_orders = [(0, 0, 0, 0)]
        if len(y_arr) >= 3 * self.seasonal_period:
            seasonal_orders.append((1, 0, 0, self.seasonal_period))
        best = None
        for (p, d, q), seasonal in product(product((0, 1, 2), (0, 1), (0, 1)), seasonal_orders):
            if p == q == 0 and seasonal[0] == 0:
                continue
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    res = SARIMAX(
                        y_arr,
                        order=(p, d, q),
                        seasonal_order=seasonal,
                        trend="c" if d == 0 else "n",
                        enforce_stationarity=False,
                        enforce_invertibility=False,
                    ).fit(disp=False)
            except Exception:  # noqa: BLE001 - skip orders that fail to converge
                continue
            if np.isfinite(res.aic) and (best is None or res.aic < best[0]):
                best = (float(res.aic), (p, d, q), seasonal, res)
        if best is None:
            raise RuntimeError("No ARIMA order could be fitted.")
        self.aic_, self.order_, self.seasonal_order_, self.result_ = best
        self.last_observed_ = float(y_arr[-1])
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        lag1 = X["lag_1"].to_numpy(dtype=float)
        if len(lag1) and not np.isclose(lag1[0], self.last_observed_, rtol=1e-9, atol=1e-12):
            raise ValueError(
                "ARIMAForecaster.predict expects the periods immediately after the fitted history."
            )
        res = self.result_
        preds = np.empty(len(lag1))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for i in range(len(lag1)):
                preds[i] = float(np.asarray(res.forecast(1))[0])
                if i + 1 < len(lag1):
                    res = res.append([lag1[i + 1]])
        return preds


def _make_lag_frame(
    series: pd.Series, lags: list[int] | None = None
) -> pd.DataFrame:
    """Build supervised lag features for one-step-ahead forecasting."""
    lags = lags or [1, 2, 3, 4, 6, 12]
    df = pd.DataFrame({"y": series.astype(float)})
    for lag in lags:
        df[f"lag_{lag}"] = df["y"].shift(lag)
    df["rolling_mean_4"] = df["y"].shift(1).rolling(4).mean()
    df["rolling_mean_12"] = df["y"].shift(1).rolling(12).mean()
    df["rolling_std_4"] = df["y"].shift(1).rolling(4).std()
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


def _candidates() -> dict[str, Any]:
    """Fresh, unfitted forecast candidates."""
    return {
        "naive_lag1": LagOneRegressor(),
        "mean_baseline": DummyRegressor(strategy="mean"),
        "persistence_linear": LinearRegression(),
        "gradient_boosting": GradientBoostingRegressor(
            random_state=42,
            n_estimators=150,
            max_depth=2,
            learning_rate=0.03,
            loss="huber",
        ),
        "random_forest": RandomForestRegressor(
            n_estimators=400,
            min_samples_leaf=3,
            max_features=0.8,
            random_state=42,
            n_jobs=2,
        ),
        "extra_trees": ExtraTreesRegressor(
            n_estimators=400,
            min_samples_leaf=3,
            max_features=0.8,
            random_state=42,
            n_jobs=2,
        ),
        "arima": ARIMAForecaster(),
    }


def _train_one(ts: pd.DataFrame, value_col: str, name: str) -> dict[str, Any]:
    train, val, test = _forecast_splits(ts, value_col)
    development = pd.concat([train, val])
    frame = pd.concat([train, val, test])
    feats = [c for c in frame.columns if c not in {"y", "sample_weight"}]
    weighted = "sample_weight" in frame
    train_weight = train["sample_weight"] if weighted else None
    val_weight = val["sample_weight"] if weighted else None
    test_weight = test["sample_weight"] if weighted else None
    lower, upper = (0.0, 1.0) if "rate" in name else (0.0, None)

    def bound(values: np.ndarray) -> np.ndarray:
        return np.clip(values, lower, upper) if upper is not None else np.maximum(values, lower)

    # Rolling-origin selection: refit every candidate on an expanding window
    # and forecast the next block, across the whole validation period. A single
    # validation window picked models that lost to the mean on later data.
    # The window spans the last 36 development months (not just the ~18-month
    # validation slice): one short window was too noisy to rank candidates.
    step = 3
    first_origin = max(24, min(len(train), len(development) - 36))
    origins = list(range(first_origin, len(development), step))
    errors: dict[str, list[float]] = {name_: [] for name_ in _candidates()}
    weights: list[float] = []
    failed: dict[str, str] = {}
    for start in origins:
        fit_part = development.iloc[:start]
        block = development.iloc[start : start + step]
        fit_w = fit_part["sample_weight"] if weighted else None
        block_w = block["sample_weight"].to_numpy() if weighted else np.ones(len(block))
        weights.extend(block_w.tolist())
        for candidate_name, candidate in _candidates().items():
            if candidate_name in failed:
                continue
            try:
                candidate.fit(fit_part[feats], fit_part["y"], sample_weight=fit_w)
                block_pred = bound(candidate.predict(block[feats]))
            except Exception as exc:  # noqa: BLE001 - e.g. statsmodels missing / no convergence
                failed[candidate_name] = str(exc)
                continue
            errors[candidate_name].extend(np.abs(block["y"].to_numpy() - block_pred).tolist())
    w = np.asarray(weights)
    validation_mae = {
        k: float(np.average(v, weights=w)) for k, v in errors.items() if k not in failed and len(v) == len(w)
    }
    # Recent-origin MAE catches models that only look good early then drift.
    recent_cut = max(1, len(w) // 3)
    recent_mae = {
        k: float(np.average(v[-recent_cut:], weights=w[-recent_cut:]))
        for k, v in errors.items()
        if k not in failed and len(v) == len(w)
    }
    best_name = min(validation_mae, key=validation_mae.get)
    # Prefer a baseline unless a complex model is clearly (>=5%) better on
    # both full and recent rolling-origin windows. Short series overfit easily.
    baseline_margin = 1.05
    selected_name = best_name
    for baseline in ("mean_baseline", "naive_lag1"):
        if baseline not in validation_mae:
            continue
        full_ok = validation_mae[baseline] <= validation_mae[best_name] * baseline_margin
        recent_ok = recent_mae.get(baseline, float("inf")) <= recent_mae.get(best_name, 0.0) * baseline_margin
        if full_ok or recent_ok:
            selected_name = baseline
            break
    # If an ML model remains selected, require it to beat naive on the recent
    # window; otherwise fall back to the stronger of mean/naive.
    if selected_name not in {"mean_baseline", "naive_lag1"}:
        naive_recent = recent_mae.get("naive_lag1")
        mean_recent = recent_mae.get("mean_baseline")
        model_recent = recent_mae.get(selected_name)
        if model_recent is not None and naive_recent is not None and model_recent > naive_recent:
            selected_name = (
                "mean_baseline"
                if mean_recent is not None and mean_recent <= naive_recent
                else "naive_lag1"
            )

    # Final gate on the chronological validation holdout (fit on train only).
    # Rolling-origin averages can hide end-of-series regime shifts that show up
    # on the true held-out months used for selection.
    holdout_mae: dict[str, float] = {}
    for candidate_name in {selected_name, "mean_baseline", "naive_lag1", best_name}:
        if candidate_name in failed or candidate_name is None:
            continue
        try:
            cand = _candidates()[candidate_name]
            cand.fit(train[feats], train["y"], sample_weight=train_weight)
            holdout_pred = bound(cand.predict(val[feats]))
            holdout_mae[candidate_name] = float(
                mean_absolute_error(val["y"], holdout_pred, sample_weight=val_weight)
            )
        except Exception as exc:  # noqa: BLE001
            failed[candidate_name] = str(exc)
    if holdout_mae:
        holdout_best = min(holdout_mae, key=holdout_mae.get)
        if selected_name not in {"mean_baseline", "naive_lag1"}:
            ml_holdout = holdout_mae.get(selected_name, float("inf"))
            baseline_holdout = min(
                (
                    holdout_mae[b]
                    for b in ("mean_baseline", "naive_lag1")
                    if b in holdout_mae
                ),
                default=float("inf"),
            )
            # Volume/quantity series need a clearer holdout win; late-rate can
            # keep a tighter bar because the target is bounded.
            holdout_margin = 0.85 if upper is None else 0.98
            if ml_holdout > baseline_holdout * holdout_margin:
                selected_name = min(
                    (
                        b
                        for b in ("mean_baseline", "naive_lag1")
                        if b in holdout_mae
                    ),
                    key=holdout_mae.get,
                    default=holdout_best,
                )
        elif holdout_best in holdout_mae and holdout_mae[holdout_best] < holdout_mae.get(
            selected_name, float("inf")
        ):
            # Keep baseline preference, but allow switching mean <-> naive.
            if holdout_best in {"mean_baseline", "naive_lag1"}:
                selected_name = holdout_best

    development_weight = development["sample_weight"] if weighted else None
    development_mean = float(
        np.average(development["y"], weights=development_weight)
        if weighted else development["y"].mean()
    )

    # Quantity series (unbounded) are short and regime-sensitive. Walk-forward
    # diagnostics repeatedly preferred persistence over ML level models, so the
    # production default is naive_lag1 unless the holdout win is overwhelming
    # against both baselines (>=25% MAE reduction).
    if upper is None:
        naive_h = holdout_mae.get("naive_lag1")
        mean_h = holdout_mae.get("mean_baseline")
        ml_h = holdout_mae.get(selected_name) if selected_name not in {"mean_baseline", "naive_lag1"} else None
        strong_ml = (
            ml_h is not None
            and naive_h is not None
            and mean_h is not None
            and ml_h <= naive_h * 0.60
            and ml_h <= mean_h * 0.60
        )
        if not strong_ml:
            selected_name = "naive_lag1"

    candidates = _candidates()
    model = candidates[selected_name]
    model.fit(development[feats], development["y"], sample_weight=development_weight)
    pred = bound(model.predict(test[feats]))
    naive_pred = test["lag_1"].to_numpy()
    mean_pred = np.full(len(test), development_mean)
    model_mae = float(mean_absolute_error(test["y"], pred, sample_weight=test_weight))
    naive_mae = float(mean_absolute_error(test["y"], naive_pred, sample_weight=test_weight))
    mean_mae = float(mean_absolute_error(test["y"], mean_pred, sample_weight=test_weight))
    metrics = {
        "mae": model_mae,
        "rmse": float(np.sqrt(mean_squared_error(test["y"], pred, sample_weight=test_weight))),
        "selected_model": selected_name,
        "failed_candidates": failed,
        "validation_mae": validation_mae,
        "recent_validation_mae": recent_mae,
        "holdout_validation_mae": holdout_mae,
        "selection_method": (
            f"rolling-origin over validation period ({len(origins)} refits, step {step}); "
            f"baseline preferred within {int((baseline_margin - 1) * 100)}% on full or recent window; "
            "ML must beat naive on recent window and chronological val holdout"
        ),
        "best_unpenalised_model": best_name,
        "validation_selected_mae": validation_mae[selected_name],
        "naive_lag1_test_mae": naive_mae,
        "mean_baseline_test_mae": mean_mae,
        "beats_naive_baseline_on_test": model_mae < naive_mae,
        "beats_mean_baseline_on_test": model_mae < mean_mae,
        "test_result_note": "Selected with validation data only; test comparison is a final holdout diagnostic.",
        "is_baseline": selected_name in {"mean_baseline", "naive_lag1"},
        "metric_weighting": "shipment_count_weighted" if weighted else "unweighted",
        "n_train": len(development),
        "n_validation": len(val),
        "n_test": len(test),
        "last_actual": test["y"].tolist(),
        "last_pred": pred.tolist(),
    }
    if selected_name == "arima":
        metrics["arima_order"] = list(model.order_)
        metrics["arima_seasonal_order"] = list(model.seasonal_order_)
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


def _slug(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_") or "unknown"


def _train_by_product_group(min_periods: int = 48, max_zero_share: float = 0.5) -> dict[str, Any]:
    """Monthly volume forecast per product category (proposal: per-category demand)."""
    shipments = load_shipments()
    out: dict[str, Any] = {}
    for group, part in shipments.groupby("Product_Group", dropna=True):
        ts = build_volume_timeseries(part, freq="ME")
        n = len(ts)
        zero_share = float((ts["total_line_item_quantity"] == 0).mean()) if n else 1.0
        if n < min_periods or zero_share > max_zero_share:
            out[str(group)] = {
                "status": "skipped_insufficient_history",
                "n_periods": n,
                "zero_month_share": zero_share,
            }
            continue
        try:
            out[str(group)] = {"status": "ok", **_train_one(
                ts, "total_line_item_quantity", f"volume_{_slug(group)}_monthly"
            )}
        except Exception as exc:  # noqa: BLE001 - one category must not stop the rest
            out[str(group)] = {"status": "failed", "error": str(exc)}
    return out


def train_forecasts() -> dict[str, Any]:
    paths = project_paths()
    delay = read_table(paths["processed"] / "delay_timeseries_monthly.csv")
    volume = read_table(paths["processed"] / "volume_timeseries_monthly.csv")

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
        "volume_by_product_group": _train_by_product_group(),
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
