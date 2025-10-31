"""Tests basiques de présence des sorties d'ingestion."""
from pathlib import Path


def test_parquet_written() -> None:
    core = Path("data/parquet/core")
    assert core.exists()
    expected = [
        "routes_core.parquet",
        "stops_core.parquet",
        "trips_core.parquet",
        "stop_times_core.parquet",
        "calendar_core.parquet",
    ]
    for filename in expected:
        assert (core / filename).exists(), f"Missing {filename}"
