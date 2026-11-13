"""Shipment quantity time-series (order/shipment volume proxy — not warehouse demand)."""

from __future__ import annotations

import pandas as pd


def build_volume_timeseries(
    shipments: pd.DataFrame, freq: str = "W"
) -> pd.DataFrame:
    """Aggregate Line Item Quantity by scheduled delivery period."""
    work = shipments.dropna(subset=["Scheduled_Delivery_Date_Parsed"]).copy()
    work = work.set_index("Scheduled_Delivery_Date_Parsed").sort_index()
    grouped = work.resample(freq).agg(
        shipment_count=("ID", "count"),
        total_line_item_quantity=("Line_Item_Quantity", "sum"),
        mean_line_item_quantity=("Line_Item_Quantity", "mean"),
        median_line_item_quantity=("Line_Item_Quantity", "median"),
    )
    grouped = grouped.reset_index().rename(
        columns={"Scheduled_Delivery_Date_Parsed": "period_start"}
    )
    grouped["frequency"] = "weekly" if freq.upper().startswith("W") else "monthly"
    grouped["note"] = (
        "Historical shipment/order quantity proxy — not verified warehouse demand "
        "or customer consumption."
    )
    return grouped
