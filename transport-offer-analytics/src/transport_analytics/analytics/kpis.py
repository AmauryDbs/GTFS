"""Calculs d'indicateurs clés de performance."""
from __future__ import annotations

from typing import List

import polars as pl

from transport_analytics.config import DERIVED_DIR, PARQUET_CORE
from transport_analytics.utils.timebands import DEFAULT_TIMEBANDS


def _time_to_minutes(time_value: str) -> int:
    """Convertit HH:MM:SS (GTFS) en minutes, supportant >24h."""
    hour, minute, _second = [int(part) for part in time_value.split(":")]
    return hour * 60 + minute


def compute_headways_by_route_daytype() -> pl.DataFrame:
    """Calcule des headways moyens par ligne et type de jour."""
    stop_times = pl.read_parquet(PARQUET_CORE / "stop_times_core.parquet")
    trips = pl.read_parquet(PARQUET_CORE / "trips_core.parquet")

    first_stops = stop_times.filter(pl.col("stop_sequence") == 1).select(
        "trip_id", "departure_time"
    )
    enriched = trips.join(first_stops, on="trip_id", how="inner").with_columns(
        pl.col("departure_time").map_elements(_time_to_minutes, return_dtype=pl.Int64).alias("dep_min"),
        pl.lit("Semaine").alias("day_type"),
    )

    aggregates: List[pl.DataFrame] = []
    for start, end, label in DEFAULT_TIMEBANDS:
        bucket = enriched.filter((pl.col("dep_min") >= start) & (pl.col("dep_min") < end))
        if bucket.is_empty():
            continue
        summary = (
            bucket.group_by(["route_id", "day_type"])
            .agg(pl.len().alias("trips"))
            .with_columns(((end - start) / pl.col("trips")).cast(pl.Float64).alias("avg_headway_min"))
            .with_columns(pl.lit(label).alias("timeband"))
        )
        aggregates.append(summary)

    result = pl.concat(aggregates, how="vertical") if aggregates else pl.DataFrame()
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    result.write_parquet(DERIVED_DIR / "headways_by_route_daytype.parquet")
    return result


if __name__ == "__main__":
    dataframe = compute_headways_by_route_daytype()
    print(dataframe.head())
