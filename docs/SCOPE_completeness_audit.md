# SCOPE — Completeness Audit vs. Project Proposal

Rechecked: 2026-11-14. This update is based on current source/configuration and a fresh run of all pipeline phases. The full backend test suite and live API checks were not rerun during this pass.

## Previously verified execution results

`python scripts/run_all_phases.py` completed successfully: all 14 phases reported `ok`, including preprocessing, model training, SHAP, RAG reindex, PostgreSQL investigation, model evaluation, walk-forward backtest, and final report generation. The frontend production build passed after the retrieval-mode UI update. The previous audit recorded 49 passing backend tests; that full suite was not rerun here. Targeted claim-checker tests were rerun and passed.

Fresh model bundles are present under `reports/models/`, including `anomaly_vendor_kpi` and both monthly forecasts. The duration metrics and saved bundle both select `random_forest`; validation MAE is 86.411 days versus 86.748 for the median baseline, while test MAE is 81.223 days versus 81.188 for the median baseline. Vendor-KPI evaluation now includes 48 test vendor-periods and synthetic injection sensitivity/false-alarm results.

## Current status by project area

### Machine learning and analytics

| Area | Current status | Notes |
|---|---|---|
| Late-delivery classification | Implemented and retrained | Source includes XGBoost, Random Forest and Logistic Regression candidates, threshold/calibration and temporal evaluation. Fresh bundle and evaluation artifacts were regenerated. |
| Delivery-duration regression | Implemented; bookkeeping reconciled | Fresh metrics, phase summary, final report and bundle all select `random_forest` with `prediction_basis=ml_model`. It beats the median on validation, but test MAE is slightly higher than the median baseline. |
| Monthly forecasts | Classical models implemented; LSTM not trained | Current source includes lag baselines and ARIMA candidates. LSTM remains an explicit data-length/regularity limitation. |
| Vendor segmentation | Implemented and retrained | K-Means clustering and low-history handling are present; fresh metrics/artifact generated. |
| Anomaly detection | Implemented and artifacts regenerated | Unusual-profile, retrospective and vendor-KPI bundles exist. Vendor-KPI evaluation includes 48 test periods and injection metrics; injection results remain synthetic, not field accuracy. |
| Inventory risk | Experimental proxy only | The target is an arithmetic rule and source fields have known quality limitations. Do not describe this as validated stock-cover-vs-lead-time prediction. |
| SHAP | Implemented and rerun | Fresh explainability output generated from the selected model. |

### RAG and document handling

| Item | Current status | Notes |
|---|---|---|
| Evidence corpus | Fixed | `backend/scope/rag/index.py` indexes `data/documents/synthetic/` and `data/documents/uploads/`, not project `docs/` or `reports/`. This removes the earlier self-citation issue. |
| BM25 | Implemented | `backend/scope/rag/bm25.py` implements Okapi BM25; RAG index stores BM25 statistics. |
| Dense embeddings | Active here; optional elsewhere | Fresh metadata reports `dense_available=true`, BGE small English vectors, dimension 384. Other environments may fall back. |
| Cross-encoder reranking | Active here; optional elsewhere | Fresh metadata reports `reranker_available=true`; per-query results now expose whether it actually ran. |
| Hybrid retrieval and evaluation | Implemented and rebuilt | Current stack is dense + Okapi BM25 + RRF + cross-encoder reranking. The 20-query gold-section benchmark has MRR 1.0 on the small synthetic corpus; this is not a production relevance claim. |
| LLM answer generation | Optional implementation | OpenAI-compatible chat-completions endpoint is supported through environment variables, with extractive fallback. No provider is configured by default in the checked-in requirements/config. Do not claim generated answers are active unless configured and verified. |
| Claim-level verification | Wired into RAG answers and investigations | RAG claims are checked against retrieved passages. Unsupported claims are excluded from answer text but remain in the response with verdicts. Investigation evidence stores the asserted claim and its passage; `checker_node` runs `verify_claims()`, updates failed ledger rows to `needs_review`, and makes the investigation status `needs_review`. |
| PDF upload | Not implemented correctly | Upload endpoint saves bytes, then treats non-Markdown files as UTF-8 text. There is no PDF text extraction and no frontend upload control. Markdown/text uploads are the supported path. |
| Corpus size and provenance | Partial | Eight synthetic policy/agreement documents are present. They are fixtures, not authoritative external contracts or a representative production corpus. |

