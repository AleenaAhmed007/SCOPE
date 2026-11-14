"""Phase 07 - Experimental inventory stockout classifier."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, f1_score, precision_recall_curve, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from scope.logging_config import setup_logging
from scope.models.common import (
    build_preprocessor,
    load_shipments,
    project_paths,
    save_json,
    save_model_bundle,
)

logger = setup_logging()

# Deliberately exclude both operands of the derived label and all post-outcome
# inventory fields. This is an exploratory proxy model, not a stock balance rule.
INVENTORY_CATEGORICAL = [
    "Vendor",
    "Country",
    "Product_Group",
    "Shipment_Mode",
    "Vendor_INCO_Term",
    "Managed_By",
]
INVENTORY_NUMERIC = [
    "Inventory_Reorder_Level",
    "Inventory_Lead_Time_Days",
    "Scheduled_Month",
    "Scheduled_Quarter",
    "Scheduled_DOW",
    "Line_Item_Value",
    "Pack_Price",
    "Unit_Price",
    "Weight_Kilograms_Numeric",
    "Freight_Cost_USD_Numeric",
]
INVENTORY_FORBIDDEN_FEATURES = {
    "Inventory_Opening_Stock",
    "Line_Item_Quantity",
    "Inventory_Stockout_Flag",
    "Inventory_Shortage_Quantity",
    "Inventory_Closing_Stock",
    "Inventory_Replenishment_Triggered",
    "Inventory_Stock_Out",
}


def _binary_metrics(y_true: pd.Series, probability: np.ndarray, threshold: float) -> dict[str, Any]:
    prediction = (probability >= threshold).astype(int)
    return {
        "f1": float(f1_score(y_true, prediction, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, probability)) if y_true.nunique() > 1 else None,
        "pr_auc": float(average_precision_score(y_true, probability)) if y_true.nunique() > 1 else None,
        "precision": float(((prediction == 1) & (y_true.to_numpy() == 1)).sum() / max(prediction.sum(), 1)),
        "recall": float(((prediction == 1) & (y_true.to_numpy() == 1)).sum() / max((y_true.to_numpy() == 1).sum(), 1)),
        "confusion_matrix": [
            [int(((y_true == 0) & (prediction == 0)).sum()), int(((y_true == 0) & (prediction == 1)).sum())],
            [int(((y_true == 1) & (prediction == 0)).sum()), int(((y_true == 1) & (prediction == 1)).sum())],
        ],
    }


def _best_f1_threshold(y_true: pd.Series, probability: np.ndarray) -> float:
    precision, recall, thresholds = precision_recall_curve(y_true, probability)
    if not len(thresholds):
        return 0.5
    f1 = 2 * precision[:-1] * recall[:-1] / (precision[:-1] + recall[:-1] + 1e-12)
    return float(thresholds[int(np.argmax(f1))])


def train_inventory_experiment() -> dict[str, Any]:
    df = load_shipments()
    target = "Inventory_Stockout_Flag"
    work = df[df[target].notna() & df["split"].isin(["train", "val", "test"])].copy()
    work[target] = work[target].astype(int)
    categorical = [column for column in INVENTORY_CATEGORICAL if column in work]
    numeric = [column for column in INVENTORY_NUMERIC if column in work]
    features = categorical + numeric
    forbidden_present = sorted(set(features) & INVENTORY_FORBIDDEN_FEATURES)
    if forbidden_present:
        raise ValueError(f"Inventory target leakage features selected: {forbidden_present}")

    train = work[work["split"] == "train"]
    val = work[work["split"] == "val"]
    test = work[work["split"] == "test"]
    if train.empty or val.empty or test.empty:
        raise ValueError("Inventory classifier requires non-empty chronological train/val/test splits.")

    candidates = {
        "logistic_regression": LogisticRegression(
            max_iter=1000, class_weight="balanced", random_state=42
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=300,
            min_samples_leaf=5,
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=2,
        ),
    }
    results: dict[str, Any] = {
        "target": target,
        "target_rule": "Inventory_Opening_Stock - Line_Item_Quantity < 0",
        "features": features,
        "forbidden_features": sorted(INVENTORY_FORBIDDEN_FEATURES),
        "class_prevalence": {name: float(part[target].mean()) for name, part in (("train", train), ("val", val), ("test", test))},
        "models": {},
        "validation_baseline": {
            "model": "training_prevalence_probability",
            "probability": float(train[target].mean()),
            "pr_auc": float(average_precision_score(val[target], np.full(len(val), train[target].mean()))),
        },
        "experimental_warning": (
            "The label is a deterministic function of excluded opening-stock and quantity fields. "
            "This model uses other attributes as an exploratory proxy; source inventory provenance is unverified."
        ),
    }

    best_name = None
    best_score = -1.0
    best_pipeline = None
    best_threshold = 0.5
    preprocessor = build_preprocessor(numeric, categorical)
    for model_name, estimator in candidates.items():
        steps = [("pre", preprocessor)]
        if model_name == "logistic_regression":
            steps.append(("scale", StandardScaler()))
        steps.append(("model", estimator))
        pipeline = Pipeline(steps)
        pipeline.fit(train[features], train[target])
        val_probability = pipeline.predict_proba(val[features])[:, 1]
        threshold = _best_f1_threshold(val[target], val_probability)
        val_metrics = _binary_metrics(val[target], val_probability, threshold)
        val_metrics["threshold"] = threshold
        results["models"][model_name] = {"validation": val_metrics}
        score = val_metrics["pr_auc"] if val_metrics["pr_auc"] is not None else -1.0
        if score > best_score:
            best_name, best_score = model_name, score
            best_pipeline, best_threshold = pipeline, threshold

    test_probability = best_pipeline.predict_proba(test[features])[:, 1]
    results["models"][best_name]["test"] = _binary_metrics(test[target], test_probability, best_threshold)
    results["models"][best_name]["test"]["threshold"] = best_threshold
    results["best_model"] = best_name
    results["predictive_model_trained"] = True
    selected_val_ap = results["models"][best_name]["validation"]["pr_auc"]
    prevalence_val_ap = results["validation_baseline"]["pr_auc"]
    results["selected_model_beats_prevalence_baseline"] = bool(
        selected_val_ap is not None
        and prevalence_val_ap is not None
        and selected_val_ap > prevalence_val_ap + 1e-9
    )

    rule = (test["Inventory_Opening_Stock"] - test["Line_Item_Quantity"] < 0).astype(int)
    results["test_rule_agreement"] = float((rule == test[target]).mean())

    bundle = {
        "pipeline": best_pipeline,
        "model_name": best_name,
        "features": features,
        "categorical": categorical,
        "numeric": numeric,
        "threshold": best_threshold,
        "target": target,
        "prediction_basis": "experimental_ml_proxy_excluding_deterministic_rule_operands",
        "metrics": results,
    }
    artifact = save_model_bundle("inventory_stockout_classifier", bundle)
    results["artifact_dir"] = str(artifact)
    save_json(project_paths()["metrics"] / "inventory_experiment.json", results)
    logger.info("Inventory proxy classifier saved: %s (best=%s)", artifact, best_name)
    return results


if __name__ == "__main__":
    print(train_inventory_experiment())
