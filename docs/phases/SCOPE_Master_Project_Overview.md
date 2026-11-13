# SCOPE — Master Project Overview and System Architecture

**Project Name:** SCOPE — Supply Chain Operations and Predictive Evidence System

**Research Title:** An Evidence-Grounded Agentic AI System for Supply Chain Disruption Detection

**Document Type:** Master Project Overview, Technical Architecture, Data Strategy, and Implementation Blueprint

**Version:** 1.0

---

# 1. Project Overview

## 1.1 What is SCOPE?

SCOPE (Supply Chain Operations and Predictive Evidence System) is an AI-powered supply chain intelligence platform designed to identify potential supply chain disruptions, predict delivery risks, analyze vendor performance, detect unusual operational patterns, and provide evidence-supported explanations.

The system combines traditional Machine Learning, time-series analysis, explainable AI, Retrieval-Augmented Generation (RAG), and agentic AI into one integrated application.

Instead of relying only on predictive models or a general-purpose chatbot, SCOPE combines:

1. Operational data analysis.
2. Predictive Machine Learning models.
3. Vendor segmentation.
4. Anomaly detection.
5. Delivery performance forecasting.
6. Document-based knowledge retrieval.
7. Evidence tracking and validation.
8. Agentic AI investigation and reporting.

The main purpose is to move from reactive supply chain monitoring towards evidence-grounded, predictive, and explainable decision support.

## 1.2 The Problem We Are Solving

Supply chains involve multiple vendors, purchase orders, manufacturing locations, shipment activities, delivery schedules, and operational dependencies.

Disruptions can occur because of:

- Delayed shipments.
- Vendor performance problems.
- Longer-than-expected delivery durations.
- Unusual operational patterns.
- Inventory shortages.
- Documentation and policy-related issues.
- Incomplete or inconsistent operational information.

Traditional reporting systems generally describe what has already happened. Predictive models can estimate what might happen, but they do not necessarily explain the result using supporting business documents.

General-purpose AI assistants can generate explanations, but their answers may not be grounded in actual operational records or authoritative documents.

SCOPE addresses these limitations by connecting predictive models, operational records, business documents, and evidence validation into one workflow.

## 1.3 Main Research Question

How can an evidence-grounded agentic AI system combine predictive Machine Learning, operational supply chain data, and document-based knowledge retrieval to detect and investigate potential supply chain disruptions?

## 1.4 Research Objectives

The main objectives are:

1. Audit and understand the available supply chain dataset.
2. Identify relevant operational patterns and data-quality problems.
3. Develop a Machine Learning model for late-delivery prediction.
4. Estimate delivery duration using regression.
5. Explore time-series forecasting where sufficient temporal data exists.
6. Segment vendors according to their operational characteristics.
7. Detect unusual supply chain records using anomaly detection.
8. Investigate whether inventory-related prediction is scientifically and technically feasible.
9. Explain model predictions using SHAP.
10. Develop a document retrieval system using RAG.
11. Build an Evidence Ledger to store supporting evidence.
12. Develop a Checker component to validate evidence and generated claims.
13. Implement a multi-agent investigation workflow using LangGraph.
14. Integrate all components through FastAPI.
15. Develop a complete React.js frontend.
16. Evaluate the system using measurable ML, retrieval, evidence, and end-to-end metrics.

---

# 2. Overall System Concept

SCOPE will operate as an integrated supply chain intelligence platform.

The system will accept two main categories of information:

**A. Structured operational data**

Examples:

- Purchase order information.
- Vendor information.
- Shipment information.
- Manufacturing site information.
- Scheduled delivery dates.
- Actual delivery dates.
- Inventory-related fields, subject to data-quality validation.

**B. Unstructured business documents**

Examples:

- Supplier contracts.
- Service Level Agreements (SLAs).
- Supply chain policies.
- Delivery requirements.
- Vendor agreements.
- Operational procedures.

These two information sources will be processed separately and combined during investigation.

The Machine Learning system will generate predictions and analytical findings. The RAG system will retrieve relevant business documents. The Evidence Ledger will preserve references to supporting information. The Checker will validate claims and evidence. LangGraph will coordinate the investigation workflow.

The final output will be available through a React-based web application.

---

# 3. Dataset Overview

## 3.1 Primary Dataset

**Dataset Name:** SCMS_with_inventory.csv

**Dataset Type:** Structured supply chain operational dataset.

**File Format:** CSV

**Primary Purpose:** Supply chain analysis, delivery-risk prediction, delivery-duration estimation, vendor intelligence, anomaly detection, and inventory-data feasibility assessment.

The dataset is the primary structured data source for SCOPE.

## 3.2 Preliminary Dataset Information

An earlier inspection of the dataset indicated approximately:

| Attribute | Preliminary observation |
|---|---:|
| Total records | 10,324 |
| Total columns | 45 |
| Vendors | 73 |
| Countries | 43 |
| Manufacturing sites | 88 |

These values are preliminary observations, not final project statistics. They must be recalculated during Phase 01 using the actual dataset.

## 3.3 Dataset Audit Requirements

Before developing any Machine Learning model, the dataset must be audited.

The audit will examine:

- Total number of rows and columns.
- Column names and data types.
- Missing values.
- Duplicate records.
- Unique values.
- Categorical distributions.
- Numerical distributions.
- Date parsing success.
- Invalid date values.
- Outliers.
- Constant columns.
- Target variable availability.
- Possible target leakage.
- Data provenance and reliability.

No model should be developed using assumptions about data quality.

## 3.4 Important Data Quality Concerns

The preliminary inspection identified several issues that require further investigation.

### A. Mixed Date Formats

Some date fields may contain:

- Valid date values.
- Missing values.
- Different date formats.
- Placeholder text such as `N/A - From RDC`.
- Values such as `Date Not Captured`.

These values must be cleaned and converted carefully.

Invalid dates should not automatically be interpreted as zero or replaced with arbitrary dates.

### B. Inventory Field Reliability

Some inventory-related fields require special investigation.

Preliminary observations included:

- `Inventory_Stock_In` appeared to contain zero values in inspected records.
- `Inventory_Lead_Time_Days` appeared constant at 30 in inspected records.
- `Inventory_Stockout_Flag` appeared aligned with `Inventory_Shortage_Quantity > 0`.

These observations must be verified across the complete dataset.

If an inventory variable is constant, derived from the target, or has uncertain provenance, it must not be treated as a reliable predictive feature.

### C. Potential Target Leakage

A feature may contain information that would not be available at the time a real prediction is made.

For example, actual delivery dates cannot be used as predictors for a prediction made before delivery.

Similarly, a stockout flag derived from shortage quantity should not be used to predict that same shortage outcome.

All model features must be selected according to the intended prediction time.

### D. Data Provenance

The source and meaning of each inventory-related field must be documented.

If fields have been added or augmented, the documentation must distinguish original dataset information from derived or externally introduced information.

No synthetic or augmented information should be presented as original operational evidence.

---

# 4. Main Dataset Fields and Their Purpose

The following fields are important examples to investigate. Their exact availability, data types, and meanings must be confirmed from the actual CSV header and data dictionary.

## 4.1 Purchase Order Information

Potential fields:

- `PO_ID`
- `PO_Ref`
- `PO_Date`
- `PO_Approved_Date`
- `PO_Status`

Purpose:

- Identify purchase orders.
- Analyze procurement activity.
- Understand order timelines.
- Connect purchase orders with delivery outcomes.

## 4.2 Vendor Information

Potential fields:

- `Supplier`
- `Vendor`
- `Vendor_ID`
- `Country`
- `Manufacturing_Site`

Purpose:

- Analyze vendor performance.
- Compare delivery patterns.
- Identify vendor-level risk indicators.
- Perform vendor segmentation.

The actual field names must be verified. The system must not assume that every example above exists in the CSV.

## 4.3 Shipment and Delivery Information

Potential fields:

- `Scheduled_Delivery_Date`
- `Delivered_to_Client_Date`
- `Shipment_Mode`
- `Shipment_Reference`
- `Delivery_Status`

Purpose:

- Analyze delivery performance.
- Create the late-delivery target.
- Estimate delivery duration.
- Identify unusual delivery patterns.

## 4.4 Product Information

Potential fields may include:

- Product name or code.
- Item description.
- Product group.
- Quantity.
- Unit price.
- Manufacturing information.

Purpose:

- Analyze product-level patterns.
- Understand order composition.
- Explore relationships between product characteristics and delivery performance.

## 4.5 Inventory Information

Potential fields:

- `Inventory_Stock_In`
- `Inventory_Lead_Time_Days`
- `Inventory_Stockout_Flag`
- `Inventory_Shortage_Quantity`

Purpose:

- Investigate inventory shortages.
- Explore inventory-related risk.
- Assess whether reliable inventory prediction is possible.

These fields must pass the data-quality, provenance, and leakage audit before being used for predictive modeling.

---

# 5. Data Preprocessing and Feature Engineering

The preprocessing pipeline will convert raw operational records into a reliable modeling dataset.

## 5.1 Data Cleaning

Tasks:

1. Load the CSV using Pandas.
2. Inspect data types.
3. Standardize column names where appropriate.
4. Remove or investigate duplicate records.
5. Handle missing values.
6. Normalize categorical values.
7. Parse date columns.
8. Identify invalid records.
9. Check constant and near-constant columns.
10. Document every transformation.

## 5.2 Date Processing

Convert valid date fields into appropriate datetime types.

Potential derived features:

- Purchase order year.
- Purchase order month.
- Purchase order quarter.
- Purchase order weekday.
- Scheduled delivery month.
- Scheduled delivery weekday.
- Procurement-to-scheduled-delivery duration, where meaningful.
- Actual delivery duration, for analysis or as a regression target.

Invalid or missing dates must remain identifiable.

## 5.3 Target Engineering

### Late Delivery Classification

A binary target can be created using:

\[
LateDelivery =
\begin{cases}
1, & DeliveredDate > ScheduledDate \\
0, & DeliveredDate \leq ScheduledDate
\end{cases}
\]

The target can only be created when both dates are valid and comparable.

Records with invalid or missing delivery dates should be handled separately rather than automatically labelled as on-time.

### Delivery Duration Regression

The regression target will estimate the elapsed time between purchase order date and client delivery date:

\[
DeliveryDuration =
DeliveredToClientDate - PODate
\]

This is the overall observed purchase-order-to-client delivery duration. It must not be described as pure supplier procurement lead time unless the dataset supports that interpretation.

