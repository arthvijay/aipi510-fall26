import pytest
from pydantic import ValidationError
from ridecast.schemas import BatchRequest, PredictionRequest


def valid():
    return {"month": 9, "hour": 8, "weekday": 1, "is_holiday": False,
            "weather_category": 1, "temperature_c": 22.0, "humidity_pct": 55.0,
            "wind_speed_kmh": 12.0}


def test_extra_fields_rejected():
    with pytest.raises(ValidationError):
        PredictionRequest(**{**valid(), "unexpected": 1})


def test_batch_limit():
    with pytest.raises(ValidationError):
        BatchRequest(instances=[valid()] * 49)
