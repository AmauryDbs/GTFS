"""Utilities for manipulating GTFS time fields."""

from __future__ import annotations

from datetime import time


def parse_gtfs_time(value: str) -> int:
    """Convert a GTFS HH:MM:SS string to seconds since midnight.

    GTFS allows times greater than 24:00:00 to represent after-midnight trips. This
    function keeps that behaviour by not applying modulo operations.
    """

    if not value:
        raise ValueError("Empty GTFS time string")
    parts = value.split(":")
    if len(parts) != 3:
        raise ValueError(f"Invalid GTFS time: {value}")
    hours, minutes, seconds = (int(part) for part in parts)
    return hours * 3600 + minutes * 60 + seconds


def format_seconds_as_time(value: int) -> str:
    """Format seconds since midnight into HH:MM."""

    hours = value // 3600
    minutes = (value % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"


def seconds_to_time(value: int) -> time:
    """Return a ``datetime.time`` representation, clipping to 24 hours."""

    value = max(0, value)
    hours = (value // 3600) % 24
    minutes = (value % 3600) // 60
    seconds = value % 60
    return time(hour=hours, minute=minutes, second=seconds)


__all__ = ["parse_gtfs_time", "format_seconds_as_time", "seconds_to_time"]
