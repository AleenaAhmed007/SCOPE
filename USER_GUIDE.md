# SCOPE — User Guide

**SCOPE** = Supply Chain Operations and Predictive Evidence System

This package contains the full project: source code, dataset, trained models, reports, FastAPI backend, and React frontend.

You do **not** need the sender’s machine. Install dependencies on your computer and run.

---

## 1. What you need installed

| Tool | Version | Why |
|------|---------|-----|
| Python | **3.11–3.13** (recommended: 3.13) | Backend + ML |
| Node.js | **18+** (includes npm) | React frontend |
| Docker Desktop | Optional but recommended | PostgreSQL |
| Git | Optional | Not required to run from this zip |

### Important

- **Do not use Python 3.15** — pandas datetime crashes on it.
- On Windows, create the venv with: `py -3.13 -m venv .venv`

---

## 2. Unzip

1. Extract the zip to a folder, e.g. `C:\Projects\SCOPE` or `~/SCOPE`.
2. Open a terminal in that folder (the folder that contains `USER_GUIDE.md`, `requirements.txt`, and `backend/`).

---

## 3. Quick start (Windows PowerShell)

### 3.1 Python environment

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### 3.2 PostgreSQL (required)

```powershell
docker compose up -d postgres
Copy-Item .env.example .env
```

The project-root `.env` is loaded automatically and uses synchronous `psycopg`.
PostgreSQL is required. If Docker is unavailable, change `SCOPE_DATABASE_URL`
in `.env` to point to another PostgreSQL server. The application does not fall
back to SQLite.

### 3.3 (Optional) Rebuild processed data + models

Trained models and processed CSV files are already included. Only re-run if you want a fresh train:

```powershell
python -m scope.data.preprocessing
python scripts/run_all_phases.py
```

### 3.4 Start the API

```powershell
uvicorn scope.api.app:app --reload --host 127.0.0.1 --port 8000
```

Check: open http://127.0.0.1:8000/health  
API docs: http://127.0.0.1:8000/docs

### 3.5 Start the frontend (new terminal)

```powershell
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (usually http://127.0.0.1:5173).

---

## 4. Quick start (macOS / Linux)

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

docker compose up -d postgres
export SCOPE_DATABASE_URL="postgresql+psycopg://scope:scope@127.0.0.1:5432/scope"

uvicorn scope.api.app:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

---

## 5. What is included in this package

| Path | Contents |
|------|----------|
| `backend/scope/` | Python package (EDA, ML, RAG, agents, API, evidence, DB) |
| `data/raw/` | Original dataset `SCMS_with_inventory.csv` + provenance |
| `data/processed/` | Feature tables / CSV outputs |
| `data/interim/` | Normalized interim data |
| `data/documents/` | Synthetic RAG documents (clearly labeled) |
| `reports/models/` | Trained model artifacts (`.joblib`) |
| `reports/metrics/` | Evaluation JSON |
| `reports/figures/` | EDA / SHAP plots |
| `reports/final_defence_report.md` | Evaluation / defence write-up |
| `frontend/` | React + Vite + Tailwind UI source |
| `notebooks/` | EDA notebook |
| `tests/` | Pytest suite |
| `configs/` | YAML configs |
| `docs/` | Data / feature dictionaries, phase docs |
| `docs/phases/` | Phase implementation and evaluation guides |
| `docker-compose.yml` | Local Postgres |
| `requirements.txt` | Python dependencies |
| `USER_GUIDE.md` | This file |

### Not included (on purpose)

| Excluded | Reason | How to recreate |
|----------|--------|-----------------|
| `.venv/` | Huge + OS-specific | `python -m venv .venv` + `pip install` |
| `frontend/node_modules/` | Huge + OS-specific | `npm install` |
| `.git/` | Not required to run | Optional |
| `__pycache__/` | Regenerated automatically | — |

---

## 6. Frontend pages

| Page | Purpose |
|------|---------|
| Dashboard | Orders, vendors, late %, anomalies |
| Orders | Look up shipment + late/duration/anomaly predictions |
| Vendors | Vendor stats + segments |
| Risk | Risk summary + SHAP |
| Documents | RAG Q&A with citations |
| Investigate | LangGraph-style agent investigation |
| Evidence | Evidence ledger explorer |

---

## 7. Useful commands

```powershell
# Smoke tests
pytest -q

# Re-run EDA only
python -c "from scope.eda import run_phase01_eda; run_phase01_eda()"

# Sample agent investigation (API must not be required)
python -c "from scope.agents.workflow import run_investigation; print(run_investigation('Investigate late risk', order_id=1)['status'])"

# Build frontend for production
cd frontend
npm run build
```

---

## 8. Environment variables

Copy `.env.example` to `.env` if needed.

| Variable | Example | Purpose |
|----------|---------|---------|
| `SCOPE_DATABASE_URL` | `postgresql+psycopg://scope:scope@127.0.0.1:5432/scope` | Database |
| `SCOPE_LOG_LEVEL` | `INFO` | Logging |
| `VITE_API_BASE` | `http://127.0.0.1:8000` | Frontend → API (optional; Vite proxy works in dev) |

Never commit real API keys. LLM provider keys are optional; the agent workflow runs without them.

---

## 9. Troubleshooting

| Problem | Fix |
|---------|-----|
| `No module named scope` | Activate `.venv` and run `pip install -e .` |
| pandas / datetime crash | Use Python 3.11–3.13, not 3.15 |
| API 404 on models | Ensure `reports/models/` was extracted; or re-run `python scripts/run_all_phases.py` |
| Frontend cannot reach API | Start uvicorn on port 8000; check CORS / `VITE_API_BASE` |
| Postgres connection error | `docker compose up -d postgres` and set `SCOPE_DATABASE_URL` |
| `npm` not found | Install Node.js 18+ from https://nodejs.org |
| PowerShell blocks venv activate | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |

---

## 10. Data / ethics notes

- Raw CSV must not be manually edited.
- Inventory_* fields are **unverified augmented data**.
- Documents under `data/documents/synthetic/` are **synthetic**, not real contracts.
- Do not upload restricted supply-chain data to public remotes.

---

## 11. Project contact / next steps for your friend

1. Follow Section 3 (or 4).
2. Open the UI and try **Orders → order ID 1 → Run prediction suite**.
3. Try **Investigate** with the same order ID.
4. Read `reports/final_defence_report.md` for metrics and limitations.

If something fails, send: OS, Python version (`python --version`), and the exact error traceback.
