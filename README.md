# SCOPE

**Supply Chain Operations and Predictive Evidence System**

An evidence-grounded agentic AI platform for supply chain disruption detection, combining predictive ML, vendor analytics, RAG, and multi-agent investigation.

## Requirements

- Python 3.11–3.13 recommended (**avoid 3.15** for now — pandas datetime crashes)
- Git

Create the venv with an explicit interpreter when needed:

```bash
py -3.13 -m venv .venv
```

## Quick start

### 1. Clone and enter the repository

```bash
cd SCOPE
```

### 2. Create a virtual environment

**Windows (PowerShell):**

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

### 4. Configure environment

```bash
copy .env.example .env
```

On Linux/macOS: `cp .env.example .env`

Edit `.env` if needed. Never commit `.env`.

### 5. Dataset

Place the primary dataset at:

```text
data/raw/SCMS_with_inventory.csv
```

Do not modify or overwrite the raw CSV. See `data/raw/PROVENANCE.md` for checksum and ingestion metadata.

### 6. Run the smoke test

```bash
pytest -q
```

## Project structure

```text
SCOPE/
├── configs/          # YAML configuration (data, models, RAG)
├── data/
│   ├── raw/          # Immutable source datasets
│   ├── interim/      # Intermediate transforms
│   └── processed/    # Model-ready datasets
├── docs/             # Documentation
├── notebooks/        # Exploratory notebooks
├── reports/          # Figures, metrics, saved models
├── backend/scope/    # Python application package
│   ├── config/       # Config loading
│   ├── data/         # Data access
│   ├── features/     # Feature engineering
│   ├── models/       # ML modules by task family
│   ├── rag/          # Retrieval-Augmented Generation
│   ├── agents/       # LangGraph agents
│   ├── evidence/     # Evidence ledger / checker
│   ├── api/          # FastAPI
│   └── ui/           # UI helpers
└── tests/            # Unit and integration tests
```

## Configuration

| File | Purpose |
|------|---------|
| `configs/data.yaml` | Dataset paths, splits, targets |
| `configs/models.yaml` | Model defaults and seeds |
| `configs/rag.yaml` | Chunking and retrieval settings |
| `.env` | Secrets and runtime env (from `.env.example`) |

Paths are configuration-driven. Do not hardcode absolute paths or API keys.

## Phase status

| Phase | Status |
|-------|--------|
| 00 Repository and Environment Setup | Complete |
| 01 Dataset Audit and Complete EDA | Complete |
| 02 Preprocessing & Feature Engineering | Complete |
| 03 Late Delivery Classification | Complete |
| 04 Delivery Duration Regression | Complete |
| 05 Time Series Forecasting | Complete |
| 06 Vendor Segmentation & Anomaly | Complete |
| 07 Inventory Prediction Experiment | Complete |
| 08 SHAP Explainability | Complete |
| 09 RAG Document Retrieval | Complete |
| 10 Evidence Ledger & Checker | Complete |
| 11 LangGraph Agentic Workflow | Complete |
| 12 React + FastAPI Integration | Complete |
| 13 Evaluation / Final Defence | Complete |

### Run all analytical phases

```bash
python scripts/run_all_phases.py
pytest -q
```

### Evaluate saved models

Evaluate one model or all saved models without retraining. Reports are written to
`reports/metrics/evaluation_<model>.json`.

```bash
python backend/scope/evaluation/model_evaluation.py --model late_delivery
python backend/scope/evaluation/model_evaluation.py --model duration
python backend/scope/evaluation/model_evaluation.py --model all
```

Available model names: `late_delivery`, `duration`, `inventory`,
`forecast_late_rate`, `forecast_volume`, `vendor_segmentation`,
`anomaly_unusual_profile`, and `anomaly_retrospective`. Train the relevant model
and generate processed data first. Inventory classification is experimental:
it excludes the fields that define the arithmetic target and reports the rule
agreement separately. Its augmented source fields are unverified. Anomaly
scores are summaries because there are no ground-truth anomaly labels.

The full phase runner now refreshes all model evaluation reports before building
the final defence report. It exits with a nonzero status if any phase fails;
see `reports/phase_run_summary.json` for the phase-by-phase details.

### PostgreSQL (required)

```bash
docker compose up -d postgres
Copy-Item .env.example .env
```

The example `.env` configures `SCOPE_DATABASE_URL` for synchronous psycopg. The
API loads the root `.env`, requires PostgreSQL at startup, and does not fall back
to SQLite. `DATABASE_URL` is also accepted for compatibility.

### Start API + frontend

```bash
uvicorn scope.api.app:app --reload --port 8000
cd frontend
npm install
npm run dev
```

Defence report: `reports/final_defence_report.md`

## Licence / data note

Do not upload restricted or sensitive supply-chain data to public remotes. Keep secrets out of Git.
