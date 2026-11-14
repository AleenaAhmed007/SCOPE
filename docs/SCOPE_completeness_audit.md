# SCOPE — Completeness Audit vs. Project Proposal

Rechecked: 2026-11-14. This update is based on current source/configuration and the artifacts present in the workspace. The execution results below are carried forward from the previous audit; tests and services were not rerun during this source recheck.

## Previously verified execution results

The previous audit recorded these successful checks: 49 backend tests passed, the frontend production build passed, FastAPI and PostgreSQL started, dashboard and health endpoints returned successfully, RAG query returned citations, and an investigation completed with validated evidence. These results have **not** been rerun as part of this update.

The current checkout's `reports/models/` contains only `.gitkeep`; model artifacts referenced in older reports are not present in this workspace snapshot. Treat old model metrics as historical until phases are rerun and artifacts are regenerated.

## Current status by project area

### Machine learning and analytics

| Area | Current status | Notes |
|---|---|---|
| Late-delivery classification | Implemented | Source includes XGBoost, Random Forest and Logistic Regression candidates, threshold/calibration and temporal evaluation. Recheck fresh metrics after retraining because model artifacts are absent here. |
| Delivery-duration regression | Implemented, weak baseline result | Older evaluation reported the selected model did not beat the median baseline on test. Reconcile phase summary, final evaluation and deployed artifact after retraining. |
| Monthly forecasts | Classical models implemented; LSTM not trained | Current source includes lag baselines and ARIMA candidates. LSTM remains an explicit data-length/regularity limitation. |
| Vendor segmentation | Implemented | K-Means clustering and low-history handling are present. Fresh metrics/artifact need regeneration in this workspace. |
| Anomaly detection | Implemented in source | Unusual-profile, retrospective and vendor-KPI detectors exist. Vendor-KPI training code saves a bundle, but no model artifacts are present in this workspace. Rerun phases and evaluation before relying on report rows. |
| Inventory risk | Experimental proxy only | The target is an arithmetic rule and source fields have known quality limitations. Do not describe this as validated stock-cover-vs-lead-time prediction. |
| SHAP | Implemented in source | Requires regenerated selected-model artifacts/results to verify the current output. |

### RAG and document handling

| Item | Current status | Notes |
|---|---|---|
| Evidence corpus | Fixed | `backend/scope/rag/index.py` indexes `data/documents/synthetic/` and `data/documents/uploads/`, not project `docs/` or `reports/`. This removes the earlier self-citation issue. |
| BM25 | Implemented | `backend/scope/rag/bm25.py` implements Okapi BM25; RAG index stores BM25 statistics. |
| Dense embeddings | Optional implementation only | Wrappers use `fastembed` and BGE, but `fastembed` is not a required dependency. The system falls back when unavailable. Confirm runtime metadata before claiming dense retrieval is active. |
| Cross-encoder reranking | Optional implementation only | Wrapper and retrieval integration exist, but dependency/model availability is not guaranteed. Runtime metadata should state whether reranking actually ran. |
| Hybrid retrieval and evaluation | Implemented in source | Dense/BM25/fused/reranked ablations and 20 hand-written retrieval cases exist. Evaluation remains a wiring check over a small synthetic corpus, not a broad quality claim. Regenerate index metadata to get current results. |
| LLM answer generation | Optional implementation | OpenAI-compatible chat-completions endpoint is supported through environment variables, with extractive fallback. No provider is configured by default in the checked-in requirements/config. Do not claim generated answers are active unless configured and verified. |
| Claim-level verification | Helper implemented, not wired end to end | `backend/scope/evidence/claims.py` checks citation resolution, numeric grounding and lexical overlap. The investigation workflow's `checker_node` still calls `run_checker()` from `checker.py`; it does not call `verify_claims()`. Generated RAG claims are not sent through this claim verifier in the workflow. |
| PDF upload | Not implemented correctly | Upload endpoint saves bytes, then treats non-Markdown files as UTF-8 text. There is no PDF text extraction and no frontend upload control. Markdown/text uploads are the supported path. |
| Corpus size and provenance | Partial | Eight synthetic policy/agreement documents are present. They are fixtures, not authoritative external contracts or a representative production corpus. |

### Agent workflow, evidence, and checker

| Item | Current status | Notes |
|---|---|---|
| Investigation graph | Implemented, deterministic sequence | Planner, analysis, document retrieval, evidence/report writing and checker nodes exist. |
| Autonomous planning | Still outstanding | `planner()` returns a hard-coded task list. Graph edges are linear; no goal-dependent tool selection or re-planning. |
| Checker revision loop | Still outstanding | Checker runs after report writing and graph ends. No conditional retry/report revision is wired. `prune_unsupported()` is currently an unused helper. |
| Checker negative-path evaluation | Still outstanding | Unit tests cover numeric mismatch. No end-to-end experiment injects corrupted/unsupported generated claims and reports detection and false-positive rates. |
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

1. Update the RAG description to say **BM25 is implemented; dense embeddings and cross-encoder reranking are optional and must be confirmed from runtime metadata**. UI currently presents dense/BM25/reranking as a guaranteed stack, which may overstate a fallback-only runtime.
2. Update the RAG evaluation description from the old TF-IDF/keyword account. Current source uses BM25 and optional dense retrieval; report generation code may still contain stale TF-IDF wording and needs alignment.
3. Keep the checker claim narrow until `verify_claims()` is wired into investigation and evaluated end to end. At present, claim-level semantic/lexical verification is a helper, not the active workflow checker.
4. Do not claim PDF upload support until real PDF extraction and a UI upload path are implemented.
5. Rerun model phases/evaluation and reconcile the duration-model selection and vendor-KPI evaluation rows. Artifacts are absent from the current workspace even though source code can create them.
6. State that LLM generation is optional and only active when configured; otherwise the extractive fallback is used.
7. Remove or qualify claims about autonomous planning and scheduled analysis until those features exist.

## Remaining work, in priority order

1. **Wire claim verification into the investigation flow:** pass generated claims and retrieved passages to `verify_claims()`, expose verdicts, and prevent unsupported claims from being labelled validated.
2. **Evaluate the Checker end to end:** inject supported, unsupported, uncited, unknown-citation and wrong-number claims; report detection rate and false-positive rate.
3. **Regenerate and reconcile artifacts:** run the intended model/evaluation phases, save bundles, rebuild the RAG index, and regenerate final reports from those current outputs. Resolve duration-model and vendor-KPI report discrepancies.
4. **Make RAG capability reporting truthful:** include/install the intended optional neural dependency where appropriate, inspect actual index metadata, and make UI/report copy reflect fallback versus dense/reranked mode.
5. **Implement proper PDF parsing and frontend upload**, if PDF upload is a required deliverable.
6. **Add planner branching and checker retry/revision**, if autonomous investigation is a required research contribution.
7. **Either implement job scheduling or remove the scheduling claim.**
8. **Add Alembic and frontend/API integration tests** if required by the proposal/deployment target.

## Verdict

Several gaps from the previous audit have been addressed: the RAG corpus is restricted to document fixtures/uploads, BM25 is real Okapi BM25, optional dense/reranker and LLM code exists, claim verification helpers exist, and vendor-KPI artifact saving is implemented. These additions are not all active end to end: neural RAG is optional, claim verification is not connected to the agent checker, and fresh model artifacts are absent from this workspace.

The highest-priority remaining research work is claim-checker integration plus a measured negative-path evaluation. The main reproducibility task is rerunning phases and reconciling generated artifacts/reports. Autonomous planning, scheduling, and proper PDF handling remain unimplemented.
