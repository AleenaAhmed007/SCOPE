# Model Results and Baseline Comparison

Source: `reports/final_evaluation.json` (generated `2026-11-14T13:58:57.187239+00:00`).

Regenerate with:

```bash
python scripts/build_model_comparison_tables.py
```

## 1. Late delivery (classification)

Positive class = late shipment. Selected model: **random_forest**.

### Validation

| Model | Role | Threshold | Precision | Recall | F1 | ROC-AUC | PR-AUC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| xgboost | candidate | 0.270 | 0.334 | 0.758 | 0.463 | 0.747 | 0.336 |
| logistic_regression | candidate | 0.622 | 0.318 | 0.758 | 0.448 | 0.733 | 0.309 |
| random_forest | selected | 0.217 | 0.361 | 0.872 | 0.511 | 0.789 | 0.366 |

### Test (incl. baselines)

| Model | Role | Threshold | Precision | Recall | F1 | ROC-AUC | PR-AUC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| xgboost | candidate | 0.270 | 0.230 | 0.650 | 0.340 | 0.764 | 0.278 |
| logistic_regression | candidate | 0.622 | 0.168 | 0.754 | 0.275 | 0.694 | 0.197 |
| random_forest | selected | 0.217 | 0.292 | 0.825 | 0.431 | 0.807 | 0.307 |
| vendor_history_only | baseline |  | 0.000 | 0.000 | 0.000 | 0.787 | 0.255 |
| prevalence_probability | baseline |  | 0.000 | 0.000 | 0.000 | 0.500 | 0.118 |

## 2. Delivery duration (regression)

Target = PO-to-client days. Selected model: **random_forest**. Lower MAE is better.

### Test

| Model | Role | MAE (days) | RMSE | Median AE | R² |
| --- | --- | --- | --- | --- | --- |
| dummy_median | baseline | 81.188 | 106.502 | 64.000 | -0.111 |
| gradient_boosting | candidate | 81.042 | 108.178 | 60.656 | -0.146 |
| xgboost | candidate | 80.801 | 109.254 | 62.506 | -0.169 |
| random_forest | selected | 81.223 | 107.160 | 61.533 | -0.124 |

## 3. Monthly forecasting

### Late rate — test

| Model | Role | MAE | Weighting | n_test |
| --- | --- | --- | --- | --- |
| extra_trees | selected | 0.0682 | shipment_count_weighted | 22 |
| naive_lag1 | baseline | 0.0872 | shipment_count_weighted | 22 |
| mean_baseline | baseline | 0.0640 | shipment_count_weighted | 22 |

### Volume — test

| Model | Role | MAE | Weighting | n_test |
| --- | --- | --- | --- | --- |
| extra_trees | selected | 994005.2 | unweighted | 22 |
| naive_lag1 | baseline | 947280.2 | unweighted | 22 |
| mean_baseline | baseline | 1205206.1 | unweighted | 22 |

## 4. Inventory stockout proxy (experimental)

Selected model: **random_forest**. Inventory fields are unverified augmented data.

| Model | Role | Split | Precision | Recall | F1 | ROC-AUC | PR-AUC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| logistic_regression | candidate | validation | 0.490 | 0.652 | 0.559 | 0.698 | 0.574 |
| random_forest | selected | validation | 0.535 | 0.738 | 0.621 | 0.776 | 0.652 |
| random_forest | selected | test | 0.588 | 0.731 | 0.651 | 0.782 | 0.705 |
| training_prevalence_probability | baseline | validation |  |  |  |  | 0.338 |
| test_prevalence | baseline | test |  |  |  |  | 0.379 |

## 5. Selected model vs baseline (summary)

| Task | Selected model | Baseline | Metric | Model | Baseline value | Delta | Beats baseline? | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| late_delivery | random_forest | vendor_history_only | roc_auc | 0.807 | 0.787 | 0.020 | true | Higher is better |
| late_delivery | random_forest | vendor_history_only | pr_auc | 0.307 | 0.255 | 0.052 | true | Higher is better |
| late_delivery | random_forest | prevalence_probability | pr_auc | 0.307 | 0.118 | 0.189 | true | Higher is better; prevalence = positive rate |
| delivery_duration | random_forest | dummy_median | mae_days | 81.223 | 81.188 | 0.036 | false | Lower MAE is better; selected beat median on validation only |
| monthly_late_rate | extra_trees | naive_lag1 | mae | 0.0682 | 0.0872 | -0.0191 | true | Lower MAE is better; selection used validation only |
| monthly_late_rate | extra_trees | mean_baseline | mae | 0.0682 | 0.0640 | 0.0042 | false | Lower MAE is better; selection used validation only |
| monthly_volume | extra_trees | naive_lag1 | mae | 994005.2 | 947280.2 | 46725.0 | false | Lower MAE is better; selection used validation only |
| monthly_volume | extra_trees | mean_baseline | mae | 994005.2 | 1205206.1 | -211200.9 | true | Lower MAE is better; selection used validation only |
| inventory_stockout_proxy | random_forest | training_prevalence_probability | pr_auc | 0.652 | 0.338 | 0.314 | true | Validation comparison used for selection; source unverified |
| inventory_stockout_proxy | random_forest | test_prevalence | pr_auc | 0.705 | 0.379 | 0.326 | true | Experimental proxy; inventory provenance unverified |

## CSV outputs

| File | Contents |
| --- | --- |
| `reports/metrics/model_results_late_delivery.csv` | Late-delivery candidates + baselines |
| `reports/metrics/model_results_duration.csv` | Duration candidates + median baseline |
| `reports/metrics/model_results_forecasting.csv` | Forecast candidates + naive/mean |
| `reports/metrics/model_results_inventory.csv` | Inventory proxy + prevalence baseline |
| `reports/metrics/model_vs_baseline_comparison.csv` | One-row-per comparison deltas |
