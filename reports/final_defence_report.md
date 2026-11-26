# SCOPE Final Evaluation and Defence Report

Generated: `2026-11-26T14:48:16.430269+00:00`

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

- Best model: **xgboost**
- Test recall: **0.9997308209959623**
- Test precision: **0.5750338687826592**
- Test F1: **0.7301142646516771**
- Test ROC-AUC: **0.7454882484910876**
- Test PR-AUC: **0.8367215948182758**
- Test positive prevalence: **0.5748326950601524**
- Positive prevalence by split: **{'train': 0.5741072830497409, 'val': 0.5653298336356969, 'test': 0.5748326950601524}**
- Post-2010 training sensitivity test ROC-AUC: **0.7454882484910876**
- Vendor-history-only baseline ROC-AUC: **0.5116494187768703**
- Rolling-origin ROC-AUC: **0.7398955350590996 ± 0.002074688854385669**

## Supporting results

- Duration best model: **gradient_boosting**
- Duration median baseline validation MAE: **1.395838962442583**
- Duration test MAE / R²: **0.9878137284186871 / 0.3754029784175036**
- Forecasting frequency: **monthly**; results include naive and mean baselines.
- Monthly late-rate model MAE: **0.008519734868261077**; beats naive: **True**, beats mean: **False**.
- Monthly volume model MAE: **1461.625**; beats naive: **False**, beats mean: **True**.
- Inventory proxy model: **random_forest**; validation PR-AUC **0.7348373498583889** vs prevalence baseline **0.4708054806662481**; test ROC-AUC / PR-AUC: **0.7008653832988258 / 0.6958500277392563**. It excludes the two operands of the deterministic target rule and is experimental against unverified augmented fields.
- Inventory rule agreement on test rows: **0.5388308283171461** (consistency check, not model accuracy).
- RAG retrieval wiring sanity MRR: **1.0** over 20 hand-authored synthetic queries; this is not a retrieval-quality claim.
- RAG runtime components: **Okapi BM25**; check per-query mode in the API response because optional components may be unavailable in another environment.
- Claim Checker corpus-corruption evaluation: **1.0 detection rate; 0.0 false-positive rate** over 414 cases (97 extractive claims from the current corpus). This is a controlled synthetic-corpus evaluation, not a free-form semantic-accuracy estimate.
- Vendor segmentation: **k=2, silhouette=0.46474835448630697**, with small-history and profile-outlier vendors separated.
- Unusual shipment profile flags: **2136 / 27079** test shipments; flagged late-rate diagnostic **0.5636274987810824** (descriptive only).
- SHAP status: **ok**

## Model evaluation table

Supervised metrics use the held-out test split unless marked as validation. Forecast candidates are selected on validation data; only the selected estimator is scored separately on test data. Unsupervised rows show descriptive diagnostics because they have no labeled ground truth.

