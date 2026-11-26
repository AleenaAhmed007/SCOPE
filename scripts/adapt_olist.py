#!/usr/bin/env python3
"""Adapt Olist delivery-risk parquet into SCOPE SCMS-shaped raw CSV."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from scope.data.olist_adapter import write_adapted_csv  # noqa: E402


def main() -> None:
    source = ROOT / "data" / "raw" / "olist_analytical.parquet"
    dest = ROOT / "data" / "raw" / "Olist_adapted_for_SCOPE.csv"
    if not source.exists():
        raise SystemExit(
            f"Missing {source}. Download HF dataset "
            "samuelalex37/olist-delivery-risk-data (olist_analytical.parquet)."
        )
    print(json.dumps(write_adapted_csv(source, dest), indent=2))


if __name__ == "__main__":
    main()
