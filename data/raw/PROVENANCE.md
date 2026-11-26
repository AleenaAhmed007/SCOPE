# Dataset Provenance

## Active (this branch): Olist Delivery Risk

| Field | Value |
|-------|-------|
| Adapted filename | Olist_adapted_for_SCOPE.csv |
| Original | data/raw/olist_analytical.parquet |
| Source | Hugging Face `samuelalex37/olist-delivery-risk-data` |
| Upstream | Brazilian E-Commerce Public Dataset by Olist (CC BY-NC-SA 4.0) |
| Adapter | `backend/scope/data/olist_adapter.py` / `scripts/adapt_olist.py` |
| Notes | Inventory_* fields are **synthetic trial proxies**. `Country` maps to Brazilian customer state. |

## Legacy: SCMS_with_inventory

Still present at `data/raw/SCMS_with_inventory.csv` for comparison; not primary on this branch.
