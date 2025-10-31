from __future__ import annotations

import argparse
import json
from pathlib import Path

from gtfs_analytics.app.services.accessibility import compute_accessibility


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute accessibility proxies")
    parser.add_argument("feed_id", help="Feed identifier")
    parser.add_argument("zones", type=Path, help="Path to a GeoJSON zones dataset")
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    parser.add_argument("--socio", type=Path, default=None, help="Optional socio-economic dataset (CSV/JSON)")
    parser.add_argument(
        "--thresholds",
        type=str,
        default=None,
        help="Comma separated thresholds in minutes (e.g. 15,30,45)",
    )
    parser.add_argument("--speed", type=float, default=None, help="Average in-vehicle speed km/h")
    parser.add_argument("--penalty", type=float, default=None, help="Transfer penalty in minutes")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_dir = args.data_dir
    feed_dir = data_dir / "feeds" / args.feed_id
    if not feed_dir.exists():
        raise SystemExit(f"Feed {args.feed_id} not found in {data_dir}")

    thresholds = [int(value) for value in args.thresholds.split(",")] if args.thresholds else None
    records = compute_accessibility(
        feed_dir,
        args.zones,
        socio_path=args.socio,
        thresholds=thresholds,
        speed_kmh=args.speed,
        penalty_min=args.penalty,
    )
    output = feed_dir / "metrics" / "fct_coverage.json"
    output.parent.mkdir(exist_ok=True)
    if records:
        output.write_text(json.dumps(records, indent=2))
        print(f"Accessibility metrics stored at {output}")
    else:
        print("No accessibility records generated.")


if __name__ == "__main__":
    main()
