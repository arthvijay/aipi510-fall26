"""Strict API request and response schemas."""
from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictFloat, StrictInt


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    month: Annotated[StrictInt, Field(ge=1, le=12)]
    hour: Annotated[StrictInt, Field(ge=0, le=23)]
    weekday: Annotated[StrictInt, Field(ge=0, le=6)]
    is_holiday: StrictBool
    weather_category: Annotated[StrictInt, Field(ge=1, le=4)]
    temperature_c: Annotated[StrictFloat, Field(ge=-8, le=39)]
    humidity_pct: Annotated[StrictFloat, Field(ge=0, le=100)]
    wind_speed_kmh: Annotated[StrictFloat, Field(ge=0, le=67)]

    def features(self) -> dict[str, object]:
        return self.model_dump()


class BatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    instances: Annotated[list[PredictionRequest], Field(min_length=1, max_length=48)]


class PredictionResponse(BaseModel):
    predicted_rentals_per_hour: float
    demand_level: str
    model_version: str
    population: str = "systemwide"
    data_period: str
    warnings: list[str]


class BatchResponse(BaseModel):
    predictions: list[PredictionResponse]
