"""Phase 03 — Late delivery classification.

Per the proposal: XGBoost compared against a Logistic Regression baseline.
Random Forest is kept as an additional tree-ensemble comparison. The model
with the best validation F1 is saved; the threshold is tuned on validation only.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
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
    CalibratedClassifier,
    build_preprocessor,
    calibration_report,
    f1_optimal_threshold,
    fit_platt,
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
    "Manufacturing_Site",
    "Brand",
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

    # scale_pos_weight for imbalance
    pos = (train["is_late"] == 1).sum()
    neg = (train["is_late"] == 0).sum()
    spw = float(neg / max(pos, 1))

    xgb = XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.04,
        subsample=0.85,
        colsample_bytree=0.75,
        min_child_weight=2,
        reg_lambda=1.25,
        eval_metric="aucpr",
        scale_pos_weight=spw,
        random_state=42,
        n_jobs=2,
    )
    rf = RandomForestClassifier(
        n_estimators=400,
        max_depth=14,
        min_samples_leaf=3,
        max_features="sqrt",
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=2,
    )
    et = ExtraTreesClassifier(
        n_estimators=400,
        max_depth=14,
        min_samples_leaf=3,
        max_features="sqrt",
        class_weight="balanced",
        random_state=42,
        n_jobs=2,
    )
    logreg = LogisticRegression(
        C=1.0,
        class_weight="balanced",
        max_iter=2000,
        solver="lbfgs",
    )
    # Each candidate gets its own preprocessor; linear model gets log+scaling.
    candidates = [
        ("xgboost", xgb, build_preprocessor(num, cat)),
        ("logistic_regression", logreg, build_preprocessor(num, cat, scale_numeric=True)),
        ("random_forest", rf, build_preprocessor(num, cat)),
        ("extra_trees", et, build_preprocessor(num, cat)),
    ]

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
        "proposal_comparison": "xgboost vs logistic_regression (baseline); random_forest is an extra comparison",
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
    # Primary selection: validation F1 at the F1-optimal threshold. Break ties
    # with validation PR-AUC so ranking quality still influences the choice.
    selection_metric = "f1"

    for name, clf, pre in candidates:
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
        val_pr = split_metrics.get("val", {}).get("pr_auc", 0.0) or 0.0
        best_pr = (
            results["models"].get(best_name or "", {}).get("val", {}).get("pr_auc", 0.0) or 0.0
        )
        if val_f1 > best_f1 + 1e-12 or (abs(val_f1 - best_f1) <= 1e-12 and val_pr > best_pr):
            best_f1 = float(val_f1)
            best_name = name
            best_pipe = pipe
            best_threshold = float(threshold)
    results["selection_metric"] = selection_metric

    xgb_test = results["models"].get("xgboost", {}).get("test", {})
    lr_test = results["models"].get("logistic_regression", {}).get("test", {})
    if xgb_test and lr_test:
        results["xgboost_vs_logistic_baseline_test"] = {
            metric: {
                "xgboost": xgb_test.get(metric),
                "logistic_regression": lr_test.get(metric),
                "gain": (xgb_test[metric] - lr_test[metric])
                if xgb_test.get(metric) is not None and lr_test.get(metric) is not None
                else None,
            }
            for metric in ("precision", "recall", "f1", "roc_auc", "pr_auc")
        }

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
    # Probability calibration (Platt) on the validation split. Class weighting
    # made raw scores ~2.5x the real late rate, so they were not usable as
    # probabilities. Calibration is monotonic: ranking metrics are unchanged.
    # The train-only fitted estimator is kept; the calibrator maps its scale.
    model = best_pipe
    if len(val) and val["is_late"].nunique() > 1:
        raw_val = best_pipe.predict_proba(val[features])[:, 1]
        a, b = fit_platt(raw_val, val["is_late"].to_numpy())
        model = CalibratedClassifier(best_pipe, a, b, fitted_on="validation split")
        cal_val = model.calibrate(raw_val)
        best_threshold = f1_optimal_threshold(val["is_late"].to_numpy(), cal_val)
        results["calibration"] = {
            "method": "platt_on_validation",
            "a": a,
            "b": b,
            "validation_raw": calibration_report(val["is_late"], raw_val),
            "validation_calibrated": calibration_report(val["is_late"], cal_val),
        }
        if len(test):
            raw_test = best_pipe.predict_proba(test[features])[:, 1]
            results["calibration"]["test_raw"] = calibration_report(test["is_late"], raw_test)
            results["calibration"]["test_calibrated"] = calibration_report(
                test["is_late"], model.calibrate(raw_test)
            )
        results["calibration"]["note"] = (
            "Validation late rate differs from test (prior shift); use "
            "recalibrate_late_model() on recent delivered outcomes to refresh "
            "calibration and threshold as conditions drift."
        )

    if len(test):
        test_proba = model.predict_proba(test[features])[:, 1]
        results["models"][best_name]["test"] = _metrics(
            test["is_late"], (test_proba >= best_threshold).astype(int), test_proba
        )
        results["models"][best_name]["decision_threshold"] = best_threshold
        results["models"][best_name]["probabilities"] = (
            "calibrated" if model is not best_pipe else "raw"
        )
        results["class_balance_test"] = {
            "positive_rate": float(test["is_late"].mean()),
            "n": len(test),
        }
        results["test_roc_auc_gain_over_vendor_only"] = (
            results["models"][best_name]["test"]["roc_auc"]
            - results["baselines"]["vendor_history_only"]["test"]["roc_auc"]
        )

    bundle = {
        "pipeline": model,
        "model_name": best_name,
        "calibrated": model is not best_pipe,
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


def recalibrate_late_model(
    recent: pd.DataFrame | None = None, window_days: int = 365
) -> dict[str, Any]:
    """Refresh calibration + decision threshold on recent delivered outcomes.

    Drift fix for operations: the base model is unchanged; only the probability
    mapping and threshold are refit on the most recent ``window_days`` of
    shipments whose outcome is known. Do not run this on the held-out test
    period when reporting test metrics.
    """
    from scope.models.common import project_paths as _paths
    import joblib

    path = _paths()["models"] / "late_delivery_classifier" / "model.joblib"
    bundle = joblib.load(path)
    model = bundle["pipeline"]
    base = getattr(model, "base_pipeline", model)
    if recent is None:
        df = load_shipments()
        known = df[df["is_late"].notna() & df["Delivered_To_Client_Date_Parsed"].notna()]
        cutoff = known["Delivered_To_Client_Date_Parsed"].max() - pd.Timedelta(days=window_days)
        recent = known[known["Scheduled_Delivery_Date_Parsed"] >= cutoff]
    y = recent["is_late"].astype(int).to_numpy()
    if len(recent) < 200 or len(np.unique(y)) < 2:
        raise ValueError(f"Not enough recent labelled outcomes to recalibrate ({len(recent)} rows).")
    raw = base.predict_proba(recent[bundle["features"]])[:, 1]
    a, b = fit_platt(raw, y)
    new_model = CalibratedClassifier(base, a, b, fitted_on=f"recent {window_days} days")
    threshold = f1_optimal_threshold(y, new_model.calibrate(raw))
    bundle.update({"pipeline": new_model, "threshold": threshold, "calibrated": True})
    joblib.dump(bundle, path)
    info = {
        "n_rows": len(recent),
        "threshold": threshold,
        "calibration": calibration_report(y, new_model.calibrate(raw)),
    }
    logger.info("Late model recalibrated on %d recent rows (threshold=%.3f)", len(recent), threshold)
    return info


if __name__ == "__main__":
    print(train_late_delivery())
