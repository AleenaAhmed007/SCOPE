"""Transparent date parsing with placeholder handling."""

from __future__ import annotations

from typing import Any

import pandas as pd

from scope.eda.constants import DATE_COLUMNS, DATE_PLACEHOLDERS
from scope.logging_config import setup_logging

logger = setup_logging()


def is_date_placeholder(value: Any) -> bool:
    """Return True if value is a known non-date placeholder string."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    text = str(value).strip()
    return text in DATE_PLACEHOLDERS


def parse_date_series(series: pd.Series, column_name: str) -> pd.DataFrame:
    """Parse a date series while preserving originals and flagging failures.

    Args:
        series: Raw date-like series.
        column_name: Source column name (used for logging only).

    Returns:
        DataFrame with columns:
        ``raw``, ``is_placeholder``, ``parsed``, ``parse_ok``.
    """
    raw = series.astype("string")
    is_placeholder = raw.map(lambda v: is_date_placeholder(v) if pd.notna(v) else False)

    # Attempt parse only on non-placeholder, non-null values
    to_parse = raw.where(~is_placeholder & raw.notna())
    # dayfirst=True covers Inventory_Date (dd/mm/yyyy) and dd-Mon-yy shipment dates
    parsed = pd.to_datetime(to_parse, errors="coerce", dayfirst=True, format="mixed")

    parse_ok = parsed.notna()
    attempted = to_parse.notna()
    failed = attempted & ~parse_ok

    logger.info(
        "Date parse [%s]: placeholders=%d parse_ok=%d failed=%d null=%d",
        column_name,
        int(is_placeholder.sum()),
        int(parse_ok.sum()),
        int(failed.sum()),
        int(raw.isna().sum()),
    )

    return pd.DataFrame(
        {
            "raw": series,
            "is_placeholder": is_placeholder,
            "parsed": parsed,
            "parse_ok": parse_ok,
        }
    )


def enrich_with_parsed_dates(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Add normalized datetime columns and return parse summary stats.

    Original string columns are preserved. New columns use suffix ``_parsed``.
    """
    out = df.copy()
    summary: dict[str, Any] = {}

    for col in DATE_COLUMNS:
        if col not in out.columns:
            summary[col] = {"present": False}
            continue
        parsed_df = parse_date_series(out[col], col)
        out[f"{col}_parsed"] = parsed_df["parsed"]
        out[f"{col}_is_placeholder"] = parsed_df["is_placeholder"]
        out[f"{col}_parse_ok"] = parsed_df["parse_ok"]

        attempted = (~parsed_df["is_placeholder"]) & parsed_df["raw"].notna()
        summary[col] = {
            "present": True,
            "n_rows": int(len(out)),
            "n_null": int(parsed_df["raw"].isna().sum()),
            "n_placeholder": int(parsed_df["is_placeholder"].sum()),
            "n_parse_ok": int(parsed_df["parse_ok"].sum()),
            "n_parse_failed": int((attempted & ~parsed_df["parse_ok"]).sum()),
            "placeholder_counts": (
                parsed_df.loc[parsed_df["is_placeholder"], "raw"]
                .astype(str)
                .value_counts()
                .to_dict()
            ),
            "min_parsed": (
                parsed_df["parsed"].min().isoformat()
                if parsed_df["parse_ok"].any()
                else None
            ),
            "max_parsed": (
                parsed_df["parsed"].max().isoformat()
                if parsed_df["parse_ok"].any()
                else None
            ),
        }

    return out, summary


def find_impossible_chronology(df: pd.DataFrame) -> dict[str, Any]:
    """Detect chronologically impossible date pairs among parsed dates.

    Checks:
    - Delivered before Scheduled (informational; late is opposite)
    - Delivery Recorded before Delivered
    - PO Sent after Delivered (when both valid)
    """
    results: dict[str, Any] = {}

    sched = df.get("Scheduled Delivery Date_parsed")
    delivered = df.get("Delivered to Client Date_parsed")
    recorded = df.get("Delivery Recorded Date_parsed")
    po_sent = df.get("PO Sent to Vendor Date_parsed")

    if sched is not None and delivered is not None:
        both = sched.notna() & delivered.notna()
        # Recorded before delivered is suspicious
        results["delivered_before_scheduled_count"] = int(
            (both & (delivered < sched)).sum()
        )
        results["delivered_after_scheduled_count"] = int(
            (both & (delivered > sched)).sum()
        )
        results["delivered_on_scheduled_count"] = int(
            (both & (delivered == sched)).sum()
        )
        results["valid_schedule_delivery_pairs"] = int(both.sum())

    if delivered is not None and recorded is not None:
        both = delivered.notna() & recorded.notna()
        results["recorded_before_delivered_count"] = int(
            (both & (recorded < delivered)).sum()
        )
        results["valid_delivered_recorded_pairs"] = int(both.sum())

    if po_sent is not None and delivered is not None:
        both = po_sent.notna() & delivered.notna()
        results["po_sent_after_delivered_count"] = int(
            (both & (po_sent > delivered)).sum()
        )
        results["valid_po_delivered_pairs"] = int(both.sum())

    return results
