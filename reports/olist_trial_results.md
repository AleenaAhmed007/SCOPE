# Olist pipeline trial — results vs SCMS

**Branch:** `cursor/olist-pipeline-trial-e3bb`  
**Dataset:** Hugging Face `samuelalex37/olist-delivery-risk-data` → adapted to SCMS schema via `scope.data.olist_adapter`  
**Rows:** 96,470 shipments · late prevalence ≈ 6.8% overall (test ≈ 4.3%) · calendar span Oct 2016–Oct 2018 (~25 months)

Inventory_* columns on this branch are **synthetic trial proxies** (not real warehouse stock).

---

## Headline comparison

| Task | Olist (this trial) | SCMS (paper baseline) | Verdict |
|---|---|---|---|
| Late delivery (test ROC-AUC) | **0.719** (logistic regression) | **0.807** (random forest) | SCMS stronger |
| Late delivery (test PR-AUC) | 0.121 | 0.307 | SCMS stronger |
| Late delivery (test F1 / prec / rec) | 0.167 / 0.100 / 0.493 | 0.431 / 0.292 / 0.825 | SCMS stronger |
| Late walk-forward mean ROC | 0.590 (5 quarters) | ~0.79 (longer history) | SCMS more stable |
| Duration test MAE | **4.82 days** (GB; median baseline 5.00) | ~81 days (RF ≈ median) | Different scale; Olist GB beats median slightly |
| Monthly late-rate forecast | mean baseline MAE **0.039** (beats naive) | extra_trees MAE 0.068 (beats naive, not mean) | Both → classical / baseline |
| Monthly volume forecast | GB MAE 4173 (loses to naive 3818); only 4 test months | extra_trees loses to naive on long series | Short Olist series → weak forecast signal |
| Inventory proxy | Synthetic; test ROC ≈ 0.53 | Experimental but richer signal on SCMS fields | Do not trust Olist inventory |

---

## What ran

Phases 02–13 completed on Olist after short-series forecast + walk-forward guards:

| Phase | Status |
|---|---|
| 02 Preprocessing | ok |
| 03 Late classification | ok — best = logistic_regression |
| 04 Duration regression | ok — best = gradient_boosting |
| 05 Forecasting | ok (after zero-weight / short-history fix) |
| 06 Vendor seg + anomaly | ok |
| 07 Inventory experiment | ok (synthetic labels) |
| 08 SHAP | ok |
| 09–11 RAG / evidence / sample investigation | ok |
| 12 Model evaluation | ok |
| 12b Walk-forward | ok (5 late quarters; early quarters skipped — insufficient pre-calibration history) |
| 13 Final defence report | regenerated |

Tree models (XGBoost / RF) collapsed on Olist late-risk after schema mapping (test ROC ≈ 0.46–0.48). Logistic regression recovers usable ranking (0.72) using state, distance-bin / estimated-days cues folded into existing SCMS fields, but precision stays low at ~4% test prevalence.

---

## Late delivery detail (Olist)

| Model | Test ROC-AUC | Test PR-AUC | Test F1 |
|---|---|---|---|
| logistic_regression (**selected**) | 0.719 | 0.121 | 0.167 |
| xgboost | 0.484 | 0.048 | 0.077 |
| random_forest | 0.459 | 0.041 | 0.068 |
| vendor-history-only baseline | 0.491 | 0.044 | 0.000 |

Vendor history alone is near-random on Olist (high seller cardinality / short repeat history). Chronological rolling-origin CV mean ROC ≈ 0.68 ± 0.06.

---

## Duration + forecast detail (Olist)

- **Duration:** GB test MAE 4.82 vs median baseline 5.00; walk-forward ML beats median in **6 / 7** quarters. Absolute error is small because Olist delivery spans are days, not SCMS’s multi-month pharma lead times.
- **Late-rate monthly:** 25 periods → selected **mean_baseline** (test MAE 0.039, n_test=4). LSTM not recommended (`lstm_recommended: false`).
- **Volume monthly:** selected gradient_boosting but **does not beat** naive/mean on the 4-month holdout; walk-forward prefers `persistence_linear`.

---

## Recommendation for the paper

Keep **SCMS** as the primary late-delivery / SCOPE defence dataset. Olist is useful as a **negative / transfer trial**:

1. Schema adapters can run the full SCOPE stack on another public delivery corpus.
2. Late-risk discrimination is weaker once high-cardinality sellers replace SCMS vendors (ROC 0.72 vs 0.81; PR-AUC much lower).
3. Monthly forecasting is under-powered at ~2 years of history; classical baselines dominate.
4. Inventory results on Olist must be labelled synthetic and excluded from claims.

Reproduce: `python scripts/adapt_olist.py` then `PYTHONPATH=backend python scripts/run_all_phases.py` with `configs/data.yaml` pointing at `Olist_adapted_for_SCOPE.csv`.
