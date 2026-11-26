# Proposal Model Results and Baseline Comparison

Aligned to SCOPE proposal **§6 Models**.

Source: `reports/final_evaluation.json` (`2026-11-26T14:31:04.815111+00:00`).

Regenerate:

```bash
python scripts/build_proposal_model_tables.py
```

## 6. Models (proposal map)

| Task | Model | Baseline | Implemented |
| --- | --- | --- | --- |
| Late-delivery risk | XGBoost, Random Forest | Logistic Regression | yes |
| Delay and volume forecasting | LSTM | Naive forecast, ARIMA | classical candidates trained; LSTM not trained (short monthly history) |
| Lead-time prediction | Gradient-boosted regression | Historical median | yes |
| Supplier segmentation | K-Means | N/A (unsupervised) | yes |
| Anomaly detection | Isolation Forest | N/A (unsupervised) | yes |
| Inventory risk | Classification on stock cover vs lead time | Logistic Regression / prevalence | yes (experimental) |
| Document retrieval | Embeddings, BM25, cross-encoder reranker | N/A (wiring benchmark) | yes |
| Explanations | SHAP | N/A | yes |

> ML and DL models are compared with simple baselines (**Logistic Regression, naive forecast, ARIMA**).

## Results by proposal task

| Task | Model | Role | Split | Metric | Value | Metric 2 | Value 2 | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Late-delivery risk | xgboost | proposed_model | test | roc_auc | 0.760 | pr_auc | 0.280 | Proposal models vs Logistic Regression baseline |
| Late-delivery risk | random_forest | proposed_model | test | roc_auc | 0.806 | pr_auc | 0.310 | Proposal models vs Logistic Regression baseline |
| Late-delivery risk | logistic_regression | baseline | test | roc_auc | 0.656 | pr_auc | 0.162 | Proposal models vs Logistic Regression baseline |
| Delay forecasting (monthly late rate) | LSTM | proposed_model | test | mae |  |  |  | Classical monthly lag models are compared with explicit baselines; no neural model is justified without a demonstrated validation gain. |
| Delay forecasting (monthly late rate) | naive_forecast | baseline | test | mae | 0.0756 |  |  | Lower MAE is better; shipment-count weighted |
| Delay forecasting (monthly late rate) | ARIMA | baseline | test | mae | 0.0584 |  |  | Lower MAE is better; shipment-count weighted |
| Delay forecasting (monthly late rate) | mean_baseline | selected_classical | test | mae | 0.0610 |  |  | Lower MAE is better; shipment-count weighted |
| Volume forecasting (monthly quantity) | LSTM | proposed_model | test | mae |  |  |  | Classical monthly lag models are compared with explicit baselines; no neural model is justified without a demonstrated validation gain. |
| Volume forecasting (monthly quantity) | naive_forecast | baseline | test | mae | 1002339.6 |  |  | Lower MAE is better; quantity proxy not warehouse demand |
| Volume forecasting (monthly quantity) | ARIMA | baseline | test | mae | 1249357.1 |  |  | Lower MAE is better; quantity proxy not warehouse demand |
| Volume forecasting (monthly quantity) | naive_lag1 | selected_classical | test | mae | 1002339.6 |  |  | Lower MAE is better; quantity proxy not warehouse demand |
| Lead-time prediction | gradient_boosting | proposed_model | test | mae_days | 81.045 | r2 | -0.148 | PO-to-client duration |
| Lead-time prediction | historical_median | baseline | test | mae_days | 81.188 | r2 | -0.111 | Simple baseline |
| Supplier segmentation | kmeans | proposed_model | full | k | 4 | silhouette | 0.268 | Unsupervised; no labeled baseline |
| Anomaly detection | isolation_forest_unusual_profile | proposed_model | test | anomaly_rate | 0.057 | n_anomaly | 550 | Unsupervised; no ground-truth labels |
| Anomaly detection | isolation_forest_vendor_kpi | proposed_model | all_periods | n_anomaly | 10 | n_periods | 277 | Proposal supplier-KPI anomaly model |
| Inventory risk | random_forest | proposed_model | test | pr_auc | 0.705 | roc_auc | 0.782 | Experimental; inventory provenance unverified |
| Inventory risk | logistic_regression | baseline | validation | pr_auc | 0.574 | roc_auc | 0.698 | Experimental; inventory provenance unverified |
| Document retrieval | embeddings+BM25+cross-encoder | proposed_model | synthetic_queries | mrr | 1.000 | recall@3 | 1.000 | Wiring sanity check on synthetic queries, not a quality benchmark |
| Explanations | SHAP | proposed_model | sample | status | ok | n_samples | 200 | Global/local explanations for late-delivery model |

## Proposed model vs baseline

| Task | Proposed model | Baseline | Metric | Model | Baseline value | Delta | Beats baseline? | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Late-delivery risk | xgboost | logistic_regression | roc_auc | 0.760 | 0.656 | 0.105 | true | Higher is better |
| Late-delivery risk | xgboost | logistic_regression | pr_auc | 0.280 | 0.162 | 0.119 | true | Higher is better |
| Late-delivery risk | xgboost | logistic_regression | f1 | 0.357 | 0.282 | 0.075 | true | Higher is better |
| Late-delivery risk | random_forest | logistic_regression | roc_auc | 0.806 | 0.656 | 0.150 | true | Higher is better |
| Late-delivery risk | random_forest | logistic_regression | pr_auc | 0.310 | 0.162 | 0.149 | true | Higher is better |
| Late-delivery risk | random_forest | logistic_regression | f1 | 0.418 | 0.282 | 0.136 | true | Higher is better |
| Delay forecasting (monthly late rate) | ARIMA (classical stand-in; LSTM not trained) | naive_forecast | mae | 0.0584 | 0.0756 | -0.0172 | true | Lower MAE is better |
| Volume forecasting (monthly quantity) | ARIMA (classical stand-in; LSTM not trained) | naive_forecast | mae | 1249357.1 | 1002339.6 | 247017.5 | false | Lower MAE is better |
| Lead-time prediction | gradient_boosting | historical_median | mae_days | 81.045 | 81.188 | -0.143 | true | Lower MAE is better |
| Inventory risk | random_forest | logistic_regression | pr_auc | 0.652 | 0.574 | 0.078 | true | Validation comparison; higher is better |

## CSV outputs

| File | Contents |
| --- | --- |
| `reports/metrics/proposal_model_map.csv` | Proposal §6 task → model map |
| `reports/metrics/proposal_model_results.csv` | Per-task metrics |
| `reports/metrics/proposal_vs_baseline.csv` | Proposed models vs baselines |
