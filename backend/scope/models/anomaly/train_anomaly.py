"""Phase 06b - Anomaly detection with Isolation Forest.

Three models:

* ``vendor_kpi`` (proposal model): Isolation Forest on supplier KPIs per
  vendor-quarter (late rate, delay days, lead time, volume). Only *adverse*
  unusual periods count (worse than the training norm: early deliveries are
  not disruptions). A second detector flags *deterioration* against the
  vendor's own trailing history (one-sided binomial test), which catches mild
  but real increases the Isolation Forest misses. ``disruption_signal`` is
  either flag. Labelled synthetic injections give detection-vs-severity curves.
* ``unusual_profile``: unusual numeric shipment profiles (pre-outcome fields).
* ``retrospective``: shipment profile + realised delay, forensic only.

Note: the SCMS dataset has no defect/quality field, so defect rate cannot be
used as a supplier KPI.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline

from scipy.stats import binom

from scope.data.table_io import write_table
from scope.logging_config import setup_logging
from scope.models.classification.train_late import NUM
from scope.models.common import (
    build_preprocessor,
    load_shipments,
    model_config,
    project_paths,
    save_json,
    save_model_bundle,
)

logger = setup_logging()

# Calendar position and parse flags are not "profile" information; they only add noise.
NON_PROFILE = {
    "Scheduled_Month",
    "Scheduled_Quarter",
    "Scheduled_DOW",
    "Weight_NonNumeric_Flag",
    "Freight_NonNumeric_Flag",
    # Vendor-history features depend on outcome availability and have a
    # different point-in-time distribution than static shipment attributes.
    "vendor_hist_late_rate",
    "vendor_hist_median_delay",
    "vendor_hist_shipment_count",
}

VENDOR_KPI_FEATURES = [
    "late_rate",
    "mean_delay_days",
    "p90_delay_days",
    "median_lead_time_days",
    "log_shipment_count",
]
MIN_SHIPMENTS_PER_PERIOD = 5
TREND_TRAILING_PERIODS = 4
TREND_MIN_TRAILING_SHIPMENTS = 20
TREND_MIN_INCREASE = 0.10
TREND_P_VALUE = 0.01
SEVERITY_LEVELS = [(0.10, 7), (0.20, 14), (0.30, 30), (0.50, 60)]


def _params() -> dict[str, Any]:
    params = dict(model_config("anomaly").get("params") or {})
    return {
        "contamination": params.get("contamination", 0.05),
        "random_state": params.get("random_state", 42),
    }


def _isolation_forest() -> IsolationForest:
    p = _params()
    return IsolationForest(
        n_estimators=300,
        contamination=p["contamination"],
        random_state=p["random_state"],
        n_jobs=2,
    )


def _fit_anomaly(df: pd.DataFrame, features: list[str], name: str) -> dict[str, Any]:
    train = df[df["split"] == "train"]
    pipe = Pipeline(
        [
            # log + scale: Isolation Forest splits uniformly between min and max,
            # so heavy-tailed USD columns would otherwise isolate only extremes.
            ("pre", build_preprocessor(features, [], scale_numeric=True)),
            ("model", _isolation_forest()),
        ]
    )
    pipe.fit(train[features])
    scores = -pipe.decision_function(df[features])
    preds = pipe.predict(df[features])  # -1 anomaly
    df_out = df[["ID", "Vendor", "Country", "split"]].copy()
    df_out["anomaly_score"] = scores
    df_out["is_anomaly"] = (preds == -1).astype(int)
    df_out["signal_type"] = "unusual_shipment_profile"
    paths = project_paths()
    out_path = write_table(df_out, paths["processed"] / f"anomaly_scores_{name}.csv")
    bundle = {
        "pipeline": pipe,
        "features": features,
        "label": "unusual_shipment_profile",
        "contamination": _params()["contamination"],
        "metrics": {
            "n_scored": len(df_out),
            "n_anomaly": int(df_out["is_anomaly"].sum()),
            "anomaly_rate": float(df_out["is_anomaly"].mean()),
            "anomaly_rate_by_split": {
                str(k): float(v) for k, v in df_out.groupby("split")["is_anomaly"].mean().items()
            },
        },
    }
    art = save_model_bundle(f"anomaly_{name}", bundle)
    bundle["metrics"]["artifact_dir"] = str(art)
    bundle["metrics"]["scores_path"] = str(out_path)
    return bundle["metrics"]


def build_vendor_period_kpis(df: pd.DataFrame, freq: str = "QE") -> pd.DataFrame:
    """Aggregate supplier KPIs per vendor and period of scheduled delivery."""
    work = df.dropna(subset=["Scheduled_Delivery_Date_Parsed", "is_late"]).copy()
    work["period_start"] = (
        work["Scheduled_Delivery_Date_Parsed"].dt.to_period(freq.rstrip("E")).dt.start_time
    )
    split_rank = {"train": 0, "val": 1, "test": 2}
    work["split_rank"] = work["split"].map(split_rank)
    grouped = work.groupby(["Vendor", "period_start"], dropna=False)
    kpis = grouped.agg(
        shipment_count=("is_late", "size"),
        late_count=("is_late", "sum"),
        late_rate=("is_late", "mean"),
        mean_delay_days=("delay_days", "mean"),
        p90_delay_days=("delay_days", lambda s: s.quantile(0.9)),
        median_lead_time_days=("delivery_duration_days", "median"),
        split_rank=("split_rank", "max"),
    ).reset_index()
    kpis = kpis[kpis["shipment_count"] >= MIN_SHIPMENTS_PER_PERIOD].copy()
    # A period belongs to the latest split it touches, so no train period
    # contains validation/test outcomes.
    inverse = {v: k for k, v in split_rank.items()}
    kpis["split"] = kpis["split_rank"].map(inverse).fillna("excluded")
    kpis["log_shipment_count"] = np.log1p(kpis["shipment_count"])
    kpis = kpis.drop(columns=["split_rank"]).sort_values(["Vendor", "period_start"])
    # Trailing history per vendor from *previous* periods only.
    g = kpis.groupby("Vendor", sort=False)
    kpis["trailing_shipments"] = g["shipment_count"].transform(
        lambda x: x.shift(1).rolling(TREND_TRAILING_PERIODS, min_periods=1).sum()
    )
    kpis["trailing_late"] = g["late_count"].transform(
        lambda x: x.shift(1).rolling(TREND_TRAILING_PERIODS, min_periods=1).sum()
    )
    return kpis.sort_values(["period_start", "Vendor"])


def deterioration_flags(kpis: pd.DataFrame) -> pd.DataFrame:
    """One-sided test: is this period's late rate above the vendor's own trailing rate?"""
    n = kpis["shipment_count"].to_numpy(dtype=float)
    k = np.rint(kpis["late_rate"].to_numpy(dtype=float) * n)
    t_n = kpis["trailing_shipments"].fillna(0).to_numpy(dtype=float)
    t_k = kpis["trailing_late"].fillna(0).to_numpy(dtype=float)
    baseline = (t_k + 1) / (t_n + 2)  # Laplace-smoothed trailing late rate
    p_value = binom.sf(k - 1, n.astype(int), baseline)
    eligible = t_n >= TREND_MIN_TRAILING_SHIPMENTS
    flag = eligible & (p_value < TREND_P_VALUE) & (k / np.maximum(n, 1) - baseline >= TREND_MIN_INCREASE)
    return pd.DataFrame(
        {
            "trailing_late_rate": np.where(eligible, baseline, np.nan),
            "deterioration_p_value": np.where(eligible, p_value, np.nan),
            "is_deteriorating": flag.astype(int),
        },
        index=kpis.index,
    )


def _adverse(kpis: pd.DataFrame, reference: dict[str, float]) -> np.ndarray:
    """Worse than the training norm on at least one adverse KPI."""
    return (
        (kpis["late_rate"] > reference["late_rate"])
        | (kpis["mean_delay_days"].fillna(-np.inf) > reference["mean_delay_days"])
        | (kpis["median_lead_time_days"].fillna(-np.inf) > reference["median_lead_time_days"])
    ).to_numpy()


def _score(pipe: Pipeline, kpis: pd.DataFrame, reference: dict[str, float]) -> pd.DataFrame:
    out = kpis.copy()
    out["anomaly_score"] = -pipe.decision_function(out[VENDOR_KPI_FEATURES])
    unusual = pipe.predict(out[VENDOR_KPI_FEATURES]) == -1
    out["is_unusual_any_direction"] = unusual.astype(int)
    out["is_anomaly"] = (unusual & _adverse(out, reference)).astype(int)
    out = out.join(deterioration_flags(out))
    out["disruption_signal"] = ((out["is_anomaly"] == 1) | (out["is_deteriorating"] == 1)).astype(int)
    return out


def _inject(base: pd.DataFrame, late_increase: float, delay_days: float, reference_lead: float) -> pd.DataFrame:
    """Labelled synthetic disruption: degrade real held-out supplier-quarters."""
    inj = base.copy()
    inj["late_rate"] = (inj["late_rate"] + late_increase).clip(0, 1)
    inj["late_count"] = np.rint(inj["late_rate"] * inj["shipment_count"])
    inj["mean_delay_days"] = inj["mean_delay_days"].fillna(0) + delay_days
    inj["p90_delay_days"] = inj["p90_delay_days"].fillna(0) + delay_days * 1.5
    inj["median_lead_time_days"] = inj["median_lead_time_days"].fillna(reference_lead) + delay_days
    return inj


def train_vendor_kpi_anomaly() -> dict[str, Any]:
    df = load_shipments()
    kpis = build_vendor_period_kpis(df)
    train = kpis[kpis["split"] == "train"]
    if len(train) < 20:
        raise ValueError(f"Too few vendor-periods for KPI anomaly model: {len(train)}")
    pipe = Pipeline(
        [
            ("pre", build_preprocessor(VENDOR_KPI_FEATURES, [], scale_numeric=False)),
            ("model", _isolation_forest()),
        ]
    )
    pipe.fit(train[VENDOR_KPI_FEATURES])
    reference = {
        "late_rate": float(train["late_rate"].median()),
        "mean_delay_days": float(train["mean_delay_days"].median()),
        "median_lead_time_days": float(train["median_lead_time_days"].median()),
    }

    scored = _score(pipe, kpis, reference)
    out_path = write_table(scored, project_paths()["processed"] / "anomaly_scores_vendor_kpi.csv")

    # Ground truth on unseen (val+test) periods: false alarms on clean data and
    # detection rate on injected disruptions of increasing severity.
    unseen = kpis[kpis["split"].isin(["val", "test"])]
    clean = scored.loc[unseen.index]
    sensitivity = []
    for late_inc, delay in SEVERITY_LEVELS:
        inj = _score(pipe, _inject(unseen, late_inc, delay, reference["median_lead_time_days"]), reference)
        sensitivity.append(
            {
                "late_rate_increase": late_inc,
                "delay_increase_days": delay,
                "detected_isolation_forest": float(inj["is_anomaly"].mean()),
                "detected_trend": float(inj["is_deteriorating"].mean()),
                "detected_combined": float(inj["disruption_signal"].mean()),
            }
        )
    injection_check = {
        "unit": "unseen (val+test) vendor-quarters",
        "n_periods": int(len(unseen)),
        "false_alarm_rate_clean": {
            "isolation_forest": float(clean["is_anomaly"].mean()) if len(clean) else None,
            "trend": float(clean["is_deteriorating"].mean()) if len(clean) else None,
            "combined": float(clean["disruption_signal"].mean()) if len(clean) else None,
        },
        "sensitivity": sensitivity,
        "label": "SYNTHETIC - evaluation only, never written to the scores table",
    }

    metrics = {
        "unit": "vendor x quarter (scheduled delivery date)",
        "features": VENDOR_KPI_FEATURES,
        "min_shipments_per_period": MIN_SHIPMENTS_PER_PERIOD,
        "adverse_reference_train_medians": reference,
        "trend_detector": {
            "trailing_periods": TREND_TRAILING_PERIODS,
            "min_trailing_shipments": TREND_MIN_TRAILING_SHIPMENTS,
            "min_increase": TREND_MIN_INCREASE,
            "p_value": TREND_P_VALUE,
        },
        "n_periods": int(len(scored)),
        "n_train_periods": int(len(train)),
        "n_anomaly": int(scored["is_anomaly"].sum()),
        "n_deteriorating": int(scored["is_deteriorating"].sum()),
        "n_unusual_but_favourable_dropped": int(
            ((scored["is_unusual_any_direction"] == 1) & (scored["is_anomaly"] == 0)).sum()
        ),
        "signal_rate_by_split": {
            str(k): float(v) for k, v in scored.groupby("split")["disruption_signal"].mean().items()
        },
        "injected_disruption_check": injection_check,
        "missing_kpi": "defect rate (not present in SCMS data)",
        "scores_path": str(out_path),
    }
    bundle = {
        "pipeline": pipe,
        "features": VENDOR_KPI_FEATURES,
        "label": "adverse_supplier_kpi_period",
        "period_freq": "QE",
        "adverse_reference": reference,
        "min_shipments_per_period": MIN_SHIPMENTS_PER_PERIOD,
        "metrics": metrics,
    }
    metrics["artifact_dir"] = str(save_model_bundle("anomaly_vendor_kpi", bundle))
    return metrics


def train_anomaly_models() -> dict[str, Any]:
    df = load_shipments()
    features = [c for c in NUM if c in df.columns and c not in NON_PROFILE]
    unusual_profile = _fit_anomaly(df, features, "unusual_profile")

    # Retrospective may include outcome fields for forensic analysis only.
    df_retro = df.copy()
    retro_feats = features.copy()
    if "delay_days" in df_retro.columns:
        train_median = df_retro.loc[df_retro["split"] == "train", "delay_days"].median()
        df_retro["delay_days"] = df_retro["delay_days"].fillna(train_median)
        retro_feats.append("delay_days")
    retro = _fit_anomaly(df_retro, retro_feats, "retrospective")

    try:
        vendor_kpi = train_vendor_kpi_anomaly()
    except Exception as exc:  # noqa: BLE001 - keep shipment-level models usable
        logger.warning("Vendor KPI anomaly model failed: %s", exc)
        vendor_kpi = {"status": "failed", "error": str(exc)}

    results = {
        "vendor_kpi": vendor_kpi,
        "unusual_profile": unusual_profile,
        "retrospective": retro,
        "contamination": _params()["contamination"],
        "label": "unusual_shipment_profile",
        "note": "vendor_kpi flags unusual supplier performance periods (proposal model). Shipment-level scores indicate unusual numeric profiles; they are not delay predictors. Retrospective includes outcome data and is forensic only.",
    }
    save_json(project_paths()["metrics"] / "anomaly_detection.json", results)
    logger.info("Anomaly models trained")
    return results


if __name__ == "__main__":
    print(train_anomaly_models())
