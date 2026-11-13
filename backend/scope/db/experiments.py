"""Persist ML experiment / model version metadata."""

from __future__ import annotations

import json
import uuid
from typing import Any

from scope.db.models import MLExperiment, ModelMetric, ModelVersion
from scope.db.session import get_session, init_db


def log_experiment(
    phase: str,
    task: str,
    model_name: str,
    metrics: dict[str, Any],
    artifact_path: str | None = None,
    features: list[str] | None = None,
) -> dict[str, str]:
    init_db()
    session = get_session()
    try:
        exp_id = str(uuid.uuid4())
        ver_id = str(uuid.uuid4())
        session.add(
            MLExperiment(
                experiment_id=exp_id,
                phase=phase,
                task=task,
                model_name=model_name,
                metrics_json=json.dumps(metrics, default=str),
                artifact_path=artifact_path,
            )
        )
        session.add(
            ModelVersion(
                version_id=ver_id,
                model_name=model_name,
                task=task,
                artifact_path=artifact_path or "",
                feature_list_json=json.dumps(features or []),
            )
        )
        # Flatten common split metrics when present
        models = metrics.get("models") or {}
        best = metrics.get("best_model")
        selected = models.get(best) if best else None
        if isinstance(selected, dict):
            for split_name, split_metrics in selected.items():
                if not isinstance(split_metrics, dict):
                    continue
                for metric_name, metric_value in split_metrics.items():
                    if isinstance(metric_value, (int, float)):
                        session.add(
                            ModelMetric(
                                metric_id=str(uuid.uuid4()),
                                version_id=ver_id,
                                split_name=split_name,
                                metric_name=metric_name,
                                metric_value=float(metric_value),
                            )
                        )
        session.commit()
        return {"experiment_id": exp_id, "version_id": ver_id}
    finally:
        session.close()
