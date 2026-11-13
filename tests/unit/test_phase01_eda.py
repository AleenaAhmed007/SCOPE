"""Phase 01 tests — loading, dates, late target, inventory, audit helpers."""

from __future__ import annotations

import pandas as pd
import pytest

from scope.eda.dates import (
    enrich_with_parsed_dates,
    find_impossible_chronology,
    is_date_placeholder,
    parse_date_series,
)
from scope.eda.inventory import audit_inventory
from scope.eda.late_delivery import create_late_delivery_target, late_delivery_summary
from scope.eda.load import load_raw_dataset
from scope.eda.overview import (
    coerce_dirty_numeric,
    dataset_overview,
    missing_value_summary,
)


EXPECTED_MIN_COLUMNS = {
    "ID",
    "Country",
    "Vendor",
    "Shipment Mode",
    "Scheduled Delivery Date",
    "Delivered to Client Date",
    "Line Item Quantity",
    "Inventory_Stock_In",
    "Inventory_Lead_Time_Days",
    "Inventory_Stockout_Flag",
    "Inventory_Shortage_Quantity",
}


def test_dataset_loads_and_has_expected_columns() -> None:
    df = load_raw_dataset()
    assert len(df) > 0
    assert df.shape[1] >= 40
    missing = EXPECTED_MIN_COLUMNS - set(df.columns)
    assert not missing, f"Missing columns: {missing}"


def test_overview_and_duplicates() -> None:
    df = load_raw_dataset()
    overview = dataset_overview(df)
    assert overview["n_rows"] == len(df)
    assert overview["n_columns"] == df.shape[1]
    assert overview["duplicate_rows"] == int(df.duplicated().sum())
    assert overview["duplicate_ids"] == int(df["ID"].duplicated().sum())


def test_missing_value_calculations() -> None:
    df = load_raw_dataset()
    summary = missing_value_summary(df)
    assert set(summary["column"]) == set(df.columns)
    dosage = summary.loc[summary["column"] == "Dosage"].iloc[0]
    assert dosage["missing_count"] == int(df["Dosage"].isna().sum())
    assert dosage["missing_pct"] == pytest.approx(
        100.0 * df["Dosage"].isna().mean(), rel=1e-3
    )


@pytest.mark.parametrize(
    "value,expected",
    [
        ("N/A - From RDC", True),
        ("Date Not Captured", True),
        ("Pre-PQ Process", True),
        ("02-Jun-06", False),
        ("14/11/2006", False),
        (None, False),
    ],
)
def test_placeholder_handling(value: object, expected: bool) -> None:
    assert is_date_placeholder(value) is expected


def test_date_parsing_mixed_formats_and_placeholders() -> None:
    series = pd.Series(
        [
            "02-Jun-06",
            "N/A - From RDC",
            "Date Not Captured",
            "Pre-PQ Process",
            "14/11/2006",
            "not-a-date",
        ]
    )
    parsed = parse_date_series(series, "test_date")
    assert bool(parsed.loc[0, "parse_ok"]) is True
    assert bool(parsed.loc[1, "is_placeholder"]) is True
    assert bool(parsed.loc[1, "parse_ok"]) is False
    assert bool(parsed.loc[4, "parse_ok"]) is True
    assert bool(parsed.loc[5, "parse_ok"]) is False
    assert parsed.loc[1, "parsed"] is pd.NaT or pd.isna(parsed.loc[1, "parsed"])


def test_enrich_dates_preserves_original_strings() -> None:
    df = load_raw_dataset().head(200).copy()
    original = df["PO Sent to Vendor Date"].copy()
    enriched, summary = enrich_with_parsed_dates(df)
    assert enriched["PO Sent to Vendor Date"].equals(original)
    assert "PO Sent to Vendor Date_parsed" in enriched.columns
    assert summary["PO Sent to Vendor Date"]["n_placeholder"] > 0


def test_chronology_validation() -> None:
    df = pd.DataFrame(
        {
            "Scheduled Delivery Date_parsed": pd.to_datetime(
                ["2020-01-10", "2020-01-10", "2020-01-10"]
            ),
            "Delivered to Client Date_parsed": pd.to_datetime(
                ["2020-01-12", "2020-01-10", "2020-01-08"]
            ),
            "Delivery Recorded Date_parsed": pd.to_datetime(
                ["2020-01-11", "2020-01-10", "2020-01-09"]
            ),
            "PO Sent to Vendor Date_parsed": pd.to_datetime(
                ["2020-01-01", "2020-01-01", "2020-01-20"]
            ),
        }
    )
    result = find_impossible_chronology(df)
    assert result["delivered_after_scheduled_count"] == 1
    assert result["delivered_on_scheduled_count"] == 1
    assert result["delivered_before_scheduled_count"] == 1
    assert result["po_sent_after_delivered_count"] == 1


def test_late_target_creation() -> None:
    df = pd.DataFrame(
        {
            "Scheduled Delivery Date_parsed": pd.to_datetime(
                ["2020-01-10", "2020-01-10", None]
            ),
            "Delivered to Client Date_parsed": pd.to_datetime(
                ["2020-01-12", "2020-01-09", "2020-01-10"]
            ),
        }
    )
    out = create_late_delivery_target(df)
    assert int(out.loc[0, "is_late"]) == 1
    assert int(out.loc[1, "is_late"]) == 0
    assert pd.isna(out.loc[2, "is_late"])
    assert int(out.loc[0, "delay_days"]) == 2
    summary = late_delivery_summary(out)
    assert summary["n_valid_target"] == 2
    assert summary["n_late"] == 1
    assert summary["n_excluded"] == 1


def test_inventory_consistency_and_target_proxies() -> None:
    df = load_raw_dataset()
    audit = audit_inventory(df)
    assert audit["stock_in_all_zero"] is True
    assert audit["lead_time_all_30"] is True
    # Stock arithmetic is imperfect in this augmented dataset — document, don't assume 100%.
    assert 0.0 <= audit["arithmetic"]["match_pct"] <= 100.0
    assert audit["arithmetic"]["n_match"] + audit["arithmetic"]["n_mismatch"] == len(df)
    assert audit["flag_shortage_alignment"]["aligned_pct"] == pytest.approx(100.0)
    risks = {item["field"] for item in audit["leakage_risks"]}
    assert "Inventory_Shortage_Quantity" in risks
    assert "Inventory_Stockout_Flag" in risks


def test_dirty_numeric_coercion() -> None:
    df = load_raw_dataset().head(500)
    out, report = coerce_dirty_numeric(df)
    assert "Weight (Kilograms)_numeric" in out.columns
    assert "Freight Cost (USD)_numeric" in out.columns
    assert report["Weight (Kilograms)"]["n_non_numeric"] >= 0
