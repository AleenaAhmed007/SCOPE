"""Phase 02 preprocessing orchestration."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from scope.config.loader import get_project_root
from scope.data.cleaning import COLUMN_MAP, normalize_columns
from scope.data.split import assign_split_labels
from scope.data.table_io import write_table
from scope.eda.load import load_raw_dataset
from scope.features.delay_features import build_delay_timeseries
from scope.features.inventory_features import build_inventory_experiment_table
from scope.features.shipment_features import (
    LEAKAGE_FORBIDDEN,
    build_shipment_frame,
    early_warning_feature_columns,
)
from scope.features.vendor_features import attach_train_only_vendor_stats, build_vendor_features
from scope.features.volume_features import build_volume_timeseries
from scope.logging_config import setup_logging

logger = setup_logging()


def run_preprocessing(project_root: Path | None = None) -> dict[str, Any]:
    """Generate interim + processed task datasets without modifying raw CSV."""
    root = project_root or get_project_root()
    interim_dir = root / "data" / "interim"
    processed_dir = root / "data" / "processed"
    reports_dir = root / "reports"
    interim_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    raw = load_raw_dataset()
    exclusions: list[dict[str, Any]] = []

    # Duplicates — document, do not auto-delete
    n_dup_rows = int(raw.duplicated().sum())
    n_dup_ids = int(raw["ID"].duplicated().sum())
    exclusions.append(
        {
            "rule": "exact_duplicate_rows",
            "count": n_dup_rows,
            "action": "retained",
        }
    )
    exclusions.append(
        {
            "rule": "duplicate_ids",
            "count": n_dup_ids,
            "action": "retained",
        }
    )

    normalized, mapping = normalize_columns(raw)
    shipments = build_shipment_frame(normalized)

    # Chronological split on scheduled delivery
    shipments["split"] = assign_split_labels(
        shipments, "Scheduled_Delivery_Date_Parsed"
    )
    train = shipments[shipments["split"] == "train"]
    shipments = attach_train_only_vendor_stats(shipments, train)

    # Exclusion: invalid late target
    invalid_late = int(shipments["is_late"].isna().sum())
    exclusions.append(
        {
            "rule": "invalid_late_target_dates",
            "count": invalid_late,
            "action": "excluded_from_classification_training",
        }
    )
    invalid_dur = int(shipments["delivery_duration_days"].isna().sum())
    exclusions.append(
        {
            "rule": "invalid_or_implausible_po_to_delivery_duration",
            "count": invalid_dur,
            "action": "excluded_from_regression_training",
        }
    )

    # Vendor features from full reference (also save train-period version)
    vendor_all = build_vendor_features(shipments)
    vendor_train = build_vendor_features(train)

    delay_ts = build_delay_timeseries(shipments, freq="W")
    delay_ts_m = build_delay_timeseries(shipments, freq="ME")
    volume_ts = build_volume_timeseries(shipments, freq="W")
    volume_ts_m = build_volume_timeseries(shipments, freq="ME")

    inventory_table, inventory_meta = build_inventory_experiment_table(shipments)

    # Persist (CSV — git-friendly, no Parquet dependency)
    interim_path = write_table(shipments, interim_dir / "shipments_normalized.csv")
    ship_out = write_table(shipments, processed_dir / "shipments.csv")
    vendor_out = write_table(vendor_all, processed_dir / "vendor_features.csv")
    vendor_train_out = write_table(vendor_train, processed_dir / "vendor_features_train_period.csv")
    delay_out = write_table(delay_ts, processed_dir / "delay_timeseries.csv")
    delay_m_out = write_table(delay_ts_m, processed_dir / "delay_timeseries_monthly.csv")
    volume_out = write_table(volume_ts, processed_dir / "volume_timeseries.csv")
    volume_m_out = write_table(volume_ts_m, processed_dir / "volume_timeseries_monthly.csv")
    inventory_out = write_table(inventory_table, processed_dir / "inventory_experiment.csv")

    split_meta = {
        "method": "chronological_on_Scheduled_Delivery_Date_Parsed",
        "counts": shipments["split"].value_counts().to_dict(),
        "train_end": str(train["Scheduled_Delivery_Date_Parsed"].max()),
    }

    feature_meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "column_mapping": mapping,
        "reverse_note": "Raw CSV column names preserved in data/raw; mapping applied only to interim/processed",
        "early_warning_features": early_warning_feature_columns(),
        "vendor_history_method": "Expanding, one-row-shifted statistics within training data; validation and test use the training-period aggregates only.",
        "leakage_forbidden": sorted(LEAKAGE_FORBIDDEN),
        "prediction_moment": (
            "After shipment attributes and scheduled delivery date are known, "
            "before actual delivery outcome is observed."
        ),
        "split": split_meta,
        "exclusions": exclusions,
        "inventory": inventory_meta,
        "outputs": {
            "interim": str(interim_path),
            "shipments": str(ship_out),
            "vendor_features": str(vendor_out),
            "delay_timeseries": str(delay_out),
            "volume_timeseries": str(volume_out),
            "inventory_experiment": str(inventory_out),
        },
    }
    meta_path = reports_dir / "preprocessing_metadata.json"
    meta_path.write_text(json.dumps(feature_meta, indent=2, default=str), encoding="utf-8")

    # Update feature dictionary appendix
    feat_doc = root / "docs" / "feature_dictionary.md"
    appendix = (
        "\n\n# Phase 02 Processing Notes\n\n"
        f"- Prediction moment: {feature_meta['prediction_moment']}\n"
        f"- Early-warning features: {', '.join(early_warning_feature_columns())}\n"
        f"- Forbidden leakage fields: {', '.join(sorted(LEAKAGE_FORBIDDEN))}\n"
        f"- Split: {split_meta}\n"
        f"- Inventory recommendation: {inventory_meta['training_recommendation']}\n"
    )
    if feat_doc.exists():
        text = feat_doc.read_text(encoding="utf-8")
        if "# Phase 02 Processing Notes" not in text:
            feat_doc.write_text(text + appendix, encoding="utf-8")

    logger.info("Preprocessing complete: %s rows -> %s", len(shipments), ship_out)
    return feature_meta


def main() -> None:
    result = run_preprocessing()
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
