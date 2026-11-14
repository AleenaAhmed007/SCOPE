# SCOPE — Completeness Audit vs. Project Proposal

Rechecked: 2026-11-14. This update is based on current source/configuration, a fresh run of all pipeline phases, and the checker benchmark run recorded below. The full backend test suite and live upload/API checks were not rerun during this pass.

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
| Evidence corpus | Improved | `backend/scope/rag/index.py` indexes synthetic fixtures, source-attributed official extracts, and user uploads; project `docs/` and `reports/` remain excluded. Official examples are U.S. FAR clauses and jurisdiction-specific. |
| BM25 | Implemented | `backend/scope/rag/bm25.py` implements Okapi BM25; RAG index stores BM25 statistics. |
| Dense embeddings | Active here; optional elsewhere | Fresh metadata reports `dense_available=true`, BGE small English vectors, dimension 384. Other environments may fall back. |
| Cross-encoder reranking | Active here; optional elsewhere | Fresh metadata reports `reranker_available=true`; per-query results now expose whether it actually ran. |
| Hybrid retrieval and evaluation | Implemented and rebuilt | Current stack is dense + Okapi BM25 + RRF + cross-encoder reranking. The 20-query gold-section benchmark has MRR 1.0 on the small synthetic corpus; this is not a production relevance claim. |
| LLM answer generation | Optional implementation | OpenAI-compatible chat-completions endpoint is supported through environment variables, with extractive fallback. No provider is configured by default in the checked-in requirements/config. Do not claim generated answers are active unless configured and verified. |
| Claim-level verification | Wired into RAG answers and investigations | RAG claims are checked against retrieved passages. Unsupported claims are excluded from answer text but remain in the response with verdicts. Investigation evidence stores the asserted claim and its passage; `checker_node` runs `verify_claims()`, updates failed ledger rows to `needs_review`, and makes the investigation status `needs_review`. |
| PDF upload | Implemented for text PDFs | Upload UI accepts PDF, Markdown, and text. `pypdf` extracts page-labelled text; encrypted, scanned/image-only, oversized, and malformed PDFs are rejected. OCR is not provided. |
| Corpus size and provenance | Partial | Eight synthetic fixtures plus source-attributed U.S. FAR extracts are present. FAR examples are authoritative only in their stated federal procurement context and do not represent every jurisdiction or private contract. |

### Agent workflow, evidence, and checker

| Item | Current status | Notes |
|---|---|---|
| Investigation graph | Implemented with conditional branches | Planner selects data analysis and/or document retrieval based on the query; Checker runs before report writing. |
| Autonomous planning | Basic branching implemented | Goal-sensitive routing chooses data, documents, or both. It is a small rule-based planner, not open-ended autonomous research or iterative tool planning. |
| Checker revision loop | One bounded retry implemented | Unsupported document claims are removed from the answer, retained in the evidence ledger as needs-review, and the remaining evidence is checked once more. API and UI expose revision history and excluded claims. |
| Checker evaluation | Human-labelled external benchmark added; results expose a major limitation | `reports/metrics/checker_claim_evaluation.json` now includes ContractNLI's human-annotated test split: 123 real NDAs, 2,091 claim/document labels (968 Entailment, 220 Contradiction, 903 NotMentioned). Accuracy 0.559, unsupported detection 0.881, false-positive rate 0.119, and supported-claim false-rejection rate 0.815. The benchmark is legal NDA text, not shipping policy; neutral cases use BM25-retrieved passages, so results are a transfer stress test, not universal accuracy. Dataset attribution/license details are in the JSON report. The older synthetic corruption result is separate and remains unsuitable as semantic-accuracy evidence. |
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
4. PDF upload now extracts selectable text with page markers; do not imply OCR or scanned-PDF support.
5. State that LLM generation is optional and only active when configured; otherwise the extractive fallback is used.
6. Describe planning as rule-based branching and a single bounded Checker retry; scheduled analysis remains unimplemented.

## Remaining work, in priority order

1. **Obtain domain-specific human labels** for shipping/procurement policies and independently authored claims; ContractNLI provides genuine human labels but its NDA domain is not a substitute for this review.
2. **Add OCR** only if scanned/image-only PDFs are a required upload format.
3. **Expand planner capabilities** only if autonomous multi-step research is required; current goal-based branching and one retry are bounded implementations.
4. **Either implement job scheduling or remove the scheduling claim.**
5. **Add Alembic and frontend/API integration tests** if required by the proposal/deployment target.

## Verdict

All pipeline phases have been rerun and the model/evaluation artifacts regenerated. Duration selection and vendor-KPI results now agree across fresh outputs. The rebuilt RAG index reports dense, BM25, and reranker active here; query results and the frontend now expose the components actually used. Claim verification is wired into answers and investigations. The human-labelled ContractNLI evaluation reports 55.9% accuracy and 81.5% false rejection of supported claims, making clear that Checker semantics need substantial improvement. PDF text extraction/upload and bounded planner branching/revision are implemented; OCR and domain-specific human review remain open.

The remaining evidence gap is domain-specific human-labelled evaluation on shipping/procurement policy documents. Autonomous research beyond simple branching and one retry, OCR, scheduling, Alembic migrations, and frontend/API integration coverage remain unimplemented.
