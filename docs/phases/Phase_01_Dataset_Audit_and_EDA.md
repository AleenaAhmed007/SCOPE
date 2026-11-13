# Phase 01 — Dataset Audit and Complete Exploratory Data Analysis (EDA)

## 1. Objective

Perform complete Exploratory Data Analysis and data-quality auditing on `SCMS_with_inventory.csv`.

Understand the structure, quality, distributions, relationships, missing values, date patterns, vendor behaviour, shipment performance and inventory-field limitations.

No ML model should be trained in this phase.

## 2. Dataset Information

Primary dataset: `SCMS_with_inventory.csv`

Previously inspected profile:
- Approximately 10,324 rows.
- 45 columns.
- 73 vendors.
- 43 countries.
- 88 manufacturing sites.

These are previously observed values, not hardcoded assumptions. Recalculate all statistics from the actual CSV.

## 3. EDA Objectives

The EDA must answer:

1. What does each column represent?
2. Which columns contain missing values?
3. Are there duplicate records?
4. Which columns have constant or near-constant values?
5. Are numerical values skewed?
6. Are there extreme outliers?
7. Are date columns valid?
8. What percentage of shipments are late?
9. Which vendors have higher historical late rates?
10. Which countries and shipment modes have different delivery patterns?
11. Are inventory fields internally consistent?
12. Are there target leakage risks?

## 4. Required EDA Sections

### 4.1 Dataset Overview

Calculate:
- Number of rows.
- Number of columns.
- Memory usage.
- Column names.
- Data types.
- Duplicate rows.
- Duplicate IDs.
- Unique counts.
- Dataset shape.

Save schema information in JSON.

### 4.2 Missing Value Analysis

For every column calculate:
- Missing count.
- Missing percentage.
- Unique values.
- Most frequent value.

Create:
- Missing value summary table.
- Missing value bar chart.
- Missingness heatmap where useful.

Do not treat placeholders such as `N/A - From RDC` as ordinary valid dates.

### 4.3 Numerical Feature Analysis

Analyze:
- Line Item Quantity
- Line Item Value
- Pack Price
- Unit Price
- Weight (Kilograms)
- Freight Cost (USD)
- Line Item Insurance (USD)
- Inventory opening stock
- Inventory stock in
- Inventory stock out
- Inventory closing stock
- Inventory reorder level
- Inventory shortage quantity

Calculate:
- Mean.
- Median.
- Standard deviation.
- Minimum.
- Maximum.
- Quartiles.
- Skewness.
- Outlier counts.

Visualizations:
- Histograms.
- Boxplots.
- Distribution plots.
- Correlation heatmap.

### 4.4 Categorical Analysis

Analyze:
- Country.
- Managed By.
- Fulfill Via.
- Vendor INCO Term.
- Shipment Mode.
- Product Group.
- Sub Classification.
- Vendor.
- Manufacturing Site.
- Brand.
- Dosage Form.

Calculate frequency and percentage distributions.

Visualizations:
- Top vendors.
- Top countries.
- Shipment mode distribution.
- Product group distribution.
- Manufacturing site distribution.

Do not create hundreds of unreadable category plots. Show top categories and group the remaining categories as Other where appropriate.

### 4.5 Date Analysis

Important date fields:
- PQ First Sent to Client Date
- PO Sent to Vendor Date
- Scheduled Delivery Date
- Delivered to Client Date
- Delivery Recorded Date
- Inventory_Date

Tasks:
- Preserve original raw date strings.
- Normalize dates into datetime columns.
- Handle mixed formats.
- Identify invalid values.
- Count successful and unsuccessful parses.
- Detect impossible chronology.
- Calculate date coverage.
- Analyze delivery delays.

Known placeholder examples:
- `N/A - From RDC`
- `Date Not Captured`

Do not silently interpret ambiguous dates.

Create tests for date parsing.

### 4.6 Late Delivery Analysis

Define:

`is_late = 1` when Delivered to Client Date is later than Scheduled Delivery Date.

Otherwise:

`is_late = 0`

Only calculate the target where both dates are valid.

Analyze:
- Late shipment count.
- On-time shipment count.
- Late delivery percentage.
- Delay distribution.
- Average delay days.
- Median delay days.
- Late rate by vendor.
- Late rate by country.
- Late rate by shipment mode.
- Late rate by product group.

Visualizations:
- Target class distribution.
- Delay histogram.
- Vendor late-rate chart.
- Country late-rate chart.
- Shipment mode comparison.

### 4.7 Vendor Analysis

Analyze each vendor using:
- Shipment count.
- Late shipment count.
- On-time shipment count.
- Late rate.
- Average schedule deviation.
- Median schedule deviation.
- Average quantity.
- Average shipment value.

Use valid records only and show sample counts.

Do not conclude that a vendor is poor solely from a small number of shipments.

### 4.8 Shipment and Product Analysis

Analyze:
- Product group shipment volume.
- Sub-classification frequency.
- Quantity distribution.
- Shipment mode.
- Country and product relationships.
- Manufacturing site activity.

### 4.9 Inventory Data Audit

