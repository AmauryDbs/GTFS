"""GTFS ingestion pipeline using standard library primitives."""

from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional

from ..core.config import get_settings
from .catalog import DatasetRegistry

GTFS_REQUIRED_FILES = [
    "agency.txt",
    "routes.txt",
    "trips.txt",
    "stop_times.txt",
    "stops.txt",
    "calendar.txt",
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
        missing = [name for name in GTFS_REQUIRED_FILES if name not in archive.namelist()]
        if missing:
            raise ValueError(f"Missing GTFS files: {', '.join(missing)}")

        tables: Dict[str, List[Dict[str, str]]] = {}
        for name in archive.namelist():
            if not name.endswith(".txt"):
                continue
            tables[name[:-4]] = _read_gtfs_table(archive, name)

    calendar = _normalise_calendar(tables["calendar"])
    day_types = _build_day_types(calendar)

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
    validity_start = min(row["start_date"] for row in calendar)
    validity_end = max(row["end_date"] for row in calendar)
    dim_feed = [
        {
            "feed_id": feed_hash,
            "provider": provider,
            "validity_start": validity_start.isoformat(),
            "validity_end": validity_end.isoformat(),
            "version_hash": feed_hash,
        }
    ]
    _write_json(derived_dir / "dim_feed.json", dim_feed)

    DatasetRegistry(output_root).upsert_feed(
        {
            "feed_id": feed_hash,
            "provider": provider,
            "validity_start": validity_start.isoformat(),
            "validity_end": validity_end.isoformat(),
            "version_hash": feed_hash,
            "source_path": str(zip_path.resolve()),
        }
    )

    return IngestionResult(feed_id=feed_hash, output_dir=feed_dir)


__all__ = ["ingest_gtfs", "IngestionResult", "GTFS_REQUIRED_FILES"]
