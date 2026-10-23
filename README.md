# MuleNet

MuleNet is a fraud network detection system designed to identify money mule accounts and coordinated fraud rings in UPI-style transaction streams. By pairing behavioural transaction features with graph-based counterparty features, MuleNet trains a gradient-boosted decision tree (XGBoost) to accurately score accounts and isolate mule networks under fixed operational investigation budgets.

An offline ML pipeline simulates synthetic transaction topologies and writes validated artifacts; a FastAPI service serves analytical endpoints and ego-network graphs; and a React + Vite dashboard surfaces ranked alerts, plain-English reasons, interactive force-directed graph visualizations, and full-model vs. behaviour-only ablation curves.

---

## Prerequisites

- **Python**: 3.10+ (Python 3.11 or 3.12 recommended)
- **Node.js**: 18.0+ (with npm 9+)
- **Git**

---

## Setup Instructions

### 1. Windows (PowerShell)

```powershell
# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install Python dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Setup Frontend
cd frontend
npm install
cd ..
```

### 2. macOS / Linux

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Setup Frontend
cd frontend
npm install
cd ..
```

### 3. Windows Subsystem for Linux (WSL)

> **Important**: For optimal disk I/O performance and file-watching with Vite and FastAPI, work directly inside your WSL home directory (e.g., `~/projects/mulenet`) rather than Windows-mounted paths like `/mnt/c/...`.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cd frontend
npm install
cd ..
```

---

## Running Commands

### Run Offline ML Pipeline
Generates transactions, computes features, trains the model, and writes artifacts to `artifacts/`:
```bash
python -m ml.run_pipeline

# Quick run (1,000 accounts for rapid iteration):
python -m ml.run_pipeline --quick

# Custom seed and destination:
python -m ml.run_pipeline --seed 42 --out artifacts
```

