# Weekly LSTM Forecast Trial (SCMS)

## Setup

- Series: weekly late rate (~483 periods) and weekly volume (~505 periods)
- LSTM: lookback=12 weeks, hidden=32, early-stopping on validation
- Classical candidates: naive, mean, linear, GB, RF, ExtraTrees, ARIMA
- Deploy rule: LSTM must beat selected classical **validation MAE by ≥2%**

## Results

| Series | Classical (val → test) | LSTM (val → test) | Deploy LSTM? |
| --- | --- | --- | --- |
| Late rate | ARIMA 0.0860 → 0.1111 | 0.0862 → 0.1132 | **No** (tie / slightly worse) |
| Volume | persistence_linear 326k → 464k | 324k → 452k | **No** (~0.7% val gain only) |

LSTM beats **naive lag-1** on the weekly test set for both series, but does **not** clearly beat the best classical model on validation.

## Conclusion

Weekly aggregation makes LSTM trainable on SCMS, but it does not earn deployment over classical one-step models under the stated rule. Keep monthly/weekly classical models as primary; report LSTM as a negative / ablation result for the paper.
