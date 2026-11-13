# Phase 10 — Evidence Ledger and Checker

## 1. Objective

Build a centralized Evidence Ledger and validation service for SCOPE.

The Evidence Ledger stores traceable evidence used by the system.

The Checker validates generated claims, numeric values, source references, and evidence consistency.

Important architectural distinction:

- Evidence Ledger is a database-backed service.
- Checker is a validation component/service.
- Neither should be presented as an autonomous AI agent.

## 2. Business Problem

Agentic AI systems may generate reports containing:

- ML predictions
- Risk scores
- Vendor performance information
- RAG document findings
- Anomaly detection results
- Forecasts

Without traceability, it becomes difficult to determine where a claim originated.

SCOPE needs a structured record of the evidence behind generated outputs.

## 3. Evidence Ledger Design

Each evidence record should contain:

- Evidence ID
- Evidence type
- Source system
- Source record ID
- Related vendor/order ID, where applicable
- Evidence content or structured value
- Document ID, if applicable
- Page number, if applicable
- Model version, if applicable
- Timestamp
- Confidence or score, if applicable
- Metadata

Possible evidence types:

- ML prediction
- SHAP explanation
- RAG document chunk
- Anomaly detection result
- Forecast output
- Structured database observation
- Human-reviewed evidence

Do not use confidence as a universal field with the same meaning across all evidence types. Preserve the original score type and semantics.

## 4. Evidence Lifecycle

Implement:

1. Evidence creation
2. Evidence validation
3. Evidence storage
4. Evidence retrieval
5. Evidence linking to claims
6. Evidence status management
7. Evidence audit history

Where possible, evidence records should be immutable.

Corrections should create new versions or audit events rather than silently overwriting historical evidence.

## 5. Checker Design

The Checker validates generated report content before it is presented.

### Validation A — Source validation

- Does the source ID exist?
- Does the document ID exist?
- Is the page reference valid where available?
- Does the evidence belong to the relevant record?

### Validation B — Numeric validation

- Do displayed values match the stored prediction?
- Are percentages calculated correctly?
- Are units consistent?
- Are date differences correct?
- Are rounded values within a documented tolerance?

### Validation C — Claim validation

- Is each factual claim supported by evidence?
- Does the cited evidence actually support the claim?
- Are unsupported statements marked or removed?
- Are assumptions clearly separated from observations?

Semantic claim validation may use an LLM, but deterministic checks must be used for structured numbers, IDs, dates, and arithmetic wherever possible.

### Validation D — Model provenance

- Is the model version recorded?
- Is the prediction linked to its model run?
- Is the feature snapshot or input reference available?
- Is the explanation linked to the same model version?

## 6. Claim-to-Evidence Linking

Generated reports should represent claims as structured objects before rendering.

Example structure:

```json
{
  "claim_id": "CLM-001",
  "claim_text": "The order is predicted to be late.",
  "claim_type": "ml_prediction",
  "evidence_ids": ["EVD-001"],
  "validation_status": "pending"
}
```

This is a conceptual example. Implement a validated schema using the project's chosen Python validation library.

Every material factual claim should have evidence or be explicitly marked as an assumption or inference.

## 7. Validation Results

Possible statuses:

- `validated`
- `needs_review`
- `unsupported`
- `invalid_source`
- `numeric_mismatch`

The final report should not silently present unsupported claims as verified facts.

## 8. PostgreSQL Requirements

PostgreSQL is mandatory.

Use SQLAlchemy, Alembic, and psycopg.

Suggested tables:

- `evidence_records`
- `evidence_links`
- `claims`
- `claim_evidence`
- `validation_runs`
- `validation_findings`
- `evidence_audit_events`

Use foreign keys and indexes appropriately.

Store structured metadata using PostgreSQL JSONB where appropriate.

Use transactions for multi-record evidence creation and linking.

No SQLite.

## 9. Suggested Folder Structure

```text
backend/
  evidence/
    ledger.py
    repository.py
    schemas.py
    links.py
    audit.py

  checker/
    source_validator.py
    numeric_validator.py
    claim_validator.py
    model_validator.py
    service.py

tests/
  test_evidence_ledger.py
  test_source_validator.py
  test_numeric_validator.py
  test_claim_validator.py
```

## 10. Expected Outputs

- Evidence Ledger service
- Evidence schemas
- Evidence repository
- Claim-to-evidence linking
- Numeric validation
- Source validation
- Claim validation
- Validation reports
- PostgreSQL migrations

## 11. Acceptance Criteria

- Evidence records have unique IDs.
- Evidence source metadata is preserved.
- Claims can link to multiple evidence records.
- Invalid source references are detected.
- Numeric mismatches are detected.
- Unsupported claims are identified.
- Validation findings are stored.
- Historical evidence changes are auditable.
- PostgreSQL constraints and migrations work.
- No SQLite dependency exists.

## 12. Cursor AI Prompt

You are implementing Phase 10 of the SCOPE project.

Build a database-backed Evidence Ledger and Checker service.

Requirements:

1. Inspect the existing repository and Phase 09 RAG implementation.
2. Design structured Pydantic schemas for evidence records, claims, links, and validation findings.
3. Implement evidence creation, retrieval, linking, and audit history.
4. Support evidence from ML predictions, SHAP explanations, RAG chunks, anomaly results, forecasts, and structured observations.
5. Preserve source IDs, document IDs, page references, model versions, timestamps, and score semantics.
6. Implement claim-to-evidence linking.
7. Implement deterministic source validation.
8. Implement deterministic numeric validation for values, dates, percentages, units, and arithmetic where applicable.
9. Implement claim support validation for document-based and generated factual claims.
10. Use an LLM for semantic validation only where necessary; do not replace deterministic checks with LLM judgments.
11. Distinguish validated, needs_review, unsupported, invalid_source, and numeric_mismatch statuses.
12. Ensure unsupported claims cannot silently appear as verified facts.
13. Preserve audit history. Avoid silently overwriting historical evidence.
14. Use PostgreSQL with SQLAlchemy and Alembic.
15. Use foreign keys, indexes, transactions, and JSONB where appropriate.
16. Add unit and integration tests for all validation components.
17. PostgreSQL only. Do not use SQLite or SQLite fallback.
18. Read database credentials from environment variables.
19. Do not fabricate evidence or validation results.
20. Document how the Evidence Ledger and Checker will be called by the agent workflow.

Inspect the repository before implementation. Explain planned schema and file changes, implement the service, run migrations, and execute tests.

## 13. Definition of Done

The Evidence Ledger can store and retrieve traceable evidence, claims can link to their sources, and the Checker can identify unsupported claims, invalid sources, and numeric mismatches with results persisted in PostgreSQL.
