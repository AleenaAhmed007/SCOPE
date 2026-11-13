"""Phase 01 EDA orchestration — reproducible audit, figures, and reports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from scope.config.loader import get_project_root
from scope.eda.constants import CATEGORICAL_COLUMNS, NUMERICAL_COLUMNS
from scope.eda.dates import enrich_with_parsed_dates, find_impossible_chronology
from scope.eda.dictionaries import (
    build_data_dictionary,
    build_feature_dictionary,
    data_dictionary_markdown,
    feature_dictionary_markdown,
)
from scope.eda import figures as fig
from scope.eda.inventory import audit_inventory
from scope.eda.late_delivery import (
    create_late_delivery_target,
    late_delivery_summary,
    late_rate_by,
    vendor_performance,
)
from scope.eda.load import load_raw_dataset
from scope.eda.overview import (
    categorical_profile,
    coerce_dirty_numeric,
    constant_columns,
    dataset_overview,
    missing_value_summary,
    numerical_profile,
)
from scope.logging_config import setup_logging

logger = setup_logging()


def _df_to_md(df: pd.DataFrame, max_rows: int | None = None) -> str:
    """Render a DataFrame as a simple Markdown table without tabulate."""
    view = df if max_rows is None else df.head(max_rows)
    if view.empty:
        return "_No rows_"
    cols = [str(c) for c in view.columns]
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for _, row in view.iterrows():
        cells = []
        for c in view.columns:
            val = row[c]
            if isinstance(val, float):
                cells.append(f"{val:.4f}" if pd.notna(val) else "")
            else:
                cells.append("" if pd.isna(val) else str(val))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, (pd.Timestamp, datetime)):
        return obj.isoformat()
    if hasattr(obj, "item"):
        try:
            return obj.item()
        except Exception:
            return str(obj)
    if pd.isna(obj):
        return None
    return obj


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_json_safe(payload), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def run_phase01_eda(project_root: Path | None = None) -> dict[str, Any]:
    """Run full Phase 01 EDA and write all required artifacts.

    Returns:
        Dictionary of key summary metrics and output paths.
    """
    root = project_root or get_project_root()
    figures_dir = root / "reports" / "figures" / "eda"
    reports_dir = root / "reports"
    docs_dir = root / "docs"
    figures_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting Phase 01 EDA")
    df = load_raw_dataset()
    overview = dataset_overview(df)

    df, dirty_report = coerce_dirty_numeric(df)
    df, date_summary = enrich_with_parsed_dates(df)
    chronology = find_impossible_chronology(df)
    df = create_late_delivery_target(df)

    original_cols = list(overview["columns"])
    missing_df = missing_value_summary(df[original_cols])
    constants = constant_columns(df[original_cols])
    num_profile = numerical_profile(df, NUMERICAL_COLUMNS)
    cat_profile = categorical_profile(df, CATEGORICAL_COLUMNS)
    late_summary = late_delivery_summary(df)
    vendor_df = vendor_performance(df, min_shipments=5)
    late_by_vendor = late_rate_by(df, "Vendor")
    late_by_country = late_rate_by(df, "Country")
    late_by_mode = late_rate_by(df, "Shipment Mode")
    late_by_product = late_rate_by(df, "Product Group")
    inventory_audit = audit_inventory(df)

    # Figures
    figure_paths = {
        "missingness": fig.plot_missingness(missing_df, figures_dir),
        "numerical_distributions": fig.plot_numerical_distributions(
            df, NUMERICAL_COLUMNS, figures_dir
        ),
        "numerical_boxplots": fig.plot_numerical_boxplots(
            df, NUMERICAL_COLUMNS, figures_dir
        ),
        "shipment_mode": fig.plot_value_counts_bar(
            df,
            "Shipment Mode",
            "Shipment Mode Distribution",
            "05_shipment_mode_distribution.png",
            figures_dir,
            top_n=10,
        ),
        "top_vendors": fig.plot_value_counts_bar(
            df,
            "Vendor",
            "Top Vendors by Shipment Count",
            "06_top_vendors.png",
            figures_dir,
            top_n=15,
        ),
        "countries": fig.plot_value_counts_bar(
            df,
            "Country",
            "Top Countries by Shipment Count",
            "07_country_distribution.png",
            figures_dir,
            top_n=15,
        ),
        "late_target": fig.plot_late_target(df, figures_dir),
        "delay_hist": fig.plot_delay_histogram(df, figures_dir),
        "late_by_vendor": fig.plot_late_rate_by(
            late_by_vendor,
            "Vendor",
            "Late Rate by Vendor (min 20 shipments)",
            "10_late_rate_by_vendor.png",
            figures_dir,
            min_shipments=20,
        ),
        "late_by_mode": fig.plot_late_rate_by(
            late_by_mode,
            "Shipment Mode",
            "Late Rate by Shipment Mode (min 20 shipments)",
            "11_late_rate_by_shipment_mode.png",
            figures_dir,
            min_shipments=20,
            top_n=10,
        ),
        "late_by_country": fig.plot_late_rate_by(
            late_by_country,
            "Country",
            "Late Rate by Country (min 20 shipments)",
            "12_late_rate_by_country.png",
            figures_dir,
            min_shipments=20,
        ),
        "inventory_dist": fig.plot_inventory_distributions(df, figures_dir),
        "inventory_consistency": fig.plot_inventory_consistency(df, figures_dir),
        "date_coverage": fig.plot_date_coverage(date_summary, figures_dir),
    }
    corr = fig.plot_correlation_heatmap(df, NUMERICAL_COLUMNS, figures_dir)
    figure_paths["correlation_pearson"] = corr["pearson_path"]
    figure_paths["correlation_spearman"] = corr["spearman_path"]

    # Dictionaries
    data_dict = build_data_dictionary(df[original_cols], missing_df)
    feature_dict = build_feature_dictionary()
    (docs_dir / "data_dictionary.md").write_text(
        data_dictionary_markdown(data_dict), encoding="utf-8"
    )
    (docs_dir / "feature_dictionary.md").write_text(
        feature_dictionary_markdown(feature_dict), encoding="utf-8"
    )

    schema = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overview": overview,
        "dtypes": overview["dtypes"],
        "unique_counts": overview["unique_counts"],
    }
    _write_json(reports_dir / "schema.json", schema)

    eda_summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overview": overview,
        "dirty_numeric": dirty_report,
        "date_parsing": date_summary,
        "chronology": chronology,
        "constants": constants,
        "numerical_profile": num_profile.to_dict(orient="records"),
        "categorical_profile": cat_profile,
        "late_delivery": late_summary,
        "late_rate_by_shipment_mode": late_by_mode.to_dict(orient="records"),
        "late_rate_by_product_group": late_by_product.to_dict(orient="records"),
        "inventory_audit_highlights": {
            k: inventory_audit[k]
            for k in [
                "provenance_note",
                "stock_in_all_zero",
                "lead_time_all_30",
                "arithmetic",
                "flag_shortage_alignment",
                "constant_columns",
                "leakage_risks",
            ]
        },
        "figure_paths": figure_paths,
        "correlations_note": "Pearson and Spearman matrices saved under reports/figures/eda/",
    }
    _write_json(reports_dir / "eda_summary.json", eda_summary)

    data_audit = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_path": "data/raw/SCMS_with_inventory.csv",
        "overview": overview,
        "missing_values": missing_df.to_dict(orient="records"),
        "duplicates": {
            "duplicate_rows": overview["duplicate_rows"],
            "duplicate_ids": overview["duplicate_ids"],
        },
        "constants": constants,
        "date_parsing": date_summary,
        "chronology_issues": chronology,
        "dirty_numeric_fields": dirty_report,
        "late_delivery_target": late_summary,
        "inventory_audit": inventory_audit,
        "exclusions": [
            {
                "rule": "Late-delivery target requires valid Scheduled and Delivered dates",
                "n_excluded": late_summary["n_excluded"],
                "action": "Marked is_late as NA; rows not deleted",
            },
            {
                "rule": "Date placeholders not parsed as datetimes",
                "placeholders": sorted(
                    {
                        p
                        for stats in date_summary.values()
                        if stats.get("present")
                        for p in stats.get("placeholder_counts", {})
                    }
                ),
                "action": "Flagged via *_is_placeholder; originals preserved",
            },
        ],
        "target_proxy_warnings": inventory_audit["leakage_risks"]
        + [
            {
                "field": "Delivered to Client Date / Delivery Recorded Date",
                "risk": "high",
                "note": "Post-outcome timestamps; do not use as features for late prediction.",
            },
            {
                "field": "delay_days / is_late",
                "risk": "target",
                "note": "Derived targets for Phase 03 — not features.",
            },
        ],
    }
    _write_json(reports_dir / "data_audit.json", data_audit)

    # Markdown reports
    eda_md = _render_eda_report(eda_summary, vendor_df, late_by_country, late_by_mode)
    audit_md = _render_audit_report(data_audit)
    (reports_dir / "eda_report.md").write_text(eda_md, encoding="utf-8")
    (reports_dir / "data_audit.md").write_text(audit_md, encoding="utf-8")

    # Persist interim enriched frame for notebook reuse (not raw overwrite)
    interim_path = root / "data" / "interim" / "scms_phase01_enriched.parquet"
    try:
        df.to_parquet(interim_path, index=False)
    except Exception:
        # Fallback if pyarrow missing
        csv_fallback = root / "data" / "interim" / "scms_phase01_enriched.csv"
        df.to_csv(csv_fallback, index=False)
        interim_path = csv_fallback
        logger.warning("Parquet unavailable; wrote CSV interim to %s", csv_fallback)

    result = {
        "n_rows": overview["n_rows"],
        "n_columns": overview["n_columns"],
        "late_pct": late_summary["late_pct"],
        "n_valid_target": late_summary["n_valid_target"],
        "figures_dir": str(figures_dir),
        "interim_path": str(interim_path),
        "reports": {
            "eda_report": str(reports_dir / "eda_report.md"),
            "eda_summary": str(reports_dir / "eda_summary.json"),
            "data_audit": str(reports_dir / "data_audit.md"),
            "data_audit_json": str(reports_dir / "data_audit.json"),
            "data_dictionary": str(docs_dir / "data_dictionary.md"),
            "feature_dictionary": str(docs_dir / "feature_dictionary.md"),
        },
    }
    logger.info("Phase 01 EDA complete: late_pct=%s", late_summary["late_pct"])
    return result


def _render_eda_report(
    summary: dict[str, Any],
    vendor_df: pd.DataFrame,
    late_by_country: pd.DataFrame,
    late_by_mode: pd.DataFrame,
) -> str:
    o = summary["overview"]
    late = summary["late_delivery"]
    inv = summary["inventory_audit_highlights"]
    top_vendors = vendor_df.head(10)
    lines = [
        "# SCOPE EDA Report — Phase 01",
        "",
        f"Generated: `{summary['generated_at']}`",
        "",
        "## 1. Dataset Overview",
        "",
        f"- Rows: **{o['n_rows']}**",
        f"- Columns: **{o['n_columns']}**",
        f"- Memory: **{o['memory_mb']} MB**",
        f"- Duplicate rows: **{o['duplicate_rows']}**",
        f"- Duplicate IDs: **{o['duplicate_ids']}**",
        "",
        "## 2. Late Delivery",
        "",
        f"- Valid target rows: **{late['n_valid_target']}**",
        f"- Excluded (invalid dates): **{late['n_excluded']}**",
        f"- Late: **{late['n_late']}** ({late['late_pct']}%)",
        f"- On-time: **{late['n_on_time']}**",
        f"- Mean delay days: **{late['delay_days_mean']:.3f}**",
        f"- Median delay days: **{late['delay_days_median']:.3f}**",
        "",
        f"Exclusion rule: {late['exclusion_reason']}",
        "",
        "## 3. Late Rate by Shipment Mode",
        "",
        _df_to_md(late_by_mode),
        "",
        "## 4. Top Countries by Late Rate (valid sample)",
        "",
        _df_to_md(late_by_country, max_rows=15),
        "",
        "## 5. Top Vendors by Volume",
        "",
        "Vendors with small sample sizes should not be ranked as poor performers.",
        "",
        _df_to_md(top_vendors),
        "",
        "## 6. Inventory Highlights (Unverified Provenance)",
        "",
        f"- Note: {inv['provenance_note']}",
        f"- Stock In all zero: **{inv['stock_in_all_zero']}**",
        f"- Lead time all 30: **{inv['lead_time_all_30']}**",
        f"- Arithmetic match %: **{inv['arithmetic']['match_pct']}**",
        f"- Flag/shortage alignment %: **{inv['flag_shortage_alignment']['aligned_pct']}**",
        "",
        "## 7. Figures",
        "",
        "All figures are saved under `reports/figures/eda/`.",
        "",
        "## 8. Modelling Notes",
        "",
        "- No ML model was trained in this phase.",
        "- Do not use post-delivery timestamps or shortage outcomes as features for late prediction.",
        "- Inventory fields require provenance review before Phase 07 experiments.",
        "",
    ]
    return "\n".join(str(x) for x in lines)


def _render_audit_report(audit: dict[str, Any]) -> str:
    o = audit["overview"]
    late = audit["late_delivery_target"]
    inv = audit["inventory_audit"]
    lines = [
        "# SCOPE Data Quality Audit — Phase 01",
        "",
        f"Generated: `{audit['generated_at']}`",
        "",
        f"Dataset: `{audit['dataset_path']}`",
        "",
        "## Overview",
        "",
        f"- Shape: {o['n_rows']} × {o['n_columns']}",
        f"- Duplicate rows: {o['duplicate_rows']}",
        f"- Duplicate IDs: {o['duplicate_ids']}",
        "",
        "## Missing Values",
        "",
        "See `reports/data_audit.json` for the full per-column table. Columns with missingness:",
        "",
    ]
    missing = [m for m in audit["missing_values"] if m["missing_count"] > 0]
    if not missing:
        lines.append("- None")
    else:
        for m in missing:
            lines.append(
                f"- `{m['column']}`: {m['missing_count']} ({m['missing_pct']}%)"
            )

    lines.extend(
        [
            "",
            "## Constants / Near-Constants",
            "",
            f"- Constant columns: {audit['constants']['constant']}",
            f"- Near-constant: {audit['constants']['near_constant']}",
            "",
            "## Date Parsing",
            "",
            "Placeholders such as `N/A - From RDC`, `Date Not Captured`, and `Pre-PQ Process` "
            "are **not** parsed as dates. Original strings are preserved.",
            "",
            "## Chronology",
            "",
            f"```json\n{json.dumps(audit['chronology_issues'], indent=2)}\n```",
            "",
            "## Late Delivery Target",
            "",
            f"- Valid: {late['n_valid_target']}",
            f"- Late %: {late['late_pct']}",
            f"- Excluded: {late['n_excluded']} (not deleted)",
            "",
            "## Inventory Audit",
            "",
            f"- {inv['provenance_note']}",
            f"- Stock_In all zero: {inv['stock_in_all_zero']}",
            f"- Lead_Time all 30: {inv['lead_time_all_30']}",
            f"- Arithmetic match %: {inv['arithmetic']['match_pct']}",
            f"- Flag/shortage aligned %: {inv['flag_shortage_alignment']['aligned_pct']}",
            f"- Duplicate product/warehouse/date: {inv['duplicate_product_warehouse_date']}",
            "",
            "## Exclusions (no silent deletes)",
            "",
        ]
    )
    for ex in audit["exclusions"]:
        lines.append(f"- {ex}")

    lines.extend(
        [
            "",
            "## Target / Proxy Warnings",
            "",
        ]
    )
    for w in audit["target_proxy_warnings"]:
        lines.append(f"- `{w['field']}` ({w['risk']}): {w['note']}")

    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    result = run_phase01_eda()
    print(json.dumps(result, indent=2))
