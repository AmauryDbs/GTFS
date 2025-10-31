"""Configuration centralisée du projet."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DATA_DIR: Path = Path(os.getenv("DATA_DIR", "./data")).resolve()

PARQUET_CORE: Path = DATA_DIR / "parquet" / "core"
PARQUET_GEO: Path = DATA_DIR / "parquet" / "geo"
DERIVED_DIR: Path = DATA_DIR / "derived"
REF_DIR: Path = DATA_DIR / "ref"

for path in (PARQUET_CORE, PARQUET_GEO, DERIVED_DIR, REF_DIR):
    path.mkdir(parents=True, exist_ok=True)
