# SCOPE Data Quality Audit — Phase 01

Generated: `2026-11-06T12:54:42.621247+00:00`

Dataset: `data/raw/SCMS_with_inventory.csv`

## Overview

- Shape: 10324 × 45
- Duplicate rows: 0
- Duplicate IDs: 0

## Missing Values

See `reports/data_audit.json` for the full per-column table. Columns with missingness:

- `Dosage`: 1736 (16.8152%)
- `Shipment Mode`: 360 (3.487%)
- `Line Item Insurance (USD)`: 287 (2.7799%)

## Constants / Near-Constants

- Constant columns: ['Inventory_Stock_In', 'Inventory_Lead_Time_Days']
- Near-constant: [{'column': 'Managed By', 'dominant_value': 'PMO - US', 'dominant_share': 0.9943, 'n_unique': 4}]

## Date Parsing

Placeholders such as `N/A - From RDC`, `Date Not Captured`, and `Pre-PQ Process` are **not** parsed as dates. Original strings are preserved.

## Chronology

```json
{
  "delivered_before_scheduled_count": 2814,
  "delivered_after_scheduled_count": 1186,
  "delivered_on_scheduled_count": 6324,
  "valid_schedule_delivery_pairs": 10324,
  "recorded_before_delivered_count": 3,
  "valid_delivered_recorded_pairs": 10324,
  "po_sent_after_delivered_count": 432,
  "valid_po_delivered_pairs": 4592
}
```

## Late Delivery Target

- Valid: 10324
- Late %: 11.4878
- Excluded: 0 (not deleted)

## Inventory Audit

- Inventory fields appear augmented/synthetic relative to classic SCMS shipment data. Do not treat them as authentic operational inventory records without independent evidence.
- Stock_In all zero: True
- Lead_Time all 30: True
- Arithmetic match %: 69.5564
- Flag/shortage aligned %: 100.0
- Duplicate product/warehouse/date: 2218

## Exclusions (no silent deletes)

- {'rule': 'Late-delivery target requires valid Scheduled and Delivered dates', 'n_excluded': 0, 'action': 'Marked is_late as NA; rows not deleted'}
- {'rule': 'Date placeholders not parsed as datetimes', 'placeholders': ['Date Not Captured', 'N/A - From RDC', 'Pre-PQ Process'], 'action': 'Flagged via *_is_placeholder; originals preserved'}

## Target / Proxy Warnings

- `Inventory_Stockout_Flag` (high): May encode outcome-like stock shortage; unsuitable as a feature for predicting shortage/stockout without careful leakage review.
- `Inventory_Shortage_Quantity` (high): Direct shortage outcome; treat as target/proxy, not a feature.
- `Inventory_Replenishment_Triggered` (medium): May be derived from closing vs reorder; confirm timing before use.
- `Inventory_Closing_Stock` (medium): End-of-period value may not be known at prediction time.
- `Delivered to Client Date / Delivery Recorded Date` (high): Post-outcome timestamps; do not use as features for late prediction.
- `delay_days / is_late` (target): Derived targets for Phase 03 — not features.
