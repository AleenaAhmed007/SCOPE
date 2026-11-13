# SCOPE EDA Report — Phase 01

Generated: `2026-11-06T12:54:42.609579+00:00`

## 1. Dataset Overview

- Rows: **10324**
- Columns: **45**
- Memory: **19.873 MB**
- Duplicate rows: **0**
- Duplicate IDs: **0**

## 2. Late Delivery

- Valid target rows: **10324**
- Excluded (invalid dates): **0**
- Late: **1186** (11.4878%)
- On-time: **9138**
- Mean delay days: **-6.024**
- Median delay days: **0.000**

Exclusion rule: Rows excluded when Scheduled Delivery Date or Delivered to Client Date could not be parsed to a valid datetime (null/placeholder/invalid).

## 3. Late Rate by Shipment Mode

| Shipment Mode | shipment_count | late_count | delay_mean | delay_median | on_time_count | late_rate |
| --- | --- | --- | --- | --- | --- | --- |
| Ocean | 371 | 65 | 5.8706 | 0.0000 | 306 | 0.1752 |
| Truck | 2830 | 455 | -9.9219 | 0.0000 | 2375 | 0.1608 |
| Air Charter | 650 | 75 | -19.0369 | -13.0000 | 575 | 0.1154 |
| Air | 6113 | 587 | -3.7638 | 0.0000 | 5526 | 0.0960 |

## 4. Top Countries by Late Rate (valid sample)

| Country | shipment_count | late_count | delay_mean | delay_median | on_time_count | late_rate |
| --- | --- | --- | --- | --- | --- | --- |
| Burundi | 98 | 38 | -8.4490 | 0.0000 | 60 | 0.3878 |
| Senegal | 3 | 1 | 1.0000 | 0.0000 | 2 | 0.3333 |
| Togo | 3 | 1 | 5.3333 | 0.0000 | 2 | 0.3333 |
| Congo, DRC | 333 | 83 | 11.2402 | 0.0000 | 250 | 0.2492 |
| Benin | 13 | 3 | 2.3846 | -4.0000 | 10 | 0.2308 |
| Mozambique | 631 | 116 | -1.2092 | 0.0000 | 515 | 0.1838 |
| Zambia | 683 | 108 | -5.2343 | 0.0000 | 575 | 0.1581 |
| Zimbabwe | 538 | 77 | -11.0074 | 0.0000 | 461 | 0.1431 |
| Ghana | 58 | 8 | -0.2241 | 0.0000 | 50 | 0.1379 |
| Guatemala | 15 | 2 | -1.0000 | 0.0000 | 13 | 0.1333 |
| South Sudan | 164 | 21 | -1.0671 | 0.0000 | 143 | 0.1280 |
| Tanzania | 519 | 66 | -4.3950 | 0.0000 | 453 | 0.1272 |
| Kenya | 111 | 14 | 0.8919 | 0.0000 | 97 | 0.1261 |
| Uganda | 779 | 98 | -7.5815 | 0.0000 | 681 | 0.1258 |
| Libya | 8 | 1 | -8.7500 | 0.0000 | 7 | 0.1250 |

## 5. Top Vendors by Volume

Vendors with small sample sizes should not be ranked as poor performers.

| Vendor | shipment_count | late_count | delay_mean | delay_median | avg_quantity | avg_value | on_time_count | late_rate | small_sample_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SCMS from RDC | 5404 | 927 | -8.2840 | 0.0000 | 24909.3164 | 200846.1205 | 4477 | 0.1715 | False |
| Orgenics, Ltd | 754 | 98 | 0.8382 | 0.0000 | 2529.3064 | 195893.0385 | 656 | 0.1300 | False |
| S. BUYS WHOLESALER | 715 | 11 | -28.6783 | 0.0000 | 1108.5524 | 13833.5715 | 704 | 0.0154 | False |
| Aurobindo Pharma Limited | 668 | 94 | 4.4117 | 0.0000 | 25443.0389 | 136801.9621 | 574 | 0.1407 | False |
| Trinity Biotech, Plc | 356 | 1 | 0.0843 | 0.0000 | 1789.9213 | 58340.8462 | 355 | 0.0028 | False |
| ABBVIE LOGISTICS (FORMERLY ABBOTT LOGISTICS BV) | 347 | 4 | 0.2939 | 0.0000 | 2518.9395 | 84864.7297 | 343 | 0.0115 | False |
| PHARMACY DIRECT | 326 | 0 | 0.0000 | 0.0000 | 97.0982 | 2678.9437 | 326 | 0.0000 | False |
| MYLAN LABORATORIES LTD (FORMERLY MATRIX LABORATORIES) | 317 | 2 | -0.6151 | 0.0000 | 24414.7129 | 227803.3612 | 315 | 0.0063 | False |
| HETERO LABS LIMITED | 277 | 2 | -0.2094 | 0.0000 | 27187.1805 | 154807.1013 | 275 | 0.0072 | False |
| CIPLA LIMITED | 175 | 23 | 4.7771 | 0.0000 | 35701.1429 | 226621.1120 | 152 | 0.1314 | False |

## 6. Inventory Highlights (Unverified Provenance)

- Note: Inventory fields appear augmented/synthetic relative to classic SCMS shipment data. Do not treat them as authentic operational inventory records without independent evidence.
- Stock In all zero: **True**
- Lead time all 30: **True**
- Arithmetic match %: **69.5564**
- Flag/shortage alignment %: **100.0**

## 7. Figures

All figures are saved under `reports/figures/eda/`.

## 8. Modelling Notes

- No ML model was trained in this phase.
- Do not use post-delivery timestamps or shortage outcomes as features for late prediction.
- Inventory fields require provenance review before Phase 07 experiments.
