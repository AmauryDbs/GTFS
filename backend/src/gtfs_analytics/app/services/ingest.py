"""GTFS ingestion pipeline using standard library primitives."""

from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional

from ..core.config import get_settings
from .catalog import DatasetRegistry

GTFS_REQUIRED_FILES = [
    "trips.txt",
    "stop_times.txt",
    "stops.txt",
]


@dataclass(slots=True)
class IngestionResult:
    feed_id: str
    output_dir: Path


def _hash_file(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_gtfs_table(archive: zipfile.ZipFile, name: str) -> List[Dict[str, str]]:
    with archive.open(name) as buffer:
        text = buffer.read().decode("utf-8-sig")
    reader = csv.DictReader(text.splitlines())
    return [dict(row) for row in reader]


def _write_json(path: Path, rows: Iterable[Dict[str, object]]) -> None:
    path.write_text(json.dumps(list(rows), indent=2, default=str))


def _normalise_calendar(rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    normalised: List[Dict[str, object]] = []
    for row in rows:
        entry = dict(row)
        entry["start_date"] = datetime.strptime(row["start_date"], "%Y%m%d").date()
        entry["end_date"] = datetime.strptime(row["end_date"], "%Y%m%d").date()
        for key in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            entry[key] = int(row.get(key, "0") or 0)
        normalised.append(entry)
    return normalised


def _build_day_types(calendar: List[Dict[str, object]]) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []

    def add(day_type_id: str, label: str, predicate: Callable[[Dict[str, object]], bool]) -> None:
        service_ids = [row["service_id"] for row in calendar if predicate(row)]
        if service_ids:
            records.append({"day_type_id": day_type_id, "label": label, "service_ids": service_ids})

    add(
        "WEEKDAY",
        "Semaine",
        lambda row: all(row[day] == 1 for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]) and row["saturday"] == 0 and row["sunday"] == 0,
    )
    add(
        "SATURDAY",
        "Samedi",
        lambda row: row["saturday"] == 1 and sum(row[day] for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "sunday"]) == 0,
    )
    add(
        "SUNDAY",
        "Dimanche",
        lambda row: row["sunday"] == 1 and sum(row[day] for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]) == 0,
    )

    if not records:
        records.append(
            {
                "day_type_id": "ALL",
                "label": "Jour-type",
                "service_ids": [row["service_id"] for row in calendar],
            }
        )

    return records


def _fallback_day_types(trips: List[Dict[str, str]]) -> List[Dict[str, object]]:
    service_ids = sorted({row.get("service_id") for row in trips if row.get("service_id")})
    if not service_ids:
        return []
    return [
        {
            "day_type_id": "ALL",
            "label": "Jour-type",
            "service_ids": service_ids,
        }
    ]


def _compute_validity(
    calendar: List[Dict[str, object]],
    calendar_dates: List[Dict[str, str]],
) -> tuple[Optional[date], Optional[date]]:
    if calendar:
        start = min(row["start_date"] for row in calendar)
        end = max(row["end_date"] for row in calendar)
        return start, end

    dates = []
    for row in calendar_dates:
        date_str = row.get("date")
        if not date_str:
            continue
        try:
            service_date = datetime.strptime(date_str, "%Y%m%d").date()
        except ValueError:
            continue
        exception_type = str(row.get("exception_type", "1") or "1")
        if exception_type == "1":
            dates.append(service_date)

    if dates:
        return min(dates), max(dates)

    return None, None


def ingest_gtfs(zip_path: Path, *, output_root: Optional[Path] = None) -> IngestionResult:
    """Ingest a GTFS feed, convert to JSON snapshots, and update the dataset registry."""

    settings = get_settings()
    output_root = Path(output_root) if output_root else settings.data_dir
    output_root.mkdir(parents=True, exist_ok=True)

    if not zip_path.exists():
        raise FileNotFoundError(zip_path)

    feed_hash = _hash_file(zip_path)
    feed_dir = output_root / "feeds" / feed_hash
    raw_dir = feed_dir / "raw"
    derived_dir = feed_dir / "derived"
    raw_dir.mkdir(parents=True, exist_ok=True)
    derived_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        missing = [name for name in GTFS_REQUIRED_FILES if name not in names]
        if missing:
            raise ValueError(f"Missing GTFS files: {', '.join(missing)}")

        tables: Dict[str, List[Dict[str, str]]] = {}
        for name in names:
            if not name.endswith(".txt"):
                continue
            tables[name[:-4]] = _read_gtfs_table(archive, name)

    calendar_rows = tables.get("calendar") or []
    calendar = _normalise_calendar(calendar_rows) if calendar_rows else []
    if calendar:
        day_types = _build_day_types(calendar)
    else:
        day_types = _fallback_day_types(tables.get("trips", []))

    for table_name, rows in tables.items():
        _write_json(raw_dir / f"{table_name}.json", rows)

    _write_json(derived_dir / "dim_calendar.json", day_types)

    stops_enriched = []
    for stop in tables["stops"]:
        stops_enriched.append(
            {
                "stop_id": stop["stop_id"],
                "name": stop.get("stop_name"),
                "lon": float(stop.get("stop_lon", "0") or 0.0),
                "lat": float(stop.get("stop_lat", "0") or 0.0),
                "feed_id": feed_hash,
            }
        )
    _write_json(derived_dir / "dim_stop.json", stops_enriched)

    agency = tables.get("agency") or []
    provider = agency[0].get("agency_name") if agency else None
    validity_start, validity_end = _compute_validity(calendar, tables.get("calendar_dates") or [])
    dim_feed = [
        {
            "feed_id": feed_hash,
            "provider": provider,
            "validity_start": validity_start.isoformat() if validity_start else None,
            "validity_end": validity_end.isoformat() if validity_end else None,
            "version_hash": feed_hash,
        }
    ]
    _write_json(derived_dir / "dim_feed.json", dim_feed)

    DatasetRegistry(output_root).upsert_feed(
        {
            "feed_id": feed_hash,
            "provider": provider,
            "validity_start": validity_start.isoformat() if validity_start else None,
            "validity_end": validity_end.isoformat() if validity_end else None,
            "version_hash": feed_hash,
            "source_path": str(zip_path.resolve()),
        }
    )

    return IngestionResult(feed_id=feed_hash, output_dir=feed_dir)


__all__ = ["ingest_gtfs", "IngestionResult", "GTFS_REQUIRED_FILES"]
