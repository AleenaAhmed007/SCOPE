# An Evidence-Grounded Agentic AI System for Supply Chain Disruption Detection

**Working title.** System name: **SCOPE** (Supply Chain Operations and Predictive Evidence System).

**Primary dataset.** USAID Supply Chain Management System (SCMS) shipment extract with inventory-related fields (`SCMS_with_inventory.csv`; 10,324 rows × 45 columns).

---

## 1. Introduction

Global health and commercial supply chains depend on many vendors, manufacturing sites, shipment modes, and contractual delivery dates. When deliveries slip, stockouts, programme delays, and costly expediting follow. Most operational dashboards remain *retrospective*: they describe what already happened. Standalone predictive models can estimate risk, but they rarely attach claims to auditable operational records or policy documents. Conversely, large language models can narrate a delay investigation fluently, yet without grounding they may invent causes, thresholds, or contractual obligations.

This gap motivates **SCOPE**—an integrated system that couples (i) leakage-aware predictive machine learning on structured shipment data, (ii) vendor and anomaly analytics, (iii) retrieval-augmented generation (RAG) over supply-chain documents, and (iv) an agentic investigation workflow that stores and checks evidence before surfacing explanations to analysts.

### 1.1 Problem statement

Supply-chain disruption detection is not a single binary classifier. Practitioners need simultaneous answers to:

1. **Will this line item likely be late?** (classification before the outcome is known)
2. **How long might fulfilment take?** (duration estimation)
3. **Is the late rate or volume regime shifting?** (time-series monitoring)
4. **Which vendors behave alike, and which periods look unusual?** (segmentation / anomaly signals)
5. **What policy or contract language supports or constrains the claim?** (document grounding)
6. **Can each generated claim be traced and validated?** (evidence ledger and checker)

Prior work often treats these layers in isolation. SCOPE’s research goal is to show that they can be engineered as one reproducible pipeline with explicit temporal leakage controls, baseline comparisons, and measurable evaluation—not as an opaque chatbot over a spreadsheet.

### 1.2 Research question

> How can an evidence-grounded agentic AI system combine predictive machine learning, operational supply-chain data, and document-based retrieval to detect and investigate potential delivery disruptions in a way that is chronologically valid, explainable, and auditable?

### 1.3 Objectives

1. Audit a real SCMS-style shipment dataset for quality, chronology, and inventory-field reliability.
2. Build a **late-delivery classifier** using only features available before delivery outcome, with chronological train/validation/test splits and class-imbalance handling.
3. Evaluate **delivery-duration regression** against a strong median baseline.
4. Train **monthly forecasts** for late rate and shipment volume with naive/mean baselines and rolling-origin selection.
5. Produce **vendor segments** and **anomaly scores** as investigative signals (not labelled fraud scores).
6. Attach **SHAP** explanations to the primary late model.
7. Implement **hybrid RAG**, an **evidence ledger**, a **claim checker**, and a **LangGraph** multi-agent investigation flow behind a FastAPI/React interface.
8. Report metrics with explicit limitations (especially for inventory fields and synthetic documents).

### 1.4 Contributions

- An end-to-end, phase-structured architecture (data audit → ML → explainability → RAG → evidence → agents → UI) for supply-chain disruption support.
- A leakage-aware late-delivery modelling protocol on SCMS (chronological split; train-only vendor history; outcome fields excluded).
- Empirical finding that a **random forest** late model reaches test ROC-AUC ≈ **0.81** and PR-AUC ≈ **0.31** at ~12% late prevalence, while duration and volume forecasting remain close to classical baselines—guiding honest system claims.
- An evidence path (ledger + checker + agent workflow) that separates *model scores* from *document-supported claims*.

### 1.5 Paper organisation

Section 2 reviews related work (predictive logistics, XAI, RAG, agents). Section 3 details data and methods. Section 4 reports results. Section 5 discusses limitations and deployment implications. Section 6 concludes.

