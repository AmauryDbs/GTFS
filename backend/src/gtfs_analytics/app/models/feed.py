"""Lightweight models for feed metadata and API responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass(slots=True)
class FeedSummary:
    feed_id: str
    provider: Optional[str] = None
    validity_start: Optional[date] = None
    validity_end: Optional[date] = None
    version_hash: str = ""


@dataclass(slots=True)
class HeadwayBin:
    feed_id: str
    day_type_id: str
    route_id: str
    direction_id: Optional[int] = None
    timebin_start: str | int = ""
    departures: int = 0
    headway_p50_min: Optional[float] = None
    headway_p90_min: Optional[float] = None


@dataclass(slots=True)
class CoverageRecord:
    feed_id: str
    zone_id: str
    day_type_id: str
    threshold_min: int
    stops_reachable: int
    pop_reachable: Optional[int] = None
    jobs_reachable: Optional[int] = None
    schools_reachable: Optional[int] = None


@dataclass(slots=True)
class LineServiceKPI:
    feed_id: str
    day_type_id: str
    route_id: str
    direction_id: Optional[int] = None
    first_departure: Optional[str] = None
    last_departure: Optional[str] = None
    departures: int = 0


@dataclass(slots=True)
class FeedCatalog:
    feeds: List[FeedSummary] = field(default_factory=list)


__all__ = [
    "FeedSummary",
    "HeadwayBin",
    "CoverageRecord",
    "LineServiceKPI",
    "FeedCatalog",
]
