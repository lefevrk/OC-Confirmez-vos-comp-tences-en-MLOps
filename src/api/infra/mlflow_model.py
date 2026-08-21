"""MLflow adapter used only during FastAPI startup."""

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any

from loguru import logger
import mlflow
from mlflow.artifacts import download_artifacts
import mlflow.sklearn as mlflow_sklearn
from mlflow.tracking import MlflowClient
import pandas as pd

from api.infra.config import Settings


@dataclass(frozen=True)
class MlflowScoringModel:
    """MLflow sklearn model and the threshold logged by its source run."""

    model: Any
    version: str
    threshold: float

    def probability(self, features: dict[str, Any]) -> float:
        """Score in memory; this method intentionally makes no MLflow call."""
        probabilities = self.model.predict_proba(pd.DataFrame([features]))
        return float(probabilities[0][1])


def load_champion(settings: Settings) -> MlflowScoringModel:
    """Fetch model, version and threshold exactly once at startup."""
    os.environ["MLFLOW_TRACKING_USERNAME"] = settings.mlflow_tracking_username
    os.environ["MLFLOW_TRACKING_PASSWORD"] = settings.mlflow_tracking_password
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    model_registry_client = MlflowClient(tracking_uri=settings.mlflow_tracking_uri)

    logger.bind(model_name=settings.model_name, model_alias=settings.model_alias).debug(
        "mlflow_champion_resolution_started"
    )
    registered_model_version = model_registry_client.get_model_version_by_alias(
        settings.model_name,
        settings.model_alias,
    )
    source_run_id = registered_model_version.run_id

    if source_run_id is None:
        raise RuntimeError("The registered model version has no source run")

    logger.bind(run_id=source_run_id).debug("mlflow_threshold_artifact_download_started")
    threshold_artifact_path = download_artifacts(
        artifact_uri=f"runs:/{source_run_id}/threshold.json"
    )
    threshold_artifact = json.loads(Path(threshold_artifact_path).read_text())
    threshold = float(threshold_artifact["optimal_threshold"])
    if not 0 <= threshold <= 1:
        raise RuntimeError(f"Champion threshold {threshold} is outside the [0, 1] range")

    logger.bind(run_id=source_run_id).debug("mlflow_sklearn_model_load_started")
    sklearn_model = mlflow_sklearn.load_model(
        f"models:/{settings.model_name}@{settings.model_alias}"
    )

    model_version = str(registered_model_version.version)
    logger.bind(model_version=model_version, threshold=threshold).info("mlflow_champion_loaded")

    return MlflowScoringModel(
        model=sklearn_model,
        version=model_version,
        threshold=threshold,
    )
