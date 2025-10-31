"""Headway and service analytics without third-party dependencies."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from ..core.config import get_settings
from ..utils.time import format_seconds_as_time, parse_gtfs_time


def _load_table(base: Path, name: str) -> List[Dict[str, object]]:
    path = base / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text())


def _compute_trip_departures(stop_times: Iterable[Dict[str, object]]) -> Dict[str, int]:
    departures: Dict[str, int] = {}
    for row in sorted(stop_times, key=lambda r: (r["trip_id"], int(r.get("stop_sequence", "0") or 0))):
        trip_id = row["trip_id"]
        if trip_id in departures:
            continue
        departures[trip_id] = parse_gtfs_time(row["departure_time"])
    return departures


def _percentile(values: List[int], percentile: float) -> float:
    if not values:
        return math.nan
    if len(values) == 1:
        return float(values[0])
    sorted_values = sorted(values)
    position = (len(sorted_values) - 1) * percentile
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return float(sorted_values[lower])
    weight = position - lower
    return float(sorted_values[lower] + weight * (sorted_values[upper] - sorted_values[lower]))


def _normalise_direction(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def compute_headways(feed_dir: Path, *, timebin_minutes: int | None = None) -> List[Dict[str, object]]:
    """Compute headway metrics per route/direction/timebin for the requested feed."""

    settings = get_settings()
    timebin_minutes = timebin_minutes or settings.timebin_minutes

    raw_dir = feed_dir / "raw"
    derived_dir = feed_dir / "derived"

    trips = _load_table(raw_dir, "trips")
    stop_times = _load_table(raw_dir, "stop_times")
    calendar = _load_table(derived_dir, "dim_calendar")

    departures = _compute_trip_departures(stop_times)
    results: List[Dict[str, object]] = []

    for day in calendar:
        service_ids: List[str] = list(day.get("service_ids", []))
        if not service_ids:
            continue
        day_type_id = day["day_type_id"]

        groups: Dict[Tuple[str, int | None, int], List[int]] = defaultdict(list)
        for trip in trips:
            if trip.get("service_id") not in service_ids:
                continue
            trip_id = trip["trip_id"]
            first_departure = departures.get(trip_id)
            if first_departure is None:
                continue
            bucket = (first_departure // (timebin_minutes * 60)) * (timebin_minutes * 60)
            route_id = trip.get("route_id", "")
            direction = _normalise_direction(trip.get("direction_id"))
            groups[(route_id, direction, bucket)].append(first_departure)

        for (route_id, direction, bucket), values in groups.items():
            values = sorted(values)
            if len(values) > 1:
                diffs = [b - a for a, b in zip(values[:-1], values[1:])]
            else:
                diffs = []
            headway_p50 = None if not diffs else _percentile(diffs, 0.5) / 60
            headway_p90 = None if not diffs else _percentile(diffs, 0.9) / 60
            results.append(
                {
                    "feed_id": feed_dir.name,
                    "day_type_id": day_type_id,
                    "route_id": route_id,
                    "direction_id": direction,
                    "timebin_start": bucket,
                    "timebin_label": format_seconds_as_time(bucket),
                    "departures": len(values),
                    "headway_p50_min": headway_p50,
                    "headway_p90_min": headway_p90,
                }
            )

    return sorted(
        results,
        key=lambda row: (
            row["day_type_id"],
            row["route_id"],
            row.get("direction_id") or -1,
            row["timebin_start"],
        ),
    )


def compute_service_kpis(feed_dir: Path) -> List[Dict[str, object]]:
    """Compute first/last departures and total departures per route/direction."""

    raw_dir = feed_dir / "raw"
    derived_dir = feed_dir / "derived"

    trips = _load_table(raw_dir, "trips")
    stop_times = _load_table(raw_dir, "stop_times")
    calendar = _load_table(derived_dir, "dim_calendar")

    departures = _compute_trip_departures(stop_times)
    records: List[Dict[str, object]] = []

    for day in calendar:
        service_ids: List[str] = list(day.get("service_ids", []))
        if not service_ids:
            continue
        day_type_id = day["day_type_id"]

        groups: Dict[Tuple[str, int | None], List[int]] = defaultdict(list)
        for trip in trips:
            if trip.get("service_id") not in service_ids:
                continue
            trip_id = trip["trip_id"]
            first_departure = departures.get(trip_id)
            if first_departure is None:
                continue
            route_id = trip.get("route_id", "")
            direction = _normalise_direction(trip.get("direction_id"))
            groups[(route_id, direction)].append(first_departure)

        for (route_id, direction), values in groups.items():
            values = sorted(values)
            records.append(
                {
                    "feed_id": feed_dir.name,
                    "day_type_id": day_type_id,
                    "route_id": route_id,
                    "direction_id": direction,
                    "first_departure": format_seconds_as_time(values[0]),
                    "last_departure": format_seconds_as_time(values[-1]),
                    "departures": len(values),
                }
            )

    return sorted(
        records,
        key=lambda row: (
            row["day_type_id"],
            row["route_id"],
            row.get("direction_id") or -1,
        ),
    )


__all__ = ["compute_headways", "compute_service_kpis"]
