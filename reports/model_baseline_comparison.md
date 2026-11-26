# Model Results and Baseline Comparison

Source: `reports/final_evaluation.json` (generated `2026-11-26T14:30:20.014789+00:00`).

Regenerate with:

```bash
python scripts/build_model_comparison_tables.py
```

## 1. Late delivery (classification)

Positive class = late shipment. Selected model: **random_forest**.

### Validation

| Model | Role | Threshold | Precision | Recall | F1 | ROC-AUC | PR-AUC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| xgboost | candidate | 0.242 | 0.332 | 0.765 | 0.463 | 0.743 | 0.331 |
| logistic_regression | candidate | 0.407 | 0.285 | 0.927 | 0.436 | 0.721 | 0.292 |
| random_forest | selected | 0.158 | 0.350 | 0.945 | 0.511 | 0.791 | 0.365 |
| extra_trees | candidate | 0.416 | 0.342 | 0.955 | 0.504 | 0.791 | 0.395 |

### Test (incl. baselines)

| Model | Role | Threshold | Precision | Recall | F1 | ROC-AUC | PR-AUC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| xgboost | candidate | 0.242 | 0.238 | 0.716 | 0.357 | 0.760 | 0.280 |
| logistic_regression | candidate | 0.407 | 0.168 | 0.885 | 0.282 | 0.656 | 0.162 |
| random_forest | selected | 0.158 | 0.274 | 0.885 | 0.418 | 0.806 | 0.310 |
| extra_trees | candidate | 0.416 | 0.267 | 0.907 | 0.413 | 0.808 | 0.300 |
| vendor_history_only | baseline |  | 0.000 | 0.000 | 0.000 | 0.787 | 0.255 |
| prevalence_probability | baseline |  | 0.000 | 0.000 | 0.000 | 0.500 | 0.118 |

## 2. Delivery duration (regression)

Target = PO-to-client days. Selected model: **random_forest**. Lower MAE is better.

### Test

| Model | Role | MAE (days) | RMSE | Median AE | R² |
| --- | --- | --- | --- | --- | --- |
| dummy_median | baseline | 81.188 | 106.502 | 64.000 | -0.111 |
| shipment_mode_median | baseline | 80.957 | 114.951 | 47.000 | -0.294 |
| gradient_boosting | candidate | 81.045 | 108.296 | 60.812 | -0.148 |
| xgboost | candidate | 79.970 | 106.470 | 63.197 | -0.110 |
| random_forest | candidate | 80.651 | 104.732 | 64.772 | -0.074 |

## 3. Monthly forecasting

### Late rate — test

| Model | Role | MAE | Weighting | n_test |
| --- | --- | --- | --- | --- |
| mean_baseline | selected | 0.0610 | shipment_count_weighted | 20 |
| naive_lag1 | baseline | 0.0756 | shipment_count_weighted | 20 |
| mean_baseline | baseline | 0.0610 | shipment_count_weighted | 20 |

### Volume — test

| Model | Role | MAE | Weighting | n_test |
| --- | --- | --- | --- | --- |
| naive_lag1 | selected | 1002339.6 | unweighted | 20 |
| naive_lag1 | baseline | 1002339.6 | unweighted | 20 |
| mean_baseline | baseline | 1244626.2 | unweighted | 20 |

## 4. Inventory stockout proxy (experimental)

Selected model: **random_forest**. Inventory fields are unverified augmented data.

| Model | Role | Split | Precision | Recall | F1 | ROC-AUC | PR-AUC |
| --- | --- | --- | --- | --- | --- | --- | --- |

## 5. Selected model vs baseline (summary)

| Task | Selected model | Baseline | Metric | Model | Baseline value | Delta | Beats baseline? | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| late_delivery | random_forest | vendor_history_only | roc_auc | 0.806 | 0.787 | 0.020 | true | Higher is better |
| late_delivery | random_forest | vendor_history_only | pr_auc | 0.310 | 0.255 | 0.055 | true | Higher is better |
| late_delivery | random_forest | prevalence_probability | pr_auc | 0.310 | 0.118 | 0.192 | true | Higher is better; prevalence = positive rate |
| delivery_duration | shipment_mode_median | dummy_median | mae_days | 80.957 | 81.188 | -0.231 | true | Lower MAE is better |
| monthly_late_rate | mean_baseline | naive_lag1 | mae | 0.0610 | 0.0756 | -0.0146 | true | Lower MAE is better; selection used validation only |
| monthly_late_rate | mean_baseline | mean_baseline | mae | 0.0610 | 0.0610 | 0.0000 | false | Lower MAE is better; selection used validation only |
| monthly_volume | naive_lag1 | naive_lag1 | mae | 1002339.6 | 1002339.6 | 0.0 | false | Lower MAE is better; selection used validation only |
| monthly_volume | naive_lag1 | mean_baseline | mae | 1002339.6 | 1244626.2 | -242286.6 | true | Lower MAE is better; selection used validation only |

## CSV outputs

| File | Contents |
| --- | --- |
| `reports/metrics/model_results_late_delivery.csv` | Late-delivery candidates + baselines |
| `reports/metrics/model_results_duration.csv` | Duration candidates + median baseline |
| `reports/metrics/model_results_forecasting.csv` | Forecast candidates + naive/mean |
| `reports/metrics/model_results_inventory.csv` | Inventory proxy + prevalence baseline |
| `reports/metrics/model_vs_baseline_comparison.csv` | One-row-per comparison deltas |