## 5.4 Feature Engineering Rules

Possible features include:

- Vendor.
- Country.
- Manufacturing site.
- Shipment mode.
- Product category.
- Order quantity.
- Purchase order month.
- Purchase order quarter.
- Historical vendor delivery performance.
- Historical late-delivery rate.

Historical features must be calculated using information available before the prediction date.

The preprocessing pipeline must prevent future information from entering training features.

---

# 6. Machine Learning Models

SCOPE will contain multiple analytical models. Each model will have a specific task and evaluation strategy.

## 6.1 Late Delivery Classification

<ins>Primary Model: XGBoost Classifier</ins>

**Problem Type:** Binary classification.

**Objective:** Predict whether a purchase order is likely to be delivered later than its scheduled delivery date.

Target:

- 0 = On time.
- 1 = Late.

Why XGBoost?

- Handles nonlinear relationships.
- Supports complex feature interactions.
- Works effectively with structured tabular data.
- Provides feature-importance and SHAP compatibility.

Comparator:

**Random Forest Classifier**

Random Forest will provide a comparison against the primary XGBoost model.

Evaluation metrics:

- Accuracy.
- Precision.
- Recall.
- F1-score.
- ROC-AUC.
- PR-AUC.
- Confusion matrix.

Because late deliveries may be less frequent than on-time deliveries, accuracy alone will not be sufficient.

The preferred model will be selected using appropriate validation metrics and business requirements.

## 6.2 Delivery Duration Regression

**Primary Candidate:** Gradient Boosting Regressor.

**Objective:** Estimate the number of days between purchase order date and client delivery date.

Target:

\[
y = DeliveryDurationDays
\]

Potential inputs:

- Vendor.
- Country.
- Manufacturing site.
- Shipment mode.
- Product information.
- Order quantity.
- Historical performance features.

Evaluation metrics:

- MAE.
- RMSE.
- R².

The model estimates historical delivery duration patterns. It does not automatically establish a causal relationship between vendor characteristics and delivery delays.

## 6.3 Time-Series Forecasting

**Candidate Model:** LSTM.

**Objective:** Forecast future supply chain patterns where sufficient time-series observations are available.

Potential forecasting targets:

- Monthly order volume.
- Monthly late-delivery counts.
- Monthly late-delivery rate.
- Delivery duration trends.

Before using LSTM, the dataset must be checked for:

- Sufficient time coverage.
- Regular or appropriately resampled time intervals.
- Enough observations.
- Reliable timestamp information.
- Appropriate forecasting targets.

Baseline models must be included, such as:

- Naive forecasting.
- Moving average.
- Exponential smoothing.

If the available dataset does not provide sufficient time-series support, LSTM will not be forced into the project. The forecasting experiment will document this limitation and use suitable simpler alternatives.

Evaluation metrics:

- MAE.
- RMSE.
- MAPE, only where the target values make it appropriate.

## 6.4 Vendor Segmentation

**Model:** K-Means Clustering.

**Problem Type:** Unsupervised learning.

**Objective:** Group vendors according to their operational performance characteristics.

Potential aggregation features:

- Number of purchase orders.
- Historical late-delivery rate.
- Average delivery duration.
- Delivery-duration variability.
- Order volume.
- Other validated vendor-level metrics.

Potential segments may include:

- Higher-performing vendors.
- Average-performing vendors.
- Higher-risk vendors.

These are descriptive cluster interpretations, not guaranteed business categories.

Important steps:

1. Aggregate data at vendor level.
2. Handle missing values.
3. Scale numerical features.
4. Evaluate candidate cluster counts.
5. Use silhouette score and other suitable diagnostics.
6. Interpret clusters using actual feature profiles.

## 6.5 Anomaly Detection

**Model:** Isolation Forest.

**Problem Type:** Unsupervised anomaly detection.

**Objective:** Identify unusual supply chain records that may deserve further investigation.

Potential anomalies:

- Unusually long delivery duration.
- Unusual order quantity.
- Rare combinations of operational features.
- Unexpected vendor performance patterns.
- Unusual delivery-related values.

An anomaly is not automatically a disruption, fraud, or operational failure.

The system will describe anomalies as records that differ from learned patterns and require human or evidence-based investigation.

## 6.6 Inventory Prediction Experiment

**Objective:** Determine whether the available inventory-related fields support a reliable predictive task.

Potential targets:

- Inventory shortage.
- Stockout occurrence.
- Shortage quantity.

Before training any model:

1. Verify field definitions.
2. Confirm data provenance.
3. Examine missingness and variation.
4. Check whether the target is derived from another field.
5. Identify which predictors would be available before the target event.
6. Check for target leakage.
7. Determine whether enough reliable observations exist.

If these conditions are not satisfied, SCOPE will document an inventory-model feasibility result rather than produce an unreliable model.

This is a valid research outcome.

---

# 7. Explainable AI — SHAP

**Technology:** SHAP (SHapley Additive exPlanations).

The purpose of SHAP is to explain how input features contribute to model predictions.

SCOPE will use SHAP to investigate:

- Which features influence late-delivery predictions.
- Which features contribute to delivery-duration estimates.
- How individual order predictions are influenced.
- Whether model behaviour appears reasonable.
- Whether unexpected feature dependence exists.

Planned visualizations:

