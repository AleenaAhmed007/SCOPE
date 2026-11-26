"""Build proposal-aligned model results and baseline comparison tables.

Follows SCOPE proposal section 6 (Models):
  Task                         | Model
  Late-delivery risk           | XGBoost, Random Forest
  Delay and volume forecasting | LSTM (classical naive/ARIMA compared)
  Lead-time prediction         | Gradient-boosted regression
  Supplier segmentation        | K-Means
  Anomaly detection            | Isolation Forest
  Inventory risk               | Classification
  Document retrieval           | Embeddings, BM25, cross-encoder reranker
  Explanations                 | SHAP

Baselines: Logistic Regression, naive forecast, ARIMA.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _r(value: Any, digits: int = 3) -> str:
    if value is None or value == "":
        return ""
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def _load() -> dict[str, Any]:
    return json.loads((_root() / "reports" / "final_evaluation.json").read_text(encoding="utf-8"))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def build_rows(fe: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    late = fe.get("late_delivery") or {}
    dur = fe.get("duration") or {}
    fc = fe.get("forecasting") or {}
    seg = fe.get("vendor_segmentation") or {}
    anom = fe.get("anomaly") or {}
    inv = fe.get("inventory") or {}
    rag = fe.get("rag_retrieval") or {}
    shap = fe.get("shap") or {}
    me = fe.get("model_evaluations") or {}

    # Optional ARIMA/naive test scores persisted under forecasting metrics if present;
    # fall back to selected-model fields + known classical comparisons.
    late_fc = fc.get("late_rate_monthly") or {}
    vol_fc = fc.get("volume_monthly") or {}
    late_eval = (me.get("forecast_late_rate") or {}).get("test") or {}
    vol_eval = (me.get("forecast_volume") or {}).get("test") or {}

    # Proposal map
    proposal_map = [
        {
            "task": "Late-delivery risk",
            "proposed_models": "XGBoost, Random Forest",
            "baseline": "Logistic Regression",
            "implemented": "yes",
        },
        {
            "task": "Delay and volume forecasting",
            "proposed_models": "LSTM",
            "baseline": "Naive forecast, ARIMA",
            "implemented": "classical candidates trained; LSTM not trained (short monthly history)",
        },
        {
            "task": "Lead-time prediction",
            "proposed_models": "Gradient-boosted regression",
            "baseline": "Historical median",
            "implemented": "yes",
        },
        {
            "task": "Supplier segmentation",
            "proposed_models": "K-Means",
            "baseline": "N/A (unsupervised)",
            "implemented": "yes",
        },
        {
            "task": "Anomaly detection",
            "proposed_models": "Isolation Forest",
            "baseline": "N/A (unsupervised)",
            "implemented": "yes",
        },
        {
            "task": "Inventory risk",
            "proposed_models": "Classification on stock cover vs lead time",
            "baseline": "Logistic Regression / prevalence",
            "implemented": "yes (experimental)",
        },
        {
            "task": "Document retrieval",
            "proposed_models": "Embeddings, BM25, cross-encoder reranker",
            "baseline": "N/A (wiring benchmark)",
            "implemented": "yes",
        },
        {
            "task": "Explanations",
            "proposed_models": "SHAP",
            "baseline": "N/A",
            "implemented": "yes",
        },
    ]

    results: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []

    # ---- Late-delivery risk: XGB + RF vs Logistic Regression ----
    for model in ("xgboost", "random_forest", "logistic_regression"):
        block = (late.get("models") or {}).get(model) or {}
        test = block.get("test") or {}
        role = "baseline" if model == "logistic_regression" else "proposed_model"
        results.append(
            {
                "task": "Late-delivery risk",
                "model": model,
                "role": role,
                "split": "test",
                "metric_1": "roc_auc",
                "value_1": _r(test.get("roc_auc")),
                "metric_2": "pr_auc",
                "value_2": _r(test.get("pr_auc")),
                "metric_3": "f1",
                "value_3": _r(test.get("f1")),
                "notes": "Proposal models vs Logistic Regression baseline",
            }
        )
    lr = ((late.get("models") or {}).get("logistic_regression") or {}).get("test") or {}
    for model in ("xgboost", "random_forest"):
        test = ((late.get("models") or {}).get(model) or {}).get("test") or {}
        for metric in ("roc_auc", "pr_auc", "f1"):
            comparisons.append(
                {
                    "task": "Late-delivery risk",
                    "proposed_model": model,
                    "baseline": "logistic_regression",
                    "metric": metric,
                    "model_value": _r(test.get(metric)),
                    "baseline_value": _r(lr.get(metric)),
                    "delta": _r((test.get(metric) or 0) - (lr.get(metric) or 0)),
                    "beats_baseline": str((test.get(metric) or 0) > (lr.get(metric) or 0)).lower(),
                    "notes": "Higher is better",
                }
            )

    # ---- Forecasting: LSTM proposed; compare naive + ARIMA (+ selected classical) ----
    # Persist ARIMA test scores computed alongside regenerator when available.
    arima_scores = fc.get("proposal_baseline_test_scores") or {}
    late_arima = (arima_scores.get("late_rate") or {}).get("arima")
    late_naive = (arima_scores.get("late_rate") or {}).get("naive_lag1", late_fc.get("naive_lag1_test_mae"))
    vol_arima = (arima_scores.get("volume") or {}).get("arima")
    vol_naive = (arima_scores.get("volume") or {}).get("naive_lag1", vol_fc.get("naive_lag1_test_mae"))

    results.append(
        {
            "task": "Delay forecasting (monthly late rate)",
            "model": "LSTM",
            "role": "proposed_model",
            "split": "test",
            "metric_1": "mae",
            "value_1": "",
            "metric_2": "",
            "value_2": "",
            "metric_3": "",
            "value_3": "",
            "notes": (fc.get("lstm") or {}).get("reason")
            or "Not trained; monthly history too short for a justified LSTM",
        }
    )
    for model, mae, role in (
        ("naive_forecast", late_naive, "baseline"),
        ("ARIMA", late_arima, "baseline"),
        (late_fc.get("selected_model", "selected_classical"), late_fc.get("mae"), "selected_classical"),
    ):
        results.append(
            {
                "task": "Delay forecasting (monthly late rate)",
                "model": str(model),
                "role": role,
                "split": "test",
                "metric_1": "mae",
                "value_1": _r(mae, 4),
                "metric_2": "",
                "value_2": "",
                "metric_3": "",
                "value_3": "",
                "notes": "Lower MAE is better; shipment-count weighted",
            }
        )
    if late_arima is not None and late_naive is not None:
        comparisons.append(
            {
                "task": "Delay forecasting (monthly late rate)",
                "proposed_model": "ARIMA (classical stand-in; LSTM not trained)",
                "baseline": "naive_forecast",
                "metric": "mae",
                "model_value": _r(late_arima, 4),
                "baseline_value": _r(late_naive, 4),
                "delta": _r(late_arima - late_naive, 4),
                "beats_baseline": str(late_arima < late_naive).lower(),
                "notes": "Lower MAE is better",
            }
        )

    results.append(
        {
            "task": "Volume forecasting (monthly quantity)",
            "model": "LSTM",
            "role": "proposed_model",
            "split": "test",
            "metric_1": "mae",
            "value_1": "",
            "metric_2": "",
            "value_2": "",
            "metric_3": "",
            "value_3": "",
            "notes": (fc.get("lstm") or {}).get("reason")
            or "Not trained; monthly history too short for a justified LSTM",
        }
    )
    for model, mae, role in (
        ("naive_forecast", vol_naive, "baseline"),
        ("ARIMA", vol_arima, "baseline"),
        (vol_fc.get("selected_model", "selected_classical"), vol_fc.get("mae"), "selected_classical"),
    ):
        results.append(
            {
                "task": "Volume forecasting (monthly quantity)",
                "model": str(model),
                "role": role,
                "split": "test",
                "metric_1": "mae",
                "value_1": _r(mae, 1),
                "metric_2": "",
                "value_2": "",
                "metric_3": "",
                "value_3": "",
                "notes": "Lower MAE is better; quantity proxy not warehouse demand",
            }
        )
    if vol_arima is not None and vol_naive is not None:
        comparisons.append(
            {
                "task": "Volume forecasting (monthly quantity)",
                "proposed_model": "ARIMA (classical stand-in; LSTM not trained)",
                "baseline": "naive_forecast",
                "metric": "mae",
                "model_value": _r(vol_arima, 1),
                "baseline_value": _r(vol_naive, 1),
                "delta": _r(vol_arima - vol_naive, 1),
                "beats_baseline": str(vol_arima < vol_naive).lower(),
                "notes": "Lower MAE is better",
            }
        )

    # ---- Lead-time: Gradient boosting vs median ----
    gb = ((dur.get("models") or {}).get("gradient_boosting") or {}).get("test") or {}
    median = ((dur.get("models") or {}).get("dummy_median") or {}).get("test") or {}
    results.append(
        {
            "task": "Lead-time prediction",
            "model": "gradient_boosting",
            "role": "proposed_model",
            "split": "test",
            "metric_1": "mae_days",
            "value_1": _r(gb.get("mae")),
            "metric_2": "r2",
            "value_2": _r(gb.get("r2")),
            "metric_3": "",
            "value_3": "",
            "notes": "PO-to-client duration",
        }
    )
    results.append(
        {
            "task": "Lead-time prediction",
            "model": "historical_median",
            "role": "baseline",
            "split": "test",
            "metric_1": "mae_days",
            "value_1": _r(median.get("mae")),
            "metric_2": "r2",
            "value_2": _r(median.get("r2")),
            "metric_3": "",
            "value_3": "",
            "notes": "Simple baseline",
        }
    )
    if gb and median:
        comparisons.append(
            {
                "task": "Lead-time prediction",
                "proposed_model": "gradient_boosting",
                "baseline": "historical_median",
                "metric": "mae_days",
                "model_value": _r(gb.get("mae")),
                "baseline_value": _r(median.get("mae")),
                "delta": _r((gb.get("mae") or 0) - (median.get("mae") or 0)),
                "beats_baseline": str((gb.get("mae") or 0) < (median.get("mae") or 0)).lower(),
                "notes": "Lower MAE is better",
            }
        )

    # ---- Supplier segmentation ----
    results.append(
        {
            "task": "Supplier segmentation",
            "model": "kmeans",
            "role": "proposed_model",
            "split": "full",
            "metric_1": "k",
            "value_1": str(seg.get("k", "")),
            "metric_2": "silhouette",
            "value_2": _r(seg.get("silhouette")),
            "metric_3": "n_clustered_vendors",
            "value_3": str(seg.get("n_clustered_vendors", "")),
            "notes": "Unsupervised; no labeled baseline",
        }
    )

    # ---- Anomaly detection ----
    unusual = anom.get("unusual_profile") or {}
    vendor_kpi = anom.get("vendor_kpi") or {}
    results.append(
        {
            "task": "Anomaly detection",
            "model": "isolation_forest_unusual_profile",
            "role": "proposed_model",
            "split": "test",
            "metric_1": "anomaly_rate",
            "value_1": _r((unusual.get("anomaly_rate_by_split") or {}).get("test")),
            "metric_2": "n_anomaly",
            "value_2": str(unusual.get("n_anomaly", "")),
            "metric_3": "",
            "value_3": "",
            "notes": "Unsupervised; no ground-truth labels",
        }
    )
    results.append(
        {
            "task": "Anomaly detection",
            "model": "isolation_forest_vendor_kpi",
            "role": "proposed_model",
            "split": "all_periods",
            "metric_1": "n_anomaly",
            "value_1": str(vendor_kpi.get("n_anomaly", "")),
            "metric_2": "n_periods",
            "value_2": str(vendor_kpi.get("n_periods", "")),
            "metric_3": "",
            "value_3": "",
            "notes": "Proposal supplier-KPI anomaly model",
        }
    )

    # ---- Inventory risk ----
    inv_models = inv.get("models") or {}
    for model, role in (("random_forest", "proposed_model"), ("logistic_regression", "baseline")):
        block = inv_models.get(model) or {}
        # RF has test; logreg may be validation-only
        split = "test" if "test" in block else ("validation" if "validation" in block else "")
        metrics = block.get(split) or {}
        results.append(
            {
                "task": "Inventory risk",
                "model": model,
                "role": role,
                "split": split,
                "metric_1": "pr_auc",
                "value_1": _r(metrics.get("pr_auc")),
                "metric_2": "roc_auc",
                "value_2": _r(metrics.get("roc_auc")),
                "metric_3": "f1",
                "value_3": _r(metrics.get("f1")),
                "notes": "Experimental; inventory provenance unverified",
            }
        )
    rf_val = (inv_models.get("random_forest") or {}).get("validation") or {}
    lr_val = (inv_models.get("logistic_regression") or {}).get("validation") or {}
    if rf_val and lr_val:
        comparisons.append(
            {
                "task": "Inventory risk",
                "proposed_model": "random_forest",
                "baseline": "logistic_regression",
                "metric": "pr_auc",
                "model_value": _r(rf_val.get("pr_auc")),
                "baseline_value": _r(lr_val.get("pr_auc")),
                "delta": _r((rf_val.get("pr_auc") or 0) - (lr_val.get("pr_auc") or 0)),
                "beats_baseline": str((rf_val.get("pr_auc") or 0) > (lr_val.get("pr_auc") or 0)).lower(),
                "notes": "Validation comparison; higher is better",
            }
        )

    # ---- Document retrieval ----
    primary = rag.get("primary") or rag.get("metrics") or {}
    if isinstance(primary, dict):
        results.append(
            {
                "task": "Document retrieval",
                "model": "embeddings+BM25+cross-encoder",
                "role": "proposed_model",
                "split": "synthetic_queries",
                "metric_1": "mrr",
                "value_1": _r(primary.get("mrr")),
                "metric_2": "recall@3",
                "value_2": _r((primary.get("section_recall_at_k") or {}).get("3")),
                "metric_3": "",
                "value_3": "",
                "notes": "Wiring sanity check on synthetic queries, not a quality benchmark",
            }
        )

    # ---- Explanations ----
    results.append(
        {
            "task": "Explanations",
            "model": "SHAP",
            "role": "proposed_model",
            "split": "sample",
            "metric_1": "status",
            "value_1": str(shap.get("status", "")),
            "metric_2": "n_samples",
            "value_2": str(shap.get("n_samples", "")),
            "metric_3": "explainer",
            "value_3": str(shap.get("explainer", "")),
            "notes": "Global/local explanations for late-delivery model",
        }
    )

    return proposal_map, results, comparisons


def _write_markdown(
    path: Path,
    proposal_map: list[dict[str, Any]],
    results: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
    generated_at: str,
) -> None:
    sections = [
        "# Proposal Model Results and Baseline Comparison",
        "",
        "Aligned to SCOPE proposal **§6 Models**.",
        "",
        f"Source: `reports/final_evaluation.json` (`{generated_at}`).",
        "",
        "Regenerate:",
        "",
        "```bash",
        "python scripts/build_proposal_model_tables.py",
        "```",
        "",
        "## 6. Models (proposal map)",
        "",
        _md_table(
            ["Task", "Model", "Baseline", "Implemented"],
            [
                [r["task"], r["proposed_models"], r["baseline"], r["implemented"]]
                for r in proposal_map
            ],
        ),
        "",
        "> ML and DL models are compared with simple baselines (**Logistic Regression, naive forecast, ARIMA**).",
        "",
        "## Results by proposal task",
        "",
        _md_table(
            ["Task", "Model", "Role", "Split", "Metric", "Value", "Metric 2", "Value 2", "Notes"],
            [
                [
                    r["task"],
                    r["model"],
                    r["role"],
                    r["split"],
                    r["metric_1"],
                    r["value_1"],
                    r["metric_2"],
                    r["value_2"],
                    r["notes"],
                ]
                for r in results
            ],
        ),
        "",
        "## Proposed model vs baseline",
        "",
        _md_table(
            [
                "Task",
                "Proposed model",
                "Baseline",
                "Metric",
                "Model",
                "Baseline value",
                "Delta",
                "Beats baseline?",
                "Notes",
            ],
            [
                [
                    r["task"],
                    r["proposed_model"],
                    r["baseline"],
                    r["metric"],
                    r["model_value"],
                    r["baseline_value"],
                    r["delta"],
                    r["beats_baseline"],
                    r["notes"],
                ]
                for r in comparisons
            ],
        ),
        "",
        "## CSV outputs",
        "",
        "| File | Contents |",
        "| --- | --- |",
        "| `reports/metrics/proposal_model_map.csv` | Proposal §6 task → model map |",
        "| `reports/metrics/proposal_model_results.csv` | Per-task metrics |",
        "| `reports/metrics/proposal_vs_baseline.csv` | Proposed models vs baselines |",
        "",
    ]
    path.write_text("\n".join(sections), encoding="utf-8")


def _attach_arima_scores(fe: dict[str, Any]) -> dict[str, Any]:
    """Compute naive/ARIMA test MAE so proposal baselines are explicit."""
    try:
        import numpy as np
        import pandas as pd
        from sklearn.metrics import mean_absolute_error

        from scope.data.table_io import read_table
        from scope.models.forecasting.train_forecast import _candidates, _forecast_splits
    except Exception:
        return fe

    def score(path: Path, col: str) -> dict[str, float]:
        ts = read_table(path)
        train, val, test = _forecast_splits(ts, col)
        development = pd.concat([train, val])
        feats = [c for c in development.columns if c not in {"y", "sample_weight"}]
        weighted = "sample_weight" in development
        w_dev = development["sample_weight"] if weighted else None
        w_test = test["sample_weight"] if weighted else None
        lower, upper = (0.0, 1.0) if col == "late_rate" else (0.0, None)

        def bound(values: np.ndarray) -> np.ndarray:
            return np.clip(values, lower, upper) if upper is not None else np.maximum(values, lower)

        out: dict[str, float] = {}
        for name in ("naive_lag1", "arima", "mean_baseline"):
            model = _candidates()[name]
            model.fit(development[feats], development["y"], sample_weight=w_dev)
            pred = bound(model.predict(test[feats]))
            out[name] = float(mean_absolute_error(test["y"], pred, sample_weight=w_test))
        return out

    root = _root()
    fc = fe.setdefault("forecasting", {})
    fc["proposal_baseline_test_scores"] = {
        "late_rate": score(root / "data" / "processed" / "delay_timeseries_monthly.csv", "late_rate"),
        "volume": score(
            root / "data" / "processed" / "volume_timeseries_monthly.csv",
            "total_line_item_quantity",
        ),
    }
    return fe


def main() -> None:
    fe = _attach_arima_scores(_load())
    proposal_map, results, comparisons = build_rows(fe)
    metrics = _root() / "reports" / "metrics"
    _write_csv(metrics / "proposal_model_map.csv", proposal_map)
    _write_csv(metrics / "proposal_model_results.csv", results)
    _write_csv(metrics / "proposal_vs_baseline.csv", comparisons)
    _write_markdown(
        _root() / "reports" / "proposal_model_baseline_comparison.md",
        proposal_map,
        results,
        comparisons,
        fe.get("generated_at", ""),
    )
    # Keep ARIMA scores in final_evaluation for reproducibility of the tables.
    (_root() / "reports" / "final_evaluation.json").write_text(
        json.dumps(fe, indent=2, default=str), encoding="utf-8"
    )
    print("Wrote proposal-aligned tables under reports/metrics/ and reports/proposal_model_baseline_comparison.md")


if __name__ == "__main__":
    main()