Inventory fields include:
- Inventory_Product_Key
- Inventory_Warehouse_ID
- Inventory_Date
- Inventory_Opening_Stock
- Inventory_Stock_In
- Inventory_Stock_Out
- Inventory_Closing_Stock
- Inventory_Reorder_Level
- Inventory_Lead_Time_Days
- Inventory_Stockout_Flag
- Inventory_Shortage_Quantity
- Inventory_Replenishment_Triggered

Previously observed warnings:
- Inventory_Stock_In was zero across inspected rows.
- Inventory_Lead_Time_Days was 30 across inspected rows.
- Inventory_Stockout_Flag aligned with Inventory_Shortage_Quantity greater than zero.

Recalculate these relationships.

Check stock arithmetic where the field definitions permit:

`Expected Closing Stock = Opening Stock + Stock In - Stock Out`

Check:
- Constant columns.
- Negative stock.
- Missing inventory values.
- Duplicate product/warehouse/date combinations.
- Repeated or irregular dates.
- Flag and shortage relationship.
- Reorder level relationships.
- Product and warehouse time coverage.

Important: Inventory provenance is unverified. Do not describe these fields as authentic operational inventory records without evidence.

### 4.10 Correlation Analysis

Calculate numerical correlations using suitable methods:
- Pearson.
- Spearman where appropriate.

Do not treat correlation as causation.

Exclude identifiers and misleading target proxies from interpretation.

## 5. Required Visualizations

Save figures in:

`reports/figures/eda/`

Required plots:
1. Dataset missingness chart.
2. Numerical distributions.
3. Numerical boxplots.
4. Correlation heatmap.
5. Shipment mode distribution.
6. Top vendor shipment count.
7. Country shipment distribution.
8. Late/on-time target distribution.
9. Delivery delay distribution.
10. Late rate by vendor.
11. Late rate by shipment mode.
12. Late rate by country.
13. Inventory field distributions.
14. Inventory consistency diagnostics.
15. Date coverage plots.

Every plot must have:
- Clear title.
- Axis labels.
- Legend where needed.
- Readable category labels.
- Correct units.

## 6. Required Notebook and Reports

Create:

```text
notebooks/
    01_complete_eda.ipynb

reports/
    eda_report.md
    eda_summary.json
    data_audit.md
    data_audit.json
    figures/
        eda/

docs/
    data_dictionary.md
    feature_dictionary.md
```

## 7. Data Dictionary

For each column document:
- Original column name.
- Data type.
- Business meaning.
- Missing percentage.
- Unique count.
- Example values.
- Whether it is an identifier.
- Whether it is suitable for ML.
- Availability time.
- Leakage risk.

If the meaning of a field is uncertain, explicitly write Unknown/Needs confirmation rather than inventing a definition.

## 8. Feature Dictionary

For every proposed feature document:
- Feature name.
- Source columns.
- Transformation.
- Business meaning.
- Prediction-time availability.
- Missing-value handling.
- Leakage status.
- Approved model tasks.

## 9. Required Libraries

- pandas
- numpy
- matplotlib
- seaborn
- scipy
- missingno (optional)
- pytest
- jupyter

## 10. Testing

Create tests for:
- Dataset loading.
- Expected columns.
- Missing-value calculations.
- Duplicate detection.
- Date parsing.
- Placeholder handling.
- Chronology validation.
- Late target creation.
- Inventory consistency.
- Target-proxy detection.

## 11. Acceptance Criteria

- All columns are audited.
- Missing values are quantified.
- Dates are parsed transparently.
- Invalid chronology is identified.
- Late-delivery target is correctly defined.
- Vendor and shipment analyses are produced.
- Inventory limitations are documented.
- EDA notebook runs from start to finish.
- Reports and plots are saved.
- No ML model is trained in this phase.

## 12. Definition of Done

Phase 01 is complete when the team has a reproducible understanding of the dataset and can justify every cleaning and modelling decision using EDA evidence.

## 13. Cursor Agent Prompt

```text
You are a senior Data Scientist and Data Quality Engineer working on SCOPE.

Inspect the actual SCMS_with_inventory.csv file and the current repository before implementing anything.

Perform complete Exploratory Data Analysis and a reproducible data audit.

Do not assume the dataset is clean and do not hardcode previously observed statistics.

Create:
- notebooks/01_complete_eda.ipynb
- reports/eda_report.md
- reports/eda_summary.json
- reports/data_audit.md
- reports/data_audit.json
- reports/figures/eda/
- docs/data_dictionary.md
- docs/feature_dictionary.md

Analyze dataset dimensions, schema, data types, missing values, duplicates, numerical distributions, categorical distributions, outliers, dates, shipment patterns, vendor performance, late delivery and inventory consistency.

Preserve original date strings and create normalized date columns.

Handle mixed date formats and placeholders such as N/A - From RDC and Date Not Captured.

Derive the late-delivery target only where scheduled and delivered dates are valid.

Audit inventory constants, stock arithmetic and target relationships. Treat added inventory fields as unverified augmented data.

Create all required charts with clear titles and labels.

Add tests for date parsing, chronology, missingness, duplicate detection, target creation and inventory leakage risks.

Do not train any ML model in this phase.

Do not silently delete records. Record every exclusion and its reason.

Run the notebook and tests if the environment permits. Report actual execution results and any blockers.

Implement Phase 01 only.
```

## 14. Next Phase

Proceed to Phase 02 only after the EDA report and data-quality audit have been reviewed and approved.
