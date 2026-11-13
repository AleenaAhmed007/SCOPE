"""YAML configuration loader and path helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Union

import yaml

from scope.logging_config import setup_logging

logger = setup_logging()


def get_project_root() -> Path:
    """Return the repository root (parent of ``backend/``).

    Returns:
        Absolute path to the project root directory.
    """
    # backend/scope/config/loader.py -> parents[3] == project root
    return Path(__file__).resolve().parents[3]


def resolve_path(relative: Union[str, Path]) -> Path:
    """Resolve a path relative to the project root.

    Args:
        relative: Path relative to the repository root.

    Returns:
        Absolute resolved path.
    """
    root = get_project_root()
    path = root / Path(relative)
    return path.resolve()


def load_yaml_config(name: str) -> Dict[str, Any]:
    """Load a YAML file from the ``configs/`` directory.

    Args:
        name: Config basename with or without ``.yaml`` extension
            (e.g. ``data``, ``data.yaml``).

    Returns:
        Parsed configuration dictionary.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the file cannot be parsed.
    """
    filename = name if name.endswith((".yaml", ".yml")) else f"{name}.yaml"
    config_path = get_project_root() / "configs" / filename

    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    logger.debug("Loaded config %s (%d top-level keys)", config_path, len(data))
    return data
