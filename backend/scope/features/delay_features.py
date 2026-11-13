"""Delay / late-rate time-series aggregates."""

from __future__ import annotations

import pandas as pd


def build_delay_timeseries(
    shipments: pd.DataFrame, freq: str = "W"
) -> pd.DataFrame:
    """Aggregate late delivery metrics by week or month on scheduled delivery date."""
    work = shipments.dropna(subset=["Scheduled_Delivery_Date_Parsed", "is_late"]).copy()
    work = work.set_index("Scheduled_Delivery_Date_Parsed").sort_index()
    grouped = work.resample(freq).agg(
        shipment_count=("is_late", "size"),
        late_count=("is_late", "sum"),
        avg_schedule_deviation=("delay_days", "mean"),
        median_schedule_deviation=("delay_days", "median"),
    )
    grouped["late_rate"] = grouped["late_count"] / grouped["shipment_count"].replace(0, pd.NA)
    grouped = grouped.reset_index().rename(
        columns={"Scheduled_Delivery_Date_Parsed": "period_start"}
    )
    grouped["frequency"] = "weekly" if freq.upper().startswith("W") else "monthly"
    return grouped
