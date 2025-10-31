"""Module d'ingestion des données GTFS."""
from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path
from typing import Dict

import polars as pl

from transport_analytics.config import PARQUET_CORE

REQUIRED = [
    "agency.txt",
    "stops.txt",
    "routes.txt",
    "trips.txt",
    "stop_times.txt",
    "calendar.txt",
]
OPTIONAL = ["calendar_dates.txt", "shapes.txt", "frequencies.txt"]


def _read_csv_from_zip(zf: zipfile.ZipFile, name: str) -> pl.DataFrame:
    """Lit un fichier CSV stocké dans l'archive GTFS."""
    with zf.open(name) as file_handle:
        return pl.read_csv(io.BytesIO(file_handle.read()), infer_schema_length=10_000)


def ingest_gtfs(gtfs_zip: Path) -> None:
    """Ingestion principale : valide la présence des fichiers requis et les écrit en Parquet."""
    if not gtfs_zip.exists():
        raise FileNotFoundError(f"GTFS introuvable: {gtfs_zip}")

    with zipfile.ZipFile(gtfs_zip, "r") as archive:
        names = set(archive.namelist())
        for required in REQUIRED:
            if required not in names:
                raise FileNotFoundError(f"Fichier GTFS manquant: {required}")

        tables: Dict[str, pl.DataFrame] = {}
        for table_name in REQUIRED + OPTIONAL:
            if table_name in names:
                tables[table_name] = _read_csv_from_zip(archive, table_name)

    routes = tables["routes.txt"].with_columns(
        pl.col("route_type").cast(pl.Int64, strict=False).alias("route_type")
    )
    stops = tables["stops.txt"].with_columns(
        pl.col("stop_lat").cast(pl.Float64, strict=False),
        pl.col("stop_lon").cast(pl.Float64, strict=False),
    )
    trips = tables["trips.txt"]
    stop_times = tables["stop_times.txt"].with_columns(
        pl.when(pl.col("arrival_time").str.contains(":"))
        .then(pl.col("arrival_time"))
        .otherwise("00:00:00")
        .alias("arrival_time"),
        pl.when(pl.col("departure_time").str.contains(":"))
        .then(pl.col("departure_time"))
        .otherwise("00:00:00")
        .alias("departure_time"),
        pl.col("stop_sequence").cast(pl.Int64, strict=False),
    )
    calendar = tables["calendar.txt"]

    (PARQUET_CORE / "routes_core.parquet").parent.mkdir(parents=True, exist_ok=True)
    routes.write_parquet(PARQUET_CORE / "routes_core.parquet")
    stops.write_parquet(PARQUET_CORE / "stops_core.parquet")
    trips.write_parquet(PARQUET_CORE / "trips_core.parquet")
    stop_times.write_parquet(PARQUET_CORE / "stop_times_core.parquet")
    calendar.write_parquet(PARQUET_CORE / "calendar_core.parquet")

    if "calendar_dates.txt" in tables:
        tables["calendar_dates.txt"].write_parquet(PARQUET_CORE / "calendar_dates.parquet")
    if "shapes.txt" in tables:
        tables["shapes.txt"].write_parquet(PARQUET_CORE / "shapes_core.parquet")
    if "frequencies.txt" in tables:
        tables["frequencies.txt"].write_parquet(PARQUET_CORE / "frequencies_core.parquet")

    print(f"Ingestion terminée → {PARQUET_CORE}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m transport_analytics.ingest.gtfs data/raw/gtfs/monreseau.zip")
        sys.exit(1)
    ingest_gtfs(Path(sys.argv[1]))
