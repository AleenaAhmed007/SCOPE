"""Phase 02 leakage and preprocessing tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from scope.data.preprocessing import run_preprocessing
from scope.data.table_io import read_table
from scope.features.shipment_features import LEAKAGE_FORBIDDEN, early_warning_feature_columns


def test_preprocessing_outputs(tmp_path_factory=None) -> None:
    meta = run_preprocessing()
    root = Path(meta["outputs"]["shipments"]).parents[1].parent  # data/processed -> root-ish
    # Validate files exist
    for key in [
        "shipments",
        "vendor_features",
        "delay_timeseries",
        "volume_timeseries",
        "inventory_experiment",
    ]:
        path = Path(meta["outputs"][key])
        assert path.exists()
        assert path.suffix == ".csv"

    df = read_table(meta["outputs"]["shipments"])
    assert "is_late" in df.columns
    assert "delivery_duration_days" in df.columns
    assert "split" in df.columns
    assert set(df["split"].dropna().unique()) <= {"train", "val", "test", "excluded"}

    # Leakage fields must not be in early-warning feature list
    early = set(early_warning_feature_columns())
    assert early.isdisjoint(LEAKAGE_FORBIDDEN)

    # Chronological: train max date <= val min date <= test ...
    train = df[df["split"] == "train"]["Scheduled_Delivery_Date_Parsed"]
    val = df[df["split"] == "val"]["Scheduled_Delivery_Date_Parsed"]
    test = df[df["split"] == "test"]["Scheduled_Delivery_Date_Parsed"]
    assert train.max() <= val.min()
    assert val.max() <= test.min()
