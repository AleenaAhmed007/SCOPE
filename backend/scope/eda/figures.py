"""EDA figure generation for Phase 01."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from scope.logging_config import setup_logging

logger = setup_logging()

sns.set_theme(style="whitegrid", context="notebook")


def _save(fig: plt.Figure, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved figure %s", path)
    return str(path)


def plot_missingness(missing_df: pd.DataFrame, out_dir: Path) -> str:
    plot_df = missing_df[missing_df["missing_count"] > 0].sort_values("missing_pct")
    fig, ax = plt.subplots(figsize=(9, max(3, 0.35 * len(plot_df) + 1)))
    if plot_df.empty:
        ax.text(0.5, 0.5, "No missing values", ha="center", va="center")
        ax.set_axis_off()
    else:
        ax.barh(plot_df["column"], plot_df["missing_pct"], color="#2F6F8F")
        ax.set_xlabel("Missing percentage (%)")
        ax.set_ylabel("Column")
    ax.set_title("Missing Value Percentage by Column")
    return _save(fig, out_dir / "01_missingness.png")


def plot_numerical_distributions(df: pd.DataFrame, columns: list[str], out_dir: Path) -> str:
    usable = []
    for col in columns:
        series_name = col if col in df.columns else f"{col}_numeric"
        if series_name in df.columns:
            usable.append(series_name)
    n = len(usable)
    cols = 3
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(14, 3.2 * rows))
    axes = np.array(axes).reshape(-1)
    for ax, col in zip(axes, usable):
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        # Cap extreme tails for readability
        if len(s) > 0:
            hi = s.quantile(0.99)
            s_plot = s[s <= hi]
            ax.hist(s_plot, bins=40, color="#3B7A57", edgecolor="white")
        ax.set_title(col, fontsize=9)
        ax.set_xlabel(col)
        ax.set_ylabel("Count")
    for ax in axes[len(usable) :]:
        ax.set_axis_off()
    fig.suptitle("Numerical Distributions (values ≤ 99th percentile)", y=1.01)
    return _save(fig, out_dir / "02_numerical_distributions.png")


def plot_numerical_boxplots(df: pd.DataFrame, columns: list[str], out_dir: Path) -> str:
    usable = []
    for col in columns:
        series_name = col if col in df.columns else f"{col}_numeric"
        if series_name in df.columns:
            usable.append(series_name)
    n = len(usable)
    cols = 3
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(14, 3.0 * rows))
    axes = np.array(axes).reshape(-1)
    for ax, col in zip(axes, usable):
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(s) > 0:
            hi = s.quantile(0.99)
            s_plot = s[s <= hi]
            ax.boxplot(s_plot, vert=True, patch_artist=True,
                       boxprops=dict(facecolor="#A7C4BC"))
        ax.set_title(col, fontsize=9)
        ax.set_ylabel(col)
    for ax in axes[len(usable) :]:
        ax.set_axis_off()
    fig.suptitle("Numerical Boxplots (values ≤ 99th percentile)", y=1.01)
    return _save(fig, out_dir / "03_numerical_boxplots.png")


def plot_correlation_heatmap(df: pd.DataFrame, columns: list[str], out_dir: Path) -> dict[str, Any]:
    frame = pd.DataFrame()
    for col in columns:
        name = col if col in df.columns else f"{col}_numeric"
        if name in df.columns:
            frame[name] = pd.to_numeric(df[name], errors="coerce")
    pearson = frame.corr(method="pearson")
    spearman = frame.corr(method="spearman")

    fig, ax = plt.subplots(figsize=(11, 9))
    sns.heatmap(pearson, annot=False, cmap="RdBu_r", center=0, ax=ax)
    ax.set_title("Pearson Correlation Heatmap (numerical features)")
    path = _save(fig, out_dir / "04_correlation_heatmap_pearson.png")

    fig2, ax2 = plt.subplots(figsize=(11, 9))
    sns.heatmap(spearman, annot=False, cmap="RdBu_r", center=0, ax=ax2)
    ax2.set_title("Spearman Correlation Heatmap (numerical features)")
    path2 = _save(fig2, out_dir / "04b_correlation_heatmap_spearman.png")

    return {
        "pearson_path": path,
        "spearman_path": path2,
        "pearson": pearson.round(4).where(pd.notnull(pearson), None).to_dict(),
        "spearman": spearman.round(4).where(pd.notnull(spearman), None).to_dict(),
    }


def plot_value_counts_bar(
    df: pd.DataFrame,
    column: str,
    title: str,
    filename: str,
    out_dir: Path,
    top_n: int = 15,
) -> str:
    vc = df[column].fillna("(Missing)").value_counts().head(top_n)
    fig, ax = plt.subplots(figsize=(10, max(4, 0.35 * len(vc) + 1)))
    ax.barh(vc.index.astype(str)[::-1], vc.values[::-1], color="#2F6F8F")
    ax.set_xlabel("Shipment count")
    ax.set_ylabel(column)
    ax.set_title(title)
    return _save(fig, out_dir / filename)


def plot_late_target(df: pd.DataFrame, out_dir: Path) -> str:
    subset = df["is_late"].dropna()
    counts = subset.value_counts().reindex([0, 1]).fillna(0)
    labels = ["On-time (0)", "Late (1)"]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(labels, counts.values, color=["#3B7A57", "#B85C38"])
    ax.set_ylabel("Count")
    ax.set_title("Late Delivery Target Distribution (valid dates only)")
    for i, v in enumerate(counts.values):
        ax.text(i, v + max(counts.values) * 0.01, str(int(v)), ha="center")
    return _save(fig, out_dir / "08_late_target_distribution.png")


def plot_delay_histogram(df: pd.DataFrame, out_dir: Path) -> str:
    delay = df.loc[df["is_late"].notna(), "delay_days"].dropna()
    # Clip extreme delays for readability but note in title
    lo, hi = delay.quantile(0.01), delay.quantile(0.99)
    clipped = delay.clip(lo, hi)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.hist(clipped, bins=50, color="#6B5B95", edgecolor="white")
    ax.axvline(0, color="black", linestyle="--", linewidth=1, label="On-time boundary")
    ax.set_xlabel("Delay days (Delivered − Scheduled)")
    ax.set_ylabel("Count")
    ax.set_title("Delivery Delay Distribution (clipped to 1st–99th percentile)")
    ax.legend()
    return _save(fig, out_dir / "09_delay_distribution.png")


def plot_late_rate_by(
    rate_df: pd.DataFrame,
    group_col: str,
    title: str,
    filename: str,
    out_dir: Path,
    top_n: int = 15,
    min_shipments: int = 20,
) -> str:
    plot_df = rate_df[rate_df["shipment_count"] >= min_shipments].head(top_n)
    fig, ax = plt.subplots(figsize=(10, max(4, 0.35 * len(plot_df) + 1)))
    if plot_df.empty:
        ax.text(0.5, 0.5, "Insufficient sample", ha="center")
        ax.set_axis_off()
    else:
        labels = plot_df[group_col].astype(str) + " (n=" + plot_df["shipment_count"].astype(str) + ")"
        ax.barh(labels[::-1], (plot_df["late_rate"] * 100)[::-1], color="#B85C38")
        ax.set_xlabel("Late rate (%)")
    ax.set_title(title)
    return _save(fig, out_dir / filename)


def plot_inventory_distributions(df: pd.DataFrame, out_dir: Path) -> str:
    cols = [
        "Inventory_Opening_Stock",
        "Inventory_Stock_Out",
        "Inventory_Closing_Stock",
        "Inventory_Reorder_Level",
        "Inventory_Shortage_Quantity",
    ]
    fig, axes = plt.subplots(2, 3, figsize=(13, 7))
    axes = axes.reshape(-1)
    for ax, col in zip(axes, cols):
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        s = s[s <= s.quantile(0.99)]
        ax.hist(s, bins=40, color="#4A6FA5", edgecolor="white")
        ax.set_title(col, fontsize=9)
        ax.set_xlabel(col)
        ax.set_ylabel("Count")
    axes[-1].set_axis_off()
    fig.suptitle("Inventory Field Distributions (unverified provenance)", y=1.01)
    return _save(fig, out_dir / "13_inventory_distributions.png")


def plot_inventory_consistency(df: pd.DataFrame, out_dir: Path) -> str:
    opening = df["Inventory_Opening_Stock"]
    stock_in = df["Inventory_Stock_In"]
    stock_out = df["Inventory_Stock_Out"]
    closing = df["Inventory_Closing_Stock"]
    expected = opening + stock_in - stock_out
    residual = closing - expected

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].hist(residual, bins=40, color="#2F6F8F", edgecolor="white")
    axes[0].set_title("Closing − Expected Closing")
    axes[0].set_xlabel("Residual")
    axes[0].set_ylabel("Count")

    flag = df["Inventory_Stockout_Flag"]
    shortage = df["Inventory_Shortage_Quantity"] > 0
    ct = pd.crosstab(flag, shortage)
    sns.heatmap(ct, annot=True, fmt="d", cmap="Blues", ax=axes[1])
    axes[1].set_title("Stockout Flag vs Shortage>0")
    axes[1].set_xlabel("Shortage > 0")
    axes[1].set_ylabel("Stockout Flag")
    fig.suptitle("Inventory Consistency Diagnostics (unverified)", y=1.02)
    return _save(fig, out_dir / "14_inventory_consistency.png")


def plot_date_coverage(date_summary: dict[str, Any], out_dir: Path) -> str:
    labels = []
    parse_ok = []
    placeholders = []
    failed = []
    nulls = []
    for col, stats in date_summary.items():
        if not stats.get("present"):
            continue
        labels.append(col.replace(" Date", "").replace("Inventory_", "Inv "))
        parse_ok.append(stats["n_parse_ok"])
        placeholders.append(stats["n_placeholder"])
        failed.append(stats["n_parse_failed"])
        nulls.append(stats["n_null"])

    x = np.arange(len(labels))
    width = 0.2
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(x - 1.5 * width, parse_ok, width, label="Parsed OK", color="#3B7A57")
    ax.bar(x - 0.5 * width, placeholders, width, label="Placeholder", color="#C4A35A")
    ax.bar(x + 0.5 * width, failed, width, label="Parse failed", color="#B85C38")
    ax.bar(x + 1.5 * width, nulls, width, label="Null", color="#888888")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_ylabel("Row count")
    ax.set_title("Date Field Coverage and Parse Outcomes")
    ax.legend()
    return _save(fig, out_dir / "15_date_coverage.png")
