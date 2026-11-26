# Dataset Provenance

## Active (this branch): DataCo SMART Supply Chain

| Field | Value |
|-------|-------|
| Adapted filename | DataCo_adapted_for_SCOPE.csv |
| Location | data/raw/DataCo_adapted_for_SCOPE.csv |
| Original filename | DataCoSupplyChainDataset.csv |
| Original location | data/raw/DataCoSupplyChainDataset.csv (local; may be gitignored if > repo limits) |
| Field dictionary | data/raw/DescriptionDataCoSupplyChain.csv |
| Source | Mendeley Data v5 |
| DOI | 10.17632/8gx2fvg2k6.5 |
| Citation | Constante, Fabian; Silva, Fernando; Pereira, António (2019), "DataCo SMART SUPPLY CHAIN FOR BIG DATA ANALYSIS", Mendeley Data, V5, doi:10.17632/8gx2fvg2k6.5 |
| Download page | https://data.mendeley.com/datasets/8gx2fvg2k6/5 |
| Adapter | `backend/scope/data/dataco_adapter.py` / `scripts/adapt_dataco.py` |
| Notes | Inventory_* fields in the adapted CSV are **synthetic trial proxies**. Do not treat them as real warehouse measurements. |

Re-adapt after refreshing the original CSV:

```bash
PYTHONPATH=backend python scripts/adapt_dataco.py
```

## Legacy: SCMS_with_inventory

| Field | Value |
|-------|-------|
| Filename | SCMS_with_inventory.csv |
| Location | data/raw/SCMS_with_inventory.csv |
| SHA-256 | 9B1088C58A45973DB124A1C2B7AD89A947C4CC9F39D55E23C760F2BACDBC003A |
| Size (bytes) | 4967844 |
| Ingestion date | 2026-11-06 |
| Notes | Still present for comparison; not the primary dataset on this branch. |
