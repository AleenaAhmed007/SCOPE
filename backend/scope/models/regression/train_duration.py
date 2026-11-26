"""Phase 04 — PO-to-client delivery duration regression."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
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


class GroupMedianRegressor(BaseEstimator, RegressorMixin):
    """Predict the training median within a categorical group (fallback = global)."""

    def __init__(self, group_col: str = "Shipment_Mode") -> None:
        self.group_col = group_col

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "GroupMedianRegressor":
        frame = X.copy()
        frame["__y__"] = np.asarray(y, dtype=float)
        self.global_median_ = float(np.median(frame["__y__"]))
        self.group_medians_ = (
            frame.groupby(self.group_col)["__y__"].median().to_dict()
            if self.group_col in frame.columns
            else {}
        )
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self.group_col not in X.columns:
            return np.full(len(X), self.global_median_)
        return (
            X[self.group_col]
            .map(self.group_medians_)
            .fillna(self.global_median_)
            .to_numpy(dtype=float)
        )


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

    # Models are selected on validation MAE, so the boosted models optimise an
    # absolute-error loss; the right-skewed target otherwise pulls squared-error
    # fits toward rare very long deliveries.
    models: dict[str, Any] = {
        "dummy_median": DummyRegressor(strategy="median"),
        "shipment_mode_median": GroupMedianRegressor(group_col="Shipment_Mode"),
        "gradient_boosting": GradientBoostingRegressor(
            loss="absolute_error",
            n_estimators=300,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42,
        ),
        "xgboost": XGBRegressor(
            objective="reg:absoluteerror",
            n_estimators=300,
            max_depth=5,
            learning_rate=0.04,
            subsample=0.85,
            colsample_bytree=0.75,
            random_state=42,
            n_jobs=2,
        ),
        "random_forest": RandomForestRegressor(
            n_estimators=300,
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
    baseline_names = {"dummy_median", "shipment_mode_median"}
    for name, reg in models.items():
        if name in baseline_names:
            # Group/global medians operate on the raw frame (need the group column).
            model = reg
            model.fit(train[features], train["delivery_duration_days"])
            predict = lambda part, m=model: m.predict(part[features])
            pipe: Any = model
        else:
            pipe = Pipeline([("pre", build_preprocessor(num, cat)), ("model", reg)])
            pipe.fit(train[features], train["delivery_duration_days"])
            predict = lambda part, p=pipe: p.predict(part[features])
        split_metrics = {}
        for split_name, part in [("val", val), ("test", test)]:
            if len(part) == 0:
                continue
            pred = predict(part)
            split_metrics[split_name] = _reg_metrics(part["delivery_duration_days"], pred)
        results["models"][name] = split_metrics
        mae = split_metrics.get("val", {}).get("mae", float("inf"))
        if mae < best_mae:
            best_mae, best_name, best_pipe = mae, name, pipe

    # Prefer a simple baseline unless a learned model clearly beats the stronger
    # shipment-mode median on validation (>=1% MAE reduction).
    mode_val_mae = results["models"]["shipment_mode_median"].get("val", {}).get("mae")
    global_val_mae = results["models"]["dummy_median"].get("val", {}).get("mae")
    if (
        best_name not in baseline_names
        and mode_val_mae is not None
        and best_mae > mode_val_mae * 0.99
    ):
        best_name = "shipment_mode_median"
        best_mae = float(mode_val_mae)
        best_pipe = models["shipment_mode_median"]
        best_pipe.fit(train[features], train["delivery_duration_days"])

    baseline_val_mae = mode_val_mae if mode_val_mae is not None else global_val_mae
    results["selected_model_beats_median_baseline_on_validation"] = bool(
        baseline_val_mae is not None
        and best_name not in baseline_names
        and best_mae < baseline_val_mae - 1e-9
    )

    # If no learned model beats the median on validation, the saved "model" is
    # the median itself. Say so explicitly so consumers never present it as an
    # order-specific ML estimate (walk-forward checks confirmed no signal).
    prediction_basis = (
        "historical_median_baseline" if best_name in baseline_names else "ml_model"
    )
    results["prediction_basis"] = prediction_basis
    bundle = {
        "pipeline": best_pipe,
        "model_name": best_name,
        "prediction_basis": prediction_basis,
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
