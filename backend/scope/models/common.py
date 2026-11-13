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
from sklearn.preprocessing import OneHotEncoder

from scope.config.loader import get_project_root


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
    numeric_features: list[str], categorical_features: list[str]
) -> ColumnTransformer:
    transformers = []
    if numeric_features:
        numeric = Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))])
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
