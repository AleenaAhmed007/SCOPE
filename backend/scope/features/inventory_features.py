"""Inventory rule-audit table with explicit provenance and leakage diagnostics."""

from __future__ import annotations

from typing import Any

import pandas as pd


def build_inventory_experiment_table(shipments: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build inventory analysis table and document why stockout prediction may be unsafe.

    Fields examined during the audit (not an approved predictor set):
    - Inventory_Opening_Stock
    - Inventory_Reorder_Level
    - Inventory_Lead_Time_Days (constant=30 — non-informative)
    - Inventory_Stock_In (constant=0 — non-informative)

    Forbidden as predictors for stockout/shortage:
    - Inventory_Shortage_Quantity (target/proxy)
    - Inventory_Stockout_Flag (target/proxy)
    - Inventory_Closing_Stock (end-of-period)
    - Inventory_Replenishment_Triggered (likely derived outcome)
    - Inventory_Stock_Out (often equals shipped qty / post-movement)
    """
    cols = [
        "ID",
        "Vendor",
        "Country",
        "Inventory_Product_Key",
        "Inventory_Warehouse_ID",
        "Inventory_Date",
        "Inventory_Date_Parsed",
        "Inventory_Opening_Stock",
        "Inventory_Stock_In",
        "Inventory_Stock_Out",
        "Inventory_Closing_Stock",
        "Inventory_Reorder_Level",
        "Inventory_Lead_Time_Days",
        "Inventory_Stockout_Flag",
        "Inventory_Shortage_Quantity",
        "Inventory_Replenishment_Triggered",
        "Line_Item_Quantity",
        "Product_Group",
    ]
    present = [c for c in cols if c in shipments.columns]
    table = shipments[present].copy()
    table["expected_closing"] = (
        table["Inventory_Opening_Stock"]
        + table["Inventory_Stock_In"]
        - table["Inventory_Stock_Out"]
    )
    table["arithmetic_ok"] = table["expected_closing"] == table["Inventory_Closing_Stock"]
    table["below_reorder"] = (
        table["Inventory_Opening_Stock"] < table["Inventory_Reorder_Level"]
    )
    table["rule_stockout_prediction"] = (
        table["Inventory_Opening_Stock"] - table["Line_Item_Quantity"] < 0
    ).astype(int)
    stockout_rows = table["Inventory_Stockout_Flag"].notna()
    rule_agreement = (
        float(
            (
                table.loc[stockout_rows, "rule_stockout_prediction"]
                == table.loc[stockout_rows, "Inventory_Stockout_Flag"].astype(int)
            ).mean()
        )
        if stockout_rows.any()
        else None
    )

    meta = {
        "provenance": "unverified_augmented",
        "stock_in_constant": bool((table["Inventory_Stock_In"] == 0).all()),
        "lead_time_constant": bool((table["Inventory_Lead_Time_Days"] == 30).all()),
        "leakage_safe_predictors": [
            "Inventory_Opening_Stock",
            "Inventory_Reorder_Level",
            "below_reorder",
            "Product_Group",
            "Vendor",
            "Country",
            "Line_Item_Quantity",
        ],
        "forbidden_predictors": [
            "Inventory_Shortage_Quantity",
            "Inventory_Stockout_Flag",
            "Inventory_Closing_Stock",
            "Inventory_Replenishment_Triggered",
            "Inventory_Stock_Out",
        ],
        "audited_target_fields": ["Inventory_Stockout_Flag", "Inventory_Shortage_Quantity"],
        "stockout_rule_agreement": rule_agreement,
        "training_recommendation": "Do not train a stockout classifier: the flag exactly matches Opening_Stock - Line_Item_Quantity < 0 in this augmented dataset. Keep it as a rule consistency check pending source-system provenance.",
    }
    return table, meta
