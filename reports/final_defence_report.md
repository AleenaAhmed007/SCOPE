# SCOPE Final Evaluation and Defence Report

Generated: `2026-11-14T09:08:38.992718+00:00`

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
- SHAP status: **fallback_native_importance**

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