### Run Backend API Server
Starts FastAPI on port `8000`:
```bash
uvicorn backend.app.main:app --reload --port 8000
```
- API Documentation (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/health](http://localhost:8000/api/health)

### Run Tests
Executes common, ML, and backend test suites:
```bash
pytest
```

### Run Frontend Development Server
Starts the React + Vite dashboard on port `5173`:
```bash
cd frontend
npm run dev
```
- Dashboard URL: [http://localhost:5173](http://localhost:5173)

---

## Ports & Endpoints

| Service | Port | Default URL |
| :--- | :--- | :--- |
| **Backend API** | `8000` | `http://localhost:8000` |
| **Frontend UI** | `5173` | `http://localhost:5173` |

---

## Environment Variables

### Backend (`backend/.env` or root `.env`)
Copy `backend/.env.example` to `backend/.env`:
```env
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
ARTIFACTS_DIR=artifacts
```
- `CORS_ORIGINS`: Comma-separated list of allowed origins.
- `ARTIFACTS_DIR`: Path to artifacts directory (resolved relative to repository root).

### Frontend (`frontend/.env`)
Copy `frontend/.env.example` to `frontend/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCKS=false
```

---

## Repository Structure

```
mulenet/
├── README.md                   # Project documentation & run guides
├── .gitignore                  # Git ignore rules for Python & Node
├── requirements.txt            # Python dependencies (pinned versions)
├── pytest.ini                  # Pytest configuration (pythonpath & testpaths)
├── docs/
│   ├── api-contract.md         # API route specifications & error models
│   ├── artifacts-contract.md   # Artifact format & python interfaces
│   ├── features-and-typologies.md # Feature definitions & synthetic parameters
│   └── test-checklist.md       # Acceptance checklist
├── common/
│   ├── __init__.py
│   ├── artifact_schema.py      # Feature/column constants & validate_artifacts()
│   ├── metrics.py              # budget_metrics() calculation
│   └── test_metrics.py         # Tests for budget metrics & tie-breaks
├── artifacts/                  # Validated sample fixture
│   ├── accounts.csv
│   ├── transactions.csv
│   ├── reasons.json
│   └── metrics.json
├── ml/
│   ├── __init__.py
│   ├── config.py               # Named simulation constants
│   ├── simulator.py            # Synthetic dataset generator
│   ├── features.py             # Feature computation logic
│   ├── train_eval.py           # XGBoost training & cross-validation
│   ├── explain.py              # SHAP reason text generation
│   ├── run_pipeline.py         # CLI pipeline orchestrator
│   └── tests/                  # ML unit tests
├── backend/
│   ├── __init__.py
│   ├── .env.example
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI entrypoint, CORS, exception handlers
│   │   ├── config.py           # Backend settings & limits
│   │   ├── errors.py           # Standard APIError & error codes
│   │   ├── schemas.py          # Pydantic v2 request & response schemas
│   │   ├── store.py            # ArtifactStore in-memory loader & dependencies
│   │   ├── routes/             # API routes (/api/*)
│   │   └── services/           # Service layer implementations
│   └── tests/                  # Backend unit & integration tests
└── frontend/
    ├── package.json            # React 18, Vite 5, Recharts, force-graph
    ├── vite.config.js          # Vite config (port 5173, strictPort)
    ├── index.html
    ├── .env.example
    └── src/
        ├── main.jsx
        ├── App.jsx             # Shell mounting all placeholder components
        ├── index.css           # Base styling
        ├── api/client.js       # API client stubs
        ├── mocks/mockResponses.js
        └── components/         # 9 Modular UI components
```

---

## Team Ownership Table

| Developer | Scope & Responsibilities | Key Files |
| :--- | :--- | :--- |
| **Dev 1 (ML)** | Synthetic transaction simulation, feature extraction, XGBoost training with GroupKFold, pipeline orchestrator, ML tests. | `ml/simulator.py`, `ml/features.py`, `ml/train_eval.py`, `ml/run_pipeline.py`, `ml/tests/` |
| **Dev 2 (Backend)** | Backend route implementations, service logic, graph extraction, plain-English SHAP reasons, backend tests. | `backend/app/services/*`, `backend/app/routes/*`, `ml/explain.py`, `backend/tests/` |
| **Dev 3 (Frontend)** | React dashboard UI, API client integration, Recharts curves, 2D force-directed network graph, responsive layout. | `frontend/src/App.jsx`, `frontend/src/components/*`, `frontend/src/api/client.js` |

---

## Git Workflow Guidelines

To collaborate effectively across the 3-person team:
1. **Branching**: Never commit directly to `main`. Branch off `main` for each feature:
   ```bash
   git checkout -b dev1/simulator-logic
   git checkout -b dev2/alert-service
   git checkout -b dev3/dashboard-ui
   ```
2. **Explicit Stage**: Add files explicitly by name rather than `git add .` to avoid committing unwanted local caches or credentials:
   ```bash
   git add ml/simulator.py ml/tests/test_simulator.py
   ```
3. **Pull Requests**: Open a pull request against `main`. Ensure all tests pass before requesting review.
4. **Syncing Main**: Merge `main` into your feature branch regularly to prevent merge conflicts:
   ```bash
   git checkout main
   git pull origin main
   git checkout <your-branch>
   git merge main
   ```
5. **Never Force-Push**: Never run `git push --force` or rewrite history on shared branches.

---

## Troubleshooting

- **CORS Error (`Access-Control-Allow-Origin`)**: Ensure `CORS_ORIGINS` in your `.env` or `backend/app/config.py` includes the exact URL used by your frontend (`http://localhost:5173` or `http://127.0.0.1:5173`).
- **Port In Use (8000 or 5173)**:
  - Windows: Run `Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process`
  - Linux/macOS: Run `lsof -ti:8000 | xargs kill -9`
- **Virtual Environment Not Activated**: If imports fail, ensure your prompt shows `(.venv)` and run `python -m pip list` to confirm installed packages.
- **503 ARTIFACTS_NOT_FOUND**: Data endpoints require valid artifacts in `artifacts/`. If missing or invalid, generate them via `python -m ml.run_pipeline` or verify `validate_artifacts("artifacts")`.
