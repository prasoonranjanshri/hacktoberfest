"""Configuration settings for MuleNet backend."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

cors_origins_raw = os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
)
CORS_ORIGINS = [orig.strip() for orig in cors_origins_raw.split(",") if orig.strip()]

artifacts_dir_raw = os.getenv("ARTIFACTS_DIR", "artifacts")
artifacts_path = Path(artifacts_dir_raw)
if artifacts_path.is_absolute():
    ARTIFACTS_DIR = artifacts_path.resolve()
else:
    ARTIFACTS_DIR = (REPO_ROOT / artifacts_path).resolve()

API_VERSION = "1.0.0"

# Query and service limits
BUDGET_MIN = 1
BUDGET_MAX = 1000
DEFAULT_BUDGET = 100
HOPS_ALLOWED = (1, 2)
MAX_NODES_MIN = 5
MAX_NODES_MAX = 100
DEFAULT_MAX_NODES = 40
CURVE_BUDGETS = list(range(10, 310, 10))
