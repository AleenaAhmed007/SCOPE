"""Dataset loading helpers for Phase 01."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from scope.data.paths import get_raw_dataset_path
from scope.logging_config import setup_logging

logger = setup_logging()


def load_raw_dataset(path: Path | None = None) -> pd.DataFrame:
    """Load the primary raw CSV without mutating the source file.

    Args:
        path: Optional override path. Defaults to configured raw dataset.

    Returns:
        DataFrame with original column names and dtypes as read by pandas.
    """
    csv_path = path or get_raw_dataset_path("primary")
    logger.info("Loading raw dataset from %s", csv_path)
    df = pd.read_csv(csv_path, low_memory=False)
    logger.info("Loaded shape=%s", df.shape)
    return df
