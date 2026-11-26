"""Phase 06a — Vendor segmentation (KMeans)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import RobustScaler

from scope.data.table_io import read_table, write_table
from scope.logging_config import setup_logging
from scope.models.common import project_paths, save_json, save_model_bundle

logger = setup_logging()


def train_vendor_segmentation(k_min: int = 2, k_max: int = 8) -> dict[str, Any]:
    paths = project_paths()
    vendors = read_table(paths["processed"] / "vendor_features.csv")
    feature_cols = [
        "shipment_count",
        "late_rate",
        "median_schedule_deviation",
        "avg_quantity",
        "median_delivery_duration_days",
        "avg_freight_numeric",
        "n_countries",
        "n_product_groups",
    ]
    work = vendors.dropna(subset=["late_rate"]).copy()
    for c in feature_cols:
        if c not in work.columns:
            continue
        work[c] = work[c].fillna(work[c].median())

    total_shipments = float(work["shipment_count"].sum())
    dominant_threshold = max(1000.0, total_shipments * 0.2)
    dominant = work["shipment_count"] > dominant_threshold
    small_history = work["shipment_count"] < 10
    cluster_work = work[~dominant & ~small_history].copy()

    log_features = [
        "shipment_count",
        "avg_quantity",
        "avg_freight_numeric",
        "n_countries",
        "n_product_groups",
    ]

    # Iteratively separate tiny clusters found by a two-way outlier screen so
    # silhouette cannot be inflated by one-vendor segments.
    profile_outlier_indices = []
    for _ in range(3):
        if len(cluster_work) < 6:
            break
        probe_features = cluster_work[feature_cols].copy()
        probe_features[log_features] = np.log1p(probe_features[log_features].clip(lower=0))
        probe_scaled = RobustScaler().fit_transform(probe_features.to_numpy())
        probe_labels = KMeans(n_clusters=2, random_state=42, n_init=30).fit_predict(probe_scaled)
        probe_sizes = pd.Series(probe_labels).value_counts()
        if int(probe_sizes.min()) >= 3:
            break
        outlier_label = probe_sizes.idxmin()
        removed = cluster_work.index[probe_labels == outlier_label].tolist()
        profile_outlier_indices.extend(removed)
        cluster_work = cluster_work.drop(index=removed)

    model_features = cluster_work[feature_cols].copy()
    model_features[log_features] = np.log1p(model_features[log_features].clip(lower=0))
    scaler = RobustScaler()
    Xs = scaler.fit_transform(model_features.to_numpy())

    candidate_scores = []
    upper_k = min(k_max, len(cluster_work) - 1)
    for candidate_k in range(k_min, upper_k + 1):
        candidate = KMeans(n_clusters=candidate_k, random_state=42, n_init=30)
        candidate_labels = candidate.fit_predict(Xs)
        sizes = pd.Series(candidate_labels).value_counts()
        if len(sizes) < 2:
            continue
        candidate_scores.append({
            "k": candidate_k,
            "silhouette": float(silhouette_score(Xs, candidate_labels)),
            "min_cluster_size": int(sizes.min()),
            "has_minimum_support": bool(sizes.min() >= 3),
            "cluster_sizes": {str(key): int(value) for key, value in sizes.items()},
            "model": candidate,
            "labels": candidate_labels,
        })
    if not candidate_scores:
        raise ValueError("Not enough vendors with sufficient history to form clusters.")
    supported = [item for item in candidate_scores if item["has_minimum_support"]]
    pool = supported or candidate_scores
    selected = max(pool, key=lambda item: (item["silhouette"], item["min_cluster_size"]))
    model = selected["model"]
    cluster_work["segment"] = [f"segment_{label}" for label in selected["labels"]]
    work["segment"] = "insufficient_history"
    work.loc[dominant, "segment"] = "dominant_vendor_review"
    work.loc[profile_outlier_indices, "segment"] = "profile_outlier_review"
    work.loc[cluster_work.index, "segment"] = cluster_work["segment"]
    sil = selected["silhouette"]

    # Segment profiles
    profiles = (
        work.groupby("segment")[feature_cols]
        .mean()
        .reset_index()
        .to_dict(orient="records")
    )
    write_table(
        work[["Vendor", "segment"] + feature_cols],
        paths["processed"] / "vendor_segments.csv",
    )

    results = {
        "k": selected["k"],
        "silhouette": sil,
        "n_vendors": len(work),
        "n_clustered_vendors": len(cluster_work),
        "n_insufficient_history": int(small_history.sum()),
        "n_dominant_vendors_separated": int(dominant.sum()),
        "n_profile_outliers_separated": len(profile_outlier_indices),
        "dominant_vendor_threshold_shipments": dominant_threshold,
        "segment_sizes": {str(key): int(value) for key, value in work["segment"].value_counts().items()},
        "profiles": profiles,
        "features": feature_cols,
        "log1p_features": log_features,
        "candidate_k_scores": [
            {key: value for key, value in item.items() if key not in {"model", "labels"}}
            for item in candidate_scores
        ],
        "caveat": "Vendors with fewer than 10 shipments and dominant vendors are separated from KMeans. Segments describe operating profiles, not vendor quality.",
    }
    bundle = {
        "pipeline": {"scaler": scaler, "kmeans": model},
        "features": feature_cols,
        "log_features": log_features,
        "dominant_threshold": dominant_threshold,
        "min_history": 10,
        "profile_outlier_vendors": work.loc[profile_outlier_indices, "Vendor"].tolist(),
        "metrics": results,
    }
    out = save_model_bundle("vendor_segmentation", bundle)
    save_json(paths["metrics"] / "vendor_segmentation.json", results)
    logger.info("Vendor segmentation saved %s silhouette=%.3f", out, sil or -1)
    results["artifact_dir"] = str(out)
    return results


if __name__ == "__main__":
    print(train_vendor_segmentation())
