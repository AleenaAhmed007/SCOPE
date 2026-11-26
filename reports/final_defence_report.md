# SCOPE Final Evaluation and Defence Report

Generated: `2026-11-26T14:30:20.014789+00:00`

## System summary

SCOPE integrates:
- Chronological preprocessing and leakage-aware features (Phase 02)
- Late-delivery classification (Phase 03)
- Delivery-duration regression (Phase 04)
- Monthly forecasting with baseline comparison (Phase 05)
- Vendor segmentation and anomaly detection (Phase 06)
- Inventory target rule audit (Phase 07)
- SHAP explainability (Phase 08)
- Hybrid RAG with synthetic-document labeling (Phase 09)
- Evidence ledger + Checker (Phase 10)
- Agentic investigation workflow (Phase 11)
- FastAPI + React frontend (Phase 12)

## Primary ML result — late delivery

- Best model: **random_forest**
- Test recall: **0.8852459016393442**
- Test precision: **0.27364864864864863**
- Test F1: **0.4180645161290323**
- Test ROC-AUC: **0.8062068028189845**
- Test PR-AUC: **0.31013547672066355**
- Test positive prevalence: **0.11806451612903225**
- Positive prevalence by split: **{'train': 0.0988098533075007, 'val': 0.1866925064599483, 'test': 0.11806451612903225}**
- Post-2010 training sensitivity test ROC-AUC: **0.8097785026442971**
- Vendor-history-only baseline ROC-AUC: **0.7866693849161142**
- Rolling-origin ROC-AUC: **0.6304146913271175 ± 0.10807678566595838**

## Supporting results

- Duration best model: **shipment_mode_median**
- Duration median baseline validation MAE: **86.74802110817942**
- Duration test MAE / R²: **80.95701357466064 / -0.29388199567790263**
- Forecasting frequency: **monthly**; results include naive and mean baselines.
- Monthly late-rate model MAE: **0.061021512815900285**; beats naive: **True**, beats mean: **False**.
- Monthly volume model MAE: **1002339.6**; beats naive: **False**, beats mean: **True**.
- Inventory proxy model: **None**; validation PR-AUC **None** vs prevalence baseline **None**; test ROC-AUC / PR-AUC: **None / None**. It excludes the two operands of the deterministic target rule and is experimental against unverified augmented fields.
- Inventory rule agreement on test rows: **None** (consistency check, not model accuracy).
- RAG retrieval wiring sanity MRR: **None** over None hand-authored synthetic queries; this is not a retrieval-quality claim.
- RAG runtime components: **lexical fallback**; check per-query mode in the API response because optional components may be unavailable in another environment.
- Claim Checker corpus-corruption evaluation: **None detection rate; None false-positive rate** over None cases (None extractive claims from the current corpus). This is a controlled synthetic-corpus evaluation, not a free-form semantic-accuracy estimate.
- Vendor segmentation: **k=None, silhouette=None**, with small-history and profile-outlier vendors separated.
- Unusual shipment profile flags: **None / None** test shipments; flagged late-rate diagnostic **None** (descriptive only).
- SHAP status: **None**

## Model evaluation table

Supervised metrics use the held-out test split unless marked as validation. Forecast candidates are selected on validation data; only the selected estimator is scored separately on test data. Unsupervised rows show descriptive diagnostics because they have no labeled ground truth.

| Task | Model | Validation result | Test / sample result | Note |
|---|---|---|---|---|
| Late delivery | xgboost | val F1 0.463; ROC-AUC 0.743; PR-AUC 0.331 | test F1 0.357; ROC-AUC 0.760; PR-AUC 0.280 | Candidate; threshold 0.242 |
| Late delivery | logistic_regression | val F1 0.436; ROC-AUC 0.721; PR-AUC 0.292 | test F1 0.282; ROC-AUC 0.656; PR-AUC 0.162 | Candidate; threshold 0.407 |
| Late delivery | random_forest | val F1 0.511; ROC-AUC 0.791; PR-AUC 0.365 | test F1 0.418; ROC-AUC 0.806; PR-AUC 0.310 | Selected; threshold 0.158 |
| Late delivery | extra_trees | val F1 0.504; ROC-AUC 0.791; PR-AUC 0.395 | test F1 0.413; ROC-AUC 0.808; PR-AUC 0.300 | Candidate; threshold 0.416 |
| Delivery duration | dummy_median | val MAE 86.748 days | test MAE 81.188 days; R2 -0.111 | Baseline |
| Delivery duration | shipment_mode_median | val MAE 86.215 days | test MAE 80.957 days; R2 -0.294 | Selected |
| Delivery duration | gradient_boosting | val MAE 88.454 days | test MAE 81.045 days; R2 -0.148 | Candidate |
| Delivery duration | xgboost | val MAE 87.497 days | test MAE 79.970 days; R2 -0.110 | Candidate |
| Delivery duration | random_forest | val MAE 87.664 days | test MAE 80.651 days; R2 -0.074 | Candidate |
| Monthly late-rate forecast | naive_lag1 | validation MAE 0.097 | test MAE 0.076 | Test baseline; n_test 20; shipment_count_weighted |
| Monthly late-rate forecast | mean_baseline | validation MAE 0.088 | test MAE 0.061 | Selected; n_test 20; shipment_count_weighted |
| Monthly late-rate forecast | persistence_linear | validation MAE 0.097 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly late-rate forecast | gradient_boosting | validation MAE 0.089 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly late-rate forecast | random_forest | validation MAE 0.090 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly late-rate forecast | extra_trees | validation MAE 0.089 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly late-rate forecast | arima | validation MAE 0.093 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly volume forecast | naive_lag1 | validation MAE 1159641.194 | test MAE 1002339.600 | Selected; n_test 20; unweighted |
| Monthly volume forecast | mean_baseline | validation MAE 946506.793 | test MAE 1244626.188 | Test baseline; n_test 20; unweighted |
| Monthly volume forecast | persistence_linear | validation MAE 957564.128 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly volume forecast | gradient_boosting | validation MAE 813376.782 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly volume forecast | random_forest | validation MAE 727292.290 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly volume forecast | extra_trees | validation MAE 747112.444 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly volume forecast | arima | validation MAE 846889.275 | not scored on test | Validation candidate; n_test N/A; N/A |
| Unusual shipment profile | Isolation Forest | N/A | Not evaluated | Saved model artifact or evaluation result missing |
| Retrospective anomaly | Isolation Forest | N/A | Not evaluated | Saved model artifact or evaluation result missing |
| Vendor KPI anomaly | Isolation Forest | N/A | Not evaluated | Saved model artifact or evaluation result missing |

