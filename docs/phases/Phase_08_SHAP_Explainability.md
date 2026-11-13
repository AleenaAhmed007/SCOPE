# Phase 08 — SHAP Explainability

## 1. Objective

Explain the predictions of the SCOPE machine learning models using SHAP (SHapley Additive exPlanations).

The primary focus is the late-delivery classification model from Phase 03.

The regression model from Phase 04 may also be explained if its preprocessing and model structure are compatible.

## 2. Business Problem

Supply chain users need to understand why a model flags an order as high risk.

A prediction without an explanation may be difficult to investigate or trust.

SHAP can help identify which input features contributed to a model prediction.

SHAP explanations describe model behavior. They do not establish causality.

## 3. Models to Explain

Priority:

1. XGBoost Late Delivery Classifier
2. Random Forest Classifier comparison
3. Delivery Duration Regression Model, if useful

Use the exact trained model artifacts from earlier phases.

Do not train a different model silently and then present its explanations as belonging to the deployed model.

## 4. SHAP Implementation

### Step 1 — Load model artifacts

Load:

- Trained model
- Preprocessing pipeline
- Feature list
- Model version
- Training configuration

Confirm that the loaded model is the same version registered in PostgreSQL.

### Step 2 — Prepare explanation data

Use a representative and appropriately selected dataset.

Avoid explaining only a hand-picked set of favorable predictions.

Document the sampling strategy and background dataset used by SHAP.

### Step 3 — Calculate global explanations

Generate:

- SHAP summary plot
- SHAP bar plot
- Feature contribution rankings

Explain which features influence model predictions most strongly across the evaluated records.

### Step 4 — Calculate local explanations

For selected predictions, generate:

- Individual feature contributions
- Positive contributions toward late classification
- Negative contributions away from late classification
- Original input values

Explain that the contribution direction depends on the model output being explained.

### Step 5 — Validate explanations

Check:

- Feature names are mapped correctly.
- Preprocessing does not misalign feature columns.
- SHAP output corresponds to the registered model version.
- Explanation values are reproducible.
- Explanations do not imply causality.

## 5. Visualization

Generate:

- Global SHAP summary plot
- Feature importance bar chart
- Individual prediction explanation
- Optional dependence plots for selected features

Use readable titles, axis labels, and descriptions.

Do not label SHAP values as probabilities unless the explained output is actually a probability.

## 6. PostgreSQL Requirements

Use PostgreSQL only.

Suggested tables:

- `explanation_runs`
- `model_explanations`
- `explanation_features`
- `model_versions`

Store:

- Model version
- Explanation run ID
- Record identifier
- Feature contribution values
- Explanation configuration
- Artifact references

Large visual outputs should be stored as files or object artifacts. PostgreSQL should store metadata and references.

Use SQLAlchemy and Alembic.

No SQLite.

## 7. Suggested Folder Structure

```text
backend/
  explainability/
    load_model.py
    global_explanations.py
    local_explanations.py
    validate.py
    report.py

artifacts/
  explanations/
    global/
    local/
    reports/

tests/
  test_explainability.py
```

## 8. Expected Outputs

- SHAP global summary plot
- SHAP feature importance plot
- Local explanation examples
- Explanation report
- Model version references
- PostgreSQL explanation metadata

## 9. Acceptance Criteria

- Explanations use the registered model artifact.
- Model version is recorded.
- Feature mapping is validated.
- Global and local explanations are generated.
- SHAP contributions are interpreted correctly.
- No causal claims are made.
- Explanation artifacts are saved.
- PostgreSQL stores explanation metadata.
- No SQLite dependency exists.

## 10. Cursor AI Prompt

You are implementing Phase 08 of the SCOPE project.

Build a SHAP-based explainability module for SCOPE machine learning models.

Requirements:

1. Inspect the repository and existing trained model artifacts.
2. Use the registered XGBoost late-delivery classifier as the primary explanation target.
3. Optionally explain the Random Forest classifier and delivery-duration regression model.
4. Load the exact model version and preprocessing pipeline used in training.
5. Validate feature names and transformed feature alignment.
6. Generate global SHAP summary and bar plots.
7. Generate local explanations for representative predictions.
8. Clearly distinguish positive and negative contributions toward the explained model output.
9. Document the SHAP background data and sampling method.
10. Ensure explanations are reproducible.
11. Do not claim SHAP establishes causality.
12. Do not describe SHAP values as probabilities unless the explained output is a probability.
13. Save plots, explanation data, and reports.
14. Add tests for model loading, feature alignment, explanation output, and model version consistency.
15. Store explanation runs, feature contributions, and model references in PostgreSQL.
16. Use SQLAlchemy and Alembic.
17. PostgreSQL only. Do not use SQLite or SQLite fallback.
18. Read credentials from environment variables.
19. Do not fabricate explanation results.
20. Document how to generate global and local explanations.

Inspect the repository first. Explain the planned changes, implement the module, and run the tests.

## 11. Definition of Done

SHAP explanations are generated from the correct registered model, feature mappings are validated, visualizations and reports are saved, and explanation metadata is stored in PostgreSQL.
