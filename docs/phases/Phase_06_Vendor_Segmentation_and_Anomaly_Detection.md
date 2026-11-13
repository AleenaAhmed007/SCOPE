# Phase 06 — Vendor Segmentation and Anomaly Detection

### Current implementation note

Vendor segmentation applies `log1p` to skewed volume features, separates vendors
with fewer than 10 shipments, separates dominant vendors and tiny profile
outliers, and compares supported cluster counts from 2 through 8. The
unsupervised signal is called an **unusual shipment profile**; it is not a late
delivery predictor and has no labeled accuracy score.
## 1. Objective

Develop unsupervised machine learning modules to:

1. Group vendors according to their operational characteristics.
2. Identify unusual supply chain records and vendor-level patterns.

The phase contains two independent experiments:

- Vendor Segmentation using K-Means
- Anomaly Detection using Isolation Forest

## 2. Business Problem

Different vendors may demonstrate different delivery patterns, order volumes, shipment characteristics, and operational risks.

Vendor segmentation can help supply chain teams understand vendor groups.

Anomaly detection can highlight unusual records that deserve further investigation.

An anomaly is an investigation signal, not proof of fraud, misconduct, or disruption.

## 3. Part A — Vendor Segmentation

### Step 1 — Identify vendor-level features

Inspect the dataset and select valid features.

Potential features:

- Vendor order count
- Total ordered quantity
- Average order quantity
- Average unit price
- Late delivery rate
- Average delivery duration
- Shipment mode distribution
- Country or manufacturing-site diversity

Historical performance features must be calculated without using future records.

Do not calculate vendor performance using the same future test period that the model is supposed to predict.

### Step 2 — Aggregate data

Create a vendor-level analytical dataset.

Each row should represent one vendor.

Example output:

```text
vendor_id
order_count
average_quantity
average_unit_price
late_delivery_rate
average_delivery_duration
```

Exclude or separately handle vendors with insufficient historical observations.

### Step 3 — Preprocess features

Use:

- SimpleImputer
- StandardScaler or RobustScaler
- Appropriate categorical encoding if categorical features are included

Investigate highly skewed features and consider log transformation where appropriate.

### Step 4 — Determine cluster count

Use:

- Elbow method
- Silhouette score
- Cluster-size inspection

Do not select the number of clusters only because a visualization looks attractive.

### Step 5 — Train K-Means

Train K-Means using the selected vendor-level features.

Save:

- Cluster assignments
- Scaler
- Trained model
- Feature list
- Cluster profiles
- Evaluation metrics

### Step 6 — Interpret clusters

Describe clusters using their actual feature values.

Possible descriptive labels include:

- High-volume vendors
- Lower-volume vendors
- Vendors with higher observed late-delivery rates

These labels must be assigned based on calculated cluster profiles, not invented in advance.

## 4. Part B — Anomaly Detection

### Step 1 — Select analytical records

Decide whether anomalies will be detected at:

- Order level
- Shipment level
- Vendor-period level

Document the chosen observation unit.

### Step 2 — Prepare features

Potential features:

- Order quantity
- Unit price
- Delivery duration
- Shipment characteristics
- Vendor historical statistics

Exclude identifiers and direct target leakage.

### Step 3 — Train Isolation Forest

Use scikit-learn IsolationForest.

Tune contamination carefully.

Do not assume that every flagged record is a genuine disruption.

### Step 4 — Investigate flagged records

Generate an anomaly report containing:

- Record identifier
- Anomaly score
- Selected feature values
- Reason for review
- Relevant vendor information

Anomaly scores are not probabilities unless separately calibrated and validated.

## 5. Evaluation

### K-Means

Report:

- Silhouette score
- Inertia
- Cluster sizes
- Cluster profiles

### Isolation Forest

Where verified anomaly labels are unavailable, do not claim conventional supervised accuracy.

Instead report:

- Number and percentage of flagged records
- Score distribution
- Feature characteristics
- Manual review findings, if available

If verified labels become available, calculate precision, recall, and F1-score.

## 6. PostgreSQL Requirements

PostgreSQL is mandatory.

Use SQLAlchemy and Alembic.

Suggested tables:

- `vendor_segments`
- `vendor_segment_runs`
- `anomaly_detection_runs`
- `anomaly_records`
- `ml_experiments`

Persist model-run metadata, cluster assignments, anomaly scores, and investigation status.

Do not use SQLite or an SQLite fallback.

## 7. Suggested Folder Structure

```text
backend/
  ml/
    segmentation/
      aggregate.py
      train.py
      evaluate.py
      profile.py

    anomaly_detection/
      features.py
      train.py
      score.py
      report.py

artifacts/
  models/
  reports/
  metrics/

tests/
  test_segmentation.py
  test_anomaly_detection.py
```

## 8. Expected Outputs

- Vendor-level analytical dataset
- K-Means model
- Vendor cluster assignments
- Cluster profile report
- Isolation Forest model
- Anomaly score dataset
- Anomaly investigation report
- PostgreSQL experiment records

## 9. Acceptance Criteria

- Vendor aggregation is reproducible.
- Historical features do not use future information.
- Cluster count has a documented rationale.
- Cluster profiles use actual calculated statistics.
- Anomaly detection unit is documented.
- Anomaly scores are not misrepresented as probabilities.
- Unsupervised evaluation is appropriate.
- Model artifacts are saved.
- PostgreSQL stores run metadata and results.
- No SQLite dependency exists.

## 10. Cursor AI Prompt

You are implementing Phase 06 of the SCOPE project.

Build vendor segmentation and anomaly detection modules.

Requirements:

1. Inspect the existing repository and actual dataset schema.
2. Reuse audited and preprocessed data from previous phases.
3. Build a vendor-level aggregation dataset.
4. Calculate vendor statistics using only information available at the relevant analysis time.
5. Prevent future-data leakage in historical vendor performance features.
6. Train K-Means using suitable scaled numerical features.
7. Evaluate cluster counts using elbow analysis, silhouette score, and cluster-size inspection.
8. Generate interpretable cluster profiles from actual calculated values.
9. Train an Isolation Forest anomaly detection model.
10. Document whether anomaly detection operates at order, shipment, or vendor-period level.
11. Generate anomaly scores and investigation reports.
12. Do not describe anomalies as confirmed fraud or disruptions.
13. Do not present anomaly scores as probabilities without calibration.
14. Save model artifacts, feature lists, metrics, and configuration.
15. Add tests for aggregation, feature leakage, clustering, anomaly scoring, and output schemas.
16. Persist run metadata, vendor segments, and anomaly records in PostgreSQL.
17. Use SQLAlchemy and Alembic.
18. PostgreSQL only. Do not use SQLite or SQLite fallback.
19. Read credentials from environment variables.
20. Do not fabricate metrics or cluster interpretations.
21. Document commands to run both modules.

Inspect the repository before changing files. Explain planned changes, implement the modules, and run tests.

## 11. Definition of Done

Both modules run reproducibly, their outputs are interpretable, leakage risks are addressed, tests pass, and their results are persisted in PostgreSQL.
