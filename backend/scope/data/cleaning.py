"""Column normalization and cleaning helpers."""

from __future__ import annotations

from typing import Any

import pandas as pd

# Original CSV name -> internal snake/Pascal style name
COLUMN_MAP: dict[str, str] = {
    "ID": "ID",
    "Project Code": "Project_Code",
    "PQ #": "PQ_Number",
    "PO / SO #": "PO_SO_Number",
    "ASN/DN #": "ASN_DN_Number",
    "Country": "Country",
    "Managed By": "Managed_By",
    "Fulfill Via": "Fulfill_Via",
    "Vendor INCO Term": "Vendor_INCO_Term",
    "Shipment Mode": "Shipment_Mode",
    "PQ First Sent to Client Date": "PQ_First_Sent_To_Client_Date",
    "PO Sent to Vendor Date": "PO_Sent_To_Vendor_Date",
    "Scheduled Delivery Date": "Scheduled_Delivery_Date",
    "Delivered to Client Date": "Delivered_To_Client_Date",
    "Delivery Recorded Date": "Delivery_Recorded_Date",
    "Product Group": "Product_Group",
    "Sub Classification": "Sub_Classification",
    "Vendor": "Vendor",
    "Item Description": "Item_Description",
    "Molecule/Test Type": "Molecule_Test_Type",
    "Brand": "Brand",
    "Dosage": "Dosage",
    "Dosage Form": "Dosage_Form",
    "Unit of Measure (Per Pack)": "Unit_Of_Measure_Per_Pack",
    "Line Item Quantity": "Line_Item_Quantity",
    "Line Item Value": "Line_Item_Value",
    "Pack Price": "Pack_Price",
    "Unit Price": "Unit_Price",
    "Manufacturing Site": "Manufacturing_Site",
    "First Line Designation": "First_Line_Designation",
    "Weight (Kilograms)": "Weight_Kilograms",
    "Freight Cost (USD)": "Freight_Cost_USD",
    "Line Item Insurance (USD)": "Line_Item_Insurance_USD",
    "Inventory_Product_Key": "Inventory_Product_Key",
    "Inventory_Warehouse_ID": "Inventory_Warehouse_ID",
    "Inventory_Date": "Inventory_Date",
    "Inventory_Opening_Stock": "Inventory_Opening_Stock",
    "Inventory_Stock_In": "Inventory_Stock_In",
    "Inventory_Stock_Out": "Inventory_Stock_Out",
    "Inventory_Closing_Stock": "Inventory_Closing_Stock",
    "Inventory_Reorder_Level": "Inventory_Reorder_Level",
    "Inventory_Lead_Time_Days": "Inventory_Lead_Time_Days",
    "Inventory_Stockout_Flag": "Inventory_Stockout_Flag",
    "Inventory_Shortage_Quantity": "Inventory_Shortage_Quantity",
    "Inventory_Replenishment_Triggered": "Inventory_Replenishment_Triggered",
}

REVERSE_COLUMN_MAP = {v: k for k, v in COLUMN_MAP.items()}


def normalize_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    """Rename columns using COLUMN_MAP; return mapping used."""
    mapping = {c: COLUMN_MAP[c] for c in df.columns if c in COLUMN_MAP}
    out = df.rename(columns=mapping).copy()
    return out, mapping


def coerce_numeric_with_flag(series: pd.Series, name: str) -> tuple[pd.Series, pd.Series]:
    """Coerce to numeric; return (numeric, non_numeric_flag)."""
    numeric = pd.to_numeric(series, errors="coerce")
    non_numeric = series.notna() & numeric.isna()
    return numeric, non_numeric.astype(int)
