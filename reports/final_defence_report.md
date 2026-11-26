# SCOPE Final Evaluation and Defence Report

Generated: `2026-11-26T16:23:34.796072+00:00`

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

- Best model: **logistic_regression**
- Test recall: **0.4927536231884058**
- Test precision: **0.10029498525073746**
- Test F1: **0.16666666666666666**
- Test ROC-AUC: **0.7189956806594697**
- Test PR-AUC: **0.12064140089036052**
- Test positive prevalence: **0.04291341303296248**
- Positive prevalence by split: **{'train': 0.0780997793540553, 'val': 0.04416033172080166, 'test': 0.04291341303296248}**
- Post-2010 training sensitivity test ROC-AUC: **0.7189956806594697**
- Vendor-history-only baseline ROC-AUC: **0.49107349854956195**
- Rolling-origin ROC-AUC: **0.6790087033593952 ± 0.06319216944759169**

## Supporting results

- Duration best model: **gradient_boosting**
- Duration median baseline validation MAE: **5.67002151731797**
- Duration test MAE / R²: **4.82266881756141 / -0.26887990713021237**
- Forecasting frequency: **monthly**; results include naive and mean baselines.
- Monthly late-rate model MAE: **0.039153582660729505**; beats naive: **True**, beats mean: **False**.
- Monthly volume model MAE: **4172.716329125306**; beats naive: **False**, beats mean: **False**.
- Inventory proxy model: **random_forest**; validation PR-AUC **0.602029180480256** vs prevalence baseline **0.5763648928818245**; test ROC-AUC / PR-AUC: **0.530827302510382 / 0.5932922568730234**. It excludes the two operands of the deterministic target rule and is experimental against unverified augmented fields.
- Inventory rule agreement on test rows: **0.4373574735678253** (consistency check, not model accuracy).
- RAG retrieval wiring sanity MRR: **1.0** over 20 hand-authored synthetic queries; this is not a retrieval-quality claim.
- RAG runtime components: **Okapi BM25**; check per-query mode in the API response because optional components may be unavailable in another environment.
- Claim Checker corpus-corruption evaluation: **1.0 detection rate; 0.0 false-positive rate** over 414 cases (97 extractive claims from the current corpus). This is a controlled synthetic-corpus evaluation, not a free-form semantic-accuracy estimate.
- Vendor segmentation: **k=2, silhouette=0.3599517794717767**, with small-history and profile-outlier vendors separated.
- Unusual shipment profile flags: **1099 / 14471** test shipments; flagged late-rate diagnostic **0.06642402183803457** (descriptive only).
- SHAP status: **ok**

## Model evaluation table

Supervised metrics use the held-out test split unless marked as validation. Forecast candidates are selected on validation data; only the selected estimator is scored separately on test data. Unsupervised rows show descriptive diagnostics because they have no labeled ground truth.

