"""Phase 13 — Evaluation summary and final defence report."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scope.config.loader import get_project_root
from scope.logging_config import setup_logging

logger = setup_logging()


def _load(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _best_late_model(late: dict[str, Any], artifact_meta: dict[str, Any]) -> str | None:
    """Resolve the report's selected model from the saved bundle first."""
    artifact_model = artifact_meta.get("model_name")
    if artifact_model in (late.get("models") or {}):
        return artifact_model
    best = late.get("best_model")
    if best in (late.get("models") or {}):
        return best
    candidates = {
        name: block.get("val", {}).get("f1")
        for name, block in (late.get("models") or {}).items()
        if isinstance(block, dict) and block.get("val", {}).get("f1") is not None
    }
    return max(candidates, key=candidates.get) if candidates else None


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        return f"{value:.{digits}f}"
    return str(value).replace("|", "\\|").replace("\n", " ")


def _rag_components(metadata: dict[str, Any] | None) -> list[str]:
    """Describe components available in the freshly built runtime index."""
    metadata = metadata or {}
    stack = metadata.get("retrieval_stack") or {}
    neural = metadata.get("neural") or {}
    components: list[str] = []
    if neural.get("dense_available") and stack.get("dense"):
        components.append("dense embeddings")
    if stack.get("lexical"):
        components.append("Okapi BM25")
    if neural.get("reranker_available") and stack.get("reranker"):
        components.append("cross-encoder reranking")
    return components or ["lexical fallback"]


def _evaluation_table_rows(payload: dict[str, Any], best_late: str | None) -> list[str]:
    rows: list[str] = []
    late = payload.get("late_delivery") or {}
    for name, metrics in (late.get("models") or {}).items():
        val, test = metrics.get("val") or {}, metrics.get("test") or {}
        rows.append(
            f"| Late delivery | {name} | val F1 {_fmt(val.get('f1'))}; ROC-AUC {_fmt(val.get('roc_auc'))}; PR-AUC {_fmt(val.get('pr_auc'))} | "
            f"test F1 {_fmt(test.get('f1'))}; ROC-AUC {_fmt(test.get('roc_auc'))}; PR-AUC {_fmt(test.get('pr_auc'))} | "
            f"{'Selected' if name == best_late else 'Candidate'}; threshold {_fmt(metrics.get('decision_threshold'))} |"
        )

    duration = payload.get("duration") or {}
    for name, metrics in (duration.get("models") or {}).items():
        val, test = metrics.get("val") or {}, metrics.get("test") or {}
        role = "Baseline" if name == "dummy_median" else ("Selected" if name == duration.get("best_model") else "Candidate")
        rows.append(
            f"| Delivery duration | {name} | val MAE {_fmt(val.get('mae'))} days | "
            f"test MAE {_fmt(test.get('mae'))} days; R2 {_fmt(test.get('r2'))} | "
            f"{role} |"
        )

    for key, label in (("late_rate_monthly", "Monthly late-rate forecast"), ("volume_monthly", "Monthly volume forecast")):
        result = (payload.get("forecasting") or {}).get(key) or {}
        for candidate, val_mae in (result.get("validation_mae") or {}).items():
            selected = candidate == result.get("selected_model")
            if selected:
                test_cell = f"test MAE {_fmt(result.get('mae'))}"
                role = "Selected"
            elif candidate == "naive_lag1":
                test_cell = f"test MAE {_fmt(result.get('naive_lag1_test_mae'))}"
                role = "Test baseline"
            elif candidate == "mean_baseline":
                test_cell = f"test MAE {_fmt(result.get('mean_baseline_test_mae'))}"
                role = "Test baseline"
            else:
                test_cell = "not scored on test"
                role = "Validation candidate"
            weighting = result.get("metric_weighting", "unweighted")
            rows.append(
                f"| {label} | {candidate} | validation MAE {_fmt(val_mae)} | {test_cell} | "
                f"{role}; n_test {_fmt(result.get('n_test'), 0) if selected or role == 'Test baseline' else 'N/A'}; {weighting if selected or role == 'Test baseline' else 'N/A'} |"
            )

    inventory = payload.get("inventory") or {}
    inventory_evaluation = (payload.get("model_evaluations") or {}).get("inventory") or {}
    inventory_test = inventory_evaluation.get("test") or {}
    inventory_best = inventory.get("best_model")
    for name, metrics in (inventory.get("models") or {}).items():
        val = metrics.get("validation") or {}
        test = metrics.get("test") or (inventory_test if name == inventory_best else {})
        rows.append(
            f"| Inventory stockout proxy | {name} | val PR-AUC {_fmt(val.get('pr_auc'))}; F1 {_fmt(val.get('f1'))} | "
            f"test PR-AUC {_fmt(test.get('pr_auc'))}; ROC-AUC {_fmt(test.get('roc_auc'))} | "
            f"{'Selected' if name == inventory_best else 'Validation candidate'}; experimental, unverified source |"
        )

    segmentation = (payload.get("model_evaluations") or {}).get("vendor_segmentation") or {}
    seg = segmentation.get("test") or {}
    if seg:
        rows.append(
            f"| Vendor segmentation | K-Means (k={_fmt(seg.get('kmeans_k'), 0)}) | silhouette {_fmt(seg.get('silhouette'))} | "
            f"{_fmt(seg.get('n_clustered'), 0)} clustered vendors; sizes {_fmt(seg.get('segment_sizes'))} | "
            "Unsupervised; not a predictive accuracy score |"
        )

    for key, label in (("anomaly_unusual_profile", "Unusual shipment profile"), ("anomaly_retrospective", "Retrospective anomaly"), ("anomaly_vendor_kpi", "Vendor KPI anomaly")):
        evaluation = (payload.get("model_evaluations") or {}).get(key) or {}
        test = evaluation.get("test") or {}
        if test:
            n_test = test.get("n_test", test.get("n_test_periods"))
            result = f"{_fmt(test.get('n_unusual'), 0)} flags / {_fmt(n_test, 0)} ({_fmt(test.get('anomaly_rate') * 100 if test.get('anomaly_rate') is not None else None, 1)}%)"
            note = "Unsupervised; no ground-truth anomaly labels"
        else:
            result = "Not evaluated"
            note = "Saved model artifact or evaluation result missing"
        rows.append(f"| {label} | Isolation Forest | N/A | {result} | {note} |")

    rag = payload.get("rag_retrieval") or {}
    if rag:
        primary = rag.get("primary") or {}
        recall = primary.get("section_recall_at_k") or rag.get("recall_at_k") or {}
        rows.append(
            f"| RAG retrieval | {' + '.join(_rag_components(payload.get('rag_index')))} | N/A | "
            f"MRR {_fmt(primary.get('mrr', rag.get('mrr')))}; Recall@3 {_fmt(recall.get('3'))} | "
            f"Wiring check only; {rag.get('n_queries')} synthetic queries |"
        )

    checker_eval = (payload.get("claim_checker_evaluation") or {}).get("corpus_grounded") or {}
    if checker_eval:
        rows.append(
            f"| Claim checker | verify_claims | {checker_eval.get('n_source_claims')} extracted corpus claims + "
            f"{checker_eval.get('n_unsupported')} controlled corruptions | detection {_fmt(checker_eval.get('detection_rate'))}; "
            f"false-positive rate {_fmt(checker_eval.get('false_positive_rate'))} | Synthetic corpus and controlled corruption evaluation |"
        )
    return rows


