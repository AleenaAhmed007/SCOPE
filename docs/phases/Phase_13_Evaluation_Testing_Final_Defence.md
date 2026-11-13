# Phase 13 — Evaluation, Testing and Final Project Defence

## 1. Objective

Perform end-to-end evaluation of the SCOPE project.

Verify that the ML models, RAG pipeline, Evidence Ledger, Checker, LangGraph workflow, FastAPI backend, Streamlit frontend, and PostgreSQL persistence work together.

Prepare final technical documentation and project defence material.

## 2. Evaluation Areas

Evaluate the project in five areas:

1. Data quality
2. Machine learning performance
3. RAG retrieval and grounding
4. Agentic workflow reliability
5. Application and database integration

## 3. Data Quality Evaluation

Report:

- Total records
- Total columns
- Missing-value distribution
- Duplicate records
- Date parsing success
- Invalid dates
- Constant and near-constant fields
- Target distribution
- Data leakage findings

Recalculate all statistics from the final dataset.

Document any synthetic, augmented, or uncertain-provenance columns.

## 4. Machine Learning Evaluation

### A. Late Delivery Classification

Evaluate:

- XGBoost
- Random Forest
- DummyClassifier baseline, where appropriate

Metrics:

- Accuracy
- Precision
- Recall
- F1-score
- ROC-AUC
- PR-AUC
- Confusion matrix

Explain why recall and precision matter for late-delivery risk detection.

### B. Delivery Duration Regression

Evaluate:

- DummyRegressor
- GradientBoostingRegressor
- Optional RandomForestRegressor

Metrics:

- MAE
- RMSE
- R²
- Median Absolute Error

Explain the error in terms of days.

### C. Time Series Forecasting

Evaluate baseline forecasting and LSTM only if implemented.

Metrics:

- MAE
- RMSE
- Appropriate percentage-based metrics where valid

Compare complex models with baseline models.

### D. Vendor Segmentation

Report:

- Cluster count
- Silhouette score
- Cluster sizes
- Vendor cluster profiles

### E. Anomaly Detection

Report:

- Total anomalies
- Anomaly percentage
- Score distribution
- Review findings, if available

Do not claim anomaly detection accuracy without verified labels.

### F. Inventory Experiment

Report:

- Inventory data provenance findings
- Feature suitability
- Leakage analysis
- Model results only if a valid model was justified

## 5. RAG Evaluation

Create a fixed test set of questions and expected source documents.

Evaluate:

- Recall@k
- Precision@k
- MRR
- Citation correctness
- Citation coverage
- Answer groundedness
- Retrieval latency

Test cases should include:

- Questions with direct document evidence
- Questions requiring multiple document chunks
- Questions with no supporting document
- Questions involving conflicting document versions
- Questions requiring page-level citations

The system should report insufficient evidence when documents do not support an answer.

## 6. Evidence Ledger and Checker Evaluation

Test:

- Evidence record creation
- Evidence retrieval
- Claim linking
- Invalid source detection
- Numeric mismatch detection
- Unsupported claim detection
- Model version validation
- Audit history

Create controlled test cases with known expected outcomes.

## 7. Agentic Workflow Evaluation

Evaluate:

- Correct task planning
- Correct tool selection
- Successful ML tool execution
- Successful RAG retrieval
- Evidence registration
- Claim-to-evidence linking
- Checker validation
- Error handling
- Human review routing
- Final report quality

Measure:

- Workflow completion rate
- Tool failure rate
- Unsupported claim rate
- Average workflow latency
- Evidence citation coverage

Do not claim perfect agent reliability based on a small number of demonstrations.

## 8. Application Testing

### Backend tests

Test:

- API input validation
- API response schemas
- Authentication, if implemented
- Database operations
- Error handling
- File upload validation

### Frontend tests

Test:

- Dashboard loading
- Order search
- Prediction display
- Vendor information
- Document upload
- RAG query
- Agentic investigation
- Evidence explorer

### Database tests

Test:

- PostgreSQL connectivity
- Alembic migrations
- Foreign-key constraints
- Transactions
- Data persistence
- Reconnection behavior

Use a dedicated PostgreSQL test database or isolated test schema.

Never switch to SQLite for tests.

## 9. End-to-End Test Scenarios

### Scenario 1 — Late Delivery Risk

1. User selects an order.
2. System retrieves its permitted features.
3. Classifier predicts late-delivery risk.
4. SHAP explanation is generated.
5. Evidence is registered.
6. Checker validates the result.
7. UI displays prediction and explanation.

### Scenario 2 — Document-Based Question

1. User asks a supply chain policy question.
2. RAG retrieves relevant chunks.
3. LLM drafts an answer.
4. Source citations are attached.
5. Checker validates citation references.
6. UI displays answer and sources.

