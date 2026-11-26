"""CSV table read/write helpers (replaces Parquet for processed/interim data)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

_AUTO_DATE_NAMES = frozenset({"period_start", "period_end"})


def table_path(path: Path | str) -> Path:
    """Normalize a table path to ``.csv`` (accepts legacy ``.parquet`` paths)."""
    p = Path(path)
    if p.suffix.lower() == ".parquet":
        return p.with_suffix(".csv")
    if p.suffix.lower() != ".csv":
        return p.with_suffix(".csv")
    return p


def _infer_date_columns(df: pd.DataFrame) -> list[str]:
    cols: list[str] = []
    for c in df.columns:
        if c in _AUTO_DATE_NAMES or c.endswith("_Parsed") or c.endswith("_Date"):
            cols.append(c)
    return cols


def write_table(df: pd.DataFrame, path: Path | str) -> Path:
    """Write a DataFrame as CSV and return the final path."""
    out = table_path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return out


def read_table(
    path: Path | str,
    *,
    parse_dates: list[str] | None = None,
) -> pd.DataFrame:
    """Read a CSV table, coercing common date columns to datetimes."""
    src = table_path(path)
    df = pd.read_csv(src, low_memory=False)
    cols = parse_dates if parse_dates is not None else _infer_date_columns(df)
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df
