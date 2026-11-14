"""Phase 08 — SHAP explanations for late-delivery model."""

from __future__ import annotations

from typing import Any

import joblib
import matplotlib

# Headless backend: the default Tk backend failed ("Can't find a usable
# init.tcl") and silently forced the native-importance fallback.
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
import pandas as pd

from scope.logging_config import setup_logging
from scope.models.common import load_shipments, project_paths, save_json

logger = setup_logging()


def run_shap_explainability(max_samples: int = 200) -> dict[str, Any]:
    paths = project_paths()
    bundle_path = paths["models"] / "late_delivery_classifier" / "model.joblib"
    bundle = joblib.load(bundle_path)
    pipe = bundle["pipeline"]
    features = bundle["features"]

    df = load_shipments()
    test_all = df[df["split"] == "test"].dropna(subset=["is_late"])
    test = test_all.sample(n=min(max_samples, len(test_all)), random_state=42)
    X = test[features]

    pre = pipe.named_steps["pre"]
    model = pipe.named_steps["model"]
    Xt = pre.transform(X)

    # Feature names after OHE
    try:
        feat_names = list(pre.get_feature_names_out())
    except Exception:
        feat_names = [f"f{i}" for i in range(Xt.shape[1])]

    try:
        import shap

        if hasattr(model, "coef_"):
            # Linear model (logistic regression baseline): background = train sample.
            train = df[df["split"] == "train"].dropna(subset=["is_late"])
            background = pre.transform(
                train[features].sample(n=min(500, len(train)), random_state=42)
            )
            explainer = shap.LinearExplainer(model, background)
            explainer_name = "LinearExplainer (log-odds)"
        else:
            # TreeExplainer works with xgboost/rf
            explainer = shap.TreeExplainer(model)
            explainer_name = "TreeExplainer"
        shap_values = explainer.shap_values(Xt)
        if isinstance(shap_values, list):
            shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        shap_values = np.asarray(shap_values)
        # RandomForest binary can yield (n, features, classes)
        if shap_values.ndim == 3:
            shap_values = shap_values[:, :, -1]
        if shap_values.ndim != 2:
            raise ValueError(f"Unexpected SHAP shape: {shap_values.shape}")

        fig_dir = paths["figures"] / "shap"
        fig_dir.mkdir(parents=True, exist_ok=True)

        plt.figure(figsize=(10, 6))
        shap.summary_plot(shap_values, Xt, feature_names=feat_names, show=False, max_display=20)
        summary_path = fig_dir / "shap_summary_late_delivery.png"
        plt.tight_layout()
        plt.savefig(summary_path, dpi=140, bbox_inches="tight")
        plt.close()

        mean_abs = np.abs(shap_values).mean(axis=0)
        importance = (
            pd.DataFrame({"feature": feat_names, "mean_abs_shap": mean_abs})
            .sort_values("mean_abs_shap", ascending=False)
            .head(30)
        )
        importance_path = paths["metrics"] / "shap_feature_importance.json"
        save_json(importance_path, importance.to_dict(orient="records"))

        # Local explanation for first test row
        local = {
            "row_id": int(test.iloc[0]["ID"]),
            "top_features": (
                pd.DataFrame(
                    {
                        "feature": feat_names,
                        "shap": shap_values[0],
                        "value": Xt[0],
                    }
                )
                .assign(abs_shap=lambda d: d["shap"].abs())
                .sort_values("abs_shap", ascending=False)
                .head(10)
                .to_dict(orient="records")
            ),
        }
        save_json(paths["metrics"] / "shap_local_example.json", local)

        result = {
            "status": "ok",
            "model_name": bundle.get("model_name"),
            "explainer": explainer_name,
            "n_samples": len(test),
            "summary_plot": str(summary_path),
            "importance_path": str(importance_path),
            "local_example": local,
            "top_global": importance.head(10).to_dict(orient="records"),
        }
    except Exception as exc:
        # Fallback: model feature importances if SHAP unavailable
        logger.warning("SHAP failed (%s); falling back to native importances", exc)
        native = getattr(model, "feature_importances_", None)
        if native is None and hasattr(model, "coef_"):
            native = np.abs(np.ravel(model.coef_))
        if native is not None:
            imp = (
                pd.DataFrame({"feature": feat_names, "importance": native})
                .sort_values("importance", ascending=False)
                .head(30)
            )
            # Not SHAP values -- keep them out of the SHAP importance file.
            save_json(paths["metrics"] / "native_feature_importance.json", imp.to_dict(orient="records"))
            result = {
                "status": "fallback_native_importance",
                "error": str(exc),
                "top_global": imp.head(10).to_dict(orient="records"),
            }
        else:
            result = {"status": "failed", "error": str(exc)}

    save_json(paths["metrics"] / "shap_explainability.json", result)
    logger.info("SHAP/explainability complete: %s", result.get("status"))
    return result


if __name__ == "__main__":
    print(run_shap_explainability())
