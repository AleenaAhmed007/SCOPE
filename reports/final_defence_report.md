# SCOPE Final Evaluation and Defence Report

Generated: `2026-11-14T10:57:03.534609+00:00`

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
- Test recall: **0.825136612021858**
- Test precision: **0.29206963249516443**
- Test F1: **0.43142857142857144**
- Test ROC-AUC: **0.8071042248791778**
- Test PR-AUC: **0.30691550525426403**
- Test positive prevalence: **0.11806451612903225**
- Positive prevalence by split: **{'train': 0.0988098533075007, 'val': 0.1866925064599483, 'test': 0.11806451612903225}**
- Post-2010 training sensitivity test ROC-AUC: **0.8132582616794785**
- Vendor-history-only baseline ROC-AUC: **0.7866693849161142**
- Rolling-origin ROC-AUC: **0.6208423335259511 ± 0.11603728981764848**

## Supporting results

- Duration best model: **random_forest**
- Duration median baseline validation MAE: **86.74802110817942**
- Duration test MAE / R²: **81.22336275142703 / -0.12444560390728854**
- Forecasting frequency: **monthly**; results include naive and mean baselines.
- Monthly late-rate model MAE: **0.06815115697827147**; beats naive: **True**, beats mean: **False**.
- Monthly volume model MAE: **994005.1897767073**; beats naive: **False**, beats mean: **True**.
- Inventory proxy model: **random_forest**; validation PR-AUC **0.652053938119597** vs prevalence baseline **0.33785529715762275**; test ROC-AUC / PR-AUC: **0.7816059623443916 / 0.7050876153767016**. It excludes the two operands of the deterministic target rule and is experimental against unverified augmented fields.
- Inventory rule agreement on test rows: **1.0** (consistency check, not model accuracy).
- RAG retrieval wiring sanity MRR: **0.8333333333333334** over 3 hand-authored synthetic queries; this is not a retrieval-quality claim.
- Vendor segmentation: **k=4, silhouette=0.26827670925046854**, with small-history and profile-outlier vendors separated.
- Unusual shipment profile flags: **181 / 1550** test shipments; flagged late-rate diagnostic **0.20441988950276244** (descriptive only).
- SHAP status: **ok**

## Model evaluation table

Supervised metrics use the held-out test split unless marked as validation. Forecast candidates are selected on validation data; only the selected estimator is scored separately on test data. Unsupervised rows show descriptive diagnostics because they have no labeled ground truth.

| Task | Model | Validation result | Test / sample result | Note |
|---|---|---|---|---|
| Late delivery | xgboost | val F1 0.463; ROC-AUC 0.747; PR-AUC 0.336 | test F1 0.340; ROC-AUC 0.764; PR-AUC 0.278 | Candidate; threshold 0.270 |
| Late delivery | random_forest | val F1 0.511; ROC-AUC 0.789; PR-AUC 0.366 | test F1 0.431; ROC-AUC 0.807; PR-AUC 0.307 | Selected; threshold 0.476 |
| Delivery duration | dummy_median | val MAE 86.748 days | test MAE 81.188 days; R² -0.111 | Baseline |
| Delivery duration | gradient_boosting | val MAE 88.151 days | test MAE 79.877 days; R² -0.083 | Candidate |
| Delivery duration | xgboost | val MAE 89.225 days | test MAE 82.075 days; R² -0.107 | Candidate |
| Delivery duration | random_forest | val MAE 86.411 days | test MAE 81.223 days; R² -0.124 | Selected |
| Monthly late-rate forecast | naive_lag1 | validation MAE 0.095 | test MAE 0.087 | Test baseline; n_test 22; shipment_count_weighted |
| Monthly late-rate forecast | persistence_linear | validation MAE 0.084 | not scored on test | Validation candidate; n_test —; — |
| Monthly late-rate forecast | gradient_boosting | validation MAE 0.080 | not scored on test | Validation candidate; n_test —; — |
| Monthly late-rate forecast | random_forest | validation MAE 0.078 | not scored on test | Validation candidate; n_test —; — |
| Monthly late-rate forecast | extra_trees | validation MAE 0.069 | test MAE 0.068 | Selected; n_test 22; shipment_count_weighted |
| Monthly late-rate forecast | mean_baseline | validation MAE 0.090 | test MAE 0.064 | Test baseline; n_test 22; shipment_count_weighted |
| Monthly volume forecast | naive_lag1 | validation MAE 1137035.111 | test MAE 947280.227 | Test baseline; n_test 22; unweighted |
| Monthly volume forecast | persistence_linear | validation MAE 685063.110 | not scored on test | Validation candidate; n_test —; — |
| Monthly volume forecast | gradient_boosting | validation MAE 617024.420 | not scored on test | Validation candidate; n_test —; — |
| Monthly volume forecast | random_forest | validation MAE 646759.741 | not scored on test | Validation candidate; n_test —; — |
| Monthly volume forecast | extra_trees | validation MAE 602625.224 | test MAE 994005.190 | Selected; n_test 22; unweighted |
| Monthly volume forecast | mean_baseline | validation MAE 1073664.915 | test MAE 1205206.061 | Test baseline; n_test 22; unweighted |
| Inventory stockout proxy | logistic_regression | val PR-AUC 0.574; F1 0.559 | test PR-AUC —; ROC-AUC — | Validation candidate; experimental, unverified source |
| Inventory stockout proxy | random_forest | val PR-AUC 0.652; F1 0.621 | test PR-AUC 0.705; ROC-AUC 0.782 | Selected; experimental, unverified source |
| Vendor segmentation | K-Means (k=4) | silhouette 0.268 | 28 clustered vendors; sizes {'0': 4, '1': 5, '2': 7, '3': 12} | Unsupervised; not a predictive accuracy score |
| Unusual shipment profile | Isolation Forest | — | 181 flags / 1550 (11.7%) | Unsupervised; no ground-truth anomaly labels |
| Retrospective anomaly | Isolation Forest | — | 159 flags / 1550 (10.3%) | Unsupervised; no ground-truth anomaly labels |
| Vendor KPI anomaly | Isolation Forest | — | Not evaluated | Saved model artifact or evaluation result missing |
| RAG retrieval | TF-IDF + keyword RRF | — | MRR 0.833; Recall@3 1.000 | Wiring check only; 3 synthetic queries |

