"""Build model-result and baseline-comparison tables from final_evaluation.json."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _r(value: float | None, digits: int = 3) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def _load() -> dict[str, Any]:
    path = _root() / "reports" / "final_evaluation.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _late_delivery_rows(fe: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ld = fe["late_delivery"]
    best = ld.get("best_model")
    results: list[dict[str, Any]] = []
    for name, block in ld["models"].items():
        for split_key, split_label in (("val", "validation"), ("test", "test")):
            m = block[split_key]
            results.append(
                {
                    "task": "late_delivery",
                    "model": name,
                    "role": "selected" if name == best else "candidate",
                    "split": split_label,
                    "threshold": _r(block.get("decision_threshold"), 3),
                    "accuracy": _r(m.get("accuracy")),
                    "precision": _r(m.get("precision")),
                    "recall": _r(m.get("recall")),
                    "f1": _r(m.get("f1")),
                    "roc_auc": _r(m.get("roc_auc")),
                    "pr_auc": _r(m.get("pr_auc")),
                }
            )

    # Baselines on test
    for bname, label in (
        ("vendor_history_only", "vendor_history_only"),
        ("prevalence_probability", "prevalence_probability"),
    ):
        m = ld["baselines"][bname]["test"]
        results.append(
            {
                "task": "late_delivery",
                "model": label,
                "role": "baseline",
                "split": "test",
                "threshold": "",
                "accuracy": _r(m.get("accuracy")),
                "precision": _r(m.get("precision")),
                "recall": _r(m.get("recall")),
                "f1": _r(m.get("f1")),
                "roc_auc": _r(m.get("roc_auc")),
                "pr_auc": _r(m.get("pr_auc")),
            }
        )

    selected = ld["models"][best]["test"]
    vendor = ld["baselines"]["vendor_history_only"]["test"]
    prevalence = ld["baselines"]["prevalence_probability"]["test"]
    comparison = [
        {
            "task": "late_delivery",
            "selected_model": best,
            "baseline": "vendor_history_only",
            "metric": "roc_auc",
            "model_value": _r(selected["roc_auc"]),
            "baseline_value": _r(vendor["roc_auc"]),
            "delta_model_minus_baseline": _r(selected["roc_auc"] - vendor["roc_auc"]),
            "beats_baseline": str(selected["roc_auc"] > vendor["roc_auc"]).lower(),
            "note": "Higher is better",
        },
        {
            "task": "late_delivery",
            "selected_model": best,
            "baseline": "vendor_history_only",
            "metric": "pr_auc",
            "model_value": _r(selected["pr_auc"]),
            "baseline_value": _r(vendor["pr_auc"]),
            "delta_model_minus_baseline": _r(selected["pr_auc"] - vendor["pr_auc"]),
            "beats_baseline": str(selected["pr_auc"] > vendor["pr_auc"]).lower(),
            "note": "Higher is better",
        },
        {
            "task": "late_delivery",
            "selected_model": best,
            "baseline": "prevalence_probability",
            "metric": "pr_auc",
            "model_value": _r(selected["pr_auc"]),
            "baseline_value": _r(prevalence["pr_auc"]),
            "delta_model_minus_baseline": _r(selected["pr_auc"] - prevalence["pr_auc"]),
            "beats_baseline": str(selected["pr_auc"] > prevalence["pr_auc"]).lower(),
            "note": "Higher is better; prevalence = positive rate",
        },
    ]
    return results, comparison


def _duration_rows(fe: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    dur = fe["duration"]
    best = dur.get("best_model")
    results: list[dict[str, Any]] = []
    for name, block in dur["models"].items():
        role = "baseline" if name == "dummy_median" else ("selected" if name == best else "candidate")
        for split_key, split_label in (("val", "validation"), ("test", "test")):
            m = block[split_key]
            results.append(
                {
                    "task": "delivery_duration",
                    "model": name,
                    "role": role,
                    "split": split_label,
                    "mae_days": _r(m.get("mae")),
                    "rmse_days": _r(m.get("rmse")),
                    "median_ae_days": _r(m.get("median_ae")),
                    "r2": _r(m.get("r2")),
                }
            )

    selected = dur["models"][best]["test"]
    median = dur["models"]["dummy_median"]["test"]
    comparison = [
        {
            "task": "delivery_duration",
            "selected_model": best,
            "baseline": "dummy_median",
            "metric": "mae_days",
            "model_value": _r(selected["mae"]),
            "baseline_value": _r(median["mae"]),
            "delta_model_minus_baseline": _r(selected["mae"] - median["mae"]),
            "beats_baseline": str(selected["mae"] < median["mae"]).lower(),
            "note": "Lower MAE is better; selected beat median on validation only",
        }
    ]
    return results, comparison


def _forecast_rows(fe: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    results: list[dict[str, Any]] = []
    comparison: list[dict[str, Any]] = []
    mapping = {
        "late_rate_monthly": ("monthly_late_rate", "shipment_count_weighted"),
        "volume_monthly": ("monthly_volume", "unweighted"),
    }
    for key, (task, weighting) in mapping.items():
        block = fe["forecasting"][key]
        selected = block["selected_model"]
        for model, val_mae in block["validation_mae"].items():
            role = "baseline" if model in {"naive_lag1", "mean_baseline"} else (
                "selected" if model == selected else "candidate"
            )
            results.append(
                {
                    "task": task,
                    "model": model,
                    "role": role,
                    "split": "validation",
                    "mae": _r(val_mae, 4) if task == "monthly_late_rate" else _r(val_mae, 1),
                    "metric_weighting": weighting,
                    "n": block.get("n_validation", ""),
                }
            )

        # Test: selected + baselines
        test_rows = [
            (selected, "selected", block["mae"]),
            ("naive_lag1", "baseline", block["naive_lag1_test_mae"]),
            ("mean_baseline", "baseline", block["mean_baseline_test_mae"]),
        ]
        for model, role, mae in test_rows:
            results.append(
                {
                    "task": task,
                    "model": model,
                    "role": role,
                    "split": "test",
                    "mae": _r(mae, 4) if task == "monthly_late_rate" else _r(mae, 1),
                    "metric_weighting": weighting,
                    "n": block.get("n_test", ""),
                }
            )

        comparison.extend(
            [
                {
                    "task": task,
                    "selected_model": selected,
                    "baseline": "naive_lag1",
                    "metric": "mae",
                    "model_value": _r(block["mae"], 4) if task == "monthly_late_rate" else _r(block["mae"], 1),
                    "baseline_value": _r(block["naive_lag1_test_mae"], 4)
                    if task == "monthly_late_rate"
                    else _r(block["naive_lag1_test_mae"], 1),
                    "delta_model_minus_baseline": _r(block["mae"] - block["naive_lag1_test_mae"], 4)
                    if task == "monthly_late_rate"
                    else _r(block["mae"] - block["naive_lag1_test_mae"], 1),
                    "beats_baseline": str(block["beats_naive_baseline_on_test"]).lower(),
                    "note": "Lower MAE is better; selection used validation only",
                },
                {
                    "task": task,
                    "selected_model": selected,
                    "baseline": "mean_baseline",
                    "metric": "mae",
                    "model_value": _r(block["mae"], 4) if task == "monthly_late_rate" else _r(block["mae"], 1),
                    "baseline_value": _r(block["mean_baseline_test_mae"], 4)
                    if task == "monthly_late_rate"
                    else _r(block["mean_baseline_test_mae"], 1),
                    "delta_model_minus_baseline": _r(block["mae"] - block["mean_baseline_test_mae"], 4)
                    if task == "monthly_late_rate"
                    else _r(block["mae"] - block["mean_baseline_test_mae"], 1),
                    "beats_baseline": str(block["beats_mean_baseline_on_test"]).lower(),
                    "note": "Lower MAE is better; selection used validation only",
                },
            ]
        )
    return results, comparison


def _inventory_rows(fe: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    inv = fe["inventory"]
    best = inv.get("best_model")
    results: list[dict[str, Any]] = []
    for name, block in inv["models"].items():
        for split_key, split_label in (("validation", "validation"), ("test", "test")):
            if split_key not in block:
                continue
            m = block[split_key]
            results.append(
                {
                    "task": "inventory_stockout_proxy",
                    "model": name,
                    "role": "selected" if name == best else "candidate",
                    "split": split_label,
                    "precision": _r(m.get("precision")),
                    "recall": _r(m.get("recall")),
                    "f1": _r(m.get("f1")),
                    "roc_auc": _r(m.get("roc_auc")),
                    "pr_auc": _r(m.get("pr_auc")),
                }
            )

    # Prevalence baseline (validation PR-AUC = positive prevalence for constant score)
    val_base = inv["validation_baseline"]
    results.append(
        {
            "task": "inventory_stockout_proxy",
            "model": "training_prevalence_probability",
            "role": "baseline",
            "split": "validation",
            "precision": "",
            "recall": "",
            "f1": "",
            "roc_auc": "",
            "pr_auc": _r(val_base.get("pr_auc")),
        }
    )
    test_prev = inv["class_prevalence"]["test"]
    results.append(
        {
            "task": "inventory_stockout_proxy",
            "model": "test_prevalence",
            "role": "baseline",
            "split": "test",
            "precision": "",
            "recall": "",
            "f1": "",
            "roc_auc": "",
            "pr_auc": _r(test_prev),
        }
    )

    selected_val = inv["models"][best]["validation"]
    selected_test = inv["models"][best]["test"]
    comparison = [
        {
            "task": "inventory_stockout_proxy",
            "selected_model": best,
            "baseline": "training_prevalence_probability",
            "metric": "pr_auc",
            "model_value": _r(selected_val["pr_auc"]),
            "baseline_value": _r(val_base["pr_auc"]),
            "delta_model_minus_baseline": _r(selected_val["pr_auc"] - val_base["pr_auc"]),
            "beats_baseline": str(selected_val["pr_auc"] > val_base["pr_auc"]).lower(),
            "note": "Validation comparison used for selection; source unverified",
        },
        {
            "task": "inventory_stockout_proxy",
            "selected_model": best,
            "baseline": "test_prevalence",
            "metric": "pr_auc",
            "model_value": _r(selected_test["pr_auc"]),
            "baseline_value": _r(test_prev),
            "delta_model_minus_baseline": _r(selected_test["pr_auc"] - test_prev),
            "beats_baseline": str(selected_test["pr_auc"] > test_prev).lower(),
            "note": "Experimental proxy; inventory provenance unverified",
        },
    ]
    return results, comparison


def _summary_comparison(parts: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for part in parts:
        rows.extend(part)
    return rows


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _write_markdown(
    out: Path,
    late_results: list[dict[str, Any]],
    duration_results: list[dict[str, Any]],
    forecast_results: list[dict[str, Any]],
    inventory_results: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
    generated_at: str,
) -> None:
    def rows_for(task: str, split: str | None = None) -> list[dict[str, Any]]:
        data = [r for r in late_results + duration_results + forecast_results + inventory_results if r["task"] == task]
        if split:
            data = [r for r in data if r.get("split") == split]
        return data

    sections: list[str] = [
        "# Model Results and Baseline Comparison",
        "",
        f"Source: `reports/final_evaluation.json` (generated `{generated_at}`).",
        "",
        "Regenerate with:",
        "",
        "```bash",
        "python scripts/build_model_comparison_tables.py",
        "```",
        "",
        "## 1. Late delivery (classification)",
        "",
        "Positive class = late shipment. Selected model: **random_forest**.",
        "",
        "### Validation",
        "",
        _md_table(
            ["Model", "Role", "Threshold", "Precision", "Recall", "F1", "ROC-AUC", "PR-AUC"],
            [
                [
                    r["model"],
                    r["role"],
                    r["threshold"],
                    r["precision"],
                    r["recall"],
                    r["f1"],
                    r["roc_auc"],
                    r["pr_auc"],
                ]
                for r in rows_for("late_delivery", "validation")
            ],
        ),
        "",
        "### Test (incl. baselines)",
        "",
        _md_table(
            ["Model", "Role", "Threshold", "Precision", "Recall", "F1", "ROC-AUC", "PR-AUC"],
            [
                [
                    r["model"],
                    r["role"],
                    r["threshold"],
                    r["precision"],
                    r["recall"],
                    r["f1"],
                    r["roc_auc"],
                    r["pr_auc"],
                ]
                for r in rows_for("late_delivery", "test")
            ],
        ),
        "",
        "## 2. Delivery duration (regression)",
        "",
        "Target = PO-to-client days. Selected model: **random_forest**. Lower MAE is better.",
        "",
        "### Test",
        "",
        _md_table(
            ["Model", "Role", "MAE (days)", "RMSE", "Median AE", "R²"],
            [
                [r["model"], r["role"], r["mae_days"], r["rmse_days"], r["median_ae_days"], r["r2"]]
                for r in rows_for("delivery_duration", "test")
            ],
        ),
        "",
        "## 3. Monthly forecasting",
        "",
        "### Late rate — test",
        "",
        _md_table(
            ["Model", "Role", "MAE", "Weighting", "n_test"],
            [
                [r["model"], r["role"], r["mae"], r["metric_weighting"], str(r["n"])]
                for r in rows_for("monthly_late_rate", "test")
            ],
        ),
        "",
        "### Volume — test",
        "",
        _md_table(
            ["Model", "Role", "MAE", "Weighting", "n_test"],
            [
                [r["model"], r["role"], r["mae"], r["metric_weighting"], str(r["n"])]
                for r in rows_for("monthly_volume", "test")
            ],
        ),
        "",
        "## 4. Inventory stockout proxy (experimental)",
        "",
        "Selected model: **random_forest**. Inventory fields are unverified augmented data.",
        "",
        _md_table(
            ["Model", "Role", "Split", "Precision", "Recall", "F1", "ROC-AUC", "PR-AUC"],
            [
                [
                    r["model"],
                    r["role"],
                    r["split"],
                    r["precision"],
                    r["recall"],
                    r["f1"],
                    r["roc_auc"],
                    r["pr_auc"],
                ]
                for r in rows_for("inventory_stockout_proxy")
            ],
        ),
        "",
        "## 5. Selected model vs baseline (summary)",
        "",
        _md_table(
            [
                "Task",
                "Selected model",
                "Baseline",
                "Metric",
                "Model",
                "Baseline value",
                "Delta",
                "Beats baseline?",
                "Note",
            ],
            [
                [
                    r["task"],
                    r["selected_model"],
                    r["baseline"],
                    r["metric"],
                    r["model_value"],
                    r["baseline_value"],
                    r["delta_model_minus_baseline"],
                    r["beats_baseline"],
                    r["note"],
                ]
                for r in comparisons
            ],
        ),
        "",
        "## CSV outputs",
        "",
        "| File | Contents |",
        "| --- | --- |",
        "| `reports/metrics/model_results_late_delivery.csv` | Late-delivery candidates + baselines |",
        "| `reports/metrics/model_results_duration.csv` | Duration candidates + median baseline |",
        "| `reports/metrics/model_results_forecasting.csv` | Forecast candidates + naive/mean |",
        "| `reports/metrics/model_results_inventory.csv` | Inventory proxy + prevalence baseline |",
        "| `reports/metrics/model_vs_baseline_comparison.csv` | One-row-per comparison deltas |",
        "",
    ]
    out.write_text("\n".join(sections), encoding="utf-8")


def main() -> None:
    fe = _load()
    metrics_dir = _root() / "reports" / "metrics"

    late_results, late_cmp = _late_delivery_rows(fe)
    duration_results, duration_cmp = _duration_rows(fe)
    forecast_results, forecast_cmp = _forecast_rows(fe)
    inventory_results, inventory_cmp = _inventory_rows(fe)
    comparisons = _summary_comparison([late_cmp, duration_cmp, forecast_cmp, inventory_cmp])

    _write_csv(metrics_dir / "model_results_late_delivery.csv", late_results)
    _write_csv(metrics_dir / "model_results_duration.csv", duration_results)
    _write_csv(metrics_dir / "model_results_forecasting.csv", forecast_results)
    _write_csv(metrics_dir / "model_results_inventory.csv", inventory_results)
    _write_csv(metrics_dir / "model_vs_baseline_comparison.csv", comparisons)

    md_path = _root() / "reports" / "model_baseline_comparison.md"
    _write_markdown(
        md_path,
        late_results,
        duration_results,
        forecast_results,
        inventory_results,
        comparisons,
        fe.get("generated_at", ""),
    )
    print(f"Wrote tables under {metrics_dir}")
    print(f"Wrote markdown report {md_path}")


if __name__ == "__main__":
    main()
