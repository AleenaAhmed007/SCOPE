"""Late-delivery target creation and shipment performance analysis."""

from __future__ import annotations

from typing import Any

import pandas as pd

from scope.logging_config import setup_logging

logger = setup_logging()


def create_late_delivery_target(df: pd.DataFrame) -> pd.DataFrame:
    """Derive ``is_late`` and ``delay_days`` where both dates parse successfully.

    Definition:
        is_late = 1 when Delivered to Client Date > Scheduled Delivery Date
        is_late = 0 when Delivered <= Scheduled
        is_late = NA when either date is invalid / missing / placeholder
    """
    out = df.copy()
    sched = out["Scheduled Delivery Date_parsed"]
    delivered = out["Delivered to Client Date_parsed"]
    valid = sched.notna() & delivered.notna()

    delay = (delivered - sched).dt.days
    out["delay_days"] = delay.where(valid)
    out["is_late"] = pd.Series(pd.NA, index=out.index, dtype="Int64")
    out.loc[valid, "is_late"] = (delay.loc[valid] > 0).astype(int)

    logger.info(
        "Late target: valid=%d late=%d on_time=%d excluded=%d",
        int(valid.sum()),
        int((out["is_late"] == 1).sum()),
        int((out["is_late"] == 0).sum()),
        int((~valid).sum()),
    )
    return out


def late_delivery_summary(df: pd.DataFrame) -> dict[str, Any]:
    """Aggregate late-delivery rates and delay statistics."""
    valid = df["is_late"].notna()
    subset = df.loc[valid]
    delay = subset["delay_days"]
    return {
        "n_valid_target": int(valid.sum()),
        "n_excluded": int((~valid).sum()),
        "n_late": int((subset["is_late"] == 1).sum()),
        "n_on_time": int((subset["is_late"] == 0).sum()),
        "late_pct": round(100.0 * (subset["is_late"] == 1).mean(), 4) if len(subset) else None,
        "delay_days_mean": float(delay.mean()) if len(delay) else None,
        "delay_days_median": float(delay.median()) if len(delay) else None,
        "delay_days_std": float(delay.std()) if len(delay) else None,
        "delay_days_min": float(delay.min()) if len(delay) else None,
        "delay_days_max": float(delay.max()) if len(delay) else None,
        "exclusion_reason": (
            "Rows excluded when Scheduled Delivery Date or Delivered to Client Date "
            "could not be parsed to a valid datetime (null/placeholder/invalid)."
        ),
    }


def late_rate_by(
    df: pd.DataFrame, group_col: str, min_shipments: int = 1
) -> pd.DataFrame:
    """Compute late rate by a categorical column using valid targets only."""
    subset = df.loc[df["is_late"].notna() & df[group_col].notna()].copy()
    grouped = (
        subset.groupby(group_col, dropna=False)
        .agg(
            shipment_count=("is_late", "size"),
            late_count=("is_late", "sum"),
            delay_mean=("delay_days", "mean"),
            delay_median=("delay_days", "median"),
        )
        .reset_index()
    )
    grouped["on_time_count"] = grouped["shipment_count"] - grouped["late_count"]
    grouped["late_rate"] = grouped["late_count"] / grouped["shipment_count"]
    grouped = grouped[grouped["shipment_count"] >= min_shipments]
    return grouped.sort_values(["late_rate", "shipment_count"], ascending=[False, False])


def vendor_performance(df: pd.DataFrame, min_shipments: int = 5) -> pd.DataFrame:
    """Vendor-level shipment and late-delivery performance table."""
    subset = df.loc[df["is_late"].notna()].copy()
    qty_col = "Line Item Quantity"
    val_col = "Line Item Value"
    grouped = (
        subset.groupby("Vendor", dropna=False)
        .agg(
            shipment_count=("is_late", "size"),
            late_count=("is_late", "sum"),
            delay_mean=("delay_days", "mean"),
            delay_median=("delay_days", "median"),
            avg_quantity=(qty_col, "mean"),
            avg_value=(val_col, "mean"),
        )
        .reset_index()
    )
    grouped["on_time_count"] = grouped["shipment_count"] - grouped["late_count"]
    grouped["late_rate"] = grouped["late_count"] / grouped["shipment_count"]
    grouped["small_sample_flag"] = grouped["shipment_count"] < min_shipments
    return grouped.sort_values(["shipment_count", "late_rate"], ascending=[False, False])