- SHAP summary plot.
- SHAP bar plot.
- SHAP waterfall plot.
- Individual prediction explanation.

SHAP explanations describe model behaviour. They do not prove that a feature causes late delivery.

For every explanation, the system should retain:

- Model name.
- Model version.
- Prediction ID.
- Feature values.
- Explanation output.
- Prediction timestamp.

---

# 8. Retrieval-Augmented Generation (RAG)

## 8.1 What is RAG?

Retrieval-Augmented Generation is a method that combines document retrieval with a language model.

Instead of answering only from the language model's internal knowledge, the system retrieves relevant information from a document collection and uses that information to construct an answer.

## 8.2 Purpose in SCOPE

The RAG component will provide document-based evidence for supply chain investigations.

Example questions:

- What does the supplier agreement say about delivery delays?
- What is the required delivery timeline?
- What actions are specified for repeated late deliveries?
- Which SLA clause applies to a particular vendor?
- What does the supply chain policy state about shortages?

## 8.3 Document Sources

Potential documents:

- Supplier contracts.
- Service Level Agreements.
- Supply chain policies.
- Procurement guidelines.
- Delivery procedures.
- Vendor agreements.

Documents must be identified by their real source.

If documents are synthetic or created for testing, they must be clearly labelled as synthetic. They must never be presented as genuine contracts or operational evidence.

## 8.4 RAG Pipeline

The pipeline will contain:

1. Document upload.
2. Text extraction.
3. Document metadata extraction.
4. Text cleaning.
5. Document chunking.
6. Embedding generation.
7. Vector indexing.
8. Keyword indexing.
9. Hybrid retrieval.
10. Optional reranking.
11. Context construction.
12. LLM response generation.
13. Citation generation.

## 8.5 Chunking Strategy

Documents will be divided into smaller text chunks.

Each chunk should preserve useful metadata:

- Document ID.
- Document name.
- Document type.
- Vendor, if applicable.
- Page number, where available.
- Section heading, where available.
- Chunk ID.
- Source location.

Chunk size and overlap will be tested rather than selected without evaluation.

## 8.6 Vector Database and Retrieval

**Preferred Vector Storage:** PostgreSQL with pgvector.

PostgreSQL will store:

- Document metadata.
- Chunk metadata.
- Evidence references.
- Vector embeddings, where pgvector is available.

If pgvector is unavailable in the deployment environment, FAISS may be used as a separate vector index, while document metadata and application records remain in PostgreSQL.

The application database will never switch to SQLite.

## 8.7 Hybrid Retrieval

SCOPE will combine:

- Semantic vector retrieval.
- BM25 or keyword retrieval.

The two result lists can be combined using Reciprocal Rank Fusion (RRF).

An optional reranker may improve the relevance of retrieved passages.

## 8.8 Citation Requirements

Every document-grounded answer should provide source references whenever available.

A citation should identify:

- Document name.
- Page number, where available.
- Relevant section or chunk.
- Evidence ID.

If the system cannot retrieve sufficient supporting information, it should state that the available documents do not provide enough evidence.

The language model must not invent document names, page numbers, or contract clauses.

---

# 9. Evidence Ledger

## 9.1 Purpose

The Evidence Ledger is a database-backed service that stores traceable references to information used during an investigation.

It is not an autonomous AI agent.

Its purpose is to make investigation results traceable and auditable.

## 9.2 Evidence Sources

Evidence may come from:

1. Operational dataset records.
2. Machine Learning predictions.
3. SHAP explanations.
4. Anomaly detection results.
5. Vendor segmentation results.
6. Retrieved document passages.
7. RAG citations.
8. Other validated analytical outputs.

## 9.3 Evidence Record Structure

Each evidence record should contain fields such as:

- Evidence ID.
- Investigation ID.
- Evidence type.
- Source type.
- Source record ID.
- Document ID, if applicable.
- Page number, if applicable.
- Model name, if applicable.
- Model version, if applicable.
- Evidence content or structured reference.
- Creation timestamp.
- Validation status.

Evidence should retain links to the underlying source instead of relying only on copied text.

---

# 10. Checker Component

## 10.1 Purpose

The Checker validates investigation outputs before they are presented as final findings.

It helps reduce unsupported claims, incorrect calculations, and citation errors.

## 10.2 Validation Responsibilities

The Checker will verify:

- Whether cited evidence exists.
- Whether document citations refer to valid source records.
- Whether numerical values match their underlying records.
- Whether prediction IDs and model versions are valid.
- Whether generated claims are supported by retrieved evidence.
- Whether the report contains unsupported conclusions.
- Whether the system distinguishes predictions from confirmed events.

## 10.3 Deterministic and Semantic Validation

The Checker will use two validation approaches.

**A. Deterministic validation**

Examples:

- Recalculate delivery duration.
- Verify a late-delivery label.
- Compare reported totals with database queries.
- Check whether an evidence ID exists.
- Validate model and prediction references.

**B. Semantic validation**

Examples:

- Determine whether a retrieved document actually supports a claim.
- Identify claims that go beyond the available evidence.
- Check whether an explanation accurately represents its source.

The Checker should flag uncertainty instead of automatically accepting every generated statement.

---

# 11. Agentic AI Architecture

## 11.1 Framework

**Framework:** LangGraph.

LangGraph will coordinate a structured multi-agent workflow.

