"""Reusable date parsing aligned with Phase 01 rules."""

from __future__ import annotations

from typing import Any

import pandas as pd

from scope.eda.constants import DATE_PLACEHOLDERS


def is_placeholder(value: Any) -> bool:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    return str(value).strip() in DATE_PLACEHOLDERS


def parse_dates(series: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Return (parsed, is_placeholder, parse_ok)."""
    raw = series.astype("string")
    placeholder = raw.map(lambda v: is_placeholder(v) if pd.notna(v) else False)
    to_parse = raw.where(~placeholder & raw.notna())
    # Normalize Sept -> Sep for %b compatibility before mixed parse
    to_parse = to_parse.str.replace("Sept", "Sep", regex=False)
    parsed = pd.to_datetime(to_parse, errors="coerce", dayfirst=True, format="mixed")
    parse_ok = parsed.notna()
    return parsed, placeholder.astype(bool), parse_ok
