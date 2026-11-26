"""Data access and ingestion utilities."""

from scope.data.paths import get_raw_dataset_path
from scope.data.table_io import read_table, write_table

__all__ = ["get_raw_dataset_path", "read_table", "write_table"]
