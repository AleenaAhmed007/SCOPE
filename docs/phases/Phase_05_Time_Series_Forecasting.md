# Phase 05 — Time Series Forecasting

### Current implementation note

The current pipeline evaluates monthly late-rate and shipment-quantity proxy
series. Candidate models are selected on validation data and compared with
naive lag-one and development-mean baselines on the held-out period. The volume
series is not verified warehouse demand.
## 1. Objective

Investigate whether the SCOPE dataset contains sufficient time-series information to support forecasting.

Potential forecasting tasks:

1. Shipment quantity forecasting
2. Delivery delay trend forecasting

An LSTM model may be implemented only if the available data has sufficient chronological depth and consistent observations.

## 2. Business Problem

Supply chain teams need visibility into future shipment volumes and possible delivery-delay trends.

Forecasting may help with:

- Shipment planning
- Capacity planning
- Identifying demand or shipment peaks
- Monitoring changes in delivery performance

## 3. Data Suitability Assessment

Before training an LSTM:

- Identify the date field suitable for time aggregation.
- Determine whether the data represents regular time intervals.
- Check missing periods.
- Check duplicate dates.
- Inspect the number of observations per time period.
- Determine whether the time series is sufficiently long.
- Check whether the available records cover enough historical cycles.

Do not assume that a dataset with thousands of rows automatically contains a sufficiently long time series.

If the dataset is too sparse or irregular, document the limitation and use simpler aggregation or forecasting methods.

## 4. Possible Forecasting Targets

### Option A — Shipment quantity

Aggregate `PO_Line_Item_Quantity` by week or month.

Target:

`Shipment_Quantity_Per_Period`

Only use this if the date and quantity fields are valid and the aggregation has business meaning.

### Option B — Delivery delay trend

Create a delay measure using valid scheduled and actual delivery dates.

Possible target:

- Average delay days per month
- Percentage of late deliveries per month

Use only periods with sufficient observations. Clearly define how missing and invalid dates are treated.

## 5. Baseline Models

Always compare complex models against simpler baselines.

Recommended baselines:

- Naive forecast
- Seasonal naive forecast, if seasonality is supported
- Moving average
- Exponential smoothing

An LSTM should not be presented as successful merely because it was implemented.

## 6. LSTM Implementation

If the suitability assessment supports deep learning:

- Create chronological sequences.
- Use a look-back window.
- Scale features using training data only.
- Use chronological validation.
- Avoid random shuffling across time.
- Apply early stopping.
- Save the scaler and sequence configuration with the model.

Potential libraries:

- TensorFlow/Keras or PyTorch
- Pandas
- NumPy
- Scikit-learn
- Matplotlib

Select one deep learning framework and keep the implementation consistent.

## 7. Evaluation

Use time-series evaluation metrics:

- MAE
- RMSE
- MAPE only when zero or near-zero actual values are handled appropriately
- sMAPE where appropriate

Use rolling-origin or walk-forward evaluation when feasible.

Compare LSTM results against the selected baseline models.

Do not report fabricated forecasting results.

## 8. PostgreSQL Requirements

PostgreSQL is mandatory for database persistence.

Use PostgreSQL with SQLAlchemy and Alembic.

Suggested tables:

- `forecast_runs`
- `forecast_models`
- `forecast_metrics`
- `forecast_predictions`

Store:

- Forecast run identifier
- Target definition
- Aggregation frequency
- Training period
- Forecast horizon
- Model version
- Evaluation metrics
- Prediction timestamps
- Artifact paths

Do not use SQLite for experiment tracking or application storage.

Forecast model files should normally be stored under `artifacts/models/`, with their metadata recorded in PostgreSQL.

## 9. Suggested Folder Structure

```text
backend/
  ml/
    forecasting/
      audit.py
      aggregation.py
      baselines.py
      lstm_model.py
      train.py
      evaluate.py
      predict.py

artifacts/
  models/
  forecasts/
  metrics/

tests/
  test_forecasting.py
```

## 10. Expected Outputs

- Time-series suitability report
- Aggregated time-series dataset
- Baseline forecasts
- LSTM model if justified by the data
- Forecast evaluation report
- Forecast plots
- PostgreSQL forecast run records

If LSTM is not justified, the phase can still be completed with a documented limitation and baseline forecasting experiments.

## 11. Acceptance Criteria

- Time-series suitability is assessed before model selection.
- Aggregation logic is documented.
- Chronological splits are used.
- No future information leaks into training.
- Baselines are evaluated.
- LSTM is used only if justified.
- Metrics are calculated from actual predictions.
- Forecast artifacts and metadata are saved.
- PostgreSQL stores forecast run information.
- No SQLite dependency is introduced.

## 12. Cursor AI Prompt

You are implementing Phase 05 of the SCOPE project.

Build a time-series forecasting module with a proper data suitability assessment.

Requirements:

1. Inspect the repository and existing cleaned dataset.
2. Inspect actual date and quantity columns before implementation.
3. Assess chronological coverage, missing periods, duplicate periods, irregular intervals, and data density.
4. Create a written suitability report before deciding whether an LSTM is appropriate.
5. Explore shipment quantity forecasting using PO_Line_Item_Quantity where valid.
6. Explore delivery delay trends using valid scheduled and actual delivery dates.
7. Document target definitions and aggregation frequency.
8. Implement naive, moving-average, and suitable statistical baselines.
9. Implement an LSTM only if data volume and time-series structure justify it.
10. Use chronological train/validation/test splits.
11. Prevent future-data leakage during scaling, feature creation, and sequence generation.
12. Evaluate using MAE and RMSE, and use percentage metrics only when mathematically appropriate.
13. Compare every complex model against baseline results.
14. Save forecast artifacts, configuration, and evaluation reports.
15. Add tests for aggregation, time ordering, sequence creation, leakage prevention, and forecast output.
16. Store forecast runs, model metadata, predictions, and metrics in PostgreSQL.
17. Use SQLAlchemy and Alembic for database operations.
18. PostgreSQL only. Do not use SQLite or an SQLite fallback.
19. Read credentials from environment variables.
20. Do not fabricate results or claim LSTM superiority without evidence.
21. Document commands for training and generating forecasts.

Inspect the repository first, explain the intended implementation, then implement and test the phase.

## 13. Definition of Done

The forecasting phase is complete when time-series suitability has been assessed, baseline forecasts have been evaluated, any LSTM implementation is justified by the data, and forecast metadata is persisted in PostgreSQL.
