"""API router definitions."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..core.config import Settings, get_settings
from ..models.feed import CoverageRecord, FeedCatalog, FeedSummary, HeadwayBin, LineServiceKPI
from ..services.accessibility import compute_accessibility
from ..services.catalog import DatasetRegistry
from ..services.headways import compute_headways, compute_service_kpis
from ..services.ingest import IngestionResult, ingest_gtfs

router = APIRouter()
local_router = APIRouter(prefix="/api", tags=["local"])


def _available_feed_ids(settings: Settings) -> List[str]:
    feeds_dir = settings.data_dir / "feeds"
    if not feeds_dir.exists():
        return []
    return sorted([path.name for path in feeds_dir.iterdir() if path.is_dir()])


@local_router.get("/feeds")
async def list_local_feed_ids(settings: Settings = Depends(get_settings)) -> dict[str, List[str]]:
    return {"feeds": _available_feed_ids(settings)}


@local_router.get("/latest_feed")
async def latest_local_feed(settings: Settings = Depends(get_settings)) -> dict[str, Optional[str]]:
    feeds = _available_feed_ids(settings)
    return {"feedId": feeds[-1] if feeds else None}


def _feed_dir(feed_id: str, settings: Settings) -> Path:
    path = settings.data_dir / "feeds" / feed_id
    if not path.exists():
        raise HTTPException(status_code=404, detail="Feed not found")
    return path


@router.post("/ingest/gtfs", response_model=IngestionResult)
async def ingest_gtfs_endpoint(
    upload: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
) -> IngestionResult:
    data = await upload.read()
    tmp_path = settings.data_dir / "tmp" / upload.filename
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.write_bytes(data)
    try:
        result = ingest_gtfs(tmp_path, output_root=settings.data_dir)
    finally:
        tmp_path.unlink(missing_ok=True)
    return result


@router.get("/feeds", response_model=FeedCatalog)
async def list_feeds(settings: Settings = Depends(get_settings)) -> FeedCatalog:
    registry = DatasetRegistry(settings.data_dir)
    feeds = [FeedSummary(**feed) for feed in registry.list_feeds()]
    return FeedCatalog(feeds=feeds)


@router.get("/headways", response_model=List[HeadwayBin])
async def headways(
    feed_id: str,
    day_type_id: Optional[str] = None,
    settings: Settings = Depends(get_settings),
) -> List[HeadwayBin]:
    feed_dir = _feed_dir(feed_id, settings)
    rows = compute_headways(feed_dir)
    if day_type_id:
        rows = [row for row in rows if row.get("day_type_id") == day_type_id]
    return [
        HeadwayBin(
            feed_id=row["feed_id"],
            day_type_id=row["day_type_id"],
            route_id=row["route_id"],
            direction_id=row.get("direction_id"),
            timebin_start=row["timebin_label"],
            departures=row["departures"],
            headway_p50_min=row.get("headway_p50_min"),
            headway_p90_min=row.get("headway_p90_min"),
        )
        for row in rows
    ]


@router.get("/feeds/{feed_id}/kpi", response_model=List[LineServiceKPI])
async def feed_kpis(feed_id: str, settings: Settings = Depends(get_settings)) -> List[LineServiceKPI]:
    feed_dir = _feed_dir(feed_id, settings)
    rows = compute_service_kpis(feed_dir)
    return [
        LineServiceKPI(
            feed_id=row["feed_id"],
            day_type_id=row["day_type_id"],
            route_id=row["route_id"],
            direction_id=row.get("direction_id"),
            first_departure=row.get("first_departure"),
            last_departure=row.get("last_departure"),
            departures=row["departures"],
        )
        for row in rows
    ]


@router.get("/coverage", response_model=List[CoverageRecord])
async def coverage(
    feed_id: str,
    zones_path: str,
    thresholds: Optional[str] = None,
    settings: Settings = Depends(get_settings),
) -> List[CoverageRecord]:
    feed_dir = _feed_dir(feed_id, settings)
    threshold_list = [int(value) for value in thresholds.split(",")] if thresholds else None
    rows = compute_accessibility(feed_dir, Path(zones_path), thresholds=threshold_list)
    return [
        CoverageRecord(
            feed_id=row["feed_id"],
            zone_id=row["zone_id"],
            day_type_id=row["day_type_id"],
            threshold_min=row["threshold_min"],
            stops_reachable=row["stops_reachable"],
            pop_reachable=row.get("pop_reachable"),
            jobs_reachable=row.get("jobs_reachable"),
            schools_reachable=row.get("schools_reachable"),
        )
        for row in rows
    ]


@router.get("/export/{artifact}")
async def export_artifact(artifact: str, settings: Settings = Depends(get_settings)) -> FileResponse:
    path = settings.data_dir / artifact
    if not path.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")
    return FileResponse(path)


__all__ = ["router", "local_router"]
