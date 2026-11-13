"""Shipment-level early-warning feature table."""

from __future__ import annotations

import pandas as pd

from scope.data.cleaning import coerce_numeric_with_flag
from scope.data.date_parser import parse_dates

# Features assumed available at prediction time (scheduled delivery known; outcome unknown)
EARLY_WARNING_CATEGORICAL = [
    "Country",
    "Managed_By",
    "Fulfill_Via",
    "Vendor_INCO_Term",
    "Shipment_Mode",
    "Product_Group",
    "Sub_Classification",
    "Vendor",
    "Manufacturing_Site",
    "Brand",
    "Dosage_Form",
    "First_Line_Designation",
]

EARLY_WARNING_NUMERIC = [
    "Line_Item_Quantity",
    "Line_Item_Value",
    "Pack_Price",
    "Unit_Price",
    "Unit_Of_Measure_Per_Pack",
    "Weight_Kilograms_Numeric",
    "Freight_Cost_USD_Numeric",
    "Line_Item_Insurance_USD",
    "Scheduled_Month",
    "Scheduled_Quarter",
    "Scheduled_DOW",
]

LEAKAGE_FORBIDDEN = {
    "Delivered_To_Client_Date",
    "Delivery_Recorded_Date",
    "is_late",
    "delay_days",
    "delivery_duration_days",
    "Inventory_Shortage_Quantity",
    "Inventory_Stockout_Flag",
    "Inventory_Closing_Stock",
    "Inventory_Replenishment_Triggered",
}


def build_shipment_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Build normalized shipment frame with targets and early-warning features."""
    out = df.copy()

    # Numeric coercion for dirty fields
    w_num, w_flag = coerce_numeric_with_flag(out["Weight_Kilograms"], "Weight")
    f_num, f_flag = coerce_numeric_with_flag(out["Freight_Cost_USD"], "Freight")
    out["Weight_Kilograms_Numeric"] = w_num
    out["Weight_NonNumeric_Flag"] = w_flag
    out["Freight_Cost_USD_Numeric"] = f_num
    out["Freight_NonNumeric_Flag"] = f_flag

    # Dates
    for raw_col, parsed_col in [
        ("Scheduled_Delivery_Date", "Scheduled_Delivery_Date_Parsed"),
        ("Delivered_To_Client_Date", "Delivered_To_Client_Date_Parsed"),
        ("PO_Sent_To_Vendor_Date", "PO_Sent_To_Vendor_Date_Parsed"),
        ("Delivery_Recorded_Date", "Delivery_Recorded_Date_Parsed"),
        ("PQ_First_Sent_To_Client_Date", "PQ_First_Sent_To_Client_Date_Parsed"),
        ("Inventory_Date", "Inventory_Date_Parsed"),
    ]:
        parsed, is_ph, ok = parse_dates(out[raw_col])
        out[parsed_col] = parsed
        out[f"{raw_col}_Is_Placeholder"] = is_ph.astype(int)
        out[f"{raw_col}_Parse_OK"] = ok.astype(int)

    sched = out["Scheduled_Delivery_Date_Parsed"]
    delivered = out["Delivered_To_Client_Date_Parsed"]
    po = out["PO_Sent_To_Vendor_Date_Parsed"]

    valid_late = sched.notna() & delivered.notna()
    out["delay_days"] = (delivered - sched).dt.days.where(valid_late)
    out["is_late"] = pd.Series(pd.NA, index=out.index, dtype="Int64")
    out.loc[valid_late, "is_late"] = (out.loc[valid_late, "delay_days"] > 0).astype(int)

    # PO-to-client duration — only chronologically plausible
    valid_dur = po.notna() & delivered.notna() & (delivered >= po)
    out["delivery_duration_days"] = (delivered - po).dt.days.where(valid_dur)

    out["Scheduled_Month"] = sched.dt.month
    out["Scheduled_Quarter"] = sched.dt.quarter
    out["Scheduled_DOW"] = sched.dt.dayofweek
    out["Scheduled_Year"] = sched.dt.year

    return out


def early_warning_feature_columns() -> list[str]:
    return EARLY_WARNING_CATEGORICAL + EARLY_WARNING_NUMERIC + [
        "Weight_NonNumeric_Flag",
        "Freight_NonNumeric_Flag",
    ]