The agents will work with defined responsibilities and shared investigation state.

## 11.2 Agent Roles

### Agent 1 — Planner Agent

Responsibilities:

- Understand the user's investigation request.
- Break the request into subtasks.
- Identify which tools and data sources are required.
- Create an investigation plan.
- Coordinate execution.

### Agent 2 — Data Analyst Agent

Responsibilities:

- Query relevant operational data.
- Retrieve ML predictions.
- Inspect vendor performance.
- Analyze anomaly results.
- Summarize structured data findings.

The agent must use approved backend services and tools rather than inventing numerical values.

### Agent 3 — Document Researcher Agent

Responsibilities:

- Search relevant business documents.
- Retrieve applicable SLA or policy passages.
- Identify supporting document citations.
- Return evidence references.

### Agent 4 — Report Writer Agent

Responsibilities:

- Combine validated operational findings.
- Combine document-based findings.
- Prepare an investigation report.
- Distinguish predictions, observations, and policy requirements.
- Include supporting evidence references.

### Agent 5 — Checker Agent

Responsibilities:

- Validate report claims.
- Check numerical accuracy.
- Check evidence references.
- Identify unsupported statements.
- Return validation findings.

The final report should be revised or flagged when important validation checks fail.

## 11.3 Evidence Ledger Is Not an Agent

The Evidence Ledger is a shared service used by the agents.

It stores and retrieves evidence records.

The Checker is responsible for validation, while the Ledger is responsible for evidence traceability.

## 11.4 Example Agentic Workflow

User query:

"Investigate why a particular purchase order may be delayed and identify the supporting evidence."

Workflow:

1. Planner Agent receives the request.
2. Planner identifies the relevant purchase order.
3. Data Analyst retrieves the order and vendor information.
4. Data Analyst requests the relevant prediction and anomaly findings.
5. Document Researcher retrieves relevant supplier agreement or SLA passages.
6. Evidence references are stored in the Evidence Ledger.
7. Report Writer prepares an initial investigation report.
8. Checker validates the calculations, claims, and citations.
9. Final report is returned to the frontend.

The system must distinguish a predicted delay from a confirmed delay.

---

# 12. Complete Technology Stack

The following is the planned technology stack for SCOPE.

## 12.1 Programming Languages

| Technology | Purpose |
|---|---|
| Python | Backend, ML, RAG, and agentic AI |
| TypeScript | React frontend |
| SQL | PostgreSQL queries and data operations |

## 12.2 Frontend

| Technology | Purpose |
|---|---|
| React.js | User interface |
| Vite | Frontend development and build tooling |
| TypeScript | Type safety |
| Tailwind CSS | Styling |
| React Router | Page navigation |
| Axios | API communication |
| Recharts | Charts and visualizations |
| Lucide React | Icons |
| React Hook Form | Form management |
| Zod | Frontend validation |

**Important:** React.js is the selected frontend framework. Streamlit is not part of the final application architecture.

## 12.3 Backend

| Technology | Purpose |
|---|---|
| FastAPI | REST API |
| Pydantic | Request and response validation |
| Uvicorn | ASGI server |
| SQLAlchemy | Database ORM |
| Alembic | Database migrations |
| psycopg | PostgreSQL driver |

## 12.4 Data Processing

| Library | Purpose |
|---|---|
| Pandas | Data manipulation |
| NumPy | Numerical processing |
| SciPy | Scientific calculations |
| Matplotlib | Visualizations |
| Seaborn | Exploratory visualizations |

## 12.5 Machine Learning

| Library | Purpose |
|---|---|
| Scikit-learn | Preprocessing, evaluation, clustering, anomaly detection |
| XGBoost | Late-delivery classification |
| SHAP | Model explanations |
| TensorFlow/Keras or PyTorch | LSTM experiment, if justified |

## 12.6 RAG and Agentic AI

| Technology | Purpose |
|---|---|
| LangChain components | Document and retrieval utilities, where useful |
| LangGraph | Multi-agent orchestration |
| Embedding model | Document and query embeddings |
| PostgreSQL | Persistent application and evidence storage |
| pgvector | Preferred vector storage |
| FAISS | Optional separate vector index |
| BM25 | Keyword retrieval |
| LLM provider | Language generation and reasoning |

The exact embedding model and LLM provider will be selected based on availability, cost, performance, and project requirements.

## 12.7 Database

**Selected Database: PostgreSQL**

Related technologies:

- SQLAlchemy.
- Alembic.
- psycopg.
- pgvector, where available.

PostgreSQL is the only application database.

SQLite must not be used for development, testing, fallback storage, or production persistence.

Automated tests should use an isolated PostgreSQL test database or schema.

## 12.8 Testing

| Library | Purpose |
|---|---|
| Pytest | Backend and ML tests |
| HTTPX | FastAPI endpoint tests |
| Vitest | Frontend unit tests |
| React Testing Library | React component tests |
| Playwright | End-to-end browser tests |

---

# 13. Overall System Architecture

