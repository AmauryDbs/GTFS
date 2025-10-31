#!/usr/bin/env python
"""CLI wrapper for GTFS ingestion."""

from __future__ import annotations

import argparse
from pathlib import Path

from gtfs_analytics.app.services.ingest import ingest_gtfs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest a GTFS zip feed")
    parser.add_argument("gtfs_zip", type=Path, help="Path to the GTFS zip file")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data",
        help="Output data directory",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = ingest_gtfs(args.gtfs_zip, output_root=args.output)
    print(f"Feed {result.feed_id} ingested into {result.output_dir}")


if __name__ == "__main__":
    main()
