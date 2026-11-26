"""CSV table IO helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from scope.data.table_io import read_table, table_path, write_table


def test_write_and_read_roundtrip(tmp_path: Path) -> None:
    df = pd.DataFrame(
        {
            "ID": [1, 2],
            "Scheduled_Delivery_Date_Parsed": pd.to_datetime(["2010-01-01", "2010-02-01"]),
            "period_start": pd.to_datetime(["2010-01-01", "2010-02-01"]),
            "value": [1.5, 2.5],
        }
    )
    out = write_table(df, tmp_path / "sample.csv")
    assert out.suffix == ".csv"
    assert out.exists()

    loaded = read_table(out)
    assert list(loaded.columns) == list(df.columns)
    assert pd.api.types.is_datetime64_any_dtype(loaded["Scheduled_Delivery_Date_Parsed"])
    assert pd.api.types.is_datetime64_any_dtype(loaded["period_start"])
    assert loaded["value"].tolist() == [1.5, 2.5]


def test_legacy_parquet_path_maps_to_csv(tmp_path: Path) -> None:
    df = pd.DataFrame({"a": [1]})
    out = write_table(df, tmp_path / "legacy.parquet")
    assert out.name == "legacy.csv"
    assert table_path(tmp_path / "legacy.parquet") == out
    assert read_table(tmp_path / "legacy.parquet")["a"].tolist() == [1]