def _baseline_table_rows(payload: dict[str, Any], best_late: str | None) -> list[str]:
    rows: list[str] = []
    late = payload.get("late_delivery") or {}
    late_test = ((late.get("models") or {}).get(best_late) or {}).get("test") or {}
    late_baselines = late.get("baselines") or {}
    vendor = (late_baselines.get("vendor_history_only") or {}).get("test") or {}
    prevalence = (late_baselines.get("prevalence_probability") or {}).get("test") or {}
    rows.append(
        f"| Late delivery | {best_late} | vendor history ROC-AUC {_fmt(vendor.get('roc_auc'))}; PR-AUC {_fmt(vendor.get('pr_auc'))} | "
        f"ROC-AUC {_fmt(late_test.get('roc_auc'))}; PR-AUC {_fmt(late_test.get('pr_auc'))} | "
        f"AUC delta {_fmt((late_test.get('roc_auc') - vendor.get('roc_auc')) if late_test.get('roc_auc') is not None and vendor.get('roc_auc') is not None else None)} |"
    )
    rows.append(
        f"| Late delivery | {best_late} | prevalence-only PR-AUC {_fmt(prevalence.get('pr_auc'))} | "
        f"PR-AUC {_fmt(late_test.get('pr_auc'))} | Above prevalence baseline |"
    )

    duration = payload.get("duration") or {}
    selected = duration.get("best_model")
    chosen_test = ((duration.get("models") or {}).get(selected) or {}).get("test") or {}
    median_test = ((duration.get("models") or {}).get("dummy_median") or {}).get("test") or {}
    chosen_val = ((duration.get("models") or {}).get(selected) or {}).get("val") or {}
    median_val = ((duration.get("models") or {}).get("dummy_median") or {}).get("val") or {}
    test_delta = chosen_test.get("mae") - median_test.get("mae") if chosen_test.get("mae") is not None and median_test.get("mae") is not None else None
    rows.append(
        f"| Delivery duration | {selected} | median baseline MAE {_fmt(median_test.get('mae'))} days | "
        f"MAE {_fmt(chosen_test.get('mae'))} days; delta {_fmt(test_delta)} days | "
        f"{'Better' if test_delta is not None and test_delta < 0 else 'Does not beat'} on test; validation {'beats' if chosen_val.get('mae', float('inf')) < median_val.get('mae', float('inf')) else 'does not beat'} median |"
    )

    evaluations = payload.get("model_evaluations") or {}
    for key, label in (("forecast_late_rate", "Monthly late rate"), ("forecast_volume", "Monthly volume")):
        result = (evaluations.get(key) or {}).get("test") or {}
        baselines = result.get("baselines") or {}
        naive = (baselines.get("naive_lag1") or {}).get("mae")
        mean = (baselines.get("development_mean") or {}).get("mae")
        rows.append(
            f"| {label} | {result.get('selected_model')} | naive MAE {_fmt(naive)}; mean MAE {_fmt(mean)} | "
            f"model MAE {_fmt(result.get('mae'))} | beats naive: {_fmt(result.get('beats_naive_lag1'))}; beats mean: {_fmt(result.get('beats_development_mean'))} |"
        )

    inventory = payload.get("inventory") or {}
    inventory_eval = (evaluations.get("inventory") or {}).get("test") or {}
    selected = inventory.get("best_model")
    val_model = ((inventory.get("models") or {}).get(selected) or {}).get("validation") or {}
    base = inventory.get("validation_baseline") or {}
    prevalence_test = (inventory.get("class_prevalence") or {}).get("test")
    inventory_test_ap = inventory_eval.get("pr_auc")
    inventory_ap_delta = inventory_test_ap - prevalence_test if inventory_test_ap is not None and prevalence_test is not None else None
    rows.append(
        f"| Inventory stockout proxy | {selected} | validation prevalence PR-AUC {_fmt(base.get('pr_auc'))} | "
        f"validation PR-AUC {_fmt(val_model.get('pr_auc'))}; test PR-AUC {_fmt(inventory_test_ap)} vs test prevalence {_fmt(prevalence_test)} | "
        f"test AP delta {_fmt(inventory_ap_delta)}; label is derived and source unverified |"
    )

    rows.extend([
        "| Vendor segmentation | K-Means | No labeled baseline | silhouette only | N/A: descriptive clusters, not prediction |",
        "| Anomaly models | Isolation Forest | No labeled anomaly baseline | flag rates only | N/A: no ground truth labels |",
        f"| RAG retrieval | {' + '.join(_rag_components(payload.get('rag_index')))} | No representative relevance baseline | "
        f"{(payload.get('rag_retrieval') or {}).get('n_queries', 'N/A')}-query synthetic benchmark | N/A: not a quality benchmark |",
    ])
    return rows


