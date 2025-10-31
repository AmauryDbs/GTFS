"""Compute headway metrics for an ingested feed."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gtfs_analytics.app.core.config import get_settings
from gtfs_analytics.app.services.headways import compute_headways, compute_service_kpis


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute headway metrics")
    parser.add_argument("feed_id", help="Feed identifier (hash)")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data",
        help="Root data directory",
    )
    parser.add_argument("--timebin", type=int, default=None, help="Timebin size in minutes")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    data_dir = args.data_dir or settings.data_dir
    feed_dir = data_dir / "feeds" / args.feed_id
    if not feed_dir.exists():
        raise SystemExit(f"Feed {args.feed_id} not found in {data_dir}")

    headways = compute_headways(feed_dir, timebin_minutes=args.timebin)
    kpis = compute_service_kpis(feed_dir)

    metrics_dir = feed_dir / "metrics"
    metrics_dir.mkdir(exist_ok=True)
    if headways:
        (metrics_dir / "fct_headway.json").write_text(json.dumps(headways, indent=2))
    if kpis:
        (metrics_dir / "line_service_kpi.json").write_text(json.dumps(kpis, indent=2))

    print(f"Headways computed for feed {args.feed_id} → {metrics_dir}")


if __name__ == "__main__":
    main()
