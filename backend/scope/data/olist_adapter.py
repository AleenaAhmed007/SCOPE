"""Map Olist Delivery Risk rows onto the SCOPE SCMS-shaped schema.

Source: Hugging Face ``samuelalex37/olist-delivery-risk-data`` (derived from the
Brazilian E-Commerce Public Dataset by Olist, CC BY-NC-SA 4.0).

Inventory_* fields are synthetic trial proxies so Phase 07 can execute under the
same leakage audit as SCMS. Do not treat them as real warehouse stock.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from scope.logging_config import setup_logging

logger = setup_logging()


def adapt_olist_frame(raw: pd.DataFrame, *, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = len(raw)

    purchase = pd.to_datetime(raw["order_purchase_timestamp"], errors="coerce")
    estimated = pd.to_datetime(raw["order_estimated_delivery_date"], errors="coerce")
    delivered = pd.to_datetime(raw["order_delivered_customer_date"], errors="coerce")
    approved = pd.to_datetime(raw["order_approved_at"], errors="coerce")

    qty = pd.to_numeric(raw["n_items"], errors="coerce").fillna(1)
    value = pd.to_numeric(raw["total_price"], errors="coerce")
    freight = pd.to_numeric(raw["total_freight"], errors="coerce")
    weight_kg = pd.to_numeric(raw["total_weight_g"], errors="coerce") / 1000.0
    late = pd.to_numeric(raw["is_late"], errors="coerce").fillna(0).astype(int)

    # Synthetic inventory proxies (trial only).
    product_key = raw["primary_category"].astype(str)
    warehouse = raw["seller_state"].astype(str).fillna("UNK")
    opening = np.maximum(1, (qty.to_numpy() * rng.uniform(0.5, 3.0, size=n)).astype(int))
    stock_out = qty.astype(int).to_numpy()
    closing = np.maximum(0, opening - stock_out)
    reorder = np.maximum(1, (opening * 0.4).astype(int))
    stockout = (closing <= 0).astype(int)
    shortage = np.maximum(0, stock_out - opening)
    replenish = ((opening < reorder) | (stockout == 1)).astype(int)

    # Stable numeric ID from order_id
    ids = pd.factorize(raw["order_id"].astype(str))[0].astype(np.int64) + 1

    out = pd.DataFrame(
        {
            "ID": ids,
            "Project Code": raw["customer_state"].astype(str),
            "PQ #": "Olist-N/A",
            "PO / SO #": raw["order_id"].astype(str),
            "ASN/DN #": raw["order_id"].astype(str),
            # Lower-cardinality geos / sellers so SCOPE one-hots generalize on holdout.
            "Country": raw["customer_state"].astype(str),
            "Managed By": np.where(raw["same_state"].astype(int) == 1, "SameState", "CrossState"),
            "Fulfill Via": np.where(raw["multi_seller_order"].astype(int) == 1, "MultiSeller", "SingleSeller"),
            "Vendor INCO Term": raw["payment_type"].astype(str),
            "Shipment Mode": pd.cut(
                pd.to_numeric(raw["distance_km"], errors="coerce").fillna(0),
                bins=[-0.1, 50, 200, 500, 1000, 1e9],
                labels=["Local", "Short", "Medium", "Long", "VeryLong"],
            ).astype(str),
            "PQ First Sent to Client Date": purchase.dt.strftime("%Y-%m-%d"),
            "PO Sent to Vendor Date": approved.fillna(purchase).dt.strftime("%Y-%m-%d"),
            "Scheduled Delivery Date": estimated.dt.strftime("%Y-%m-%d"),
            "Delivered to Client Date": delivered.dt.strftime("%Y-%m-%d"),
            "Delivery Recorded Date": delivered.dt.strftime("%Y-%m-%d"),
            "Product Group": raw["primary_category"].astype(str),
            "Sub Classification": raw["seller_state"].astype(str),
            "Vendor": raw["seller_state"].astype(str),  # state-level vendor proxy (not raw seller id)
            "Item Description": raw["primary_category"].astype(str),
            "Molecule/Test Type": raw["primary_category"].astype(str),
            "Brand": raw["seller_state"].astype(str),
            "Dosage": "N/A",
            "Dosage Form": raw["payment_type"].astype(str),
            # Store promised horizon (known at checkout) in UoM slot for numeric use.
            "Unit of Measure (Per Pack)": pd.to_numeric(raw["estimated_delivery_days"], errors="coerce"),
            "Line Item Quantity": qty,
            "Line Item Value": value,
            "Pack Price": pd.to_numeric(raw["price_per_item"], errors="coerce"),
            "Unit Price": pd.to_numeric(raw["price_per_item"], errors="coerce"),
            "Manufacturing Site": raw["seller_state"].astype(str),
            "First Line Designation": np.where(raw["is_sao_paulo_seller"].astype(int) == 1, "Yes", "No"),
            "Weight (Kilograms)": weight_kg,
            "Freight Cost (USD)": freight,  # BRL in source; numeric freight feature
            "Line Item Insurance (USD)": pd.to_numeric(raw["distance_km"], errors="coerce"),
            "Inventory_Product_Key": product_key,
            "Inventory_Warehouse_ID": warehouse,
            "Inventory_Date": purchase.dt.strftime("%Y-%m-%d"),
            "Inventory_Opening_Stock": opening,
            "Inventory_Stock_In": 0,
            "Inventory_Stock_Out": stock_out,
            "Inventory_Closing_Stock": closing,
            "Inventory_Reorder_Level": reorder,
            "Inventory_Lead_Time_Days": 30,
            "Inventory_Stockout_Flag": stockout,
            "Inventory_Shortage_Quantity": shortage,
            "Inventory_Replenishment_Triggered": replenish,
            # Trial metadata (ignored by COLUMN_MAP)
            "Olist_is_late": late,
            "Olist_distance_km": pd.to_numeric(raw["distance_km"], errors="coerce"),
            "Olist_estimated_delivery_days": pd.to_numeric(
                raw["estimated_delivery_days"], errors="coerce"
            ),
        }
    )
    return out


def write_adapted_csv(source: Path, dest: Path) -> dict[str, Any]:
    logger.info("Loading Olist parquet from %s", source)
    raw = pd.read_parquet(source)
    logger.info("Olist raw shape=%s late_rate=%.4f", raw.shape, float(raw["is_late"].mean()))
    adapted = adapt_olist_frame(raw)
    dest.parent.mkdir(parents=True, exist_ok=True)
    adapted.to_csv(dest, index=False)
    meta = {
        "source": str(source),
        "dest": str(dest),
        "rows": int(len(adapted)),
        "late_rate": float(raw["is_late"].mean()),
        "inventory_provenance": "synthetic_trial_proxy",
        "source_citation": (
            "Olist Delivery Risk analytical table "
            "(HF samuelalex37/olist-delivery-risk-data; derived from Olist Brazilian "
            "E-Commerce Public Dataset, CC BY-NC-SA 4.0)"
        ),
    }
    logger.info("Wrote adapted Olist CSV -> %s (%d rows)", dest, len(adapted))
    return meta
