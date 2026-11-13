"""Phase 03 — Late delivery classification (XGBoost + Random Forest)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_recall_curve
from sklearn.model_selection import TimeSeriesSplit, cross_validate
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from scope.logging_config import setup_logging
from scope.db.experiments import log_experiment
from scope.models.common import (
    build_preprocessor,
    load_shipments,
    project_paths,
    save_json,
    save_model_bundle,
)

logger = setup_logging()

CAT = [
    "Country",
    "Managed_By",
    "Fulfill_Via",
    "Vendor_INCO_Term",
    "Shipment_Mode",
    "Product_Group",
    "Sub_Classification",
    "Vendor",
    "Dosage_Form",
    "First_Line_Designation",
]
NUM = [
    "Line_Item_Quantity",
    "Line_Item_Value",
    "Pack_Price",
    "Unit_Price",
    "Unit_Of_Measure_Per_Pack",
    "Weight_Kilograms_Numeric",
    "Freight_Cost_USD_Numeric",
    "Line_Item_Insurance_USD",
    "Scheduled_Month",
    "Scheduled_Quarter",
    "Scheduled_DOW",
    "Weight_NonNumeric_Flag",
    "Freight_NonNumeric_Flag",
    "vendor_hist_late_rate",
    "vendor_hist_median_delay",
]


def _metrics(y_true, y_pred, y_prob) -> dict[str, Any]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else None,
        "pr_auc": float(average_precision_score(y_true, y_prob))
        if len(np.unique(y_true)) > 1
        else None,
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
        "classification_report": classification_report(y_true, y_pred, output_dict=True, zero_division=0),
    }


def train_late_delivery() -> dict[str, Any]:
    df = load_shipments()
    work = df[df["is_late"].notna() & df["split"].isin(["train", "val", "test"])].copy()
    work["is_late"] = work["is_late"].astype(int)

    features = [c for c in CAT + NUM if c in work.columns]
    cat = [c for c in CAT if c in features]
    num = [c for c in NUM if c in features]

    train = work[work["split"] == "train"].sort_values("Scheduled_Delivery_Date_Parsed")
    val = work[work["split"] == "val"].sort_values("Scheduled_Delivery_Date_Parsed")
    test = work[work["split"] == "test"].sort_values("Scheduled_Delivery_Date_Parsed")

    pre = build_preprocessor(num, cat)
    # scale_pos_weight for imbalance
    pos = (train["is_late"] == 1).sum()
    neg = (train["is_late"] == 0).sum()
    spw = float(neg / max(pos, 1))

    xgb = XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=2,
        eval_metric="logloss",
        scale_pos_weight=spw,
        random_state=42,
        n_jobs=2,
    )
    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=2,
    )

    results: dict[str, Any] = {
        "target": "is_late",
        "definition": "1 if Delivered > Scheduled else 0",
        "prediction_moment": "Before delivery outcome; uses scheduled date calendar + order/vendor attrs",
        "features": features,
        "n_train": len(train),
        "n_val": len(val),
        "n_test": len(test),
        "class_balance_train": train["is_late"].value_counts().to_dict(),
        "class_balance_by_split": {
            split_name: {
                "n": int(len(part)),
                "positive_rate": float(part["is_late"].mean()) if len(part) else None,
            }
            for split_name, part in (("train", train), ("val", val), ("test", test))
        },
        "models": {},
    }

    train_prevalence = float(train["is_late"].mean())
    results["baselines"] = {
        "train_prevalence_probability": train_prevalence,
        "majority_class": int(train_prevalence >= 0.5),
        "vendor_history_only": {},
    }
    for split_name, part in (("val", val), ("test", test)):
        if not len(part):
            continue
        vendor_score = part["vendor_hist_late_rate"].fillna(train_prevalence).clip(0, 1).to_numpy()
        prior_score = np.full(len(part), train_prevalence)
        results["baselines"]["vendor_history_only"][split_name] = _metrics(
            part["is_late"], (vendor_score >= 0.5).astype(int), vendor_score
        )
        results["baselines"].setdefault("prevalence_probability", {})[split_name] = _metrics(
            part["is_late"], (prior_score >= 0.5).astype(int), prior_score
        )

    best_name = None
    best_f1 = -1.0
    best_pipe = None
    best_threshold = 0.5

    for name, clf in [("xgboost", xgb), ("random_forest", rf)]:
        pipe = Pipeline([("pre", pre), ("model", clf)])
        pipe.fit(train[features], train["is_late"])
        val_proba = pipe.predict_proba(val[features])[:, 1] if len(val) else np.array([])
        if len(val):
            precision, recall, thresholds = precision_recall_curve(val["is_late"], val_proba)
            f1_by_threshold = 2 * precision[:-1] * recall[:-1] / (
                precision[:-1] + recall[:-1] + 1e-12
            )
            threshold = float(thresholds[int(np.argmax(f1_by_threshold))]) if len(thresholds) else 0.5
        else:
            threshold = 0.5
        split_metrics = {}
        for split_name, part in [("val", val), ("test", test)]:
            if len(part) == 0:
                continue
            proba = pipe.predict_proba(part[features])[:, 1]
            pred = (proba >= threshold).astype(int)
            split_metrics[split_name] = _metrics(part["is_late"], pred, proba)
        split_metrics["decision_threshold"] = float(threshold)
        results["models"][name] = split_metrics
        val_f1 = split_metrics.get("val", {}).get("f1", 0.0) or 0.0
        if val_f1 > best_f1:
            best_f1 = val_f1
            best_name = name
            best_pipe = pipe
            best_threshold = float(threshold)

    # Rolling-origin diagnostic includes the full development period, including
    # validation dates, so it reflects the drift the model must face later.
    development = pd.concat([train, val]).sort_values("Scheduled_Delivery_Date_Parsed")
    cv_scores = cross_validate(
        best_pipe,
        development[features],
        development["is_late"],
        cv=TimeSeriesSplit(n_splits=3),
        scoring={"roc_auc": "roc_auc", "pr_auc": "average_precision"},
        n_jobs=1,
    )
    results["rolling_origin_cv"] = {
        "method": "TimeSeriesSplit",
        "n_splits": 3,
        "period": "train_plus_validation",
        "roc_auc_mean": float(cv_scores["test_roc_auc"].mean()),
        "roc_auc_std": float(cv_scores["test_roc_auc"].std()),
        "pr_auc_mean": float(cv_scores["test_pr_auc"].mean()),
        "pr_auc_std": float(cv_scores["test_pr_auc"].std()),
    }
    recent_train = train[train["Scheduled_Delivery_Date_Parsed"] >= "2010-01-01"]
    if len(recent_train) and len(val) and len(test):
        recent_pipe = clone(best_pipe).fit(recent_train[features], recent_train["is_late"])
        recent_val_proba = recent_pipe.predict_proba(val[features])[:, 1]
        recent_test_proba = recent_pipe.predict_proba(test[features])[:, 1]
        results["post_2010_training_sensitivity"] = {
            "n_train": len(recent_train),
            "validation": _metrics(
                val["is_late"], (recent_val_proba >= best_threshold).astype(int), recent_val_proba
            ),
            "test": _metrics(
                test["is_late"], (recent_test_proba >= best_threshold).astype(int), recent_test_proba
            ),
            "threshold_source": "full-training validation split; not retuned on test",
        }
    # Keep the train-only fitted estimator: the validation threshold was
    # calibrated on its probabilities, so refitting would change that scale.
    if len(test):
        test_proba = best_pipe.predict_proba(test[features])[:, 1]
        results["models"][best_name]["test"] = _metrics(
            test["is_late"], (test_proba >= best_threshold).astype(int), test_proba
        )
        results["models"][best_name]["decision_threshold"] = best_threshold
        results["class_balance_test"] = {
            "positive_rate": float(test["is_late"].mean()),
            "n": len(test),
        }
        results["test_roc_auc_gain_over_vendor_only"] = (
            results["models"][best_name]["test"]["roc_auc"]
            - results["baselines"]["vendor_history_only"]["test"]["roc_auc"]
        )

    bundle = {
        "pipeline": best_pipe,
        "model_name": best_name,
        "features": features,
        "categorical": cat,
        "numeric": num,
        "threshold": best_threshold,
        "target": "is_late",
        "metrics": results,
    }
    out = save_model_bundle("late_delivery_classifier", bundle)
    paths = project_paths()
    results["best_model"] = best_name
    results["artifact_dir"] = str(out)
    save_json(paths["metrics"] / "late_delivery_classification.json", results)
    try:
        results["db_ids"] = log_experiment(
            phase="03",
            task="late_delivery_classification",
            model_name=str(best_name),
            metrics=results,
            artifact_path=str(out),
            features=features,
        )
    except Exception as exc:
        logger.warning("Could not persist experiment metadata: %s", exc)
    logger.info("Late delivery model saved to %s (best=%s val_f1=%.3f)", out, best_name, best_f1)
    return results


if __name__ == "__main__":
    print(train_late_delivery())
