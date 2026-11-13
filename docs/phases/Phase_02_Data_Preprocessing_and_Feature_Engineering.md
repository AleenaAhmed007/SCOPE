# Phase 02 — Data Preprocessing and Feature Engineering

## 1. Objective

Convert the audited raw dataset into clean, consistent, reusable datasets for the different SCOPE machine-learning tasks.

This phase uses the outputs of Phase 01.

The raw dataset must remain unchanged.

## 2. Why This Phase Is Required

Raw supply-chain data may contain:
- Missing values.
- Mixed date formats.
- Duplicate records.
- Invalid chronology.
- Outliers.
- Inconsistent categorical values.
- Features unavailable at prediction time.

Preprocessing ensures that each model receives appropriate and leakage-safe features.

## 3. Input Files

Primary input:

`data/raw/SCMS_with_inventory.csv`

Phase 01 outputs:
- `reports/data_audit.md`
- `reports/data_audit.json`
- `docs/data_dictionary.md`
- `docs/feature_dictionary.md`

## 4. Preprocessing Strategy

### 4.1 Preserve Raw Data

Never modify the original CSV.

Create separate datasets:

- Raw: original records.
- Interim: normalized and validated records.
- Processed: task-specific feature tables.

### 4.2 Column Normalization

Create consistent internal column names.

For example:

- `Shipment_Mode`
- `Vendor`
- `Country`
- `Scheduled_Delivery_Date`
- `Delivered_To_Client_Date`

Maintain a mapping to the original column names.

Do not destroy original column names in the raw dataset.

### 4.3 Missing Values

Analyze missingness before imputation.

Numerical columns:
- Median imputation where appropriate.
- Group-based imputation only where justified.
- Missing indicators where missingness itself is informative.

Categorical columns:
- Most-frequent imputation where appropriate.
- Explicit `Unknown` category where suitable.

Date columns:
- Do not fill missing dates with arbitrary dates.
- Keep invalid or missing date flags.
- Exclude records from tasks requiring unavailable dates.

Fit all imputers on training data only.

### 4.4 Date Preprocessing

Create normalized datetime fields for:
- PQ First Sent to Client Date.
- PO Sent to Vendor Date.
- Scheduled Delivery Date.
- Delivered to Client Date.
- Delivery Recorded Date.
- Inventory_Date.

Rules:
- Preserve original strings.
- Apply validated date parsing rules from Phase 01.
- Track parse failures.
- Do not silently swap day and month.
- Do not retain impossible negative durations without review.

Create derived fields only when source dates are valid.

### 4.5 Duplicate Handling

Identify:
- Exact duplicate rows.
- Duplicate IDs.
- Potential duplicate shipments.
- Repeated inventory product/warehouse/date combinations.

Do not automatically delete records unless the duplicate rule is documented and approved.

Create a record-level exclusion log.

### 4.6 Outlier Handling

Use:
- IQR.
- Percentiles.
- Domain-specific thresholds.
- Robust scaling where appropriate.

Do not automatically delete all outliers.

Extreme shipment quantity or freight cost may be genuine business events.

Record any capping or transformation in the feature dictionary.

## 5. Target Engineering

### 5.1 Late Delivery Classification

Target:

`is_late`

Rule:

`1` if Delivered to Client Date is later than Scheduled Delivery Date.

`0` otherwise.

If either date is missing or invalid, the target is unknown and must not be fabricated.

### 5.2 Delivery Duration Regression

Target:

`delivery_duration_days`

Formula:

`Delivered to Client Date - PO Sent to Vendor Date`

Only use records with valid and chronologically plausible dates.

Describe this as PO-to-client delivery duration, not generic supplier procurement lead time.

## 6. Task-Specific Feature Tables

### 6.1 Shipment-Level Dataset

Create:

`data/processed/shipments.parquet`

Candidate features:
- Country.
- Managed By.
- Fulfill Via.
- Vendor INCO Term.
- Shipment Mode.
- Product Group.
- Sub Classification.
- Vendor.
- Manufacturing Site.
- Line Item Quantity.
- Weight (Kilograms).
- Freight Cost (USD).
- Calendar features from dates genuinely available at prediction time.

Do not include:
- Delivered to Client Date.
- Delivery Recorded Date.
- Actual delivery duration.
- Target-derived status.
- Any post-outcome information.

Define the prediction moment before approving the feature list.

### 6.2 Vendor-Level Dataset

Create:

`data/processed/vendor_features.parquet`

Possible features:
- Shipment count.
- Historical late rate.
- Median schedule deviation.
- Average shipment quantity.
- Median valid delivery duration.
- Average freight cost.

Calculate vendor metrics from the training/reference period only when evaluating future performance.

Do not use vendor name as a numerical feature.

### 6.3 Delay Time-Series Dataset

Create:

`data/processed/delay_timeseries.parquet`

Aggregate by week or month:
- Shipment count.
- Late shipment count.
- Late delivery rate.
- Average schedule deviation.

Sort chronologically and handle missing periods consistently.

### 6.4 Volume Time-Series Dataset

