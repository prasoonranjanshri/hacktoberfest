"""In-memory artifact store and lifecycle management."""

from pathlib import Path
import json
from typing import Any, Optional
import pandas as pd

from backend.app.config import ARTIFACTS_DIR
from backend.app.errors import APIError, ARTIFACTS_NOT_FOUND
from common.artifact_schema import validate_artifacts


class ArtifactStore:
    """Loads and holds validated artifacts in memory."""

    def __init__(self, artifacts_dir: Path = ARTIFACTS_DIR):
        self.artifacts_dir = Path(artifacts_dir)
        self.loaded: bool = False
        self.errors: list[str] = []
        self.data_source: Optional[str] = None
        self.generated_at: Optional[str] = None
        self.accounts_df: Optional[pd.DataFrame] = None
        self.transactions_df: Optional[pd.DataFrame] = None
        self.reasons: Optional[dict[str, list[dict[str, Any]]]] = None
        self.metrics: Optional[dict[str, Any]] = None
        self.drift: Optional[dict[str, Any]] = None
        self.load()

    def load(self) -> None:
        """Attempt to validate and load all artifacts into memory."""
        self.errors = validate_artifacts(self.artifacts_dir)
        if self.errors:
            self.loaded = False
            return

        try:
            accounts_file = self.artifacts_dir / "accounts.csv"
            txns_file = self.artifacts_dir / "transactions.csv"
            reasons_file = self.artifacts_dir / "reasons.json"
            metrics_file = self.artifacts_dir / "metrics.json"
            drift_file = self.artifacts_dir / "drift.json"

            self.accounts_df = pd.read_csv(
                accounts_file,
                dtype={"account_id": str, "typology": str, "ring_id": str},
                keep_default_na=False,
            )
            self.transactions_df = pd.read_csv(
                txns_file,
                dtype={
                    "sender_id": str,
                    "receiver_id": str,
                    "txn_id": str,
                    "typology": str,
                },
                keep_default_na=False,
            )
            with open(reasons_file, "r", encoding="utf-8") as f:
                self.reasons = json.load(f)
            with open(metrics_file, "r", encoding="utf-8") as f:
                self.metrics = json.load(f)

            if drift_file.exists():
                try:
                    with open(drift_file, "r", encoding="utf-8") as f:
                        self.drift = json.load(f)
                except Exception:
                    self.drift = None
            else:
                self.drift = None

            self.data_source = self.metrics.get("data_source")
            self.generated_at = self.metrics.get("generated_at")
            self.loaded = True
        except Exception as e:
            self.errors.append(f"Failed to load artifacts into memory: {e}")
            self.loaded = False


_store_instance: Optional[ArtifactStore] = None


def get_store() -> ArtifactStore:
    """Dependency to retrieve the artifact store singleton."""
    global _store_instance
    if _store_instance is None:
        _store_instance = ArtifactStore()
    return _store_instance


def require_loaded_store() -> ArtifactStore:
    """Dependency ensuring artifacts are present and valid before handling request."""
    store = get_store()
    if not store.loaded:
        raise APIError(
            code=ARTIFACTS_NOT_FOUND,
            message="Artifacts missing or invalid. Run: python -m ml.run_pipeline",
            status_code=503,
            details={"errors": store.errors},
        )
    return store
