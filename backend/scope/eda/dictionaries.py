"""Data dictionary and proposed feature dictionary generation."""

from __future__ import annotations

from typing import Any

import pandas as pd

from scope.eda.constants import (
    COLUMN_MEANINGS,
    IDENTIFIER_COLUMNS,
    INVENTORY_COLUMNS,
)


def _leakage_risk(column: str) -> str:
    high = {
        "Delivered to Client Date",
        "Delivery Recorded Date",
        "Inventory_Stockout_Flag",
        "Inventory_Shortage_Quantity",
        "Inventory_Closing_Stock",
        "Inventory_Replenishment_Triggered",
    }
    medium = {
        "Freight Cost (USD)",
        "Weight (Kilograms)",
        "Line Item Insurance (USD)",
        "ASN/DN #",
        "Inventory_Stock_Out",
    }
    if column in high or column.endswith("_parsed") and "Delivered" in column:
        return "high — often known only after delivery / outcome"
    if column in medium:
        return "medium — may be unavailable at prediction time; confirm timing"
    if column.startswith("Inventory_"):
        return "medium/unknown — inventory provenance unverified"
    return "low/unknown — confirm availability at prediction time"


def _ml_suitability(column: str, n_unique: int, missing_pct: float) -> str:
    if column in IDENTIFIER_COLUMNS:
        return "No — identifier"
    if column in {"Item Description"}:
        return "Maybe — text feature / embedding later; high cardinality"
    if n_unique <= 1:
        return "No — constant / non-informative"
    if missing_pct > 40:
        return "Caution — high missingness"
    if column.startswith("Inventory_"):
        return "Caution — unverified augmented inventory field"
    return "Candidate — subject to leakage and availability review"


def build_data_dictionary(
    df: pd.DataFrame, missing_df: pd.DataFrame
) -> list[dict[str, Any]]:
    """Build per-column data dictionary records from the audited frame."""
    missing_map = missing_df.set_index("column").to_dict(orient="index")
    records = []
    for col in df.columns:
        if col.endswith(("_parsed", "_is_placeholder", "_parse_ok", "_numeric")):
            continue
        meta = missing_map.get(col, {})
        examples = (
            df[col].dropna().astype(str).unique()[:5].tolist()
            if df[col].notna().any()
            else []
        )
        n_unique = int(meta.get("n_unique", df[col].nunique(dropna=True)))
        missing_pct = float(meta.get("missing_pct", 0.0))
        records.append(
            {
                "column": col,
                "dtype": str(df[col].dtype),
                "business_meaning": COLUMN_MEANINGS.get(
                    col, "Unknown / Needs confirmation"
                ),
                "missing_pct": missing_pct,
                "n_unique": n_unique,
                "example_values": examples,
                "is_identifier": col in IDENTIFIER_COLUMNS,
                "ml_suitability": _ml_suitability(col, n_unique, missing_pct),
                "availability_time": (
                    "Unknown / Needs confirmation"
                    if col in INVENTORY_COLUMNS or col in {
                        "Delivered to Client Date",
                        "Delivery Recorded Date",
                        "Freight Cost (USD)",
                        "Weight (Kilograms)",
                    }
                    else "Likely available at/before shipment planning — Needs confirmation"
                ),
                "leakage_risk": _leakage_risk(col),
            }
        )
    return records


