# Phase 03 — Late Delivery Classification

## 1. Objective

Build machine learning models to predict whether a shipment/order is likely to be delivered late.

This is the primary supervised classification task of the SCOPE project.

The main model will be XGBoost, with Random Forest as a comparison model.

## 2. Business Problem

Supply chain teams need early warnings about potentially delayed deliveries so they can investigate risks and take corrective action.

The model should predict:

- On-time delivery
- Late delivery

The prediction must use only information available at the prediction time.

## 3. Target Variable

Create a binary target:

`Is_Late`

Suggested definition:

- `1`: Delivered to Client Date is later than Scheduled Delivery Date.
- `0`: Delivered to Client Date is on or before Scheduled Delivery Date.

Rows with missing or invalid dates required for target creation must be excluded from supervised training and reported separately.

Do not assume old row counts. Recalculate the target distribution from the current dataset.

## 4. Important Leakage Prevention

Do not use the following as model inputs:

- Delivered to Client Date
- Actual delivery outcome fields
- Late delivery indicators derived from actual delivery
- Delivery duration calculated using the actual delivery date
- Inventory shortage quantity or stockout flags if they reveal information unavailable at prediction time
- Any field that directly or indirectly reveals the target

The feature set must represent information available before the delivery outcome is known.

Document the prediction timestamp and feature availability assumptions.

## 5. Suggested Features

Inspect actual dataset column names before implementation.

Potential feature groups:

### Order information
- `PO_Line_Item_Quantity`
- `Unit_Price`
- `Line_Item_Insurance`

### Vendor information
- `Vendor`
- `Vendor_INCO_Term`
- Historical vendor performance calculated using training-period data only

### Location information
- `Country`
- `Manufacturing Site`
- `Fulfill Via`
- `Shipment Mode`

### Product information
- `Product Group`
- `Sub Classification`
- `Brand`
- `Dosage`

### Time information
- PO month
- PO quarter
- Day of week
- Scheduled delivery month

Only use a field if it is available at the intended prediction time.

## 6. Implementation Steps

### Step 1 — Prepare the dataset

- Load the cleaned dataset from Phase 02.
- Validate target labels.
- Remove rows with invalid target dates.
- Check class imbalance.
- Separate identifiers from predictive features.
- Record the final feature list.

### Step 2 — Split the data

Use a chronological train/validation/test split where possible.

For example:

- Earlier period: training
- Following period: validation
- Latest period: testing

Do not randomly mix future records into training when evaluating future prediction performance.

If chronological splitting is not feasible, document the reason and use a suitable grouped or stratified alternative.

### Step 3 — Build preprocessing pipeline

Use:

- SimpleImputer for missing numerical values
- OneHotEncoder for categorical variables
- StandardScaler only where useful for the selected model
- ColumnTransformer
- Pipeline

Fit all preprocessing components on training data only.

### Step 4 — Train models

Primary model:

- XGBoost Classifier

Comparison model:

- Random Forest Classifier

Optional baseline:

- DummyClassifier

### Step 5 — Hyperparameter tuning

Use validation data or cross-validation restricted to the training period.

Tune parameters such as:

- `n_estimators`
- `max_depth`
- `learning_rate`
- `subsample`
- `colsample_bytree`
- `min_child_weight`

Avoid tuning against the final test set.

### Step 6 — Evaluate models

Report:

- Accuracy
- Precision
- Recall
- F1-score
- ROC-AUC
- PR-AUC
- Confusion matrix
- Classification report

Because late deliveries may be less frequent, do not rely on accuracy alone.

Recall for the late class is particularly important because missed late-delivery risks can be costly.

### Step 7 — Save model artifacts

Save:

- Trained model
- Preprocessing pipeline
- Feature list
- Target definition
- Evaluation metrics
- Training configuration

Use versioned artifacts under `artifacts/models/`.

Record model metadata and experiment results in PostgreSQL.

## 7. PostgreSQL Requirements

Use PostgreSQL only. Do not use SQLite.

Use SQLAlchemy for database access and Alembic for schema migrations.

Suggested tables:

- `ml_experiments`
- `model_versions`
- `model_metrics`
- `prediction_logs`

Store model metadata, metrics, experiment identifiers, and prediction audit information in PostgreSQL.

Do not store large model binary files directly in PostgreSQL unless there is a clear requirement. Store artifact paths and checksums instead.

## 8. Suggested Folder Structure

```text
backend/
  ml/
    classification/
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
  test_classification.py
```

## 9. Expected Outputs

- XGBoost classification model
- Random Forest comparison model
- Evaluation report
- Confusion matrix
- Feature importance report
- Saved preprocessing pipeline
- PostgreSQL experiment records

## 10. Acceptance Criteria

- Target definition is documented.
- Invalid target dates are handled.
- Data leakage checks are implemented.
- Chronological evaluation is used where feasible.
- Both models are evaluated on the same test period.
- Metrics are saved and reproducible.
- Model artifacts can be loaded for inference.
- PostgreSQL stores experiment and model metadata.
- No SQLite database or SQLite dependency is introduced.

## 11. Cursor AI Prompt

You are working on Phase 03 of the SCOPE project.

Implement a production-quality late-delivery classification pipeline.

Requirements:

1. Inspect the existing repository and reuse the Phase 01 audit and Phase 02 preprocessing outputs.
2. Inspect actual dataset column names. Never assume a column exists without checking.
3. Create `Is_Late` using Delivered to Client Date and Scheduled Delivery Date.
4. Exclude rows where the required target dates are invalid.
5. Prevent target leakage. Do not use actual delivery outcome fields as predictors.
6. Create a chronological train/validation/test split where possible.
7. Build preprocessing using scikit-learn Pipeline and ColumnTransformer.
8. Train XGBoost Classifier as the primary model.
9. Train Random Forest Classifier as a comparison model.
10. Include a DummyClassifier baseline if appropriate.
11. Evaluate using accuracy, precision, recall, F1, ROC-AUC, PR-AUC, and confusion matrix.
12. Pay particular attention to recall for the late-delivery class.
13. Save trained models, preprocessing pipelines, feature lists, metrics, and configuration files.
14. Add unit tests for target generation, leakage prevention, splitting, and inference.
15. Record experiments, model versions, metrics, and prediction audit metadata in PostgreSQL using SQLAlchemy.
16. Use Alembic migrations for database schema changes.
17. PostgreSQL is mandatory. Do not use SQLite under any circumstances.
18. Read database connection details from environment variables. Never hardcode credentials.
19. Do not fabricate model metrics. Generate metrics only by running the actual pipeline.
20. Update project documentation with the commands required to train and evaluate the models.

Before coding, inspect the repository and report the files you intend to create or modify. Then implement the phase and run the tests.

## 12. Definition of Done

Phase 03 is complete when the classification pipeline is reproducible, leakage-safe, evaluated on an appropriate holdout period, tested, and its experiment metadata is stored in PostgreSQL.
