"""Dataset loading helpers for Phase 01."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from scope.data.paths import get_raw_dataset_path
from scope.logging_config import setup_logging

logger = setup_logging()


def load_raw_dataset(path: Path | None = None, dataset_key: str = "primary") -> pd.DataFrame:
    """Load the primary raw CSV without mutating the source file.

    Args:
        path: Optional override path. Defaults to configured raw dataset.
        dataset_key: Key under ``datasets`` in ``configs/data.yaml``.

    Returns:
        DataFrame with original column names and dtypes as read by pandas.
    """
    from scope.config.loader import load_yaml_config

    csv_path = path or get_raw_dataset_path(dataset_key)
    encoding = "utf-8"
    try:
        cfg = load_yaml_config("data")
        encoding = cfg.get("datasets", {}).get(dataset_key, {}).get("encoding") or encoding
    except FileNotFoundError:
        pass
    logger.info("Loading raw dataset from %s (encoding=%s)", csv_path, encoding)
    df = pd.read_csv(csv_path, encoding=encoding, low_memory=False)
    logger.info("Loaded shape=%s", df.shape)
    return df