def build_feature_dictionary() -> list[dict[str, Any]]:
    """Propose Phase-02+ features grounded in EDA (not yet engineered)."""
    return [
        {
            "feature_name": "is_late",
            "source_columns": [
                "Scheduled Delivery Date",
                "Delivered to Client Date",
            ],
            "transformation": "1 if delivered > scheduled else 0; NA if either date invalid",
            "business_meaning": "Late delivery classification target",
            "prediction_time_availability": "Target only — not a feature",
            "missing_value_handling": "Exclude rows without valid date pair",
            "leakage_status": "Target",
            "approved_model_tasks": ["classification (Phase 03)"],
        },
        {
            "feature_name": "delay_days",
            "source_columns": [
                "Scheduled Delivery Date",
                "Delivered to Client Date",
            ],
            "transformation": "delivered_date - scheduled_date in days",
            "business_meaning": "Schedule deviation in days",
            "prediction_time_availability": "Target / evaluation only",
            "missing_value_handling": "NA when dates invalid",
            "leakage_status": "Target / proxy",
            "approved_model_tasks": ["regression evaluation", "EDA"],
        },
        {
            "feature_name": "country",
            "source_columns": ["Country"],
            "transformation": "Categorical encode / target encode with CV",
            "business_meaning": "Destination country",
            "prediction_time_availability": "Likely available at order time",
            "missing_value_handling": "None observed in raw — monitor",
            "leakage_status": "OK pending confirmation",
            "approved_model_tasks": ["classification", "regression", "clustering"],
        },
        {
            "feature_name": "shipment_mode",
            "source_columns": ["Shipment Mode"],
            "transformation": "Categorical encode; impute missing as Unknown",
            "business_meaning": "Transport mode",
            "prediction_time_availability": "Likely available at planning time",
            "missing_value_handling": "Fill with 'Unknown' (~3.5% missing)",
            "leakage_status": "OK pending confirmation",
            "approved_model_tasks": ["classification", "regression"],
        },
        {
            "feature_name": "vendor",
            "source_columns": ["Vendor"],
            "transformation": "Categorical / frequency / target encode with CV",
            "business_meaning": "Supplier identity",
            "prediction_time_availability": "Available at PO time",
            "missing_value_handling": "None observed",
            "leakage_status": "OK — avoid using post-delivery vendor metrics as raw features without time awareness",
            "approved_model_tasks": ["classification", "regression", "clustering", "anomaly"],
        },
        {
            "feature_name": "product_group",
            "source_columns": ["Product Group"],
            "transformation": "Categorical encode",
            "business_meaning": "Product family",
            "prediction_time_availability": "Available at order time",
            "missing_value_handling": "None observed",
            "leakage_status": "OK",
            "approved_model_tasks": ["classification", "regression", "clustering"],
        },
        {
            "feature_name": "line_item_quantity",
            "source_columns": ["Line Item Quantity"],
            "transformation": "Numeric; optional log1p for skew",
            "business_meaning": "Ordered quantity",
            "prediction_time_availability": "Available at order time",
            "missing_value_handling": "None observed",
            "leakage_status": "OK",
            "approved_model_tasks": ["classification", "regression", "forecasting"],
        },
        {
            "feature_name": "line_item_value",
            "source_columns": ["Line Item Value"],
            "transformation": "Numeric; optional log1p",
            "business_meaning": "Shipment line monetary value",
            "prediction_time_availability": "Likely available at order time",
            "missing_value_handling": "None observed",
            "leakage_status": "OK pending confirmation",
            "approved_model_tasks": ["classification", "regression", "anomaly"],
        },
        {
            "feature_name": "weight_kg_numeric",
            "source_columns": ["Weight (Kilograms)"],
            "transformation": "Coerce to float; non-numeric text -> NA + indicator",
            "business_meaning": "Shipment weight",
            "prediction_time_availability": "Uncertain — sometimes recorded later / cross-referenced",
            "missing_value_handling": "NA + missing indicator for non-numeric texts",
            "leakage_status": "Medium — confirm timing",
            "approved_model_tasks": ["classification", "regression — after availability check"],
        },
        {
            "feature_name": "freight_cost_usd_numeric",
            "source_columns": ["Freight Cost (USD)"],
            "transformation": "Coerce to float; non-numeric -> NA + indicator",
            "business_meaning": "Freight cost",
            "prediction_time_availability": "Often post-hoc / invoiced separately",
            "missing_value_handling": "NA + missing indicator",
            "leakage_status": "Medium/high — confirm timing before modelling",
            "approved_model_tasks": ["EDA; modelling only after availability proof"],
        },
        {
            "feature_name": "scheduled_month",
            "source_columns": ["Scheduled Delivery Date"],
            "transformation": "Extract month/quarter from parsed scheduled date",
            "business_meaning": "Seasonality of planned delivery",
            "prediction_time_availability": "Available when schedule is known",
            "missing_value_handling": "Exclude if schedule unparseable",
            "leakage_status": "OK",
            "approved_model_tasks": ["classification", "regression", "forecasting"],
        },
        {
            "feature_name": "inventory_opening_stock",
            "source_columns": ["Inventory_Opening_Stock"],
            "transformation": "Numeric as-is",
            "business_meaning": "Opening stock (unverified provenance)",
            "prediction_time_availability": "Unknown — do not assume authentic",
            "missing_value_handling": "None observed",
            "leakage_status": "Unknown / caution",
            "approved_model_tasks": [
                "inventory experiment (Phase 07) only after provenance review"
            ],
        },
        {
            "feature_name": "inventory_shortage_quantity",
            "source_columns": ["Inventory_Shortage_Quantity"],
            "transformation": "Numeric target/proxy",
            "business_meaning": "Shortage quantity (unverified)",
            "prediction_time_availability": "Outcome-like",
            "missing_value_handling": "None observed",
            "leakage_status": "Target / high leakage if used as feature",
            "approved_model_tasks": ["possible inventory target — not a feature"],
        },
    ]


def data_dictionary_markdown(records: list[dict[str, Any]]) -> str:
    lines = [
        "# Data Dictionary — SCMS_with_inventory.csv",
        "",
        "Generated during Phase 01 EDA. Meanings marked Unknown/Needs confirmation are intentional.",
        "",
        "Inventory_* fields are treated as **unverified augmented data**.",
        "",
    ]
    for r in records:
        lines.extend(
            [
                f"## `{r['column']}`",
                "",
                f"- **Data type:** `{r['dtype']}`",
                f"- **Business meaning:** {r['business_meaning']}",
                f"- **Missing %:** {r['missing_pct']}",
                f"- **Unique count:** {r['n_unique']}",
                f"- **Example values:** {r['example_values']}",
                f"- **Identifier:** {r['is_identifier']}",
                f"- **ML suitability:** {r['ml_suitability']}",
                f"- **Availability time:** {r['availability_time']}",
                f"- **Leakage risk:** {r['leakage_risk']}",
                "",
            ]
        )
    return "\n".join(lines)


def feature_dictionary_markdown(records: list[dict[str, Any]]) -> str:
    lines = [
        "# Feature Dictionary — Proposed Features (Phase 01)",
        "",
        "These are proposed features for later phases. No features were engineered into a training matrix in Phase 01.",
        "",
    ]
    for r in records:
        lines.extend(
            [
                f"## `{r['feature_name']}`",
                "",
                f"- **Source columns:** {', '.join(r['source_columns'])}",
                f"- **Transformation:** {r['transformation']}",
                f"- **Business meaning:** {r['business_meaning']}",
                f"- **Prediction-time availability:** {r['prediction_time_availability']}",
                f"- **Missing-value handling:** {r['missing_value_handling']}",
                f"- **Leakage status:** {r['leakage_status']}",
                f"- **Approved model tasks:** {', '.join(r['approved_model_tasks'])}",
                "",
            ]
        )
    return "\n".join(lines)