### Scenario 3 — Agentic Disruption Investigation

1. User submits an investigation request.
2. Planner creates a plan.
3. Data Analyst retrieves relevant analytical findings.
4. Document Researcher retrieves relevant documents.
5. Evidence Ledger stores findings.
6. Report Writer prepares a report.
7. Checker validates claims.
8. Final report is displayed or routed for review.

## 10. Performance and Reliability

Measure:

- API response latency
- ML inference latency
- RAG retrieval latency
- Agent workflow duration
- PostgreSQL query performance
- Memory usage where feasible

Identify bottlenecks and document improvements.

Do not invent response-time results.

## 11. Final Documentation

Prepare:

- Project README
- System architecture
- Dataset audit report
- ML model report
- RAG evaluation report
- Agentic workflow documentation
- Database ER diagram
- API documentation
- Installation guide
- User guide
- Limitations and future work

## 12. Final Defence Preparation

Prepare a presentation covering:

1. Research problem
2. Motivation
3. Research objectives
4. Dataset description
5. Data quality limitations
6. Proposed architecture
7. Machine learning experiments
8. RAG pipeline
9. Evidence Ledger and Checker
10. LangGraph workflow
11. FastAPI and Streamlit application
12. Evaluation results
13. Limitations
14. Future improvements
15. Conclusion

Prepare a live demonstration with at least the three end-to-end scenarios defined above.

## 13. PostgreSQL Requirements

Verify that the complete application uses PostgreSQL.

Check:

- Database migrations
- Foreign keys
- Indexes
- Connection pooling
- Transaction handling
- Data persistence
- Backup and restore procedure

Use SQLAlchemy and Alembic.

Do not use SQLite in development, testing, staging, or production.

## 14. Suggested Folder Structure

```text
evaluation/
  datasets/
  ml/
  rag/
  agents/
  end_to_end/
  reports/

docs/
  architecture/
  database/
  evaluation/
  user_guide/
  defence/

presentation/
  SCOPE_Final_Defence.pptx

tests/
  unit/
  integration/
  end_to_end/
```

## 15. Expected Outputs

- Final evaluation report
- ML comparison tables
- RAG evaluation results
- Evidence Checker test results
- Agent workflow evaluation
- API and integration test results
- Database validation report
- Final architecture documentation
- User guide
- Final defence presentation
- Limitations and future work

## 16. Acceptance Criteria

- All phase outputs are reviewed.
- Data statistics are recalculated.
- ML metrics come from actual test predictions.
- RAG metrics come from an actual evaluation dataset.
- Agentic workflow test scenarios are executed.
- Evidence validation tests pass.
- API and frontend integration is verified.
- PostgreSQL migrations and persistence are verified.
- No SQLite dependency exists.
- Limitations are documented honestly.
- Final presentation matches actual implementation and results.

## 17. Cursor AI Prompt

You are implementing Phase 13 of the SCOPE project.

Perform a comprehensive final evaluation, testing, and documentation review.

Requirements:

1. Inspect the complete repository and all previous phase outputs.
2. Recalculate final dataset statistics from the actual dataset.
3. Review data quality, date parsing, missing values, duplicates, and leakage risks.
4. Evaluate late-delivery classification using actual holdout predictions.
5. Evaluate delivery-duration regression using actual holdout predictions.
6. Evaluate forecasting only for implemented and justified forecasting models.
7. Report vendor segmentation metrics and cluster profiles.
8. Report anomaly findings without inventing ground-truth accuracy.
9. Report inventory findings and clearly state whether predictive modeling was justified.
10. Evaluate RAG using a fixed question and reference-document dataset.
11. Calculate retrieval, ranking, citation, and groundedness metrics where supported.
12. Test Evidence Ledger and Checker using controlled validation cases.
13. Test the LangGraph workflow using the three end-to-end scenarios.
14. Test FastAPI routes and Streamlit integration.
15. Test PostgreSQL migrations, constraints, transactions, and persistence.
16. Use PostgreSQL test infrastructure. Do not use SQLite for tests.
17. Review the entire codebase for SQLite dependencies or fallback configurations and remove them.
18. Generate final reports using only actual experiment results.
19. Document limitations, assumptions, and future work.
20. Prepare final architecture, database, installation, and user documentation.
21. Prepare a defence presentation based on the actual implemented system.
22. Do not fabricate metrics, citations, test results, or completed functionality.

Inspect the repository first. Create an evaluation plan, execute the tests and experiments, fix justified defects, and produce the final documentation.

## 18. Definition of Done

SCOPE is ready for final submission when the complete application has been tested, evaluation results are reproducible, PostgreSQL persistence is verified, limitations are documented, and the final defence material accurately reflects the implemented system.