| Task | Model | Validation result | Test / sample result | Note |
|---|---|---|---|---|
| Late delivery | xgboost | val F1 0.209; ROC-AUC 0.736; PR-AUC 0.118 | test F1 0.077; ROC-AUC 0.484; PR-AUC 0.048 | Candidate; threshold 0.578 |
| Late delivery | logistic_regression | val F1 0.235; ROC-AUC 0.778; PR-AUC 0.142 | test F1 0.167; ROC-AUC 0.719; PR-AUC 0.121 | Selected; threshold 0.107 |
| Late delivery | random_forest | val F1 0.191; ROC-AUC 0.714; PR-AUC 0.112 | test F1 0.068; ROC-AUC 0.459; PR-AUC 0.041 | Candidate; threshold 0.614 |
| Delivery duration | dummy_median | val MAE 5.670 days | test MAE 5.001 days; R2 -0.263 | Baseline |
| Delivery duration | gradient_boosting | val MAE 4.476 days | test MAE 4.823 days; R2 -0.269 | Selected |
| Delivery duration | xgboost | val MAE 4.590 days | test MAE 5.092 days; R2 -0.436 | Candidate |
| Delivery duration | random_forest | val MAE 5.160 days | test MAE 6.510 days; R2 -1.350 | Candidate |
| Monthly late-rate forecast | naive_lag1 | validation MAE 0.059 | test MAE 0.050 | Test baseline; n_test 4; shipment_count_weighted |
| Monthly late-rate forecast | mean_baseline | validation MAE 0.050 | test MAE 0.039 | Selected; n_test 4; shipment_count_weighted |
| Monthly late-rate forecast | persistence_linear | validation MAE 0.070 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly late-rate forecast | gradient_boosting | validation MAE 0.070 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly late-rate forecast | random_forest | validation MAE 0.051 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly late-rate forecast | extra_trees | validation MAE 0.050 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly late-rate forecast | arima | validation MAE 0.051 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly volume forecast | naive_lag1 | validation MAE 2232.200 | test MAE 3817.500 | Test baseline; n_test 4; unweighted |
| Monthly volume forecast | mean_baseline | validation MAE 3082.282 | test MAE 4048.000 | Test baseline; n_test 4; unweighted |
| Monthly volume forecast | persistence_linear | validation MAE 1697.142 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly volume forecast | gradient_boosting | validation MAE 1581.172 | test MAE 4172.716 | Selected; n_test 4; unweighted |
| Monthly volume forecast | random_forest | validation MAE 3079.893 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly volume forecast | extra_trees | validation MAE 2487.307 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly volume forecast | arima | validation MAE 1971.861 | not scored on test | Validation candidate; n_test N/A; N/A |
| Inventory stockout proxy | logistic_regression | val PR-AUC 0.600; F1 0.745 | test PR-AUC N/A; ROC-AUC N/A | Validation candidate; experimental, unverified source |
| Inventory stockout proxy | random_forest | val PR-AUC 0.602; F1 0.745 | test PR-AUC 0.593; ROC-AUC 0.531 | Selected; experimental, unverified source |
| Vendor segmentation | K-Means (k=2) | silhouette 0.360 | 14 clustered vendors; sizes {'0': 11, '1': 3} | Unsupervised; not a predictive accuracy score |
| Unusual shipment profile | Isolation Forest | N/A | 1099 flags / 14471 (7.6%) | Unsupervised; no ground-truth anomaly labels |
| Retrospective anomaly | Isolation Forest | N/A | 1247 flags / 14471 (8.6%) | Unsupervised; no ground-truth anomaly labels |
| Vendor KPI anomaly | Isolation Forest | N/A | 0 flags / 17 (0.0%) | Unsupervised; no ground-truth anomaly labels |
| RAG retrieval | Okapi BM25 | N/A | MRR 1.000; Recall@3 1.000 | Wiring check only; 20 synthetic queries |
| Claim checker | verify_claims | 97 extracted corpus claims + 317 controlled corruptions | detection 1.000; false-positive rate 0.000 | Synthetic corpus and controlled corruption evaluation |

## Model vs baseline comparison

For MAE, lower is better; for AUC, PR-AUC, and F1, higher is better. Baselines and models use the same split when directly compared.

| Task | Selected model | Baseline | Model result | Comparison |
|---|---|---|---|---|
| Late delivery | logistic_regression | vendor history ROC-AUC 0.491; PR-AUC 0.044 | ROC-AUC 0.719; PR-AUC 0.121 | AUC delta 0.228 |
| Late delivery | logistic_regression | prevalence-only PR-AUC 0.043 | PR-AUC 0.121 | Above prevalence baseline |
| Delivery duration | gradient_boosting | median baseline MAE 5.001 days | MAE 4.823 days; delta -0.179 days | Better on test; validation beats median |
| Monthly late rate | mean_baseline | naive MAE 0.050; mean MAE 0.039 | model MAE 0.039 | beats naive: yes; beats mean: no |
| Monthly volume | gradient_boosting | naive MAE 3817.500; mean MAE 4048.000 | model MAE 4172.716 | beats naive: no; beats mean: no |
| Inventory stockout proxy | random_forest | validation prevalence PR-AUC 0.576 | validation PR-AUC 0.602; test PR-AUC 0.593 vs test prevalence 0.582 | test AP delta 0.011; label is derived and source unverified |
| Vendor segmentation | K-Means | No labeled baseline | silhouette only | N/A: descriptive clusters, not prediction |
| Anomaly models | Isolation Forest | No labeled anomaly baseline | flag rates only | N/A: no ground truth labels |
| RAG retrieval | Okapi BM25 | No representative relevance baseline | 20-query synthetic benchmark | N/A: not a quality benchmark |

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
