"""Dataset overview, missingness, and duplicate auditing."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from scope.eda.constants import DIRTY_NUMERIC_COLUMNS
from scope.logging_config import setup_logging

logger = setup_logging()


def coerce_dirty_numeric(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Coerce known dirty numeric columns; keep original text columns.

    Adds ``{col}_numeric`` for each dirty column.
    """
    out = df.copy()
    report: dict[str, Any] = {}
    for col in DIRTY_NUMERIC_COLUMNS:
        if col not in out.columns:
            continue
        numeric = pd.to_numeric(out[col], errors="coerce")
        out[f"{col}_numeric"] = numeric
        report[col] = {
            "n_numeric": int(numeric.notna().sum()),
            "n_non_numeric": int(numeric.isna().sum() - out[col].isna().sum()),
            "n_null_original": int(out[col].isna().sum()),
            "top_non_numeric": (
                out.loc[numeric.isna() & out[col].notna(), col]
                .astype(str)
                .value_counts()
                .head(15)
                .to_dict()
            ),
        }
    return out, report


def dataset_overview(df: pd.DataFrame) -> dict[str, Any]:
    """Compute high-level schema and shape statistics."""
    memory = float(df.memory_usage(deep=True).sum())
    dtypes = {c: str(t) for c, t in df.dtypes.items()}
    unique_counts = {c: int(df[c].nunique(dropna=True)) for c in df.columns}
    return {
        "n_rows": int(len(df)),
        "n_columns": int(df.shape[1]),
        "memory_bytes": memory,
        "memory_mb": round(memory / 1e6, 3),
        "columns": list(df.columns),
        "dtypes": dtypes,
        "unique_counts": unique_counts,
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_ids": int(df["ID"].duplicated().sum()) if "ID" in df.columns else None,
    }


def missing_value_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Per-column missingness, uniqueness, and mode."""
    rows = []
    n = len(df)
    for col in df.columns:
        missing = int(df[col].isna().sum())
        mode = df[col].mode(dropna=True)
        rows.append(
            {
                "column": col,
                "dtype": str(df[col].dtype),
                "missing_count": missing,
                "missing_pct": round(100.0 * missing / n, 4) if n else 0.0,
                "n_unique": int(df[col].nunique(dropna=True)),
                "most_frequent": mode.iloc[0] if len(mode) else None,
                "most_frequent_count": int((df[col] == mode.iloc[0]).sum()) if len(mode) else 0,
            }
        )
    return pd.DataFrame(rows).sort_values("missing_pct", ascending=False)


def constant_columns(df: pd.DataFrame, near_threshold: float = 0.99) -> dict[str, Any]:
    """Identify constant and near-constant columns."""
    constants: list[str] = []
    near_constants: list[dict[str, Any]] = []
    n = len(df)
    for col in df.columns:
        nunique = df[col].nunique(dropna=True)
        if nunique <= 1:
            constants.append(col)
            continue
        mode_count = df[col].value_counts(dropna=True).iloc[0]
        share = mode_count / n if n else 0.0
        if share >= near_threshold:
            near_constants.append(
                {
                    "column": col,
                    "dominant_value": df[col].value_counts(dropna=True).index[0],
                    "dominant_share": round(float(share), 4),
                    "n_unique": int(nunique),
                }
            )
    return {"constant": constants, "near_constant": near_constants}


def iqr_outlier_count(series: pd.Series) -> int:
    """Count Tukey IQR outliers (values outside 1.5 * IQR fences)."""
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return 0
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:
        return 0
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return int(((s < lower) | (s > upper)).sum())


def numerical_profile(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Describe numerical columns with skew and outlier counts."""
    rows = []
    for col in columns:
        if col in df.columns:
            series = pd.to_numeric(df[col], errors="coerce")
        elif f"{col}_numeric" in df.columns:
            series = df[f"{col}_numeric"]
            col = f"{col}_numeric"
        else:
            continue
        s = series.dropna()
        rows.append(
            {
                "column": col,
                "count": int(s.count()),
                "missing": int(series.isna().sum()),
                "mean": float(s.mean()) if len(s) else np.nan,
                "median": float(s.median()) if len(s) else np.nan,
                "std": float(s.std()) if len(s) else np.nan,
                "min": float(s.min()) if len(s) else np.nan,
                "q25": float(s.quantile(0.25)) if len(s) else np.nan,
                "q75": float(s.quantile(0.75)) if len(s) else np.nan,
                "max": float(s.max()) if len(s) else np.nan,
                "skewness": float(s.skew()) if len(s) else np.nan,
                "iqr_outlier_count": iqr_outlier_count(series),
            }
        )
    return pd.DataFrame(rows)


def categorical_profile(
    df: pd.DataFrame, columns: list[str], top_n: int = 15
) -> dict[str, Any]:
    """Frequency tables for categorical columns (top-N + Other)."""
    profiles: dict[str, Any] = {}
    n = len(df)
    for col in columns:
        if col not in df.columns:
            continue
        vc = df[col].fillna("(Missing)").value_counts()
        top = vc.head(top_n)
        other_count = int(vc.iloc[top_n:].sum()) if len(vc) > top_n else 0
        table = top.rename("count").to_frame()
        table["pct"] = (table["count"] / n * 100).round(2)
        profiles[col] = {
            "n_unique": int(df[col].nunique(dropna=True)),
            "top": table.reset_index(names=["value"]).to_dict(orient="records"),
            "other_count": other_count,
            "other_pct": round(100.0 * other_count / n, 2) if n else 0.0,
        }
    return profiles
