"""Regression tests for point-in-time features and model/report contracts."""

from __future__ import annotations

import pandas as pd

from scope.evaluation.final_report import _best_late_model
from scope.features.inventory_features import build_inventory_experiment_table
from scope.features.vendor_features import attach_train_only_vendor_stats
from scope.models.classification.train_inventory import (
    INVENTORY_CATEGORICAL,
    INVENTORY_NUMERIC,
    INVENTORY_FORBIDDEN_FEATURES,
)


def test_vendor_history_uses_only_previously_delivered_outcomes() -> None:
    rows = pd.DataFrame(
        {
            "ID": [1, 2, 3],
            "Vendor": ["A", "A", "A"],
            "split": ["train", "train", "val"],
            "Scheduled_Delivery_Date_Parsed": pd.to_datetime(
                ["2020-01-10", "2020-01-20", "2020-03-01"]
            ),
            "Delivered_To_Client_Date_Parsed": pd.to_datetime(
                ["2020-02-01", "2020-02-15", "2020-03-05"]
            ),
            "is_late": [1.0, 0.0, 1.0],
            "delay_days": [22.0, -5.0, 4.0],
        }
    )

    result = attach_train_only_vendor_stats(rows, rows.iloc[:2])

    assert pd.isna(result.loc[0, "vendor_hist_late_rate"])
    # Shipment 1 was scheduled earlier, but had not delivered by shipment 2's
    # scheduled date, so its outcome is unavailable at that prediction point.
    assert pd.isna(result.loc[1, "vendor_hist_late_rate"])
    assert result.loc[2, "vendor_hist_late_rate"] == 0.5
    assert result.loc[2, "vendor_hist_median_delay"] == 8.5
    assert "vendor_hist_shipment_count" not in result.columns


def test_inventory_rule_agreement_is_exact() -> None:
    shipments = pd.DataFrame(
        {
            "ID": [1, 2, 3],
            "Inventory_Opening_Stock": [2, 8, 0],
            "Inventory_Stock_In": [0, 0, 0],
            "Inventory_Stock_Out": [5, 1, 0],
            "Inventory_Closing_Stock": [0, 0, 0],
            "Inventory_Reorder_Level": [4, 4, 1],
            "Inventory_Lead_Time_Days": [30, 30, 30],
            "Inventory_Stockout_Flag": [1, 0, 0],
            "Inventory_Shortage_Quantity": [3, 0, 0],
            "Inventory_Replenishment_Triggered": [1, 0, 0],
            "Line_Item_Quantity": [5, 3, 0],
        }
    )

    _, metadata = build_inventory_experiment_table(shipments)

    assert metadata["stockout_rule_agreement"] == 1.0


def test_inventory_classifier_excludes_rule_operands_and_outcomes() -> None:
    assert not (set(INVENTORY_CATEGORICAL + INVENTORY_NUMERIC) & INVENTORY_FORBIDDEN_FEATURES)
    assert "Inventory_Opening_Stock" in INVENTORY_FORBIDDEN_FEATURES
    assert "Line_Item_Quantity" in INVENTORY_FORBIDDEN_FEATURES


def test_final_report_uses_saved_late_model_artifact() -> None:
    late = {
        "best_model": "xgboost",
        "models": {"xgboost": {"val": {"f1": 0.4}}, "random_forest": {"val": {"f1": 0.5}}},
    }
    artifact = {"model_name": "xgboost"}

    assert _best_late_model(late, artifact) == artifact["model_name"]
