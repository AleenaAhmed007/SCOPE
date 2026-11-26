# SCOPE Data Quality Audit — Phase 01

Generated: `2026-11-26T16:15:24.690402+00:00`

Dataset: `data/raw/SCMS_with_inventory.csv`

## Overview

- Shape: 96470 × 48
- Duplicate rows: 0
- Duplicate IDs: 0

## Missing Values

See `reports/data_audit.json` for the full per-column table. Columns with missingness:

- `Dosage`: 96470 (100.0%)
- `Line Item Insurance (USD)`: 477 (0.4945%)
- `Olist_distance_km`: 477 (0.4945%)
- `Vendor INCO Term`: 1 (0.001%)
- `Dosage Form`: 1 (0.001%)

## Constants / Near-Constants

- Constant columns: ['PQ #', 'Dosage', 'Inventory_Stock_In', 'Inventory_Lead_Time_Days']
- Near-constant: []

## Date Parsing

Placeholders such as `N/A - From RDC`, `Date Not Captured`, and `Pre-PQ Process` are **not** parsed as dates. Original strings are preserved.

## Chronology

```json
{
  "delivered_before_scheduled_count": 88644,
  "delivered_after_scheduled_count": 6534,
  "delivered_on_scheduled_count": 1292,
  "valid_schedule_delivery_pairs": 96470,
  "recorded_before_delivered_count": 0,
  "valid_delivered_recorded_pairs": 96470,
  "po_sent_after_delivered_count": 38,
  "valid_po_delivered_pairs": 96470
}
```

## Late Delivery Target

- Valid: 96470
- Late %: 6.7731
- Excluded: 0 (not deleted)

## Inventory Audit

- Inventory fields appear augmented/synthetic relative to classic SCMS shipment data. Do not treat them as authentic operational inventory records without independent evidence.
- Stock_In all zero: True
- Lead_Time all 30: True
- Arithmetic match %: 97.9258
- Flag/shortage aligned %: 44.4117
- Duplicate product/warehouse/date: 61574

## Exclusions (no silent deletes)

- {'rule': 'Late-delivery target requires valid Scheduled and Delivered dates', 'n_excluded': 0, 'action': 'Marked is_late as NA; rows not deleted'}
- {'rule': 'Date placeholders not parsed as datetimes', 'placeholders': [], 'action': 'Flagged via *_is_placeholder; originals preserved'}

## Target / Proxy Warnings

- `Inventory_Stockout_Flag` (high): May encode outcome-like stock shortage; unsuitable as a feature for predicting shortage/stockout without careful leakage review.
- `Inventory_Shortage_Quantity` (high): Direct shortage outcome; treat as target/proxy, not a feature.
- `Inventory_Replenishment_Triggered` (medium): May be derived from closing vs reorder; confirm timing before use.
- `Inventory_Closing_Stock` (medium): End-of-period value may not be known at prediction time.
- `Delivered to Client Date / Delivery Recorded Date` (high): Post-outcome timestamps; do not use as features for late prediction.
- `delay_days / is_late` (target): Derived targets for Phase 03 — not features.
