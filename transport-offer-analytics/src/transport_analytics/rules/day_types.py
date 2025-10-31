"""Construction des jours-types à partir des règles YAML."""
from __future__ import annotations

import datetime as dt
from typing import Dict, Iterable, List, Tuple

import polars as pl
import yaml

from transport_analytics.config import PARQUET_CORE, REF_DIR


def _load_rules() -> Dict[str, Dict[str, str]]:
    with (REF_DIR / "day_types.yaml").open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _date_range(start: dt.date, end: dt.date) -> Iterable[dt.date]:
    current = start
    while current <= end:
        yield current
        current += dt.timedelta(days=1)


def build_service_day_map() -> pl.DataFrame:
    """Retourne un DataFrame (service_id, date, day_type)."""
    rules = _load_rules()
    defaults = rules.get("defaults", {})
    overrides = rules.get("overrides", {})

    calendar = pl.read_parquet(PARQUET_CORE / "calendar_core.parquet")
    rows: List[Tuple[str, str, str]] = []

    for record in calendar.iter_rows(named=True):
        start = dt.datetime.strptime(str(record["start_date"]), "%Y%m%d").date()
        end = dt.datetime.strptime(str(record["end_date"]), "%Y%m%d").date()
        for current in _date_range(start, end):
            weekday_name = current.strftime("%A").lower()
            flag = record.get(weekday_name, 0)
            if flag == 1:
                date_iso = current.isoformat()
                day_type = overrides.get(date_iso, defaults.get(weekday_name, "Semaine"))
                rows.append((str(record["service_id"]), date_iso, day_type))

    return pl.DataFrame(rows, schema=["service_id", "date", "day_type"])