## Model vs baseline comparison

For MAE, lower is better; for AUC, PR-AUC, and F1, higher is better. Baselines and models use the same split when directly compared.

| Task | Selected model | Baseline | Model result | Comparison |
|---|---|---|---|---|
| Late delivery | random_forest | vendor history ROC-AUC 0.787; PR-AUC 0.255 | ROC-AUC 0.807; PR-AUC 0.307 | AUC Δ 0.020 |
| Late delivery | random_forest | prevalence-only PR-AUC 0.118 | PR-AUC 0.307 | Above prevalence baseline |
| Delivery duration | random_forest | median baseline MAE 81.188 days | MAE 81.223 days; Δ 0.036 days | Does not beat on test; validation beats median |
| Monthly late rate | extra_trees | naive MAE 0.087; mean MAE 0.064 | model MAE 0.068 | beats naive: yes; beats mean: no |
| Monthly volume | extra_trees | naive MAE 947280.227; mean MAE 1205206.061 | model MAE 994005.190 | beats naive: no; beats mean: yes |
| Inventory stockout proxy | random_forest | validation prevalence PR-AUC 0.338 | validation PR-AUC 0.652; test PR-AUC 0.705 vs test prevalence 0.379 | test AP Δ 0.326; label is derived and source unverified |
| Vendor segmentation | K-Means | No labeled baseline | silhouette only | N/A: descriptive clusters, not prediction |
| Anomaly models | Isolation Forest | No labeled anomaly baseline | flag rates only | N/A: no ground truth labels |
| RAG retrieval | TF-IDF + keyword RRF | No representative relevance baseline | 3-query sanity check | N/A: not a quality benchmark |

## Important limitations

1. Inventory fields are **unverified augmented data**. The proxy classifier does not use the two fields that define its label; its scores are not operationally validated, and rule agreement is only a consistency check.
2. Synthetic RAG documents are **not official contracts/policies**.
3. Anomaly scores describe unusual shipment profiles and are not delay predictors; retrospective analysis is forensic only.
4. PostgreSQL is required. Start it with `docker compose up -d postgres` and set `SCOPE_DATABASE_URL=postgresql+psycopg://scope:scope@127.0.0.1:5432/scope`. The application fails startup if PostgreSQL is unavailable; it does not switch database backends.
5. RAG uses hybrid TF-IDF + keyword RRF (upgradeable to dense embeddings + FAISS/pgvector).
6. RAG retrieval sanity queries are synthetic and too small to estimate production relevance.
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
