"""Lecture simplifiée du catalogue Intake."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


def load_catalog(path: str | os.PathLike[str]) -> Dict[str, Any]:
    """Charge un fichier YAML de catalogue."""
    with Path(path).open("r", encoding="utf-8") as handle:
        document = yaml.safe_load(handle)
    return document or {}
