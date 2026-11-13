# Phase 12 — React.js Frontend and FastAPI Integration

## 1. Objective

Integrate all SCOPE modules into a complete web application using:

- React.js with Vite
- Tailwind CSS
- FastAPI
- PostgreSQL
- LangGraph

React.js will provide the user interface, while FastAPI will handle backend operations and communicate with ML, RAG, and agentic AI services.

## 2. System Architecture

```text
             React.js Frontend
                (Vite)
                   |
                REST API
                   |
                FastAPI
                   |
          Application Services
                   |
       +-----------+-----------+
       |           |           |
       v           v           v
      ML          RAG       LangGraph
   Services     Services     Agents
       |           |           |
       +-----------+-----------+
                   |
             Evidence Ledger
                   |
                Checker
                   |
                   v
               PostgreSQL
```

## 3. Frontend Technology

Use:

- React.js
- Vite
- JavaScript or TypeScript (prefer TypeScript)
- Tailwind CSS
- React Router
- Axios
- Recharts
- Lucide React
- React Hook Form
- Zod for frontend validation

## 4. Frontend Pages

### Page 1 — Dashboard

Display:
- Total orders
- Total vendors
- Late delivery percentage
- Average delivery duration
- Anomaly count
- Recent investigation runs
- Risk distribution charts

All values must come from FastAPI endpoints, not hardcoded sample statistics.

### Page 2 — Order Investigation

Features:
- Search by order or shipment ID
- View order details
- Run late-delivery prediction
- View delivery duration estimate
- View anomaly findings
- Start agentic investigation

### Page 3 — Vendor Intelligence

Features:
- Vendor listing
- Vendor segmentation
- Historical performance
- Vendor-level risk indicators
- Cluster visualizations

### Page 4 — Risk Analysis

Features:
- Late-delivery predictions
- Risk distribution
- Model version
- SHAP explanations
- Anomaly results

### Page 5 — Document Intelligence

Features:
- Upload PDF, DOCX, TXT, and Markdown files
- Ask questions about documents
- View retrieved passages
- Display source and page citations

### Page 6 — Agentic Investigation

Features:
- Submit investigation query
- Display investigation plan
- Show agent workflow progress
- View ML findings
- View document findings
- View evidence references
- Display Checker results
- Show final investigation report

### Page 7 — Evidence Explorer

Features:
- Evidence ID
- Evidence type
- Source
- Related order/vendor
- Document page
- Model version
- Validation status

## 5. Backend — FastAPI

Implement REST endpoints:

### Health
- `GET /health`
- `GET /api/v1/system/status`

### Orders
- `GET /api/v1/orders`
- `GET /api/v1/orders/{order_id}`

### Vendors
- `GET /api/v1/vendors`
- `GET /api/v1/vendors/{vendor_id}`
- `GET /api/v1/vendors/segments`

### Predictions
- `POST /api/v1/predictions/late-delivery`
- `POST /api/v1/predictions/delivery-duration`
- `POST /api/v1/predictions/anomaly`

### RAG
- `POST /api/v1/rag/query`
- `POST /api/v1/documents/upload`
- `GET /api/v1/documents`

### Agentic Investigation
- `POST /api/v1/investigations`
- `GET /api/v1/investigations/{run_id}`
- `GET /api/v1/investigations/{run_id}/report`

### Evidence
- `GET /api/v1/evidence/{evidence_id}`
- `GET /api/v1/investigations/{run_id}/evidence`

## 6. Frontend Folder Structure

```text
frontend/
  src/
    components/
      layout/
        Sidebar.tsx
        Navbar.tsx
        MainLayout.tsx

      dashboard/
        MetricCard.tsx
        RiskChart.tsx
        RecentInvestigations.tsx

      orders/
        OrderTable.tsx
        OrderDetails.tsx
        PredictionCard.tsx

      vendors/
        VendorTable.tsx
        VendorSegmentChart.tsx

      investigation/
        InvestigationForm.tsx
        AgentProgress.tsx
        InvestigationReport.tsx

      evidence/
        EvidenceTable.tsx
        CitationCard.tsx

    pages/
      Dashboard.tsx
      OrderInvestigation.tsx
      VendorIntelligence.tsx
      RiskAnalysis.tsx
      DocumentIntelligence.tsx
      AgenticInvestigation.tsx
      EvidenceExplorer.tsx

    services/
      api.ts
      orderService.ts
      vendorService.ts
      predictionService.ts
      ragService.ts
      investigationService.ts
      evidenceService.ts

    hooks/
    types/
    utils/
    App.tsx
    main.tsx

  package.json
  vite.config.ts
  tsconfig.json
```