---

## 2. Methodology

### 2.1 Dataset and provenance

| Item | Detail |
|---|---|
| Source file | `data/raw/SCMS_with_inventory.csv` (immutable; checksum recorded in provenance) |
| Domain | USAID SCMS-style pharmaceutical / health commodity shipments |
| Size | 10,324 shipments; 45 columns; ~73 vendors; ~43 countries (Phase 01 audit) |
| Late label | \(y=1\) if *Delivered to Client Date* > *Scheduled Delivery Date*; else 0 |
| Observed late rate | ≈ **11.5%** on valid schedule–delivery pairs |
| Inventory fields | Treated as **augmented / unverified** relative to classic SCMS; used only in a labelled experimental track with leakage controls |

Date placeholders (e.g. `Date Not Captured`, `N/A - From RDC`) are flagged and never coerced into fake timestamps. Raw CSV is never overwritten; transforms land in interim/processed layers.

### 2.2 Overall system architecture

SCOPE is implemented as a phased Python backend (`backend/scope`) with:

1. **Structured path:** preprocess → late classification → duration regression → forecasting → vendor clustering → anomaly detection → optional inventory experiment → SHAP.
2. **Unstructured path:** document corpus (official FAR excerpts + clearly marked synthetic policies) → hybrid RAG index.
3. **Evidence path:** PostgreSQL ledger of evidence items; checker that validates extractive / corrupted claims in controlled evaluations.
4. **Agent path:** LangGraph workflow that plans an investigation, pulls ML findings and documents, and records evidence IDs.
5. **Interface:** FastAPI services + React frontend.

Evaluation artefacts are written under `reports/metrics/` and summarised in a final defence report.

### 2.3 Preprocessing and leakage control

**Chronological split.** Rows are ordered by parsed *Scheduled Delivery Date* and assigned to train / validation / test in approximately 70% / 15% / 15% proportions. Stratification by label is configured where compatible with the time order; the governing principle is *time*, not random shuffle, to avoid future leakage.

**Prediction moment (late model).** Features must be knowable *before* the delivery outcome. Forbidden inputs include actual delivery timestamps, `delay_days` / `is_late`, and post-outcome inventory shortage fields used as features for predicting shortage.

**Vendor history.** Expanding historical late rate and median delay are computed from **outcomes already known before** each row’s scheduled date, using training-period statistics only for the attached train-time view—no peeking into validation/test futures.

**Imputation / encoding.** Numeric median imputation and categorical unknown/most-frequent handling inside scikit-learn column transformers; calendar features from the scheduled date (month, quarter, day-of-week); numeric parses of weight/freight with non-numeric flags.

### 2.4 Late-delivery classification

**Task.** Binary classification of `is_late`.

**Candidates.** Logistic regression, random forest, and XGBoost (proposal comparison). Class imbalance is addressed with class weights / `scale_pos_weight` rather than synthetic oversampling (SMOTE was trialled in development and not retained for the primary protocol).

**Thresholding.** Probabilities are calibrated (Platt scaling on validation where enabled). The operating threshold maximises validation F1 (or an equivalent F1-oriented search), then frozen for the test report.

**Baselines.** (i) prevalence-only ranking for PR-AUC context; (ii) vendor-history-only score; (iii) rolling-origin / walk-forward refits on unseen quarters with recalibration.

**Primary metrics.** ROC-AUC, PR-AUC, precision, recall, F1, calibration (ECE / Brier). On the SCMS holdout, the selected **random forest** achieved approximately ROC-AUC **0.807**, PR-AUC **0.307**, recall **0.825**, precision **0.292**, F1 **0.431** (test late prevalence ≈ 0.118).

### 2.5 Delivery-duration regression

**Target.** Days from *PO Sent to Vendor Date* to *Delivered to Client Date* on plausible rows (extreme values capped using the training 99th percentile).

