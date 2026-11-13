"""Phase 07 - Audit the augmented inventory stockout rule; do not train a classifier."""

from __future__ import annotations

from typing import Any

import pandas as pd

from scope.logging_config import setup_logging
from scope.models.common import load_shipments, project_paths, save_json

logger = setup_logging()


def train_inventory_experiment() -> dict[str, Any]:
    df = load_shipments()
    work = df.copy()
    target = "Inventory_Stockout_Flag"
    work = work[work[target].notna() & work["split"].isin(["train", "val", "test"])]
    work["rule_stockout_prediction"] = (
        work["Inventory_Opening_Stock"] - work["Line_Item_Quantity"] < 0
    ).astype(int)
    work["reorder_rule_prediction"] = (
        work["Inventory_Opening_Stock"] < work["Inventory_Reorder_Level"]
    ).astype(int)

    split_metrics = {}
    for split_name in ("train", "val", "test"):
        part = work[work["split"] == split_name]
        if part.empty:
            continue
        split_metrics[split_name] = {
            "n": len(part),
            "target_prevalence": float(part[target].mean()),
            "opening_stock_minus_quantity_agreement": float(
                (part["rule_stockout_prediction"] == part[target].astype(int)).mean()
            ),
            "below_reorder_agreement": float(
                (part["reorder_rule_prediction"] == part[target].astype(int)).mean()
            ),
        }

    results = {
        "status": "predictive_model_removed_target_is_arithmetic_derivative",
        "predictive_model_trained": False,
        "target": target,
        "deterministic_rule": "Inventory_Opening_Stock - Line_Item_Quantity < 0",
        "split_checks": split_metrics,
        "data_quality_warning": "Inventory fields are unverified augmented data, not a warehouse system of record.",
        "interpretation": "The target matches this arithmetic rule, so a learned classifier would leak the answer. Treat this as a rule audit, not predictive performance.",
    }
    save_json(project_paths()["metrics"] / "inventory_experiment.json", results)
    logger.info("Inventory classifier skipped: target is a deterministic arithmetic rule")
    return results


if __name__ == "__main__":
    print(train_inventory_experiment())