```text
                    USER
                     |
                     v
           REACT.JS FRONTEND
             Vite + TypeScript
                     |
                     v
               FASTAPI
              REST API
                     |
        +------------+-------------+
        |            |             |
        v            v             v
   ML SERVICES   RAG SERVICES   LANGGRAPH
        |            |          AGENTS
        |            |             |
        v            v             |
   Predictions   Document Search  |
   Segmentation  Hybrid Retrieval  |
   Anomalies      Citations        |
   SHAP                            |
        |            |             |
        +------------+-------------+
                     |
                     v
               EVIDENCE LEDGER
                     |
                     v
                  CHECKER
                     |
                     v
             FINAL INVESTIGATION
                     |
                     v
               REACT FRONTEND

                     |
                     v
                 POSTGRESQL
          SQLAlchemy + Alembic
                 psycopg
                  pgvector
```

The architecture separates the user interface, API layer, analytical services, agent orchestration, and persistent storage.

---

# 14. React Frontend Application

The frontend will provide a central interface for all SCOPE capabilities.

## 14.1 Dashboard

Displays:

- Total purchase orders.
- Total vendors.
- Late-delivery percentage.
- Average delivery duration.
- Anomaly count.
- Risk distribution.
- Recent investigations.
- Model and data status.

All displayed metrics must be obtained from the backend.

## 14.2 Order Investigation

Allows users to:

- Search for an order.
- View purchase order details.
- View scheduled and actual delivery information.
- Request a late-delivery prediction.
- Request a delivery-duration estimate.
- View anomaly findings.
- Start an investigation.

## 14.3 Vendor Intelligence

Displays:

- Vendor information.
- Vendor-level performance.
- Delivery statistics.
- Vendor segments.
- Risk indicators.
- Historical performance charts.

## 14.4 Risk Analysis

Displays:

- Late-delivery predictions.
- Risk distributions.
- Prediction explanations.
- SHAP visualizations.
- Anomaly findings.
- Model versions.

## 14.5 Document Intelligence

Allows users to:

- Upload business documents.
- Search document content.
- Ask questions.
- View retrieved passages.
- Inspect citations.
- Review document metadata.

## 14.6 Agentic Investigation

Allows users to:

- Submit investigation queries.
- View investigation status.
- Inspect agent progress.
- Review structured data findings.
- Review document findings.
- Inspect evidence.
- View Checker validation.
- Read the final report.

## 14.7 Evidence Explorer

Allows users to inspect:

- Evidence IDs.
- Evidence types.
- Related investigations.
- Source records.
- Document references.
- Page numbers.
- Model versions.
- Validation status.

---

# 15. FastAPI Backend Architecture

FastAPI will provide the communication layer between React and the internal SCOPE services.

Planned endpoint groups:

## Health and System

- `GET /health`
- `GET /api/v1/system/status`

## Orders

- `GET /api/v1/orders`
- `GET /api/v1/orders/{order_id}`

## Vendors

- `GET /api/v1/vendors`
- `GET /api/v1/vendors/{vendor_id}`
- `GET /api/v1/vendors/segments`

## Predictions

- `POST /api/v1/predictions/late-delivery`
- `POST /api/v1/predictions/delivery-duration`
- `POST /api/v1/predictions/anomaly`

## Documents and RAG

- `POST /api/v1/documents/upload`
- `GET /api/v1/documents`
- `POST /api/v1/rag/query`

## Investigations

- `POST /api/v1/investigations`
- `GET /api/v1/investigations/{run_id}`
- `GET /api/v1/investigations/{run_id}/report`

## Evidence

- `GET /api/v1/evidence/{evidence_id}`
- `GET /api/v1/investigations/{run_id}/evidence`

These are planned API contracts. Their final request and response schemas will be defined during implementation.

---

# 16. PostgreSQL Database Design

PostgreSQL will provide persistent storage for application records and analytical metadata.

The final schema will be developed using SQLAlchemy models and Alembic migrations.

Potential logical tables include:

| Table | Purpose |
|---|---|
| orders | Purchase order and delivery information |
| vendors | Vendor information |
| predictions | Model prediction records |
| model_versions | Model version metadata |
| vendor_segments | Vendor clustering results |
| anomaly_results | Anomaly detection results |
| documents | Uploaded document metadata |
| document_chunks | Extracted document chunks |
| investigations | Investigation requests and status |
| agent_runs | Agent execution records |
| evidence | Evidence Ledger records |
| checker_results | Validation results |
| investigation_reports | Final investigation reports |

The actual database schema must be normalized and designed around verified source fields and application requirements.

If pgvector is enabled, embeddings may be stored in PostgreSQL alongside document chunk metadata.

---

# 17. Model Training and Prediction Workflow

The model lifecycle will follow a reproducible process.

1. Load the raw dataset.
2. Validate the dataset.
3. Run preprocessing.
4. Generate leakage-safe features.
5. Split the data appropriately.
6. Train candidate models.
7. Evaluate models.
8. Select the appropriate model.
9. Save the trained artifact.
10. Record the model version and metadata.
11. Load the model through the backend.
12. Generate predictions through FastAPI.
13. Store prediction records in PostgreSQL.
14. Make prediction outputs available to the React frontend.

Where time ordering matters, validation must use chronological splits rather than relying only on random splits.

Preprocessing must be fitted on training data and then applied to validation or test data.

Model artifacts must retain their preprocessing requirements and feature schema.

---

# 18. Evaluation Strategy

SCOPE will be evaluated at multiple levels.

## 18.1 Data Quality Evaluation

Measure and document:

- Missing-value rates.
- Duplicate records.
- Date parsing success.
- Invalid records.
- Constant columns.
- Feature reliability.
- Target validity.
- Leakage risks.

## 18.2 Classification Evaluation

Metrics:

- Precision.
- Recall.
- F1-score.
- ROC-AUC.
- PR-AUC.
- Confusion matrix.

## 18.3 Regression Evaluation

Metrics:

- MAE.
- RMSE.
- R².

## 18.4 Forecasting Evaluation

Metrics:

- MAE.
- RMSE.
- Appropriate percentage-based metrics where valid.

Compare the forecasting model against simple baselines.

## 18.5 Clustering Evaluation

Metrics and analysis:

- Silhouette score.
- Cluster size distribution.
- Cluster feature profiles.
- Interpretability.

## 18.6 Anomaly Detection Evaluation

Where labelled anomaly data is unavailable, evaluate:

- Anomaly score distribution.
- Stability.
- Sampled case review.
- Domain plausibility.
- Expert or manual assessment, where available.

Do not report precision or recall without reliable ground-truth labels.

## 18.7 RAG Evaluation

Metrics:

- Recall@k.
- MRR.
- Retrieval relevance.
- Citation correctness.
- Citation coverage.
- Answer faithfulness.

A test set of questions with expected supporting documents or passages should be prepared.

## 18.8 Evidence and Checker Evaluation

Evaluate:

- Evidence reference validity.
- Numerical consistency.
- Citation correctness.
- Unsupported-claim detection.
- Validation success rate.

## 18.9 Agentic Workflow Evaluation

Evaluate:

- Investigation completion rate.
- Correct tool selection.
- Evidence coverage.
- Report factuality.
- Numerical fidelity.
- Citation coverage.
- Latency.
- Failure handling.

## 18.10 Frontend and API Evaluation

Test:

- API response correctness.
- Frontend navigation.
- Form validation.
- Loading states.
- Error states.
- Document uploads.
- Investigation status updates.
- Evidence display.
- End-to-end user workflows.

No evaluation metric or model performance result should be invented. Actual results must be generated from executed experiments.

---

# 19. Example End-to-End Use Case

**Scenario:** A supply chain manager wants to investigate a purchase order that may be delivered late.

### Step 1 — User Request

The manager enters a purchase order ID in the React application.

### Step 2 — Data Retrieval

FastAPI retrieves the relevant order, vendor, and delivery information from PostgreSQL.

### Step 3 — Predictive Analysis

The late-delivery model estimates the risk of late delivery.

The regression model estimates delivery duration, where applicable.

### Step 4 — Explainability

SHAP provides an explanation of the model prediction.

### Step 5 — Anomaly Analysis

The anomaly detection service checks whether the order has unusual characteristics.

### Step 6 — Document Retrieval

The Document Researcher retrieves relevant supplier agreement and SLA passages through RAG.

### Step 7 — Evidence Collection

The Evidence Ledger records references to the operational records, predictions, explanations, and document passages.

### Step 8 — Validation

The Checker verifies calculations, source references, and evidence support.

### Step 9 — Final Report

The Report Writer prepares a report containing:

- Order summary.
- Vendor information.
- Predicted delivery risk.
- Delivery-duration estimate, where available.
- Relevant model explanation.
- Anomaly findings.
- Supporting document citations.
- Evidence references.
- Validation findings.
- Uncertainties and limitations.

### Step 10 — User Interface

The React frontend displays the completed investigation.

The report must distinguish:

- Confirmed historical facts.
- Model-generated predictions.
- Retrieved policy or contract requirements.
- Inferences.
- Unverified hypotheses.

---

# 20. Project Folder Structure

The planned repository structure is:

```text
SCOPE/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── types/
│   │   ├── utils/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── backend/
│   ├── scope/
│   │   ├── api/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── database/
│   │   ├── ml/
│   │   ├── rag/
│   │   ├── agents/
│   │   ├── evidence/
│   │   └── checker/
│   ├── alembic/
│   ├── tests/
│   └── requirements.txt
│
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── external_documents/
│
├── notebooks/
│   ├── 01_data_audit.ipynb
│   ├── 02_eda.ipynb
│   ├── 03_preprocessing.ipynb
│   ├── 04_classification.ipynb
│   ├── 05_regression.ipynb
│   ├── 06_forecasting.ipynb
│   ├── 07_vendor_segmentation.ipynb
│   ├── 08_anomaly_detection.ipynb
│   ├── 09_inventory_experiment.ipynb
│   └── 10_shap_explainability.ipynb
│
├── models/
│   ├── classification/
│   ├── regression/
│   ├── forecasting/
│   └── artifacts/
│
├── documents/
│   ├── project_overview/
│   ├── research/
│   ├── architecture/
│   └── phases/
│
├── tests/
│
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

The actual repository can be adjusted during implementation. Existing working files and modules should be preserved.

---

# 21. Project Implementation Phases

The development process will follow these phases:

| Phase | Name | Main Outcome |
|---|---|---|
| 00 | Repository Setup | Project structure and environment |
| 01 | Dataset Audit and EDA | Data-quality report and exploratory analysis |
| 02 | Preprocessing and Feature Engineering | Clean and leakage-safe modeling data |
| 03 | Late Delivery Classification | XGBoost and Random Forest comparison |
| 04 | Delivery Duration Regression | Delivery-duration prediction model |
| 05 | Time-Series Forecasting | Forecasting experiment and baseline comparison |
| 06 | Vendor Segmentation and Anomaly Detection | Vendor clusters and anomaly results |
| 07 | Inventory Prediction Experiment | Feasibility audit and conditional model |
| 08 | SHAP Explainability | Model explanation outputs |
| 09 | RAG Document Retrieval | Document ingestion and hybrid retrieval |
| 10 | Evidence Ledger and Checker | Evidence storage and validation |
| 11 | LangGraph Agentic AI Workflow | Multi-agent investigation |
| 12 | React Frontend and FastAPI Integration | Complete web application |
| 13 | Evaluation, Testing, and Final Defence | Evaluation results and final presentation |

The phases will be implemented in order where dependencies require it. Some activities may overlap after their prerequisites are satisfied.

---

# 22. Research Contribution

SCOPE aims to demonstrate an integrated approach to supply chain disruption detection.

Its research contribution is based on combining:

1. Predictive analysis of supply chain delivery risk.
2. Explainable Machine Learning.
3. Vendor performance segmentation.
4. Unsupervised anomaly detection.
5. Document-grounded retrieval.
6. Traceable evidence management.
7. Validation of generated claims.
8. Multi-agent investigation and reporting.

The central research idea is not simply to create a chatbot or train a prediction model.

It is to create a system in which predictive findings and document-based information can be combined into an investigation, with supporting evidence and validation before the final report is presented.

Any claimed improvement over existing approaches must be supported by experiments and comparisons.

---

# 23. Important Research Limitations

The following limitations must be acknowledged.

## 23.1 Dataset Limitations

The available dataset may not contain every variable needed to explain real-world supply chain disruptions.

Some operational fields may be missing, inconsistent, or unreliable.

## 23.2 Historical Data

Historical patterns do not guarantee future supply chain behaviour.

Model predictions are estimates, not confirmed future events.

## 23.3 Inventory Data

Inventory prediction depends on reliable and sufficiently detailed inventory information.

If the current dataset does not support a valid task, the project will document that limitation rather than make unsupported claims.

## 23.4 Forecasting Data

A dataset with limited historical coverage may not support a reliable LSTM model.

Simpler forecasting baselines will be preferred when appropriate.

## 23.5 RAG Document Availability

RAG quality depends on the availability, quality, and relevance of the source documents.

Synthetic documents may be used for controlled demonstrations, but must be labelled clearly.

## 23.6 Explainability

SHAP explains model behaviour but does not establish causality.

## 23.7 Agentic AI

An agentic workflow can make incorrect decisions or generate unsupported statements.

The Evidence Ledger and Checker are included to improve traceability and validation, but they do not guarantee that every output is correct.

Human review remains important for consequential business decisions.

---

# 24. Security, Reliability, and Reproducibility

The application must follow these principles:

- Keep secrets on the backend.
- Use environment variables for credentials.
- Never expose database passwords or LLM API keys to React.
- Validate uploaded files.
- Validate API requests.
- Configure CORS appropriately.
- Use controlled database access.
- Use SQLAlchemy and Alembic for database management.
- Record model versions.
- Record investigation IDs.
- Preserve source references.
- Log relevant application errors.
- Keep raw data unchanged.
- Version preprocessing and model artifacts.
- Document synthetic data.
- Provide reproducible evaluation scripts.

**Database rule:** PostgreSQL only. Do not use SQLite or SQLite fallback under any circumstances.

---

# 25. Final Expected Deliverable

At completion, SCOPE will provide a working web-based supply chain intelligence platform containing:

1. A React.js frontend.
2. A FastAPI backend.
3. PostgreSQL database integration.
4. A documented data preprocessing pipeline.
5. A late-delivery classification model.
6. A delivery-duration regression model.
7. A time-series forecasting experiment, if justified by the data.
8. Vendor segmentation.
9. Anomaly detection.
10. An inventory prediction feasibility assessment.
11. SHAP-based explainability.
12. A RAG document retrieval system.
13. An Evidence Ledger.
14. A Checker validation component.
15. A LangGraph multi-agent workflow.
16. Integrated investigation reports.
17. Model and system evaluation results.
18. Technical documentation.
19. Testing documentation.
20. Final research presentation and defence material.

---

# 26. Final Project Definition

SCOPE is an evidence-grounded, AI-powered supply chain intelligence platform that combines structured operational data, predictive Machine Learning, explainable AI, document-based Retrieval-Augmented Generation, evidence traceability, and multi-agent orchestration.

The system uses XGBoost for late-delivery classification, Gradient Boosting for delivery-duration regression, K-Means for vendor segmentation, Isolation Forest for anomaly detection, and an LSTM forecasting experiment where data availability justifies it.

SHAP provides model explanations. RAG retrieves supporting information from supply chain documents. The Evidence Ledger stores traceable evidence references, while the Checker validates numerical and evidence-based claims.

LangGraph coordinates the Planner, Data Analyst, Document Researcher, Report Writer, and Checker workflow.

FastAPI provides backend services, React.js with Vite and TypeScript provides the frontend, and PostgreSQL provides persistent storage.

The ultimate goal is to provide supply chain decision-makers with predictions and investigations that are not only useful, but also explainable, traceable, and grounded in available evidence.
