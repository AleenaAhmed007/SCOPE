# SCOPE EDA Report — Phase 01

Generated: `2026-11-26T16:15:24.686824+00:00`

## 1. Dataset Overview

- Rows: **96470**
- Columns: **48**
- Memory: **163.777 MB**
- Duplicate rows: **0**
- Duplicate IDs: **0**

## 2. Late Delivery

- Valid target rows: **96470**
- Excluded (invalid dates): **0**
- Late: **6534** (6.7731%)
- On-time: **89936**
- Mean delay days: **-11.876**
- Median delay days: **-12.000**

Exclusion rule: Rows excluded when Scheduled Delivery Date or Delivered to Client Date could not be parsed to a valid datetime (null/placeholder/invalid).

## 3. Late Rate by Shipment Mode

| Shipment Mode | shipment_count | late_count | delay_mean | delay_median | on_time_count | late_rate |
| --- | --- | --- | --- | --- | --- | --- |
| VeryLong | 15342 | 1598 | -12.8048 | -14.0000 | 13744 | 0.1042 |
| Long | 25762 | 1834 | -12.6860 | -14.0000 | 23928 | 0.0712 |
| Medium | 30235 | 1941 | -12.2756 | -13.0000 | 28294 | 0.0642 |
| Short | 12900 | 596 | -10.4723 | -10.0000 | 12304 | 0.0462 |
| Local | 12231 | 565 | -9.4964 | -9.0000 | 11666 | 0.0462 |

## 4. Top Countries by Late Rate (valid sample)

| Country | shipment_count | late_count | delay_mean | delay_median | on_time_count | late_rate |
| --- | --- | --- | --- | --- | --- | --- |
| AL | 397 | 85 | -8.7078 | -10.0000 | 312 | 0.2141 |
| MA | 717 | 125 | -9.5718 | -11.0000 | 592 | 0.1743 |
| SE | 335 | 51 | -10.0209 | -13.0000 | 284 | 0.1522 |
| PI | 476 | 66 | -11.3067 | -14.0000 | 410 | 0.1387 |
| CE | 1279 | 176 | -10.8045 | -13.0000 | 1103 | 0.1376 |
| RR | 41 | 5 | -17.2927 | -20.0000 | 36 | 0.1220 |
| BA | 3256 | 396 | -10.7945 | -12.0000 | 2860 | 0.1216 |
| RJ | 12350 | 1495 | -11.7612 | -13.0000 | 10855 | 0.1211 |
| PA | 946 | 106 | -14.0666 | -16.0000 | 840 | 0.1121 |
| ES | 1995 | 214 | -10.4962 | -12.0000 | 1781 | 0.1073 |
| PB | 517 | 54 | -13.2611 | -14.0000 | 463 | 0.1044 |
| TO | 274 | 27 | -12.1314 | -13.0000 | 247 | 0.0985 |
| MS | 701 | 68 | -11.0528 | -12.0000 | 633 | 0.0970 |
| PE | 1593 | 153 | -13.2938 | -14.0000 | 1440 | 0.0960 |
| RN | 474 | 44 | -13.6498 | -15.0000 | 430 | 0.0928 |

## 5. Top Vendors by Volume

Vendors with small sample sizes should not be ranked as poor performers.

| Vendor | shipment_count | late_count | delay_mean | delay_median | avg_quantity | avg_value | on_time_count | late_rate | small_sample_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SP | 68387 | 5014 | -11.1250 | -12.0000 | 1.1482 | 124.3991 | 63373 | 0.0733 | False |
| MG | 7662 | 370 | -13.3149 | -13.0000 | 1.1270 | 127.7952 | 7292 | 0.0483 | False |
| PR | 7444 | 402 | -14.0897 | -15.0000 | 1.1445 | 165.5734 | 7042 | 0.0540 | False |
| RJ | 4183 | 301 | -12.4093 | -13.0000 | 1.1212 | 196.2320 | 3882 | 0.0720 | False |
| SC | 3558 | 175 | -14.0253 | -14.0000 | 1.1265 | 172.3623 | 3383 | 0.0492 | False |
| RS | 1944 | 61 | -16.2253 | -17.0000 | 1.1152 | 192.2622 | 1883 | 0.0314 | False |
| DF | 806 | 43 | -13.2370 | -14.0000 | 1.0980 | 117.8513 | 763 | 0.0533 | False |
| BA | 547 | 27 | -12.5996 | -13.0000 | 1.1389 | 507.1511 | 520 | 0.0494 | False |
| GO | 448 | 13 | -13.9821 | -14.0000 | 1.1250 | 144.3892 | 435 | 0.0290 | False |
| PE | 400 | 15 | -15.7025 | -15.0000 | 1.1025 | 227.5609 | 385 | 0.0375 | False |

## 6. Inventory Highlights (Unverified Provenance)

- Note: Inventory fields appear augmented/synthetic relative to classic SCMS shipment data. Do not treat them as authentic operational inventory records without independent evidence.
- Stock In all zero: **True**
- Lead time all 30: **True**
- Arithmetic match %: **97.9258**
- Flag/shortage alignment %: **44.4117**

## 7. Figures

All figures are saved under `reports/figures/eda/`.

## 8. Modelling Notes

- No ML model was trained in this phase.
- Do not use post-delivery timestamps or shortage outcomes as features for late prediction.
- Inventory fields require provenance review before Phase 07 experiments.