def build_final_evaluation() -> dict[str, Any]:
    root = get_project_root()
    metrics = root / "reports" / "metrics"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "late_delivery": _load(metrics / "late_delivery_classification.json"),
        "duration": _load(metrics / "delivery_duration_regression.json"),
        "forecasting": _load(metrics / "forecasting.json"),
        "vendor_segmentation": _load(metrics / "vendor_segmentation.json"),
        "anomaly": _load(metrics / "anomaly_detection.json"),
        "inventory": _load(metrics / "inventory_experiment.json"),
        "shap": _load(metrics / "shap_explainability.json"),
        "rag_retrieval": _load(metrics / "rag_retrieval_evaluation.json"),
        "rag_index": _load(root / "reports" / "models" / "rag_index" / "metadata.json"),
        "claim_checker_evaluation": _load(metrics / "checker_claim_evaluation.json"),
        "walk_forward_backtest": _load(metrics / "walk_forward_backtest.json"),
        "model_evaluations": {
            name: _load(metrics / f"evaluation_{name}.json")
            for name in (
                "late_delivery",
                "duration",
                "inventory",
                "forecast_late_rate",
                "forecast_volume",
                "vendor_segmentation",
                "anomaly_unusual_profile",
                "anomaly_retrospective",
                "anomaly_vendor_kpi",
            )
        },
        "preprocessing": _load(root / "reports" / "preprocessing_metadata.json"),
        "phase_run": _load(root / "reports" / "phase_run_summary.json"),
    }

    # Defence narrative — metrics may be nested under models[best].test
    late = payload.get("late_delivery") or {}
    late_models = late.get("models") or {}
    artifact_meta = _load(root / "reports" / "models" / "late_delivery_classifier" / "metadata.json") or {}
    best = _best_late_model(late, artifact_meta)
    test = (late_models.get(best) or {}).get("test") or {}

    duration = payload.get("duration") or {}
    forecast = payload.get("forecasting") or {}
    shap = payload.get("shap") or {}
    inventory = payload.get("inventory") or {}
    inventory_test = (payload.get("model_evaluations", {}).get("inventory") or {}).get("test") or {}
    inventory_best = inventory.get("best_model")
    inventory_validation = ((inventory.get("models") or {}).get(inventory_best) or {}).get("validation") or {}
    inventory_baseline = inventory.get("validation_baseline") or {}
    rag_retrieval = payload.get("rag_retrieval") or {}
    checker_eval = (payload.get("claim_checker_evaluation") or {}).get("corpus_grounded") or {}
    vendor_baseline = ((late.get("baselines") or {}).get("vendor_history_only") or {}).get("test") or {}
    forecast_evaluations = payload.get("model_evaluations") or {}
    monthly_late = (forecast_evaluations.get("forecast_late_rate") or {}).get("test") or {}
    monthly_volume = (forecast_evaluations.get("forecast_volume") or {}).get("test") or {}
    segmentation = (forecast_evaluations.get("vendor_segmentation") or {}).get("test") or {}
    unusual_profile = (forecast_evaluations.get("anomaly_unusual_profile") or {}).get("test") or {}
    evaluation_table = "\n".join(_evaluation_table_rows(payload, best))
    baseline_table = "\n".join(_baseline_table_rows(payload, best))

    md = f"""# SCOPE Final Evaluation and Defence Report

Generated: `{payload['generated_at']}`

## System summary

SCOPE integrates:
- Chronological preprocessing and leakage-aware features (Phase 02)
- Late-delivery classification (Phase 03)
- Delivery-duration regression (Phase 04)
- Monthly forecasting with baseline comparison (Phase 05)
- Vendor segmentation and anomaly detection (Phase 06)
- Inventory target rule audit (Phase 07)
- SHAP explainability (Phase 08)
- Hybrid RAG with synthetic-document labeling (Phase 09)
- Evidence ledger + Checker (Phase 10)
- Agentic investigation workflow (Phase 11)
- FastAPI + React frontend (Phase 12)

## Primary ML result — late delivery

- Best model: **{best}**
- Test recall: **{test.get('recall')}**
- Test precision: **{test.get('precision')}**
- Test F1: **{test.get('f1')}**
- Test ROC-AUC: **{test.get('roc_auc')}**
- Test PR-AUC: **{test.get('pr_auc')}**
- Test positive prevalence: **{(late.get('class_balance_test') or {}).get('positive_rate')}**
- Positive prevalence by split: **{ {name: block.get('positive_rate') for name, block in (late.get('class_balance_by_split') or {}).items()} }**
- Post-2010 training sensitivity test ROC-AUC: **{(late.get('post_2010_training_sensitivity') or {}).get('test', {}).get('roc_auc')}**
- Vendor-history-only baseline ROC-AUC: **{vendor_baseline.get('roc_auc')}**
- Rolling-origin ROC-AUC: **{(late.get('rolling_origin_cv') or {}).get('roc_auc_mean')} ± {(late.get('rolling_origin_cv') or {}).get('roc_auc_std')}**

## Supporting results

- Duration best model: **{duration.get('best_model')}**
- Duration median baseline validation MAE: **{((duration.get('models') or {}).get('dummy_median') or {}).get('val', {}).get('mae')}**
- Duration test MAE / R²: **{((duration.get('models') or {}).get(duration.get('best_model')) or {}).get('test', {}).get('mae')} / {((duration.get('models') or {}).get(duration.get('best_model')) or {}).get('test', {}).get('r2')}**
- Forecasting frequency: **{forecast.get('frequency')}**; results include naive and mean baselines.
- Monthly late-rate model MAE: **{monthly_late.get('mae')}**; beats naive: **{monthly_late.get('beats_naive_lag1')}**, beats mean: **{monthly_late.get('beats_development_mean')}**.
- Monthly volume model MAE: **{monthly_volume.get('mae')}**; beats naive: **{monthly_volume.get('beats_naive_lag1')}**, beats mean: **{monthly_volume.get('beats_development_mean')}**.
- Inventory proxy model: **{inventory_best}**; validation PR-AUC **{inventory_validation.get('pr_auc')}** vs prevalence baseline **{inventory_baseline.get('pr_auc')}**; test ROC-AUC / PR-AUC: **{inventory_test.get('roc_auc')} / {inventory_test.get('pr_auc')}**. It excludes the two operands of the deterministic target rule and is experimental against unverified augmented fields.
- Inventory rule agreement on test rows: **{inventory_test.get('target_rule_agreement')}** (consistency check, not model accuracy).
- RAG retrieval wiring sanity MRR: **{(rag_retrieval.get('primary') or {}).get('mrr', rag_retrieval.get('mrr'))}** over {rag_retrieval.get('n_queries')} hand-authored synthetic queries; this is not a retrieval-quality claim.
- RAG runtime components: **{' + '.join(_rag_components(payload.get('rag_index')))}**; check per-query mode in the API response because optional components may be unavailable in another environment.
- Claim Checker corpus-corruption evaluation: **{checker_eval.get('detection_rate')} detection rate; {checker_eval.get('false_positive_rate')} false-positive rate** over {checker_eval.get('n_cases')} cases ({checker_eval.get('n_source_claims')} extractive claims from the current corpus). This is a controlled synthetic-corpus evaluation, not a free-form semantic-accuracy estimate.
- Vendor segmentation: **k={segmentation.get('kmeans_k')}, silhouette={segmentation.get('silhouette')}**, with small-history and profile-outlier vendors separated.
- Unusual shipment profile flags: **{unusual_profile.get('n_unusual')} / {unusual_profile.get('n_test')}** test shipments; flagged late-rate diagnostic **{(unusual_profile.get('late_rate_diagnostic') or {}).get('flagged')}** (descriptive only).
- SHAP status: **{shap.get('status')}**

## Model evaluation table

Supervised metrics use the held-out test split unless marked as validation. Forecast candidates are selected on validation data; only the selected estimator is scored separately on test data. Unsupervised rows show descriptive diagnostics because they have no labeled ground truth.

| Task | Model | Validation result | Test / sample result | Note |
|---|---|---|---|---|
{evaluation_table}

## Model vs baseline comparison

For MAE, lower is better; for AUC, PR-AUC, and F1, higher is better. Baselines and models use the same split when directly compared.

| Task | Selected model | Baseline | Model result | Comparison |
|---|---|---|---|---|
{baseline_table}

## Important limitations

1. Inventory fields are **unverified augmented data**. The proxy classifier does not use the two fields that define its label; its scores are not operationally validated, and rule agreement is only a consistency check.
2. Synthetic RAG documents are **not official contracts/policies**.
3. Anomaly scores describe unusual shipment profiles and are not delay predictors; retrospective analysis is forensic only.
4. PostgreSQL is required. Start it with `docker compose up -d postgres` and set `SCOPE_DATABASE_URL=postgresql+psycopg://scope:scope@127.0.0.1:5432/scope`. The application fails startup if PostgreSQL is unavailable; it does not switch database backends.
5. RAG uses the active components recorded in `reports/models/rag_index/metadata.json`; dense embeddings and cross-encoder reranking are optional runtime capabilities, with BM25 as the lexical retriever.
6. RAG retrieval queries use a small synthetic corpus and are too limited to estimate production relevance.
7. Anomaly scores are investigative signals, not fraud probabilities or labeled accuracy.
8. Delivery-duration predictions should be treated as low-confidence unless the selected model beats the median baseline on validation data.
9. Late-delivery prevalence changes across train, validation, and test; rolling-origin CV shows substantial temporal variation.

## Reproducibility

```bash
py -3.13 -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
pip install -e .
docker compose up -d postgres
$env:SCOPE_DATABASE_URL='postgresql+psycopg://scope:scope@127.0.0.1:5432/scope'
python -m scope.data.preprocessing
python scripts/run_all_phases.py
uvicorn scope.api.app:app --reload --port 8000
cd frontend && npm install && npm run dev
pytest -q
```

## Defence talking points

- Prediction moment is documented: scheduled delivery known, outcome unknown.
- Chronological splits reduce temporal leakage.
- Checker validates numeric claims and citation presence.
- Agents coordinate ML + RAG + evidence rather than free-form hallucination.
- Forecasts use monthly lag models selected against naive and mean baselines.
"""
    out_md = root / "reports" / "final_defence_report.md"
    out_json = root / "reports" / "final_evaluation.json"
    out_md.write_text(md, encoding="utf-8")
    out_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    logger.info("Final evaluation written to %s", out_md)
    return {"report": str(out_md), "json": str(out_json)}