Create:

`data/processed/volume_timeseries.parquet`

Aggregate `Line Item Quantity` by week or month.

Describe this as historical shipment/order quantity proxy.

Do not describe it as verified warehouse demand or customer consumption.

### 6.5 Anomaly Feature Tables

Create separate feature sets:

1. Retrospective anomaly analysis.
2. Early-warning anomaly analysis.

Retrospective analysis may include historical delivery outcomes.

Early-warning analysis must only include features available at the defined prediction time.

## 7. Inventory Preprocessing

Inventory fields must be handled cautiously.

- Verify data provenance.
- Identify constant columns.
- Check product/warehouse/date history.
- Check stock arithmetic.
- Remove direct target proxies from predictive inputs.
- Do not use `Inventory_Shortage_Quantity` as an early-warning predictor.
- Do not use closing stock or stockout outcome fields to predict an event that has already occurred.
- Do not assume `Inventory_Stock_In` represents genuine stock movements.

If no valid leakage-safe predictors remain, document why the stockout model cannot be trained.

## 8. Encoding Categorical Variables

Use:
- OneHotEncoder for suitable low/medium-cardinality categories.
- Carefully evaluated frequency or target encoding for high-cardinality features.
- Unknown-category handling for inference.

Target encoding must be fitted within training folds to avoid leakage.

Never encode vendor names using arbitrary integer labels and treat them as numerical quantities.

## 9. Scaling Numerical Variables

Possible methods:
- StandardScaler.
- RobustScaler.
- MinMaxScaler.

Use scaling when appropriate for the model.

Tree-based models generally do not require standard scaling, but other algorithms may.

Fit scalers only on training data.

## 10. Train/Validation/Test Split

For time-dependent modelling, use chronological splits.

An initial possible strategy:
- Earliest 70%: training.
- Next 15%: validation.
- Latest 15%: testing.

Choose exact boundaries after reviewing date coverage and sample sizes.

Do not randomly shuffle the final time-based evaluation.

Avoid records from the same future period leaking into training.

## 11. Reusable Preprocessing Architecture

Create:

```text
backend/scope/
    data/
        loader.py
        validation.py
        cleaning.py
        date_parser.py
        audit.py

    features/
        shipment_features.py
        vendor_features.py
        delay_features.py
        volume_features.py
        inventory_features.py

    data/
        preprocessing.py
        split.py
```

Use sklearn:
- Pipeline.
- ColumnTransformer.
- SimpleImputer.
- OneHotEncoder.
- StandardScaler.
- RobustScaler.

Keep transformations reproducible.

## 12. Expected Deliverables

- Clean interim dataset.
- Shipment feature dataset.
- Vendor feature dataset.
- Delay time-series dataset.
- Volume time-series dataset.
- Feature dictionaries.
- Preprocessing pipelines.
- Train/validation/test split definitions.
- Exclusion logs.
- Unit tests.
- Processing CLI.

## 13. Acceptance Criteria

- Raw data remains unchanged.
- Date parsing follows Phase 01 rules.
- Invalid records are documented.
- Target definitions are correct.
- No leakage in early-warning features.
- Preprocessing is reproducible.
- Train-only fitting is enforced.
- Time-based splits are chronological.
- Parquet outputs are generated.
- Tests pass.

## 14. Definition of Done

Phase 02 is complete when all approved task-specific datasets can be generated reproducibly and every feature has documented meaning, availability and leakage status.

## 15. Cursor Agent Prompt

```text
You are a senior Data Engineer and ML Engineer working on SCOPE.

Inspect the repository and read the outputs of Phase 01 before making changes.

Implement reusable preprocessing and feature engineering modules for SCMS_with_inventory.csv.

Preserve the raw CSV unchanged.

Create:
- Shipment-level processed dataset.
- Vendor-level feature dataset.
- Weekly/monthly delay time series.
- Weekly/monthly shipment quantity time series.
- Separate retrospective and early-warning anomaly feature tables.
- Inventory experiment table only if leakage-safe features exist.

Implement:
- Missing-value handling.
- Categorical normalization.
- Validated date parsing.
- Duplicate detection and documented exclusions.
- Outlier diagnostics.
- Late-delivery target creation.
- PO-to-client delivery duration creation.
- Calendar feature engineering.
- Categorical encoding.
- Numerical scaling where required.
- Chronological train/validation/test splitting.

Use sklearn Pipeline and ColumnTransformer.

Fit all imputers, encoders and scalers on training data only.

Maintain feature availability and leakage metadata.

Never include delivered date, delivery recorded date, actual delay, shortage quantity or other target proxies as early-warning features.

Treat inventory fields as unverified augmented data.

Do not call Line Item Quantity warehouse demand.

Save processed datasets in Parquet format.

Add tests for every major transformation and leakage rule.

Create a command-line interface to run preprocessing reproducibly.

Run tests and report actual results.

Implement Phase 02 only. Do not train models yet.
```

## 16. Next Phase

After preprocessing and feature validation, proceed to Phase 03: Late Delivery Classification using XGBoost and Random Forest.
