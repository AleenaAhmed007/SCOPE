# SCOPE Final Evaluation Table (SCMS)

Primary dataset: `data/raw/SCMS_with_inventory.csv`.

## Classification — Late-delivery risk (test)

| Model | Role | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| xgboost | proposed | 0.690 | 0.229 | 0.683 | 0.342 | 0.760 | 0.298 |
| logistic_regression | baseline | 0.454 | 0.165 | 0.891 | 0.278 | 0.696 | 0.198 |
| random_forest | proposed | 0.726 | 0.283 | 0.858 | 0.425 | 0.803 | 0.296 |

**Best:** `random_forest` (test n=1550, late rate≈0.118).

## Classification — Inventory stockout experimental

| Model | Split | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| logistic_regression | validation | — | 0.496 | 0.654 | 0.564 | 0.697 | 0.572 |
| random_forest | test | 0.709 | 0.595 | 0.727 | 0.654 | 0.773 | 0.695 |

*Inventory fields are unverified/augmented — experimental only.*

## Regression — Delivery duration (test)

| Model | Role | MAE (days) | RMSE | R² |
| --- | --- | ---: | ---: | ---: |
| dummy_median | baseline | 81.188 | 106.502 | -0.111 |
| gradient_boosting | proposed | 81.204 | 107.151 | -0.124 |
| xgboost | proposed | 81.370 | 108.628 | -0.155 |
| random_forest | proposed | 80.729 | 105.137 | -0.082 |

**Selected basis:** `historical_median_baseline` / best reported `dummy_median`.

## Forecasting (MAE ↓ better)

| Task | Model | Role | Test MAE | RMSE | Notes |
| --- | --- | --- | ---: | ---: | --- |
| Forecast late-rate (monthly) | extra_trees | selected_classical | 0.068 | 0.083 | beats_naive=True; beats_mean=False |
| Forecast late-rate (monthly) | naive_lag1 | baseline | 0.087 | — | baseline |
| Forecast late-rate (monthly) | mean_baseline | baseline | 0.064 | — | baseline |
| Forecast volume (monthly) | extra_trees | selected_classical | 994,005.2 | 1,207,766.4 | beats_naive=False; beats_mean=True |
| Forecast volume (monthly) | naive_lag1 | baseline | 947,280.2 | — | baseline |
| Forecast volume (monthly) | mean_baseline | baseline | 1,205,206.1 | — | baseline |
| Forecast late-rate (weekly) | arima | selected_classical | 0.111 | 0.143 | weekly classical |
| Forecast volume (weekly) | persistence_linear | selected_classical | 464,212.5 | 682,923.5 | weekly classical |
| Forecast late-rate (weekly neural) | bilstm_exog_attn | neural_trial | 0.131 | — | deploy=False; val_mae=0.08429374401579108 |
| Forecast volume (weekly neural) | gru_lb12_h48 | neural_trial | 458,616.8 | — | deploy=True; val_mae=314877.2000446961 |

## Unsupervised / RAG / SHAP / Backtests

| Task | Model | Key metrics |
| --- | --- | --- |
| Vendor segmentation | kmeans_k=4 | silhouette=0.26827670925046854 |
| Anomaly (unusual shipment profile) | isolation_forest | anomaly_rate=0.05741935483870968; n_unusual=89 |
| Document retrieval (RAG) | hybrid_rrf_rerank | MRR=1.0; recall@3=1.0 |
| Explainability (SHAP) | random_forest | status=ok; explainer=TreeExplainer |
| Walk-forward late delivery | refit_quarterly | min_roc=0.7085450729120636; beats_vendor_only=9/10; precision=0.319, recall=0.790, ROC-AUC=0.789 |
| Walk-forward duration | rf_refit | ml_beats_median=2/8 |

## Flat CSV

Machine-readable: `reports/final_evaluation_table.csv`.
## Alternative datasets (if stronger results needed)

| Dataset | Why better for ML | Fit to SCOPE | Caution |
| --- | --- | --- | --- |
| **Olist Delivery Risk** (Brazilian e-commerce; HF `samuelalex37/olist-delivery-risk-data`) | ~96k orders, ~8% late, checkout-time features, distance engineered, frozen splits | Late-risk + duration (+ RAG docs separately) | Marketplace not pharma SCMS; license CC BY-NC-SA |
| **LaDe** (Cainiao last-mile; HF) | Millions of real packages, rich timestamps, ETA benchmarks | Duration / ETA / anomaly at scale | Heavy; different domain (courier last-mile) |
| DataCo (already tried) | Large labeled late risk | Pipeline runs | Weak ML-vs-baseline lift; no real inventory |
| SynDelay | Synthetic delay labels for benchmarking | Delay classification | Synthetic — weaker paper claim than real data |

**Recommendation:** Keep **SCMS** as primary paper dataset. If a second dataset is needed for stronger classification metrics / external validity, trial **Olist Delivery Risk** next (not DataCo).
