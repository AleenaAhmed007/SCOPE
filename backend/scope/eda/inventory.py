"""Inventory field audit — treat fields as unverified augmented data."""

from __future__ import annotations

from typing import Any

import pandas as pd

from scope.eda.constants import INVENTORY_COLUMNS
from scope.logging_config import setup_logging

logger = setup_logging()


def audit_inventory(df: pd.DataFrame) -> dict[str, Any]:
    """Audit inventory columns for constants, arithmetic, and flag consistency.

    Important: inventory provenance is unverified. Results describe the CSV
    contents only and do not certify operational authenticity.
    """
    present = [c for c in INVENTORY_COLUMNS if c in df.columns]
    missing_cols = [c for c in INVENTORY_COLUMNS if c not in df.columns]

    constants = {}
    for col in present:
        nunique = int(df[col].nunique(dropna=True))
        if nunique <= 1:
            constants[col] = {
                "n_unique": nunique,
                "value": df[col].dropna().iloc[0] if nunique == 1 else None,
            }

    opening = df["Inventory_Opening_Stock"]
    stock_in = df["Inventory_Stock_In"]
    stock_out = df["Inventory_Stock_Out"]
    closing = df["Inventory_Closing_Stock"]
    expected = opening + stock_in - stock_out
    arithmetic_match = expected == closing

    flag = df["Inventory_Stockout_Flag"]
    shortage = df["Inventory_Shortage_Quantity"]
    flag_shortage_aligned = (
        ((flag == 1) & (shortage > 0)) | ((flag == 0) & (shortage == 0))
    )

    neg_cols = {}
    for col in [
        "Inventory_Opening_Stock",
        "Inventory_Stock_In",
        "Inventory_Stock_Out",
        "Inventory_Closing_Stock",
        "Inventory_Reorder_Level",
        "Inventory_Shortage_Quantity",
    ]:
        if col in df.columns:
            neg_cols[col] = int((pd.to_numeric(df[col], errors="coerce") < 0).sum())

    key_cols = [
        "Inventory_Product_Key",
        "Inventory_Warehouse_ID",
        "Inventory_Date",
    ]
    dup_key = int(df.duplicated(subset=key_cols).sum()) if all(c in df.columns for c in key_cols) else None

    below_reorder = int((closing < df["Inventory_Reorder_Level"]).sum())
    replenish = df["Inventory_Replenishment_Triggered"]

    result = {
        "provenance_note": (
            "Inventory fields appear augmented/synthetic relative to classic SCMS "
            "shipment data. Do not treat them as authentic operational inventory "
            "records without independent evidence."
        ),
        "present_columns": present,
        "missing_columns": missing_cols,
        "constant_columns": constants,
        "stock_in_all_zero": bool((stock_in == 0).all()),
        "lead_time_all_30": bool((df["Inventory_Lead_Time_Days"] == 30).all()),
        "arithmetic": {
            "formula": "Expected Closing = Opening + Stock_In - Stock_Out",
            "n_match": int(arithmetic_match.sum()),
            "n_mismatch": int((~arithmetic_match).sum()),
            "match_pct": round(100.0 * arithmetic_match.mean(), 4),
        },
        "flag_shortage_alignment": {
            "n_aligned": int(flag_shortage_aligned.sum()),
            "n_misaligned": int((~flag_shortage_aligned).sum()),
            "aligned_pct": round(100.0 * flag_shortage_aligned.mean(), 4),
            "rule": "flag==1 iff shortage_quantity > 0",
        },
        "negative_value_counts": neg_cols,
        "duplicate_product_warehouse_date": dup_key,
        "closing_below_reorder_count": below_reorder,
        "replenishment_triggered_rate": round(float(replenish.mean()), 4),
        "stockout_flag_rate": round(float(flag.mean()), 4),
        "n_unique_products": int(df["Inventory_Product_Key"].nunique()),
        "n_unique_warehouses": int(df["Inventory_Warehouse_ID"].nunique()),
        "n_unique_inventory_dates": int(df["Inventory_Date"].nunique()),
        "leakage_risks": [
            {
                "field": "Inventory_Stockout_Flag",
                "risk": "high",
                "note": (
                    "May encode outcome-like stock shortage; unsuitable as a feature "
                    "for predicting shortage/stockout without careful leakage review."
                ),
            },
            {
                "field": "Inventory_Shortage_Quantity",
                "risk": "high",
                "note": "Direct shortage outcome; treat as target/proxy, not a feature.",
            },
            {
                "field": "Inventory_Replenishment_Triggered",
                "risk": "medium",
                "note": "May be derived from closing vs reorder; confirm timing before use.",
            },
            {
                "field": "Inventory_Closing_Stock",
                "risk": "medium",
                "note": "End-of-period value may not be known at prediction time.",
            },
        ],
    }
    logger.info(
        "Inventory audit: arithmetic_match=%.2f%% stock_in_constant=%s lead_time_constant=%s",
        result["arithmetic"]["match_pct"],
        result["stock_in_all_zero"],
        result["lead_time_all_30"],
    )
    return result
