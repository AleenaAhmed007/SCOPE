"""Chronological train/validation/test splitting."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def chronological_split(
    df: pd.DataFrame,
    date_col: str,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Split by sorted date column into train/val/test without shuffling future into train."""
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6
    work = df.dropna(subset=[date_col]).sort_values(date_col).reset_index(drop=True)
    n = len(work)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    train = work.iloc[:n_train].copy()
    val = work.iloc[n_train : n_train + n_val].copy()
    test = work.iloc[n_train + n_val :].copy()
    meta = {
        "date_col": date_col,
        "n_total": n,
        "n_train": len(train),
        "n_val": len(val),
        "n_test": len(test),
        "train_end": str(train[date_col].max()) if len(train) else None,
        "val_end": str(val[date_col].max()) if len(val) else None,
        "test_end": str(test[date_col].max()) if len(test) else None,
        "method": "chronological",
    }
    return train, val, test, meta


def assign_split_labels(
    df: pd.DataFrame,
    date_col: str,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
) -> pd.Series:
    """Return a Series of split labels aligned to df index."""
    order = df[date_col].rank(method="first")
    n = order.notna().sum()
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    labels = pd.Series("excluded", index=df.index, dtype="object")
    ranked = order.dropna().sort_values()
    idx = ranked.index.to_list()
    labels.loc[idx[:n_train]] = "train"
    labels.loc[idx[n_train : n_train + n_val]] = "val"
    labels.loc[idx[n_train + n_val :]] = "test"
    return labels
