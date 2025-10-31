"""Application settings and constants."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import List


@dataclass(slots=True)
class Settings:
    """Application configuration loaded from environment variables."""

    data_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parents[5] / "data")
    timebin_minutes: int = 15
    accessibility_thresholds: List[int] = field(default_factory=lambda: [15, 30, 45])
    default_boarding_penalty_min: float = 5.0
    default_service_speed_kmh: float = 25.0

    def __post_init__(self) -> None:
        data_dir_env = os.getenv("GTFS_DATA_DIR")
        if data_dir_env:
            self.data_dir = Path(data_dir_env)
        timebin_env = os.getenv("GTFS_TIMEBIN_MINUTES")
        if timebin_env:
            self.timebin_minutes = int(timebin_env)
        thresholds_env = os.getenv("GTFS_ACCESSIBILITY_THRESHOLDS")
        if thresholds_env:
            values = [value.strip() for value in thresholds_env.split(",") if value.strip()]
            if values:
                self.accessibility_thresholds = [int(value) for value in values]
        penalty_env = os.getenv("GTFS_DEFAULT_BOARDING_PENALTY_MIN")
        if penalty_env:
            self.default_boarding_penalty_min = float(penalty_env)
        speed_env = os.getenv("GTFS_DEFAULT_SERVICE_SPEED_KMH")
        if speed_env:
            self.default_service_speed_kmh = float(speed_env)

        self.data_dir = self.data_dir.expanduser().resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()


__all__ = ["Settings", "get_settings"]
