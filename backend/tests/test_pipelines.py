from __future__ import annotations

import json
import zipfile
from pathlib import Path
import sys

sys.path.append(str((Path(__file__).resolve().parents[1] / "src").resolve()))

import pytest

from gtfs_analytics.app.services.accessibility import compute_accessibility
from gtfs_analytics.app.services.catalog import DatasetRegistry
from gtfs_analytics.app.services.headways import compute_headways, compute_service_kpis
from gtfs_analytics.app.services.ingest import ingest_gtfs


@pytest.fixture()
def sample_gtfs_zip(tmp_path: Path) -> Path:
    files = {
        "agency.txt": "\n".join(
            [
                "agency_id,agency_name,agency_url,agency_timezone",
                "A1,Sample Agency,https://example.com,Europe/Paris",
            ]
        )
        + "\n",
        "routes.txt": "\n".join(
            [
                "route_id,agency_id,route_short_name,route_long_name,route_type",
                "R1,A1,1,Route 1,3",
            ]
        )
        + "\n",
        "trips.txt": "\n".join(
            [
                "route_id,service_id,trip_id,direction_id",
                "R1,WD,R1_TRIP_1,0",
                "R1,WD,R1_TRIP_2,0",
                "R1,SAT,R1_TRIP_3,0",
                "R1,SUN,R1_TRIP_4,0",
            ]
        )
        + "\n",
        "stop_times.txt": "\n".join(
            [
                "trip_id,arrival_time,departure_time,stop_id,stop_sequence",
                "R1_TRIP_1,06:00:00,06:00:00,S1,1",
                "R1_TRIP_1,06:15:00,06:15:00,S2,2",
                "R1_TRIP_2,07:00:00,07:00:00,S1,1",
                "R1_TRIP_2,07:15:00,07:15:00,S2,2",
                "R1_TRIP_3,08:00:00,08:00:00,S1,1",
                "R1_TRIP_3,08:15:00,08:15:00,S2,2",
                "R1_TRIP_4,09:00:00,09:00:00,S1,1",
                "R1_TRIP_4,09:15:00,09:15:00,S2,2",
            ]
        )
        + "\n",
        "stops.txt": "\n".join(
            [
                "stop_id,stop_name,stop_lat,stop_lon",
                "S1,Stop 1,48.8566,2.3522",
                "S2,Stop 2,48.858,2.36",
            ]
        )
        + "\n",
        "calendar.txt": "\n".join(
            [
                "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date",
                "WD,1,1,1,1,1,0,0,20240101,20241231",
                "SAT,0,0,0,0,0,1,0,20240101,20241231",
                "SUN,0,0,0,0,0,0,1,20240101,20241231",
            ]
        )
        + "\n",
    }
    zip_path = tmp_path / "sample_gtfs.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return zip_path


def test_ingest_and_headways(tmp_path: Path, sample_gtfs_zip: Path) -> None:
    data_dir = tmp_path / "data"
    result = ingest_gtfs(sample_gtfs_zip, output_root=data_dir)

    assert (result.output_dir / "raw" / "trips.json").exists()
    registry = DatasetRegistry(data_dir)
    feeds = registry.list_feeds()
    assert any(feed["feed_id"] == result.feed_id for feed in feeds)

    headways = compute_headways(result.output_dir)
    assert headways
    assert any(row["day_type_id"] == "WEEKDAY" for row in headways)

    kpis = compute_service_kpis(result.output_dir)
    assert kpis
    assert sum(row["departures"] for row in kpis) >= 4


def test_accessibility_proxy(tmp_path: Path, sample_gtfs_zip: Path) -> None:
    data_dir = tmp_path / "data"
    result = ingest_gtfs(sample_gtfs_zip, output_root=data_dir)

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"zone_id": "Z1"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [2.34, 48.85],
                            [2.37, 48.85],
                            [2.37, 48.87],
                            [2.34, 48.87],
                            [2.34, 48.85],
                        ]
                    ],
                },
            }
        ],
    }
    zones_path = tmp_path / "zones.geojson"
    zones_path.write_text(json.dumps(geojson))

    records = compute_accessibility(result.output_dir, zones_path, thresholds=[30])
    assert records
    assert any(record["stops_reachable"] >= 1 for record in records)


def test_ingest_without_calendar(tmp_path: Path) -> None:
    files = {
        "agency.txt": "\n".join(
            [
                "agency_id,agency_name,agency_url,agency_timezone",
                "A1,Sample Agency,https://example.com,Europe/Paris",
            ]
        )
        + "\n",
        "routes.txt": "\n".join(
            [
                "route_id,agency_id,route_short_name,route_long_name,route_type",
                "R1,A1,1,Route 1,3",
            ]
        )
        + "\n",
        "trips.txt": "\n".join(
            [
                "route_id,service_id,trip_id,direction_id",
                "R1,WD,R1_TRIP_1,0",
                "R1,WD,R1_TRIP_2,0",
            ]
        )
        + "\n",
        "stop_times.txt": "\n".join(
            [
                "trip_id,arrival_time,departure_time,stop_id,stop_sequence",
                "R1_TRIP_1,06:00:00,06:00:00,S1,1",
                "R1_TRIP_1,06:15:00,06:15:00,S2,2",
                "R1_TRIP_2,07:00:00,07:00:00,S1,1",
                "R1_TRIP_2,07:15:00,07:15:00,S2,2",
            ]
        )
        + "\n",
        "stops.txt": "\n".join(
            [
                "stop_id,stop_name,stop_lat,stop_lon",
                "S1,Stop 1,48.8566,2.3522",
                "S2,Stop 2,48.858,2.36",
            ]
        )
        + "\n",
        "calendar_dates.txt": "\n".join(
            [
                "service_id,date,exception_type",
                "WD,20240101,1",
                "WD,20240131,1",
            ]
        )
        + "\n",
    }
    zip_path = tmp_path / "gtfs_without_calendar.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)

    data_dir = tmp_path / "data"
    result = ingest_gtfs(zip_path, output_root=data_dir)

    dim_calendar = json.loads((result.output_dir / "derived" / "dim_calendar.json").read_text())
    assert dim_calendar
    assert dim_calendar[0]["day_type_id"] == "ALL"
    assert dim_calendar[0]["service_ids"] == ["WD"]

    dim_feed = json.loads((result.output_dir / "derived" / "dim_feed.json").read_text())
    assert dim_feed[0]["validity_start"] == "2024-01-01"
    assert dim_feed[0]["validity_end"] == "2024-01-31"

    registry = DatasetRegistry(data_dir)
    feeds = registry.list_feeds()
    stored = next(feed for feed in feeds if feed["feed_id"] == result.feed_id)
    assert stored["validity_start"] == "2024-01-01"
    assert stored["validity_end"] == "2024-01-31"
