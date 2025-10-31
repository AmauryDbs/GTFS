"""Fonctions de jointures spatiales avec DuckDB."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import duckdb
import polars as pl

from transport_analytics.config import PARQUET_CORE, PARQUET_GEO


def stops_to_mesh(mesh_path: str | Path, out_path: Optional[str | Path] = None) -> str:
    """Rattache les arrêts aux polygones d'une maille géographique."""
    connection = duckdb.connect()
    connection.sql("INSTALL spatial; LOAD spatial;")
    connection.sql(
        """
        CREATE VIEW stops AS
        SELECT * FROM read_parquet(?)
        """,
        [(PARQUET_CORE / "stops_core.parquet").as_posix()],
    )
    connection.sql(
        """
        CREATE VIEW mesh AS
        SELECT * FROM st_read(?)
        """,
        [Path(mesh_path).as_posix()],
    )
    query = """
    SELECT
      m.*, s.stop_id
    FROM mesh m
    JOIN (
      SELECT stop_id, ST_Point(stop_lon, stop_lat) AS geom FROM stops
    ) s
    ON ST_Contains(m.geom, s.geom)
    """
    df: pl.DataFrame = connection.sql(query).pl()
    output = Path(out_path) if out_path is not None else PARQUET_GEO / "stop_to_mesh.parquet"
    df.write_parquet(output.as_posix())
    return output.as_posix()
