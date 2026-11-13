"""Phase 0 smoke tests — environment, imports, config, dataset, logging."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
import yaml


def test_python_environment() -> None:
    """Verify core scientific stack imports."""
    import numpy as np
    import pandas as pd
    import sklearn

    assert np.__version__
    assert pd.__version__
    assert sklearn.__version__


def test_scope_package_importable() -> None:
    """Verify the SCOPE package and submodules import cleanly."""
    import scope
    from scope import agents, api, data, evidence, features, models, rag, ui
    from scope.config import get_project_root, load_yaml_config, resolve_path
    from scope.data import get_raw_dataset_path
    from scope.logging_config import setup_logging

    assert scope.__version__
    assert callable(get_project_root)
    assert callable(load_yaml_config)
    assert callable(resolve_path)
    assert callable(get_raw_dataset_path)
    assert callable(setup_logging)
    assert agents and api and data and evidence and features and models and rag and ui


def test_project_root_layout() -> None:
    """Verify expected top-level directories exist."""
    from scope.config import get_project_root

    root = get_project_root()
    for name in ("backend", "configs", "data", "tests", "docs", "notebooks", "reports"):
        assert (root / name).is_dir(), f"Missing directory: {name}"


@pytest.mark.parametrize("config_name", ["data", "models", "rag"])
def test_yaml_configs_load(config_name: str) -> None:
    """Verify YAML configs load and return dictionaries."""
    from scope.config import load_yaml_config

    config = load_yaml_config(config_name)
    assert isinstance(config, dict)
    assert len(config) > 0


def test_data_config_paths() -> None:
    """Verify data config exposes the primary dataset path."""
    from scope.config import load_yaml_config

    config = load_yaml_config("data")
    primary = config["datasets"]["primary"]
    assert primary["filename"] == "SCMS_with_inventory.csv"
    assert "relative_path" in primary


def test_raw_dataset_path_resolves() -> None:
    """Verify the raw CSV exists at the configured location."""
    from scope.data import get_raw_dataset_path

    path = get_raw_dataset_path("primary")
    assert path.exists()
    assert path.name == "SCMS_with_inventory.csv"
    assert path.stat().st_size > 0


def test_logging_works(caplog: pytest.LogCaptureFixture) -> None:
    """Verify SCOPE logging emits messages."""
    from scope.logging_config import setup_logging

    with caplog.at_level(logging.INFO, logger="scope"):
        logger = setup_logging("INFO")
        logger.info("smoke-test-log-message")

    assert any("smoke-test-log-message" in record.message for record in caplog.records)


def test_configs_are_valid_yaml() -> None:
    """Verify configs directory YAML files parse without error."""
    from scope.config import get_project_root

    configs_dir = get_project_root() / "configs"
    yaml_files = list(configs_dir.glob("*.yaml")) + list(configs_dir.glob("*.yml"))
    assert yaml_files, "No YAML configs found"

    for path in yaml_files:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        assert data is not None


def test_env_example_exists() -> None:
    """Verify .env.example is present for secret templating."""
    from scope.config import get_project_root

    env_example = get_project_root() / ".env.example"
    assert env_example.exists()
