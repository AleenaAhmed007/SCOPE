#!/usr/bin/env python3
"""Build the SCOPE final evaluation markdown + CSV from reports/metrics."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
M = ROOT / "reports" / "metrics"


def load(name: str) -> dict:
    p = M / name
    return json.loads(p.read_text()) if p.exists() else {}


def fmt(x, nd: int = 3) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "—"
    if isinstance(x, float):
        if abs(x) >= 1000:
            return f"{x:,.1f}"
        return f"{x:.{nd}f}"
    return str(x)


def main() -> None:
    late = load("late_delivery_classification.json")
    dur = load("delivery_duration_regression.json")
    inv = load("inventory_experiment.json")
    fc = load("forecasting.json")
    weekly = load("forecast_weekly_lstm.json")
    seg = load("evaluation_vendor_segmentation.json") or load("vendor_segmentation.json")
    anom = load("evaluation_anomaly_unusual_profile.json")
    rag = load("rag_retrieval_evaluation.json")
    shap = load("shap_explainability.json")
    bt = load("walk_forward_backtest.json")
    ev_inv = load("evaluation_inventory.json")

    rows: list[dict] = []

    def add(**kw):
        rows.append(kw)

    for model, blob in late.get("models", {}).items():
        t = blob.get("test", {})
        add(
            task="Late-delivery risk",
            model=model,
            role="baseline" if model == "logistic_regression" else "proposed",
            split="test",
            n=late.get("n_test"),
            accuracy=t.get("accuracy"),
            precision=t.get("precision"),
            recall=t.get("recall"),
            f1=t.get("f1"),
            roc_auc=t.get("roc_auc"),
            pr_auc=t.get("pr_auc"),
            mae=None,
            rmse=None,
            r2=None,
            other=None,
            notes=f"best={late.get('best_model')}",
        )

    for model, blob in dur.get("models", {}).items():
        t = blob.get("test", blob)
        add(
            task="Lead-time / delivery duration",
            model=model,
            role="baseline" if "dummy" in model or "median" in model else "proposed",
            split="test",
            n=dur.get("n_test"),
            accuracy=None,
            precision=None,
            recall=None,
            f1=None,
            roc_auc=None,
            pr_auc=None,
            mae=t.get("mae"),
            rmse=t.get("rmse"),
            r2=t.get("r2"),
            other=f"median_ae={t.get('median_ae')}",
            notes=f"best={dur.get('best_model')}; basis={dur.get('prediction_basis')}",
        )

    lr = inv.get("models", {}).get("logistic_regression", {}).get("validation", {})
    add(
        task="Inventory stockout (experimental)",
        model="logistic_regression",
        role="baseline",
        split="validation",
        n=None,
        accuracy=None,
        precision=lr.get("precision"),
        recall=lr.get("recall"),
        f1=lr.get("f1"),
        roc_auc=lr.get("roc_auc"),
        pr_auc=lr.get("pr_auc"),
        mae=None,
        rmse=None,
        r2=None,
        other=None,
        notes="validation only in training artifact",
    )
    et = ev_inv.get("test") or inv.get("models", {}).get("random_forest", {}).get("test") or {}
    add(
        task="Inventory stockout (experimental)",
        model="random_forest",
        role="proposed",
        split="test",
        n=et.get("n_test") or 1550,
        accuracy=et.get("accuracy"),
        precision=et.get("precision"),
        recall=et.get("recall"),
        f1=et.get("f1"),
        roc_auc=et.get("roc_auc"),
        pr_auc=et.get("pr_auc"),
        mae=None,
        rmse=None,
        r2=None,
        other=None,
        notes="unverified augmented inventory",
    )

    for key, label in [
        ("late_rate_monthly", "Forecast late-rate (monthly)"),
        ("volume_monthly", "Forecast volume (monthly)"),
    ]:
        blob = fc.get(key, {})
        add(
            task=label,
            model=blob.get("selected_model"),
            role="selected_classical",
            split="test",
            n=blob.get("n_test"),
            accuracy=None,
            precision=None,
            recall=None,
            f1=None,
            roc_auc=None,
            pr_auc=None,
            mae=blob.get("mae"),
            rmse=blob.get("rmse"),
            r2=None,
            other=(
                f"beats_naive={blob.get('beats_naive_baseline_on_test')}; "
                f"beats_mean={blob.get('beats_mean_baseline_on_test')}"
            ),
            notes="",
        )
        add(
            task=label,
            model="naive_lag1",
            role="baseline",
            split="test",
            n=blob.get("n_test"),
            accuracy=None,
            precision=None,
            recall=None,
            f1=None,
            roc_auc=None,
            pr_auc=None,
            mae=blob.get("naive_lag1_test_mae"),
            rmse=None,
            r2=None,
            other=None,
            notes="baseline",
        )
        add(
            task=label,
            model="mean_baseline",
            role="baseline",
            split="test",
            n=blob.get("n_test"),
            accuracy=None,
            precision=None,
            recall=None,
            f1=None,
            roc_auc=None,
            pr_auc=None,
            mae=blob.get("mean_baseline_test_mae"),
            rmse=None,
            r2=None,
            other=None,
            notes="baseline",
        )

    wclass = weekly.get("classical") or {}
    wlstm = weekly.get("lstm") or {}
    for key, label in [
        ("late_rate_weekly", "Forecast late-rate (weekly)"),
        ("volume_weekly", "Forecast volume (weekly)"),
    ]:
        blob = wclass.get(key, {})
        if blob:
            add(
                task=label,
                model=blob.get("selected_model"),
                role="selected_classical",
                split="test",
                n=blob.get("n_test"),
                accuracy=None,
                precision=None,
                recall=None,
                f1=None,
                roc_auc=None,
                pr_auc=None,
                mae=blob.get("mae"),
                rmse=blob.get("rmse"),
                r2=None,
                other=None,
                notes="weekly classical",
            )

    for key, label in [
        ("late_rate", "Forecast late-rate (weekly neural)"),
        ("volume", "Forecast volume (weekly neural)"),
    ]:
        v = wlstm.get(f"{key}_verdict", {})
        best = wlstm.get(key) or {}
        if isinstance(best, dict) and best.get("config"):
            add(
                task=label,
                model=best.get("config"),
                role="neural_trial",
                split="test",
                n=best.get("n_test"),
                accuracy=None,
                precision=None,
                recall=None,
                f1=None,
                roc_auc=None,
                pr_auc=None,
                mae=best.get("test_mae") or v.get("lstm_test_mae"),
                rmse=None,
                r2=None,
                other=f"deploy={v.get('deploy_lstm')}; val_mae={best.get('validation_mae')}",
                notes=str(v.get("reason") or ""),
            )

    if seg:
        t = seg.get("test", seg)
        add(
            task="Vendor segmentation",
            model=f"kmeans_k={t.get('kmeans_k') or seg.get('kmeans_k')}",
            role="unsupervised",
            split="full",
            n=t.get("n_vendors") or seg.get("n_vendors"),
            accuracy=None,
            precision=None,
            recall=None,
            f1=None,
            roc_auc=None,
            pr_auc=None,
            mae=None,
            rmse=None,
            r2=None,
            other=f"silhouette={t.get('silhouette') or seg.get('silhouette')}",
            notes=t.get("caveat") or "",
        )

    if anom:
        t = anom.get("test", anom)
        add(
            task="Anomaly (unusual shipment profile)",
            model="isolation_forest",
            role="unsupervised",
            split="test",
            n=t.get("n_test"),
            accuracy=None,
            precision=None,
            recall=None,
            f1=None,
            roc_auc=None,
            pr_auc=None,
            mae=None,
            rmse=None,
            r2=None,
            other=f"anomaly_rate={t.get('anomaly_rate')}; n_unusual={t.get('n_unusual')}",
            notes=t.get("note") or "",
        )

    if rag:
        prim = rag.get("primary", {})
        add(
            task="Document retrieval (RAG)",
            model=prim.get("variant") or "hybrid",
            role="proposed",
            split="synthetic_queries",
            n=rag.get("n_queries"),
            accuracy=None,
            precision=None,
            recall=None,
            f1=None,
            roc_auc=None,
            pr_auc=None,
            mae=None,
            rmse=None,
            r2=None,
            other=f"MRR={prim.get('mrr')}; recall@3={(prim.get('section_recall_at_k') or {}).get('3')}",
            notes="synthetic query wiring benchmark",
        )

    if shap:
        add(
            task="Explainability (SHAP)",
            model=shap.get("model_name"),
            role="explainer",
            split="sample",
            n=shap.get("n_samples"),
            accuracy=None,
            precision=None,
            recall=None,
            f1=None,
            roc_auc=None,
            pr_auc=None,
            mae=None,
            rmse=None,
            r2=None,
            other=f"status={shap.get('status')}; explainer={shap.get('explainer')}",
            notes="",
        )

    if bt.get("late_delivery", {}).get("summary"):
        s = bt["late_delivery"]["summary"]
        add(
            task="Walk-forward late delivery",
            model="refit_quarterly",
            role="backtest",
            split="quarters",
            n=s.get("n_quarters"),
            accuracy=None,
            precision=s.get("mean_precision"),
            recall=s.get("mean_recall"),
            f1=None,
            roc_auc=s.get("mean_roc_auc"),
            pr_auc=None,
            mae=None,
            rmse=None,
            r2=None,
            other=(
                f"min_roc={s.get('min_roc_auc')}; "
                f"beats_vendor_only={s.get('quarters_model_beats_vendor_only')}/{s.get('n_quarters')}"
            ),
            notes="SCMS out-of-time quarterly",
        )
    if bt.get("duration"):
        d = bt["duration"]
        add(
            task="Walk-forward duration",
            model="rf_refit",
            role="backtest",
            split="quarters",
            n=d.get("n_quarters"),
            accuracy=None,
            precision=None,
            recall=None,
            f1=None,
            roc_auc=None,
            pr_auc=None,
            mae=None,
            rmse=None,
            r2=None,
            other=f"ml_beats_median={d.get('ml_beats_median_quarters')}/{d.get('n_quarters')}",
            notes=d.get("conclusion") or "",
        )

    df = pd.DataFrame(rows)

    lines = [
        "# SCOPE Final Evaluation Table (SCMS)",
        "",
        "Primary dataset: `data/raw/SCMS_with_inventory.csv`.",
        "",
        "## Classification — Late-delivery risk (test)",
        "",
        "| Model | Role | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, r in df[df.task == "Late-delivery risk"].iterrows():
        lines.append(
            f"| {r.model} | {r.role} | {fmt(r.accuracy)} | {fmt(r.precision)} | "
            f"{fmt(r.recall)} | {fmt(r.f1)} | {fmt(r.roc_auc)} | {fmt(r.pr_auc)} |"
        )
    pos = (late.get("class_balance_by_split") or {}).get("test", {}).get("positive_rate")
    lines += [
        "",
        f"**Best:** `{late.get('best_model')}` (test n={late.get('n_test')}, late rate≈{fmt(pos)}).",
        "",
        "## Classification — Inventory stockout experimental",
        "",
        "| Model | Split | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, r in df[df.task.str.startswith("Inventory")].iterrows():
        lines.append(
            f"| {r.model} | {r.split} | {fmt(r.accuracy)} | {fmt(r.precision)} | "
            f"{fmt(r.recall)} | {fmt(r.f1)} | {fmt(r.roc_auc)} | {fmt(r.pr_auc)} |"
        )
    lines += [
        "",
        "*Inventory fields are unverified/augmented — experimental only.*",
        "",
        "## Regression — Delivery duration (test)",
        "",
        "| Model | Role | MAE (days) | RMSE | R² |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for _, r in df[df.task.str.startswith("Lead-time")].iterrows():
        lines.append(
            f"| {r.model} | {r.role} | {fmt(r.mae)} | {fmt(r.rmse)} | {fmt(r.r2)} |"
        )
    lines += [
        "",
        f"**Selected basis:** `{dur.get('prediction_basis')}` / best reported `{dur.get('best_model')}`.",
        "",
        "## Forecasting (MAE ↓ better)",
        "",
        "| Task | Model | Role | Test MAE | RMSE | Notes |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for _, r in df[df.task.str.startswith("Forecast")].iterrows():
        lines.append(
            f"| {r.task} | {r.model} | {r.role} | {fmt(r.mae)} | {fmt(r.rmse)} | "
            f"{(r.other or r.notes or '')} |"
        )
    lines += [
        "",
        "## Unsupervised / RAG / SHAP / Backtests",
        "",
        "| Task | Model | Key metrics |",
        "| --- | --- | --- |",
    ]
    for task in [
        "Vendor segmentation",
        "Anomaly (unusual shipment profile)",
        "Document retrieval (RAG)",
        "Explainability (SHAP)",
        "Walk-forward late delivery",
        "Walk-forward duration",
    ]:
        for _, r in df[df.task == task].iterrows():
            extra = []
            if pd.notna(r.precision):
                extra.append(f"precision={fmt(r.precision)}")
            if pd.notna(r.recall):
                extra.append(f"recall={fmt(r.recall)}")
            if pd.notna(r.roc_auc):
                extra.append(f"ROC-AUC={fmt(r.roc_auc)}")
            metric = r.other or ""
            if extra:
                metric = (metric + "; " if metric else "") + ", ".join(extra)
            lines.append(f"| {r.task} | {r.model} | {metric} |")

    lines += [
        "",
        "## Flat CSV",
        "",
        "Machine-readable: `reports/final_evaluation_table.csv`.",
    ]

    (ROOT / "reports" / "final_evaluation_table.md").write_text("\n".join(lines))
    df.to_csv(ROOT / "reports" / "final_evaluation_table.csv", index=False)
    df.to_csv(M / "final_evaluation_table.csv", index=False)
    print("Wrote reports/final_evaluation_table.md and CSV")
    print(df[df.task == "Late-delivery risk"][
        ["model", "accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc"]
    ].to_string(index=False))


if __name__ == "__main__":
    main()
