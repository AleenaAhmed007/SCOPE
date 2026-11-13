# Phase 04 — Delivery Duration Regression

## 1. Objective

Build a regression model to estimate the number of days required for an order to travel from Purchase Order Date to Delivered to Client Date.

This task estimates observed order-to-client delivery duration. It must not be described as pure procurement lead-time prediction.

## 2. Business Problem

Supply chain teams need an estimated delivery duration to support planning, scheduling, and disruption assessment.

The model will estimate:

`Predicted_Delivery_Duration_Days`

## 3. Target Variable

Calculate:

`Delivery_Duration_Days = Delivered to Client Date - PO Sent to Vendor Date`

Use this definition only if both dates are valid and the business meaning of the fields is confirmed.

If the project chooses a different start date, document the rationale and apply it consistently.

Exclude invalid or impossible date differences from model training. Report how many rows were excluded and why.

## 4. Leakage Prevention

Do not use:

- Delivered to Client Date
- Actual delivery duration
- Any variable calculated from the actual delivery date
- Late delivery outcome fields
- Any post-delivery information

Scheduled Delivery Date may be used only if the prediction scenario occurs after that schedule is established.

Clearly document when the prediction is supposed to happen.

## 5. Potential Features

Inspect actual column names and data availability first.

Potential features:

- `PO_Line_Item_Quantity`
- `Unit_Price`
- `Line_Item_Insurance`
- `Vendor`
- `Vendor_INCO_Term`
- `Country`
- `Manufacturing Site`
- `Fulfill Via`
- `Shipment Mode`
- `Product Group`
- `Sub Classification`
- PO month and quarter
- Scheduled delivery interval, if available at prediction time

Historical vendor statistics must be calculated using past records only.

## 6. Implementation Steps

### Step 1 — Prepare regression target

- Parse the required date fields.
- Calculate delivery duration in days.
- Inspect negative and unusually large durations.
- Define an outlier investigation policy.
- Keep a record of excluded rows.

Do not automatically remove unusual observations without documenting the rule.

### Step 2 — Split the data

Use chronological train/validation/test splitting where feasible.

The test set must represent a later period than the training set.

### Step 3 — Preprocess features

Use:

- SimpleImputer
- OneHotEncoder
- ColumnTransformer
- Pipeline

Fit preprocessing on training data only.

### Step 4 — Train baseline and regression models

Recommended models:

- DummyRegressor baseline
- GradientBoostingRegressor
- Optional RandomForestRegressor comparison

### Step 5 — Evaluate

Report:

- MAE
- RMSE
- R²
- Median Absolute Error

MAE is particularly useful because it expresses the average absolute prediction error in days.

Also inspect residuals and performance across vendors, shipment modes, and time periods where sample sizes are sufficient.

### Step 6 — Save artifacts

Save:

- Regression model
- Preprocessing pipeline
- Feature list
- Target definition
- Evaluation metrics
- Training configuration

Store experiment metadata and model metrics in PostgreSQL.

## 7. PostgreSQL Requirements

PostgreSQL is the only supported relational database.

Use:

- PostgreSQL
- SQLAlchemy
- Alembic
- `psycopg`

Suggested tables:

- `ml_experiments`
- `model_versions`
- `model_metrics`
- `prediction_logs`

Use migrations for schema changes.

Do not use SQLite, SQLite files, or SQLite fallback configurations.

## 8. Suggested Folder Structure

```text
backend/
  ml/
    regression/
      train.py
      evaluate.py
      predict.py
      features.py
      pipeline.py

artifacts/
  models/
  metrics/
  reports/

tests/
  test_regression.py
```

## 9. Expected Outputs

- Delivery duration regression model
- Baseline comparison
- Evaluation metrics
- Residual analysis
- Saved preprocessing pipeline
- PostgreSQL experiment metadata

## 10. Acceptance Criteria

- Target duration is calculated using documented date fields.
- Invalid date rows are handled.
- Outlier policy is documented.
- Leakage prevention is implemented.
- Chronological test evaluation is used where feasible.
- Baseline and regression models are compared.
- MAE, RMSE, and R² are reported.
- Artifacts can be loaded for inference.
- Experiment metadata is stored in PostgreSQL.
- No SQLite dependency is introduced.

## 11. Cursor AI Prompt

You are implementing Phase 04 of the SCOPE project.

Build a reproducible delivery-duration regression pipeline.

Requirements:

1. Inspect the existing repository and reuse audited and preprocessed data.
2. Verify the actual names and meaning of the date columns.
3. Define the target as the number of days between PO Sent to Vendor Date and Delivered to Client Date, unless the repository's documented business definition specifies otherwise.
4. Exclude invalid dates and investigate negative or implausible durations.
5. Document all target exclusions and outlier handling.
6. Prevent leakage from actual delivery dates and post-delivery fields.
7. Use chronological train/validation/test splitting where possible.
8. Build preprocessing with scikit-learn Pipeline and ColumnTransformer.
9. Train a DummyRegressor baseline.
10. Train GradientBoostingRegressor.
11. Optionally train RandomForestRegressor as a comparison.
12. Evaluate with MAE, RMSE, R², and Median Absolute Error.
13. Generate residual analysis and error reports.
14. Save models, preprocessing pipelines, feature lists, metrics, and configuration.
15. Add tests for target calculation, invalid dates, leakage, splitting, and inference.
16. Store experiment metadata, model versions, and metrics in PostgreSQL.
17. Use SQLAlchemy and Alembic.
18. PostgreSQL only. Never use SQLite or an SQLite fallback.
19. Read database credentials from environment variables.
20. Do not invent or hardcode performance metrics.
21. Update documentation with training and evaluation commands.

Inspect the repository before implementation. Explain the planned changes, implement the pipeline, and run the tests.

## 12. Definition of Done

The regression model is reproducible, leakage-safe, evaluated on a future holdout period where feasible, tested, and registered in PostgreSQL with its experiment metadata.
