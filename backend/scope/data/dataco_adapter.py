"""Map DataCo SMART Supply Chain rows onto the SCOPE SCMS-shaped schema.

This is a trial adapter for branch experiments. Inventory_* fields are
synthesized proxies (not real warehouse data) so Phase 07 can execute and be
audited with the same leakage rules as SCMS. Source: Mendeley Data
doi:10.17632/8gx2fvg2k6.5 — do not cite Kaggle mirrors in repo docs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from scope.logging_config import setup_logging

logger = setup_logging()

DATACO_ENCODING = "latin-1"


def _parse_dataco_datetime(series: pd.Series) -> pd.Series:
    """DataCo timestamps are US-style M/D/YYYY[ HH:MM]; emit timezone-naive datetimes."""
    return pd.to_datetime(series, errors="coerce", dayfirst=False, format="mixed")


def adapt_dataco_frame(raw: pd.DataFrame, *, seed: int = 42) -> pd.DataFrame:
    """Convert a DataCo raw frame into SCMS_with_inventory-compatible columns."""
    rng = np.random.default_rng(seed)
    n = len(raw)

    order_dt = _parse_dataco_datetime(raw["order date (DateOrders)"])
    ship_dt = _parse_dataco_datetime(raw["shipping date (DateOrders)"])
    scheduled_days = pd.to_numeric(raw["Days for shipment (scheduled)"], errors="coerce").fillna(0)
    scheduled_dt = order_dt + pd.to_timedelta(scheduled_days, unit="D")

    # Prefer DataCo's labeled late risk; fall back to schedule vs actual ship date.
    late_label = pd.to_numeric(raw["Late_delivery_risk"], errors="coerce")
    # Shipping canceled rows have ambiguous outcomes — leave late blank later via dates.

    qty = pd.to_numeric(raw["Order Item Quantity"], errors="coerce")
    value = pd.to_numeric(raw["Order Item Total"], errors="coerce")
    price = pd.to_numeric(raw["Product Price"], errors="coerce")
    sales = pd.to_numeric(raw["Sales"], errors="coerce")

    # Synthetic inventory proxies keyed by product + market (trial only).
    product_key = raw["Product Card Id"].astype(str)
    warehouse = raw["Market"].astype(str).fillna("UNK")
    # Opening stock ~ recent demand scale; stockout when qty exceeds opening.
    opening = np.maximum(1, (qty.fillna(1).to_numpy() * rng.uniform(0.5, 3.0, size=n)).astype(int))
    stock_out = qty.fillna(0).astype(int).to_numpy()
    closing = np.maximum(0, opening - stock_out)
    reorder = np.maximum(1, (opening * 0.4).astype(int))
    stockout = (closing <= 0).astype(int)
    shortage = np.maximum(0, stock_out - opening)
    replenish = ((opening < reorder) | (stockout == 1)).astype(int)

    out = pd.DataFrame(
        {
            "ID": pd.to_numeric(raw["Order Item Id"], errors="coerce").astype("Int64"),
            "Project Code": raw["Order Region"].astype(str),
            "PQ #": "DataCo-N/A",
            "PO / SO #": raw["Order Id"].astype(str),
            "ASN/DN #": raw["Order Item Id"].astype(str),
            "Country": raw["Order Country"].astype(str),
            "Managed By": raw["Market"].astype(str),
            "Fulfill Via": raw["Customer Segment"].astype(str),
            "Vendor INCO Term": raw["Type"].astype(str),  # payment type proxy
            "Shipment Mode": raw["Shipping Mode"].astype(str),
            "PQ First Sent to Client Date": order_dt.dt.strftime("%Y-%m-%d"),
            "PO Sent to Vendor Date": order_dt.dt.strftime("%Y-%m-%d"),
            "Scheduled Delivery Date": scheduled_dt.dt.strftime("%Y-%m-%d"),
            "Delivered to Client Date": ship_dt.dt.strftime("%Y-%m-%d"),
            "Delivery Recorded Date": ship_dt.dt.strftime("%Y-%m-%d"),
            "Product Group": raw["Category Name"].astype(str),
            "Sub Classification": raw["Department Name"].astype(str),
            "Vendor": raw["Department Name"].astype(str),
            "Item Description": raw["Product Name"].astype(str),
            "Molecule/Test Type": raw.get("Category Name", pd.Series(["Unknown"] * n)).astype(str),
            "Brand": raw["Product Name"].astype(str),
            "Dosage": "N/A",
            "Dosage Form": raw["Customer Segment"].astype(str),
            "Unit of Measure (Per Pack)": 1,
            "Line Item Quantity": qty,
            "Line Item Value": value.fillna(sales),
            "Pack Price": price,
            "Unit Price": price,
            "Manufacturing Site": raw["Order City"].astype(str),
            "First Line Designation": np.where(
                late_label.fillna(-1).to_numpy() >= 0, "Yes", "No"
            ),
            # Weight unknown in DataCo; freight/insurance use sales/discount proxies.
            "Weight (Kilograms)": pd.NA,
            "Freight Cost (USD)": (value.fillna(sales) * 0.05).round(2),
            "Line Item Insurance (USD)": pd.to_numeric(
                raw.get("Order Item Discount"), errors="coerce"
            ),
            "Inventory_Product_Key": product_key,
            "Inventory_Warehouse_ID": warehouse,
            "Inventory_Date": order_dt.dt.strftime("%Y-%m-%d"),
            "Inventory_Opening_Stock": opening,
            "Inventory_Stock_In": 0,
            "Inventory_Stock_Out": stock_out,
            "Inventory_Closing_Stock": closing,
            "Inventory_Reorder_Level": reorder,
            "Inventory_Lead_Time_Days": 30,
            "Inventory_Stockout_Flag": stockout,
            "Inventory_Shortage_Quantity": shortage,
            "Inventory_Replenishment_Triggered": replenish,
            # Trial metadata (ignored by COLUMN_MAP / models)
            "DataCo_Delivery_Status": raw["Delivery Status"].astype(str),
            "DataCo_Late_delivery_risk": late_label,
            "DataCo_Days_shipping_real": pd.to_numeric(
                raw["Days for shipping (real)"], errors="coerce"
            ),
            "DataCo_Days_shipment_scheduled": scheduled_days,
        }
    )

    # Drop canceled shipments from late evaluation by blanking delivery dates
    canceled = raw["Delivery Status"].astype(str).str.contains("canceled", case=False, na=False)
    out.loc[canceled, "Delivered to Client Date"] = pd.NA
    out.loc[canceled, "Delivery Recorded Date"] = pd.NA

    return out


def load_and_adapt_dataco(path: Path) -> pd.DataFrame:
    logger.info("Loading DataCo CSV from %s (encoding=%s)", path, DATACO_ENCODING)
    raw = pd.read_csv(path, encoding=DATACO_ENCODING, low_memory=False)
    logger.info("DataCo raw shape=%s", raw.shape)
    adapted = adapt_dataco_frame(raw)
    logger.info("DataCo adapted shape=%s", adapted.shape)
    return adapted


def write_adapted_csv(source: Path, dest: Path) -> dict[str, Any]:
    adapted = load_and_adapt_dataco(source)
    dest.parent.mkdir(parents=True, exist_ok=True)
    adapted.to_csv(dest, index=False)
    meta = {
        "source": str(source),
        "dest": str(dest),
        "rows": int(len(adapted)),
        "columns": list(adapted.columns),
        "inventory_provenance": "synthetic_trial_proxy",
        "source_citation": "Constante et al. (2019), Mendeley Data, doi:10.17632/8gx2fvg2k6.5",
    }
    logger.info("Wrote adapted DataCo CSV -> %s (%d rows)", dest, len(adapted))
    return meta
