# Phase 07 — Inventory Prediction Experiment

## 1. Objective

Investigate whether the available dataset supports a reliable inventory-related prediction experiment.

This phase is conditional because inventory fields may have been added or augmented and their original provenance may not be established.

The phase must begin with a data-provenance and leakage audit.
### Current dataset finding

The current augmented dataset's `Inventory_Stockout_Flag` matches
`Inventory_Opening_Stock - Line_Item_Quantity < 0` on every non-null row checked.
The pipeline therefore does not train a stockout classifier. It records rule
agreement as a data consistency check until original inventory provenance is
verified.

## 2. Business Problem

Inventory visibility can help supply chain teams identify potential shortages and prioritize replenishment investigations.

However, an inventory prediction model is useful only if its inputs are genuine, temporally valid, and available before the outcome.

## 3. Data Audit Before Modeling

Inspect these candidate fields if they exist:

- `Inventory_Stock_In`
- `Inventory_Lead_Time_Days`
- `Inventory_Stockout_Flag`
- `Inventory_Shortage_Quantity`

Verify:

1. Where did these columns originate?
2. Are they part of the original dataset?
3. Were they generated or synthetically added?
4. What does each field mean?
5. At what point in time was each value available?
6. Are there constant or near-constant fields?
7. Are there fields directly derived from one another?

Previously observed concerns include:

- `Inventory_Stock_In` appeared to be zero in inspected rows.
- `Inventory_Lead_Time_Days` appeared constant at 30.
- `Inventory_Stockout_Flag` appeared aligned with positive `Inventory_Shortage_Quantity`.
- Inventory shortage quantity may reveal the stockout outcome.

These observations must be revalidated against the current dataset. Do not assume they are still true.

## 4. Leakage Prevention

If the target is `Inventory_Stockout_Flag`, do not use:

- `Inventory_Shortage_Quantity` if it directly determines the target
- Any post-outcome inventory measurement
- Any feature created from the target
- Any information unavailable at prediction time

A model trained on a direct copy or transformation of the target is not a valid predictive model.

## 5. Modeling Decision

### Option A — Proceed with a valid inventory model

Proceed only if genuine, leakage-safe predictors are available.

Potential algorithms:

- Logistic Regression baseline
- Random Forest Classifier
- XGBoost Classifier

Evaluate using:

- Precision
- Recall
- F1-score
- PR-AUC
- ROC-AUC
- Confusion matrix

Use chronological splitting where appropriate.

### Option B — Do not train a model

If the data lacks genuine inventory predictors, document the limitation.

Produce:

- Inventory data quality report
- Provenance findings
- Leakage analysis
- Feature suitability table
- Recommendation for additional inventory data collection

This is an acceptable completion of the phase.

## 6. Additional Data Needed

A stronger inventory forecasting task may require:

- Timestamped stock levels
- Historical demand
- Goods received quantities
- Goods issued quantities
- Reorder points
- Supplier replenishment times
- SKU/product identifiers
- Warehouse or manufacturing-site identifiers
- Stockout event timestamps

These should be collected from a verified source before building a production inventory model.

## 7. PostgreSQL Requirements

Use PostgreSQL only.

Suggested tables:

- `inventory_data_audits`
- `inventory_model_runs`
- `inventory_predictions`
- `inventory_feature_reviews`

Use SQLAlchemy and Alembic.

Store provenance findings, feature decisions, model metadata, and evaluation metrics.

Do not use SQLite.

## 8. Suggested Folder Structure

```text
backend/
  ml/
    inventory/
      audit.py
      features.py
      train.py
      evaluate.py
      report.py

artifacts/
  inventory/
    audit/
    models/
    reports/

tests/
  test_inventory.py
```

## 9. Expected Outputs

- Inventory provenance report
- Feature suitability report
- Leakage assessment
- Inventory prediction model, only if justified
- Evaluation report, if a model is trained
- PostgreSQL audit and experiment records

## 10. Acceptance Criteria

- Inventory column provenance is investigated.
- Constant and near-constant fields are identified.
- Direct target leakage is checked.
- Prediction-time feature availability is documented.
- Model training occurs only if valid predictors exist.
- If modeling is not justified, the phase produces a documented audit instead.
- PostgreSQL stores audit and experiment metadata.
- No SQLite dependency exists.

## 11. Cursor AI Prompt

You are implementing Phase 07 of the SCOPE project.

Conduct an inventory data-provenance and predictive suitability experiment.

Requirements:

1. Inspect the actual dataset and repository.
2. Verify whether the following fields exist: Inventory_Stock_In, Inventory_Lead_Time_Days, Inventory_Stockout_Flag, and Inventory_Shortage_Quantity.
3. Recalculate missing-value rates, unique values, constant columns, and relationships among inventory fields.
4. Investigate whether inventory fields are original, derived, or synthetically added based on available project evidence.
5. Do not invent provenance information.
6. Identify direct and indirect target leakage.
7. Define the intended prediction timestamp.
8. Use only features genuinely available at that timestamp.
9. Train an inventory classifier only if valid predictors and a defensible target exist.
10. If the data is unsuitable, do not force model training. Produce a detailed audit and data requirements report.
11. If modeling is justified, compare Logistic Regression, Random Forest, and optionally XGBoost.
12. Evaluate with precision, recall, F1, PR-AUC, ROC-AUC, and confusion matrix where appropriate.
13. Save audit reports, feature decisions, model artifacts, and metrics.
14. Add tests for provenance checks, constant fields, leakage checks, and model eligibility.
15. Persist audit findings and experiment metadata in PostgreSQL.
16. Use SQLAlchemy and Alembic.
17. PostgreSQL only. Never use SQLite or SQLite fallback.
18. Read credentials from environment variables.
19. Never fabricate data provenance or model results.
20. Document the commands and final modeling decision.

Inspect the repository before implementation. Explain the planned changes, implement the audit and any justified model, then run tests.

## 12. Definition of Done

The inventory phase is complete when the data has been audited, leakage risks are documented, and either a valid model is implemented or a defensible no-model decision is documented and stored in PostgreSQL.