| Task | Model | Validation result | Test / sample result | Note |
|---|---|---|---|---|
| Late delivery | xgboost | val F1 0.723; ROC-AUC 0.738; PR-AUC 0.826 | test F1 0.730; ROC-AUC 0.745; PR-AUC 0.837 | Selected; threshold 0.323 |
| Late delivery | logistic_regression | val F1 0.722; ROC-AUC 0.730; PR-AUC 0.823 | test F1 0.730; ROC-AUC 0.743; PR-AUC 0.835 | Candidate; threshold 0.249 |
| Late delivery | random_forest | val F1 0.723; ROC-AUC 0.737; PR-AUC 0.827 | test F1 0.730; ROC-AUC 0.749; PR-AUC 0.839 | Candidate; threshold 0.324 |
| Delivery duration | dummy_median | val MAE 1.396 days | test MAE 1.392 days; R2 -0.096 | Baseline |
| Delivery duration | gradient_boosting | val MAE 0.983 days | test MAE 0.988 days; R2 0.375 | Selected |
| Delivery duration | xgboost | val MAE 0.997 days | test MAE 0.997 days; R2 0.380 | Candidate |
| Delivery duration | random_forest | val MAE 0.990 days | test MAE 0.992 days; R2 0.381 | Candidate |
| Monthly late-rate forecast | naive_lag1 | validation MAE 0.015 | test MAE 0.014 | Test baseline; n_test 8; shipment_count_weighted |
| Monthly late-rate forecast | mean_baseline | validation MAE 0.011 | test MAE 0.009 | Selected; n_test 8; shipment_count_weighted |
| Monthly late-rate forecast | persistence_linear | validation MAE 0.019 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly late-rate forecast | gradient_boosting | validation MAE 0.014 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly late-rate forecast | random_forest | validation MAE 0.014 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly late-rate forecast | extra_trees | validation MAE 0.013 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly late-rate forecast | arima | validation MAE 0.013 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly volume forecast | naive_lag1 | validation MAE 491.500 | test MAE 1461.625 | Selected; n_test 8; unweighted |
| Monthly volume forecast | mean_baseline | validation MAE 783.625 | test MAE 6125.346 | Test baseline; n_test 8; unweighted |
| Monthly volume forecast | persistence_linear | validation MAE 852.955 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly volume forecast | gradient_boosting | validation MAE 749.979 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly volume forecast | random_forest | validation MAE 833.387 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly volume forecast | extra_trees | validation MAE 819.967 | not scored on test | Validation candidate; n_test N/A; N/A |
| Monthly volume forecast | arima | validation MAE 760.966 | not scored on test | Validation candidate; n_test N/A; N/A |
| Inventory stockout proxy | logistic_regression | val PR-AUC 0.721; F1 0.760 | test PR-AUC N/A; ROC-AUC N/A | Validation candidate; experimental, unverified source |
| Inventory stockout proxy | random_forest | val PR-AUC 0.735; F1 0.762 | test PR-AUC 0.696; ROC-AUC 0.701 | Selected; experimental, unverified source |
| Vendor segmentation | K-Means (k=2) | silhouette 0.465 | 5 clustered vendors; sizes {'0': 4, '1': 1} | Unsupervised; not a predictive accuracy score |
| Unusual shipment profile | Isolation Forest | N/A | 2136 flags / 27079 (7.9%) | Unsupervised; no ground-truth anomaly labels |
| Retrospective anomaly | Isolation Forest | N/A | 1963 flags / 27079 (7.2%) | Unsupervised; no ground-truth anomaly labels |
| Vendor KPI anomaly | Isolation Forest | N/A | 6 flags / 30 (20.0%) | Unsupervised; no ground-truth anomaly labels |
| RAG retrieval | Okapi BM25 | N/A | MRR 1.000; Recall@3 1.000 | Wiring check only; 20 synthetic queries |
| Claim checker | verify_claims | 97 extracted corpus claims + 317 controlled corruptions | detection 1.000; false-positive rate 0.000 | Synthetic corpus and controlled corruption evaluation |

## Model vs baseline comparison

For MAE, lower is better; for AUC, PR-AUC, and F1, higher is better. Baselines and models use the same split when directly compared.

| Task | Selected model | Baseline | Model result | Comparison |
|---|---|---|---|---|
| Late delivery | xgboost | vendor history ROC-AUC 0.512; PR-AUC 0.591 | ROC-AUC 0.745; PR-AUC 0.837 | AUC delta 0.234 |
| Late delivery | xgboost | prevalence-only PR-AUC 0.575 | PR-AUC 0.837 | Above prevalence baseline |
| Delivery duration | gradient_boosting | median baseline MAE 1.392 days | MAE 0.988 days; delta -0.404 days | Better on test; validation beats median |
| Monthly late rate | mean_baseline | naive MAE 0.014; mean MAE 0.009 | model MAE 0.009 | beats naive: yes; beats mean: no |
| Monthly volume | naive_lag1 | naive MAE 1461.625; mean MAE 6125.346 | model MAE 1461.625 | beats naive: no; beats mean: yes |
| Inventory stockout proxy | random_forest | validation prevalence PR-AUC 0.471 | validation PR-AUC 0.735; test PR-AUC 0.696 vs test prevalence 0.520 | test AP delta 0.176; label is derived and source unverified |
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
