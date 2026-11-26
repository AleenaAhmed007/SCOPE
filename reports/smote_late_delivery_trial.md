# SMOTE Trial — Late Delivery (SCMS)

**Decision: do not add SMOTE.**

Train-only SMOTE / BorderlineSMOTE (k=3,5) was tried after the existing preprocessor, with and without `class_weight` / `scale_pos_weight`. Val/test were never resampled. Threshold still tuned on validation F1.

## vs current baseline (RF, no SMOTE)

| Setup | Test ROC-AUC | PR-AUC | F1 |
| --- | ---: | ---: | ---: |
| **Current RF (class_weight=balanced)** | **0.803** | **0.296** | **0.426** |
| Best SMOTE trial (RF, SMOTE k=3) | 0.793 | 0.285 | 0.417 |
| BorderlineSMOTE RF | 0.793 | 0.286 | 0.430 |

No SMOTE variant beat the baseline on ROC-AUC **and** (F1 or PR-AUC). Keep existing imbalance handling only.

Raw numbers: `reports/metrics/smote_late_delivery_trial.json`
