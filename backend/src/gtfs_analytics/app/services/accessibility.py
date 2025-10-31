"""Accessibility proxy computations using GTFS stop coverage."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from ..core.config import get_settings


def _haversine_distance_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    radius = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _load_json(path: Path) -> List[Dict[str, object]]:
    return json.loads(path.read_text())


def _load_zones(zones_path: Path) -> List[Dict[str, float]]:
    data = json.loads(zones_path.read_text())
    features = data.get("features", [])
    zones: List[Dict[str, float]] = []

    for feature in features:
        properties = feature.get("properties", {})
        geometry = feature.get("geometry") or {}
        zone_id = properties.get("zone_id")
        if zone_id is None:
            continue
        coords = geometry.get("coordinates") or []
        if geometry.get("type") == "Polygon" and coords:
            ring = coords[0]
        elif geometry.get("type") == "MultiPolygon" and coords:
            ring = coords[0][0]
        else:
            continue
        ring = [(float(x), float(y)) for x, y in ring]
        if ring and ring[0] == ring[-1]:
            ring = ring[:-1]
        lon, lat = _polygon_centroid(ring)
        zones.append({"zone_id": str(zone_id), "lon": lon, "lat": lat})

    return zones


def _polygon_centroid(points: Iterable[tuple[float, float]]) -> tuple[float, float]:
    pts = list(points)
    if not pts:
        return 0.0, 0.0
    area = 0.0
    cx = 0.0
    cy = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        cross = x1 * y2 - x2 * y1
        area += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    area *= 0.5
    if abs(area) < 1e-12:
        mean_x = sum(x for x, _ in pts) / len(pts)
        mean_y = sum(y for _, y in pts) / len(pts)
        return mean_x, mean_y
    cx /= 6 * area
    cy /= 6 * area
    return cx, cy


def _load_active_stop_ids(feed_dir: Path, service_ids: Iterable[str]) -> List[str]:
    stop_times = _load_json(feed_dir / "raw" / "stop_times.json")
    trips = _load_json(feed_dir / "raw" / "trips.json")
    active_trip_ids = {trip["trip_id"] for trip in trips if trip.get("service_id") in set(service_ids)}
    stop_ids = {row["stop_id"] for row in stop_times if row.get("trip_id") in active_trip_ids}
    return sorted(stop_ids)


def _load_stops(feed_dir: Path, stop_ids: Iterable[str]) -> List[Dict[str, float]]:
    stops = _load_json(feed_dir / "derived" / "dim_stop.json")
    stop_map = {row["stop_id"]: row for row in stops}
    results = []
    for stop_id in stop_ids:
        record = stop_map.get(stop_id)
        if not record:
            continue
        try:
            lon = float(record.get("lon", 0.0))
            lat = float(record.get("lat", 0.0))
        except (TypeError, ValueError):
            continue
        results.append({"stop_id": stop_id, "lon": lon, "lat": lat})
    return results


def _load_socio(path: Optional[Path]) -> Dict[str, Dict[str, int]]:
    if path is None:
        return {}
    if not path.exists():
        return {}
    suffix = path.suffix.lower()
    metrics: Dict[str, Dict[str, int]] = {}
    if suffix in {".json", ".geojson"}:
        payload = json.loads(path.read_text())
        records = payload.get("features") if isinstance(payload, dict) else payload
        if isinstance(records, list):
            for item in records:
                if isinstance(item, dict):
                    properties = item.get("properties", item)
                    zone_id = properties.get("zone_id")
                    if zone_id is None:
                        continue
                    metrics[str(zone_id)] = {
                        "population": int(properties.get("population", 0) or 0),
                        "jobs": int(properties.get("jobs", 0) or 0),
                        "schools": int(properties.get("schools", 0) or 0),
                    }
    elif suffix == ".csv":
        with path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                zone_id = row.get("zone_id")
                if zone_id is None:
                    continue
                metrics[str(zone_id)] = {
                    "population": int(row.get("population", 0) or 0),
                    "jobs": int(row.get("jobs", 0) or 0),
                    "schools": int(row.get("schools", 0) or 0),
                }
    return metrics


def _estimate_travel_minutes(distance_m: float, *, speed_kmh: float, penalty_min: float) -> float:
    travel_min = distance_m / (speed_kmh * 1000 / 60)
    return travel_min + penalty_min


def compute_accessibility(
    feed_dir: Path,
    zones_path: Path,
    *,
    socio_path: Optional[Path] = None,
    thresholds: Optional[List[int]] = None,
    speed_kmh: Optional[float] = None,
    penalty_min: Optional[float] = None,
) -> List[Dict[str, object]]:
    settings = get_settings()
    thresholds = thresholds or settings.accessibility_thresholds
    speed_kmh = speed_kmh or settings.default_service_speed_kmh
    penalty_min = penalty_min or settings.default_boarding_penalty_min

    zones = _load_zones(zones_path)
    calendar = _load_json(feed_dir / "derived" / "dim_calendar.json")
    socio = _load_socio(Path(socio_path) if socio_path else None)

    records: List[Dict[str, object]] = []

    for day in calendar:
        service_ids: List[str] = list(day.get("service_ids", []))
        if not service_ids:
            continue
        day_type_id = day["day_type_id"]
        stop_ids = _load_active_stop_ids(feed_dir, service_ids)
        if not stop_ids:
            continue
        stops = _load_stops(feed_dir, stop_ids)
        if not stops:
            continue

        for zone in zones:
            metrics = socio.get(zone["zone_id"], {"population": 0, "jobs": 0, "schools": 0})
            for threshold in thresholds:
                reachable = 0
                for stop in stops:
                    distance = _haversine_distance_m(zone["lon"], zone["lat"], stop["lon"], stop["lat"])
                    minutes = _estimate_travel_minutes(distance, speed_kmh=speed_kmh, penalty_min=penalty_min)
                    if minutes <= threshold:
                        reachable += 1
                records.append(
                    {
                        "feed_id": feed_dir.name,
                        "zone_id": zone["zone_id"],
                        "day_type_id": day_type_id,
                        "threshold_min": threshold,
                        "stops_reachable": reachable,
                        "pop_reachable": metrics["population"] if reachable else 0,
                        "jobs_reachable": metrics["jobs"] if reachable else 0,
                        "schools_reachable": metrics["schools"] if reachable else 0,
                    }
                )

    return sorted(
        records,
        key=lambda row: (
            row["zone_id"],
            row["day_type_id"],
            row["threshold_min"],
        ),
    )


__all__ = ["compute_accessibility"]