### Agent workflow, evidence, and checker

| Item | Current status | Notes |
|---|---|---|
| Investigation graph | Implemented, deterministic sequence | Planner, analysis, document retrieval, evidence/report writing and checker nodes exist. |
| Autonomous planning | Still outstanding | `planner()` returns a hard-coded task list. Graph edges are linear; no goal-dependent tool selection or re-planning. |
| Checker revision loop | Still outstanding | Checker now runs before the final report is written, so the report contains verdicts. No conditional retry/report revision is wired; `prune_unsupported()` remains unused. |
| Checker negative-path evaluation | Expanded to corpus-grounded corruption cases | The current evaluation uses 97 extracted claims and 317 controlled corruptions (414 cases total), from the indexed document corpus. Detection 1.00, false-positive rate 0.00, supported-claim false-rejection 0.00. The corpus is synthetic and corruptions are controlled; this is not broad semantic accuracy. |
| Evidence ledger | Implemented | PostgreSQL-backed evidence and validation records are present in source. |
| Analytical scheduling | Not implemented | No scheduler, queue/worker, or analytical job table was found. Remove any proposal/architecture claim that analyses run as scheduled jobs, or implement this layer. |

### Application and delivery

| Item | Current status | Notes |
|---|---|---|
| FastAPI and React application | Implemented | Previous audit recorded successful API and frontend build checks; not rerun in this update. |
| Docker Compose | PostgreSQL only | `docker-compose.yml` defines PostgreSQL, not backend or frontend containers. |
| Database migrations | Missing | Initialization uses SQLAlchemy `Base.metadata.create_all`; no Alembic setup found. |
| Frontend tests | Missing | `frontend/package.json` has no Vitest/RTL/Playwright scripts or dependencies. |
| API integration coverage | Partial | Unit/smoke tests exist, but no dedicated end-to-end tests for the investigation and evidence flows were found. |
| Notebooks | Partial | One EDA notebook; later phases are implemented as Python modules. |
| Charting library | Proposal deviation | Recharts is used instead of Plotly. This is a technology choice unless the proposal requires Plotly specifically. |

## Audit wording and report corrections still needed

1. RAG UI now reports the active components for each query; Overview copy states that dense retrieval and reranking depend on availability. Current index metadata reports dense, BM25, and reranking available.
2. Final report wording now describes the active stack from current index metadata instead of the stale TF-IDF description.
3. Keep checker results qualified: the expanded evaluation uses corpus-derived extractive claims and controlled corruptions, but the document corpus itself is synthetic. It does not establish free-form semantic accuracy.
4. Do not claim PDF upload support until real PDF extraction and a UI upload path are implemented.
5. State that LLM generation is optional and only active when configured; otherwise the extractive fallback is used.
6. Remove or qualify claims about autonomous planning and scheduled analysis until those features exist.

## Remaining work, in priority order

1. **Add human-labelled checker evaluation** with representative non-synthetic policy documents and independently authored unsupported claims before making broad semantic-accuracy claims.
2. **Implement proper PDF parsing and frontend upload**, if PDF upload is a required deliverable.
3. **Add planner branching and checker retry/revision**, if autonomous investigation is a required research contribution.
4. **Either implement job scheduling or remove the scheduling claim.**
5. **Add Alembic and frontend/API integration tests** if required by the proposal/deployment target.

## Verdict

All pipeline phases have been rerun and the model/evaluation artifacts regenerated. Duration selection and vendor-KPI results now agree across fresh outputs. The rebuilt RAG index reports dense, BM25, and reranker active here; query results and the frontend now expose the components actually used. Claim verification is wired into answers and investigations, with a 414-case corpus-derived corruption evaluation.

The main evidence gap is human-labelled evaluation on representative real documents. Autonomous planning/revision, scheduling, and proper PDF handling remain unimplemented.
