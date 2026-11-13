"""Point-in-time vendor history features."""

from __future__ import annotations

import numpy as np
import pandas as pd


def build_vendor_features(shipments: pd.DataFrame) -> pd.DataFrame:
    """Aggregate vendor performance from a reference shipment table."""
    work = shipments.copy()
    late_ok = work["is_late"].notna()
    dur_ok = work["delivery_duration_days"].notna()

    rows = []
    for vendor, g in work.groupby("Vendor", dropna=False):
        g_late = g.loc[g["is_late"].notna()]
        g_dur = g.loc[g["delivery_duration_days"].notna()]
        rows.append(
            {
                "Vendor": vendor,
                "shipment_count": int(len(g)),
                "late_count": int((g_late["is_late"] == 1).sum()),
                "on_time_count": int((g_late["is_late"] == 0).sum()),
                "late_rate": float(g_late["is_late"].mean()) if len(g_late) else None,
                "median_schedule_deviation": float(g_late["delay_days"].median())
                if len(g_late)
                else None,
                "mean_schedule_deviation": float(g_late["delay_days"].mean())
                if len(g_late)
                else None,
                "avg_quantity": float(g["Line_Item_Quantity"].mean()),
                "median_delivery_duration_days": float(g_dur["delivery_duration_days"].median())
                if len(g_dur)
                else None,
                "avg_freight_numeric": float(g["Freight_Cost_USD_Numeric"].mean(skipna=True)),
                "n_countries": int(g["Country"].nunique()),
                "n_product_groups": int(g["Product_Group"].nunique()),
            }
        )
    return pd.DataFrame(rows).sort_values("shipment_count", ascending=False)


def attach_train_only_vendor_stats(
    full: pd.DataFrame, train: pd.DataFrame
) -> pd.DataFrame:
    """Attach outcomes observable before each row's scheduled delivery date.

    A historical outcome becomes usable only after its delivered date. This
    creates the same expanding, point-in-time features for train, validation,
    and test rows and excludes the current row's own outcome.
    """
    del train  # retained in the signature for compatibility with callers
    columns = ["vendor_hist_late_rate", "vendor_hist_median_delay"]
    result = full.copy()
    for feature in columns:
        result[feature] = float("nan")

    schedule_col = "Scheduled_Delivery_Date_Parsed"
    delivered_col = "Delivered_To_Client_Date_Parsed"

    for vendor, group in full.groupby("Vendor", dropna=False, sort=False):
        group = group.sort_values(schedule_col)
        history = group.loc[
            group[delivered_col].notna() & group["is_late"].notna(),
            [delivered_col, "is_late", "delay_days"],
        ].sort_values(delivered_col)
        if history.empty:
            continue

        # Search the outcome-known prefix for each prediction timestamp.
        delivered_ns = history[delivered_col].astype("int64").to_numpy()
        late_values = history["is_late"].astype(float).to_numpy()
        delays = history["delay_days"].astype(float).to_numpy()
        schedule = group[schedule_col]
        valid_schedule = schedule.notna()
        positions = np.searchsorted(
            delivered_ns,
            schedule.loc[valid_schedule].astype("int64").to_numpy(),
            side="left",
        )
        for row_index, n_prior in zip(schedule.loc[valid_schedule].index, positions):
            if n_prior == 0:
                continue
            result.at[row_index, "vendor_hist_late_rate"] = float(late_values[:n_prior].mean())
            prior_delays = delays[:n_prior]
            prior_delays = prior_delays[np.isfinite(prior_delays)]
            if len(prior_delays):
                result.at[row_index, "vendor_hist_median_delay"] = float(np.median(prior_delays))
    return result