**Models.** Dummy median baseline, gradient boosting, XGBoost, random forest. Selection prefers beating the median on validation; if ML does not reliably beat the median under walk-forward checks, the system may serve the historical median and flag it as a baseline.

**Metrics.** MAE, RMSE, \(R^2\), median absolute error.

### 2.6 Time-series forecasting

Monthly series are built for (a) shipment-count-weighted **late rate** and (b) **volume** (line-item quantity proxy—not verified warehouse demand).

**Protocol.** Lag features (1–4) and rolling means; expanding-window / rolling-origin candidate selection on validation MAE; preference for naive lag-1 or mean baselines when complex models are not clearly better (≈2% tolerance). ARIMA is included as a classical candidate. Neural sequence models are only recommended when monthly history and validation gain justify them; on SCMS monthly length they are not required for the primary claim.

**Metrics.** MAE / RMSE vs naive and mean; shipment-count weighting for late-rate errors.

### 2.7 Vendor segmentation and anomaly detection

- **Segmentation.** K-Means on vendor KPI features (e.g. late rate, volume, lead-time summaries), with insufficient-history and profile-outlier vendors separated before clustering; silhouette reported descriptively.
- **Anomalies.** Isolation Forest variants for unusual shipment profiles, retrospective flags, and vendor–quarter KPI deterioration—treated as **investigative signals**, not labelled accuracy scores.

### 2.8 Inventory experiment (feasibility only)

Inventory columns are audited for constancy and arithmetic consistency. A stockout-flag proxy classifier is trained **without** using the two operands of the deterministic label rule. Results are reported as experimental and are **not** operational inventory claims.

### 2.9 Explainability

SHAP values are computed for the selected late-delivery pipeline on a bounded sample to attribute local and global feature influence for analyst review.

### 2.10 RAG, evidence ledger, checker, and agents

- **RAG.** Chunked documents indexed with hybrid retrieval (BM25 required; dense embeddings and cross-encoder reranking when available). Synthetic policy documents are labelled as synthetic; official FAR excerpts are stored separately.
- **Evidence ledger.** PostgreSQL store for evidence items linked to investigations.
- **Checker.** Validates claims against retrieved text under controlled corpus-corruption tests (reported detection / false-positive rates are for that protocol, not free-form factuality).
- **Agents.** A LangGraph workflow plans investigation steps, gathers ML and document findings, and emits a structured investigation record with evidence IDs.

### 2.11 Implementation and reproducibility

- Language / stack: Python 3.11–3.13, scikit-learn / XGBoost, FastAPI, React, PostgreSQL, LangGraph.
- Configuration via YAML (`configs/data.yaml`); pipeline orchestration via `scripts/run_all_phases.py`.
- Random seed fixed (default 42) for stochastic estimators where applicable.
- Metrics and model bundles written under `reports/` for audit.

### 2.12 Ethical and validity notes

1. Inventory provenance is unverified—do not generalise inventory metrics to real warehouse truth.
2. Synthetic RAG documents must not be presented as authentic contracts.
3. Late prevalence shifts across time; a single test split understates temporal variance (hence walk-forward reporting).
4. Precision at high recall remains limited by base rate and threshold choice; the system is framed as decision support, not autonomous fulfilment control.

---

## Suggested figure captions (for the paper)

- **Figure 1.** SCOPE architecture: structured ML path, document RAG path, evidence/checker path, and agent UI.
- **Figure 2.** Chronological split and prediction-time feature boundary for late delivery.
- **Figure 3.** Late-model ROC/PR curves vs vendor-history baseline.
- **Figure 4.** Walk-forward quarterly ROC for the late model.

## Suggested table captions

- **Table 1.** Dataset statistics and late-label definition.
- **Table 2.** Late-delivery model comparison (validation + test).
- **Table 3.** Duration and monthly forecast results vs baselines.
- **Table 4.** System-component evaluation scope and limitations.
