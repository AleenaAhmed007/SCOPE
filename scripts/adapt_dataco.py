#!/usr/bin/env python3
"""Adapt Mendeley DataCo CSV into SCOPE SCMS-shaped raw CSV."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from scope.data.dataco_adapter import write_adapted_csv  # noqa: E402


def main() -> None:
    source = ROOT / "data" / "raw" / "DataCoSupplyChainDataset.csv"
    dest = ROOT / "data" / "raw" / "DataCo_adapted_for_SCOPE.csv"
    if not source.exists():
        raise SystemExit(
            f"Missing {source}. Download from Mendeley Data "
            "https://data.mendeley.com/datasets/8gx2fvg2k6/5 "
            "(file DataCoSupplyChainDataset.csv) into data/raw/."
        )
    meta = write_adapted_csv(source, dest)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