## 7. Backend Folder Structure

```text
backend/
  scope/
    api/
      main.py
      routes/
        health.py
        orders.py
        vendors.py
        predictions.py
        rag.py
        investigations.py
        evidence.py

    services/
    repositories/
    schemas/
    database/
    ml/
    rag/
    agents/
    evidence/
    checker/

  alembic/
  tests/
  requirements.txt
```

Adapt these paths to the existing repository rather than duplicating modules already implemented in earlier phases.

## 8. API Integration

- Configure Axios with a centralized API base URL.
- Use environment variables for frontend configuration.
- Implement loading, success, empty, and error states.
- Validate request and response structures.
- Use polling for long-running investigations.
- Preserve investigation IDs for report retrieval.
- Do not expose backend secrets in frontend code.

Example frontend environment variable:

`VITE_API_BASE_URL=http://localhost:8000`

Example Axios configuration:

```typescript
import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});
```

## 9. PostgreSQL Requirements

PostgreSQL is the only database.

Use SQLAlchemy, Alembic, and psycopg.

All persistent records must use PostgreSQL, including:

- Orders and vendor records
- Predictions
- RAG metadata
- Agent runs
- Evidence records
- Validation findings
- Application audit logs

Never use SQLite or an SQLite fallback.

## 10. Security Requirements

- Keep database credentials on the backend.
- Keep LLM and embedding API keys on the backend.
- Configure CORS correctly.
- Validate file uploads.
- Validate API inputs.
- Use parameterized database queries.
- Implement authentication and authorization where required.
- Never expose secrets through Vite environment variables.

## 11. Cursor AI Prompt

You are implementing Phase 12 of the SCOPE project.

IMPORTANT: The frontend must use React.js with Vite and TypeScript. Do not use Streamlit, Flask templates, or another frontend framework.

Build a complete React frontend integrated with the existing FastAPI backend.

Requirements:

1. Inspect the existing repository before making changes.
2. Build the frontend using React.js, Vite, and TypeScript.
3. Use Tailwind CSS for styling.
4. Use React Router for navigation.
5. Use Axios for backend API communication.
6. Use Recharts for dashboard and analytical visualizations.
7. Use Lucide React for icons.
8. Build Dashboard, Order Investigation, Vendor Intelligence, Risk Analysis, Document Intelligence, Agentic Investigation, and Evidence Explorer pages.
9. Connect every page to real FastAPI endpoints.
10. Do not hardcode dashboard metrics, predictions, vendor data, or investigation results.
11. Display loading, error, empty, and success states.
12. Support PDF, DOCX, TXT, and Markdown document uploads through the backend.
13. Display RAG citations with document names and page numbers when available.
14. Display agent progress, investigation IDs, evidence references, and Checker results.
15. Implement polling for long-running investigation requests.
16. Keep API configuration centralized.
17. Use VITE_API_BASE_URL for the backend address.
18. Never place database passwords, LLM API keys, or backend secrets in frontend environment variables.
19. Use FastAPI as the only application backend.
20. Use PostgreSQL for all persistent storage.
21. Use SQLAlchemy, Alembic, and psycopg.
22. PostgreSQL only. Never use SQLite or SQLite fallback.
23. Add frontend tests and backend API integration tests.
24. Ensure the application runs locally with documented commands.
25. Preserve existing ML, RAG, Evidence Ledger, Checker, and LangGraph functionality.
26. Do not replace working backend logic with mock responses.

First inspect the repository and present the proposed changes. Then implement the React frontend, connect APIs, and run tests.

## 12. Definition of Done

The SCOPE application has a functional React.js frontend, FastAPI backend, connected ML/RAG/agentic modules, and PostgreSQL persistence. All seven frontend pages work with actual backend data.
