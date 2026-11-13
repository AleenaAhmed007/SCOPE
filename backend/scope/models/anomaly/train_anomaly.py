"""Phase 06b - Unusual shipment profiles and retrospective anomaly analysis."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline

from scope.logging_config import setup_logging
from scope.models.classification.train_late import NUM
from scope.models.common import (
    build_preprocessor,
    load_shipments,
    project_paths,
    save_json,
    save_model_bundle,
)

logger = setup_logging()


def _fit_anomaly(df: pd.DataFrame, features: list[str], cat: list[str], num: list[str], name: str) -> dict[str, Any]:
    train = df[df["split"] == "train"]
    pre = build_preprocessor(num, cat)
    model = IsolationForest(
        n_estimators=200,
        contamination="auto",
        random_state=42,
        n_jobs=2,
    )
    pipe = Pipeline([("pre", pre), ("model", model)])
    pipe.fit(train[features])
    scores = -pipe.decision_function(df[features])
    preds = pipe.predict(df[features])  # -1 anomaly
    df_out = df[["ID", "Vendor", "Country", "split"]].copy()
    df_out["anomaly_score"] = scores
    df_out["is_anomaly"] = (preds == -1).astype(int)
    df_out["signal_type"] = "unusual_shipment_profile"
    paths = project_paths()
    out_path = paths["processed"] / f"anomaly_scores_{name}.parquet"
    df_out.to_parquet(out_path, index=False)
    bundle = {
        "pipeline": pipe,
        "features": features,
        "label": "unusual_shipment_profile",
        "metrics": {
            "n_scored": len(df_out),
            "n_anomaly": int(df_out["is_anomaly"].sum()),
            "anomaly_rate": float(df_out["is_anomaly"].mean()),
        },
    }
    art = save_model_bundle(f"anomaly_{name}", bundle)
    bundle["metrics"]["artifact_dir"] = str(art)
    bundle["metrics"]["scores_path"] = str(out_path)
    return bundle["metrics"]


def train_anomaly_models() -> dict[str, Any]:
    df = load_shipments()
    # Exclude sparse categorical IDs and focus the anomaly score on numeric shipment profile.
    # Vendor-history features depend on outcome availability and have a
    # different point-in-time distribution than static shipment attributes.
    vendor_history = {"vendor_hist_late_rate", "vendor_hist_median_delay", "vendor_hist_shipment_count"}
    features = [c for c in NUM if c in df.columns and c not in vendor_history]
    cat: list[str] = []
    num = features.copy()
    unusual_profile = _fit_anomaly(df, features, cat, num, "unusual_profile")

    # Retrospective may include outcome fields for forensic analysis only
    retro_feats = features + [c for c in ["delay_days"] if c in df.columns]
    # delay_days has NA — fill for retrospective forensic model only
    df_retro = df.copy()
    df_retro["delay_days"] = df_retro["delay_days"].fillna(df_retro["delay_days"].median())
    retro_num = num + (["delay_days"] if "delay_days" in retro_feats else [])
    retro = _fit_anomaly(df_retro, retro_feats, cat, retro_num, "retrospective")

    results = {
        "unusual_profile": unusual_profile,
        "retrospective": retro,
        "label": "unusual_shipment_profile",
        "note": "Scores indicate unusual numeric shipment profiles. They are not delay predictors or labeled accuracy estimates; retrospective includes outcome data and is forensic only.",
    }
    save_json(project_paths()["metrics"] / "anomaly_detection.json", results)
    logger.info("Anomaly models trained")
    return results


if __name__ == "__main__":
    print(train_anomaly_models())