## Model vs baseline comparison

For MAE, lower is better; for AUC, PR-AUC, and F1, higher is better. Baselines and models use the same split when directly compared.

| Task | Selected model | Baseline | Model result | Comparison |
|---|---|---|---|---|
| Late delivery | random_forest | vendor history ROC-AUC 0.787; PR-AUC 0.255 | ROC-AUC 0.806; PR-AUC 0.310 | AUC delta 0.020 |
| Late delivery | random_forest | prevalence-only PR-AUC 0.118 | PR-AUC 0.310 | Above prevalence baseline |
| Delivery duration | shipment_mode_median | median baseline MAE 81.188 days | MAE 80.957 days; delta -0.231 days | Better on test; validation beats median |
| Monthly late rate | mean_baseline | naive MAE 0.076; mean MAE 0.061 | model MAE 0.061 | beats naive: yes; beats mean: no |
| Monthly volume | naive_lag1 | naive MAE 1002339.600; mean MAE 1244626.188 | model MAE 1002339.600 | beats naive: no; beats mean: yes |
| Inventory stockout proxy | None | validation prevalence PR-AUC N/A | validation PR-AUC N/A; test PR-AUC N/A vs test prevalence N/A | test AP delta N/A; label is derived and source unverified |
| Vendor segmentation | K-Means | No labeled baseline | silhouette only | N/A: descriptive clusters, not prediction |
| Anomaly models | Isolation Forest | No labeled anomaly baseline | flag rates only | N/A: no ground truth labels |
| RAG retrieval | lexical fallback | No representative relevance baseline | N/A-query synthetic benchmark | N/A: not a quality benchmark |

## Important limitations

1. Inventory fields are **unverified augmented data**. The proxy classifier does not use the two fields that define its label; its scores are not operationally validated, and rule agreement is only a consistency check.
2. Synthetic RAG documents are **not official contracts/policies**.
3. Anomaly scores describe unusual shipment profiles and are not delay predictors; retrospective analysis is forensic only.
4. PostgreSQL is required. Start it with `docker compose up -d postgres` and set `SCOPE_DATABASE_URL=postgresql+psycopg://scope:scope@127.0.0.1:5432/scope`. The application fails startup if PostgreSQL is unavailable; it does not switch database backends.
5. RAG uses the active components recorded in `reports/models/rag_index/metadata.json`; dense embeddings and cross-encoder reranking are optional runtime capabilities, with BM25 as the lexical retriever.
6. RAG retrieval queries use a small synthetic corpus and are too limited to estimate production relevance.
7. Anomaly scores are investigative signals, not fraud probabilities or labeled accuracy.
8. Delivery-duration predictions should be treated as low-confidence unless the selected model beats the median baseline on validation data.
9. Late-delivery prevalence changes across train, validation, and test; rolling-origin CV shows substantial temporal variation.

## Reproducibility

```bash
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
docker compose up -d postgres
$env:SCOPE_DATABASE_URL='postgresql+psycopg://scope:scope@127.0.0.1:5432/scope'
python -m scope.data.preprocessing
python scripts/run_all_phases.py
uvicorn scope.api.app:app --reload --port 8000
cd frontend && npm install && npm run dev
pytest -q
```

## Defence talking points

- Prediction moment is documented: scheduled delivery known, outcome unknown.
- Chronological splits reduce temporal leakage.
- Checker validates numeric claims and citation presence.
- Agents coordinate ML + RAG + evidence rather than free-form hallucination.
- Forecasts use monthly lag models selected against naive and mean baselines.
