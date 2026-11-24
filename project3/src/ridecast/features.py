"""Canonical feature construction shared by training and serving."""
from __future__ import annotations

from typing import Any

FEATURE_COLUMNS = [
    "month", "hour", "weekday", "is_holiday", "is_workingday",
    "weather_category", "temperature_c", "humidity_pct", "wind_speed_kmh",
]


def source_to_canonical(temp: float, humidity: float, wind: float) -> tuple[float, float, float]:
    return -8.0 + temp * 47.0, humidity * 100.0, wind * 67.0


def canonical_to_source(temp_c: float, humidity_pct: float, wind_kmh: float) -> tuple[float, float, float]:
    return (temp_c + 8.0) / 47.0, humidity_pct / 100.0, wind_kmh / 67.0


def make_features(values: dict[str, Any]) -> dict[str, Any]:
    weekday = int(values["weekday"])
    return {**values, "is_workingday": weekday < 5 and not bool(values["is_holiday"])}


def feature_columns() -> list[str]:
    return FEATURE_COLUMNS.copy()
