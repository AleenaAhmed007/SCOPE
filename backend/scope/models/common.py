"""Shared ML utilities: pipelines, metrics, artifact IO."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from scope.config.loader import get_project_root, load_yaml_config


def model_config(section: str | None = None) -> dict[str, Any]:
    """Return ``configs/models.yaml`` (or one section of it); empty dict if missing."""
    try:
        cfg = load_yaml_config("models")
    except FileNotFoundError:
        cfg = {}
    if section is None:
        return cfg
    return cfg.get(section) or {}


def signed_log1p(values: np.ndarray) -> np.ndarray:
    """Symmetric log transform for heavy-tailed money/quantity columns."""
    arr = np.asarray(values, dtype=float)
    return np.sign(arr) * np.log1p(np.abs(arr))


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def fit_platt(raw_proba: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Fit Platt scaling ``sigmoid(a * logit(p) + b)`` on held-out data."""
    from sklearn.linear_model import LogisticRegression

    lr = LogisticRegression(C=1e6, max_iter=1000)
    lr.fit(_logit(raw_proba).reshape(-1, 1), np.asarray(y, dtype=int))
    return float(lr.coef_[0, 0]), float(lr.intercept_[0])


class CalibratedClassifier:
    """A fitted classifier pipeline whose probabilities are Platt-calibrated.

    Exposes ``predict_proba`` (calibrated) so API/agents/evaluation get real
    probabilities, and ``named_steps``/``base_pipeline`` so SHAP can still
    explain the underlying model. Calibration is monotonic, so ranking (ROC-AUC,
    PR-AUC) is unchanged.
    """

    def __init__(self, base_pipeline: Any, a: float, b: float, fitted_on: str = "") -> None:
        self.base_pipeline = base_pipeline
        self.a = a
        self.b = b
        self.fitted_on = fitted_on

    @property
    def named_steps(self) -> Any:
        return self.base_pipeline.named_steps

    @property
    def classes_(self) -> np.ndarray:
        return self.base_pipeline.classes_

    def calibrate(self, raw_proba: np.ndarray) -> np.ndarray:
        return 1.0 / (1.0 + np.exp(-(self.a * _logit(raw_proba) + self.b)))

    def predict_raw_proba(self, X: pd.DataFrame) -> np.ndarray:
        return self.base_pipeline.predict_proba(X)[:, 1]

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        p = self.calibrate(self.predict_raw_proba(X))
        return np.column_stack([1 - p, p])

    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        return (self.predict_proba(X)[:, 1] >= threshold).astype(int)


def f1_optimal_threshold(y: np.ndarray, proba: np.ndarray) -> float:
    from sklearn.metrics import precision_recall_curve

    precision, recall, thresholds = precision_recall_curve(y, proba)
    if not len(thresholds):
        return 0.5
    f1 = 2 * precision[:-1] * recall[:-1] / (precision[:-1] + recall[:-1] + 1e-12)
    return float(thresholds[int(np.argmax(f1))])


def calibration_report(y: np.ndarray, proba: np.ndarray, n_bins: int = 10) -> dict[str, Any]:
    """Brier score, expected calibration error and mean predicted vs actual."""
    from sklearn.metrics import brier_score_loss

    y = np.asarray(y, dtype=float)
    proba = np.asarray(proba, dtype=float)
    bins = np.minimum((proba * n_bins).astype(int), n_bins - 1)
    ece = sum(
        abs(proba[bins == k].mean() - y[bins == k].mean()) * (bins == k).mean()
        for k in range(n_bins)
        if (bins == k).any()
    )
    return {
        "brier": float(brier_score_loss(y, proba)),
        "brier_constant_prevalence": float(brier_score_loss(y, np.full(len(y), y.mean()))),
        "ece": float(ece),
        "mean_predicted": float(proba.mean()),
        "actual_rate": float(y.mean()),
    }


def project_paths() -> dict[str, Path]:
    root = get_project_root()
    return {
        "root": root,
        "processed": root / "data" / "processed",
        "models": root / "reports" / "models",
        "metrics": root / "reports" / "metrics",
        "figures": root / "reports" / "figures",
    }


def load_shipments() -> pd.DataFrame:
    path = project_paths()["processed"] / "shipments.parquet"
    return pd.read_parquet(path)


def build_preprocessor(
    numeric_features: list[str],
    categorical_features: list[str],
    scale_numeric: bool = False,
) -> ColumnTransformer:
    """Build a fresh (unfitted) preprocessor.

    Tree models use raw imputed numerics. Linear models (``scale_numeric=True``)
    additionally get a signed log transform and standardisation, otherwise
    heavy-tailed USD/quantity columns dominate the coefficients.

    Always call this once per estimator: a single ColumnTransformer instance
    shared by several pipelines is silently refitted by each of them.
    """
    transformers = []
    if numeric_features:
        steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
        if scale_numeric:
            steps += [
                ("log", FunctionTransformer(signed_log1p, feature_names_out="one-to-one")),
                ("scale", StandardScaler()),
            ]
        numeric = Pipeline(steps=steps)
        transformers.append(("num", numeric, numeric_features))
    if categorical_features:
        categorical = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False, max_categories=40)),
            ]
        )
        transformers.append(("cat", categorical, categorical_features))
    if not transformers:
        raise ValueError("At least one numeric or categorical feature is required.")
    return ColumnTransformer(
        transformers=transformers
    )


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def save_model_bundle(name: str, bundle: dict[str, Any]) -> Path:
    paths = project_paths()
    out = paths["models"] / name
    out.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, out / "model.joblib")
    meta = {k: v for k, v in bundle.items() if k != "pipeline"}
    save_json(out / "metadata.json", meta)
    return out
