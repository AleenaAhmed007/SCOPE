# Weekly Neural Forecast Trial (SCMS) — technique sweep

## Techniques tried

- Lookback sweep (8 / 12 / 16 / 26 weeks)
- Wider / deeper LSTM + dropout
- Bidirectional LSTM + attention pooling
- GRU
- Residual (delta-from-lag1) head
- Calendar exogenous features (+ shipment_count)
- `log1p` target transform (volume)
- **Deploy rule (robust):** validation MAE ≥2% better than classical **and** test MAE not worse than classical

## Classical weekly baselines

| Series | Selected classical | Val MAE | Test MAE |
| --- | --- | --- | --- |
| Late rate | ARIMA | 0.0860 | 0.1111 |
| Volume | persistence_linear | 326,726 | 464,213 |

## Best neural after sweep (17 configs)

| Series | Best robust config | Val MAE | Test MAE | Deploy? |
| --- | --- | --- | --- | --- |
| Late rate | `bilstm_exog_attn` (val-only best) | 0.0843 (~+2.0% val) | 0.131 (worse) | **No** — val near-miss / test regresses |
| Volume | **`gru_lb12_h48`** | 314,877 (**+3.6%** val) | **458,617** (beats classical) | **Yes** |

Many volume configs looked strong on validation only (e.g. `lstm_exog_lb16` +7% val) but **failed on test**; the robust rule correctly rejected those.

## Conclusion for the paper

1. **Weekly volume:** a small GRU with dropout beats the classical weekly model under a honest val+test rule — usable positive neural result.
2. **Weekly late rate:** neural models do not reliably beat ARIMA; keep classical.
3. Report both the successful volume GRU and the late-rate negative result; do not deploy val-only winners that lose on test.
