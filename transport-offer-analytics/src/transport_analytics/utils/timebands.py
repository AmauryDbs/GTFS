"""Gestion des plages horaires standardisées."""
from __future__ import annotations

from typing import List, Tuple

# timebands exprimées en minutes depuis minuit
DEFAULT_TIMEBANDS: List[Tuple[int, int, str]] = [
    (360, 540, "AM-Peak"),  # 06:00–09:00
    (540, 960, "Interpeak"),  # 09:00–16:00
    (960, 1140, "PM-Peak"),  # 16:00–19:00
    (1140, 1320, "Evening"),  # 19:00–22:00
    (1320, 1500, "Late"),  # 22:00–01:00
]


def hhmm_to_minutes(hhmm: str) -> int:
    """Convertit une chaîne HH:MM en minutes depuis minuit."""
    hour, minute = hhmm.split(":")
    return int(hour) * 60 + int(minute)
