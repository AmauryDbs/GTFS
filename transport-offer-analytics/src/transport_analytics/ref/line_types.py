"""Chargement des typologies de lignes."""
from __future__ import annotations

from typing import Dict

import yaml

from transport_analytics.config import REF_DIR


def load_line_types() -> Dict[str, Dict[str, str]]:
    """Retourne le mapping typologique décrit en YAML."""
    with (REF_DIR / "line_types.yaml").open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}
