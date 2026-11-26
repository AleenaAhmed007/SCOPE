# DataCo Trial Report (SCOPE pipeline)

**Branch:** `cursor/dataco-pipeline-trial-e3bb`  
**Source:** Constante et al. (2019), Mendeley Data V5, doi:10.17632/8gx2fvg2k6.5  
**Page:** https://data.mendeley.com/datasets/8gx2fvg2k6/5  

## What was done

1. Downloaded `DataCoSupplyChainDataset.csv` (~91 MB, 180,519 rows) from Mendeley.
2. Adapted columns to the SCOPE SCMS-shaped schema via `backend/scope/data/dataco_adapter.py`.
3. Pointed `configs/data.yaml` primary dataset at `data/raw/DataCo_adapted_for_SCOPE.csv`.
4. Ran `scripts/run_all_phases.py` end-to-end on the adapted data.

Inventory_* fields in the adapted CSV are **synthetic trial proxies** (DataCo has no warehouse stock). They exist only so Phase 07 can execute under the same leakage audit rules.

## Phase outcomes

| Phase | Status | Notes |
|-------|--------|-------|
| 02 Preprocessing | ok | 180,519 shipments; late label agreement with `Late_delivery_risk` = 100%; 7,754 canceled rows excluded from late/duration |
| 03 Late classification | ok | Best=XGBoost; test ROC-AUC≈0.75, PR-AUC≈0.84; F1-threshold flags almost all as late (base rate ~57%) |
| 04 Duration regression | ok | Best=GradientBoosting; test MAE≈0.99 days vs dummy median MAE≈1.39 |
| 05 Forecasting | ok | Late-rate → mean baseline; volume → naive lag-1 (same pattern as SCMS caution) |
| 06a Vendor segments | ok | Only 11 “vendors” (Department Name proxy); silhouette≈0.46 |
| 06b Anomaly | ok | Weight always missing → imputer skips that column |
| 07 Inventory | ok | Synthetic stockout proxy; **not operational** |
| 08 SHAP | ok | Top drivers: Shipping Mode (Standard/First Class) |
| 09 RAG | ok | Unchanged document corpus |
| 10 Evidence ledger | failed | PostgreSQL not available in this environment |
| 11 Sample investigation | failed | Same Postgres dependency (deterministic path still needs ledger) |
| 12 Model evaluation | ok | Metrics under `reports/metrics/evaluation_*.json` |
| 12b Walk-forward backtest | ok | 10 quarters late ROC-AUC mean≈0.74 (beats vendor-only every quarter); duration ML beats median 8/8 |
| 13 Final defence report | ok | Regenerated |

## Fit vs SCMS

| Aspect | DataCo trial | Implication |
|--------|--------------|-------------|
| Scale | ~18× more rows | Training works; vendor PIT features needed vectorization |
| Late label | Native `Late_delivery_risk` | Stronger, cleaner late target than SCMS date math alone |
| Shipment mode | Same Day / First / Second / Standard | Dominant SHAP driver; schedule tightness encodes late risk |
| Weight / freight | Weight absent; freight = 5% of line value | Weak numeric signal |
| Vendor | Department Name (11 values) | Segmentation thin vs SCMS real vendors |
| Inventory | Synthetic | Do not claim inventory validation on DataCo |
| Geography | 164 order countries | High-cardinality Country one-hot |

## Recommendation

DataCo **runs through the SCOPE ML stack** and is usable for late-delivery / duration / forecast / anomaly / SHAP trials at scale. Prefer it when you want a large labeled late-risk dataset. Keep SCMS (or a real WMS extract) for inventory and vendor-quality stories. Do not treat adapted inventory metrics as evidence of stockout prediction quality.
