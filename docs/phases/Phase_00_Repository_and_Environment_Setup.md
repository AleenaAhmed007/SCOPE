# Phase 00 — Repository and Environment Setup

## 1. Objective

Create a clean, modular, reproducible Python project structure for SCOPE (Supply Chain Operations and Predictive Evidence System).

The purpose of this phase is to prepare the development environment and project architecture before implementing EDA, preprocessing, machine learning, RAG or agentic AI.

## 2. Why This Phase Is Required

A proper repository structure helps:
- Organize ML, data engineering, RAG and agent modules.
- Avoid duplicate code.
- Maintain reproducibility.
- Manage dependencies.
- Support testing and debugging.
- Make collaboration easier.

## 3. Technology Stack

- Python 3.11
- Git and GitHub
- pandas
- NumPy
- scikit-learn
- XGBoost
- Matplotlib
- Seaborn
- Jupyter Notebook
- Pytest
- FastAPI
- Streamlit
- LangGraph
- FAISS or Chroma
- SQLite

Install additional libraries only when required by a specific phase.

## 4. Recommended Project Structure

```text
SCOPE/
│
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
│
├── configs/
│   ├── data.yaml
│   ├── models.yaml
│   └── rag.yaml
│
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
│
├── notebooks/
│
├── reports/
│   ├── figures/
│   ├── metrics/
│   └── models/
│
├── docs/
│   ├── README.md
│   └── phases/
│
├── backend/
│   └── scope/
│       ├── config/
│       ├── data/
│       ├── features/
│       ├── models/
│       │   ├── classification/
│       │   ├── regression/
│       │   ├── forecasting/
│       │   ├── clustering/
│       │   ├── anomaly/
│       │   └── explainability/
│       ├── rag/
│       ├── agents/
│       ├── evidence/
│       ├── api/
│       └── ui/
│
└── tests/
    ├── unit/
    └── integration/
```

## 5. Dataset Setup

Primary dataset:

`SCMS_with_inventory.csv`

Place the dataset at:

`data/raw/SCMS_with_inventory.csv`

Rules:
- Never overwrite the original CSV.
- Never manually modify raw records.
- Record file checksum and ingestion date.
- Keep raw, interim and processed datasets separate.
- Do not upload restricted or sensitive data to GitHub.

## 6. Environment Setup

Create a virtual environment.

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## 7. Initial Requirements

Create a requirements file containing the core project dependencies.

Do not install every optional deep-learning or LLM dependency without checking compatibility. Add TensorFlow, embedding libraries and provider SDKs only when needed.

## 8. Configuration

Use YAML configuration files for:
- Dataset paths.
- Target definitions.
- Model parameters.
- Random seeds.
- Train/validation/test boundaries.
- RAG chunking and retrieval settings.

Use `.env` for API keys and secrets.

Never hardcode API keys.

## 9. Testing

Create a smoke test that verifies:
- Python environment works.
- Project modules can be imported.
- Dataset path can be resolved.
- Configuration can be loaded.
- Logging works.

Run:

```bash
pytest -q
```

## 10. Expected Deliverables

- Working repository.
- Virtual environment.
- requirements.txt.
- README.md.
- Configuration files.
- .gitignore.
- .env.example.
- Basic source modules.
- Test structure.
- Dataset provenance note.

## 11. Acceptance Criteria

- Project installs in a clean environment.
- Raw CSV remains unchanged.
- Secrets are not committed.
- Imports work.
- Smoke test passes.
- README contains setup instructions.

## 12. Definition of Done

Phase 0 is complete when another team member can clone the repository, install dependencies, configure the project and run its smoke test successfully.

## 13. Cursor Agent Prompt

```text
You are the senior Python software engineer for SCOPE (Supply Chain Operations and Predictive Evidence System).

Inspect the current repository before making changes.

Create a clean Python 3.11 project structure using the architecture described in this document.

Create:
- requirements.txt
- README.md
- .gitignore
- .env.example
- configs/
- data/raw/
- data/interim/
- data/processed/
- notebooks/
- reports/
- docs/
- backend/scope/
- tests/

Create modular packages for data, features, classification, regression, forecasting, clustering, anomaly detection, explainability, RAG, agents, evidence, API and UI.

Use type hints, docstrings, logging and configuration-driven paths.

Do not implement machine learning models in this phase.

Do not overwrite or modify the original SCMS_with_inventory.csv.

Add a smoke test and provide exact setup, installation and test commands.

Inspect existing files and reuse useful code instead of duplicating it.

At the end, list all created and modified files, explain the structure and report actual test results.

Implement Phase 0 only.
```

## 14. Next Phase

After successful repository setup, proceed to Phase 01: Dataset Audit and Complete EDA.
