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
| Claim-level verification | Wired into RAG answers and investigations | RAG claims are checked against retrieved passages. Unsupported claims are excluded from answer text but remain in the response with verdicts. Investigation evidence stores the asserted claim and its passage; `checker_node` runs `verify_claims()`, updates failed ledger rows to `needs_review`, and makes the investigation status `needs_review`. |
| PDF upload | Not implemented correctly | Upload endpoint saves bytes, then treats non-Markdown files as UTF-8 text. There is no PDF text extraction and no frontend upload control. Markdown/text uploads are the supported path. |
| Corpus size and provenance | Partial | Eight synthetic policy/agreement documents are present. They are fixtures, not authoritative external contracts or a representative production corpus. |

### Agent workflow, evidence, and checker

| Item | Current status | Notes |
|---|---|---|
| Investigation graph | Implemented, deterministic sequence | Planner, analysis, document retrieval, evidence/report writing and checker nodes exist. |
| Autonomous planning | Still outstanding | `planner()` returns a hard-coded task list. Graph edges are linear; no goal-dependent tool selection or re-planning. |
| Checker revision loop | Still outstanding | Checker now runs before the final report is written, so the report contains verdicts. No conditional retry/report revision is wired; `prune_unsupported()` remains unused. |
| Checker negative-path evaluation | Implemented on synthetic fixtures | `python -m scope.evaluation.checker_claim_evaluation` evaluates 50 labelled cases: 10 supported and 40 negatives across unsupported, uncited, unknown-citation and wrong-number cases. Latest run: detection 1.00, false-positive rate 0.00, supported-claim false-rejection rate 0.00. These are deterministic wiring metrics, not real-world semantic accuracy. |
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
3. Describe claim support as a lexical/numeric heuristic, not semantic entailment. The checker is active in the investigation flow, but the evaluation is a small synthetic fixture.
4. Do not claim PDF upload support until real PDF extraction and a UI upload path are implemented.
5. Rerun model phases/evaluation and reconcile the duration-model selection and vendor-KPI evaluation rows. Artifacts are absent from the current workspace even though source code can create them.
6. State that LLM generation is optional and only active when configured; otherwise the extractive fallback is used.
7. Remove or qualify claims about autonomous planning and scheduled analysis until those features exist.

## Remaining work, in priority order

1. **Regenerate and reconcile artifacts:** run the intended model/evaluation phases, save bundles, rebuild the RAG index, and regenerate final reports from current outputs. Resolve duration-model and vendor-KPI report discrepancies.
2. **Make RAG capability reporting truthful:** inspect actual index metadata and ensure UI/report copy reflects fallback versus dense/reranked mode.
3. **Expand checker evaluation beyond fixtures** before making broad semantic-accuracy claims; current rates use deterministic synthetic examples.
4. **Implement proper PDF parsing and frontend upload**, if PDF upload is a required deliverable.
5. **Add planner branching and checker retry/revision**, if autonomous investigation is a required research contribution.
6. **Either implement job scheduling or remove the scheduling claim.**
7. **Add Alembic and frontend/API integration tests** if required by the proposal/deployment target.

## Verdict

Several gaps from the previous audit have been addressed: the RAG corpus is restricted to document fixtures/uploads, BM25 is real Okapi BM25, optional dense/reranker and LLM code exists, claim verification is wired into RAG answers and investigations, and a synthetic negative-path checker evaluation is recorded. Neural RAG remains optional, and fresh model artifacts are absent from this workspace.

The highest-priority remaining work is rerunning phases and reconciling generated artifacts/reports. The checker rejects the tested unsupported claim categories, though the reported rates are synthetic-fixture results. Autonomous planning, scheduling, and proper PDF handling remain unimplemented.
