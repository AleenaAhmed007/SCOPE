"""Dataset path resolution helpers."""

from __future__ import annotations

from pathlib import Path

from scope.config.loader import load_yaml_config, resolve_path
from scope.logging_config import setup_logging

logger = setup_logging()


def get_raw_dataset_path(dataset_key: str = "primary") -> Path:
    """Resolve the absolute path to a configured raw dataset.

    Args:
        dataset_key: Key under ``datasets`` in ``configs/data.yaml``.

    Returns:
        Absolute path to the raw dataset file.

    Raises:
        KeyError: If the dataset key is missing from configuration.
        FileNotFoundError: If the resolved file does not exist.
    """
    config = load_yaml_config("data")
    datasets = config.get("datasets", {})
    if dataset_key not in datasets:
        raise KeyError(f"Unknown dataset key: {dataset_key!r}")

    relative = datasets[dataset_key]["relative_path"]
    path = resolve_path(relative)

    if not path.exists():
        raise FileNotFoundError(f"Raw dataset not found: {path}")

    logger.info("Resolved raw dataset '%s' -> %s", dataset_key, path)
    return path
