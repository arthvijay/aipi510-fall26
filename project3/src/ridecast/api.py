"""FastAPI inference service."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException

from .artifacts import load_release
from .config import load_config
from .features import make_features
from .schemas import BatchRequest, BatchResponse, PredictionRequest, PredictionResponse

STATE: dict[str, Any] = {}


def _warnings(values: dict, metadata: dict) -> list[str]:
    warnings = []
    ranges = metadata.get("feature_ranges", {})
    for key in ("temperature_c", "humidity_pct", "wind_speed_kmh"):
        if key in ranges and not ranges[key][0] <= values[key] <= ranges[key][1]:
            warnings.append(f"{key} is outside the observed training range.")
    return warnings


def _predict(request: PredictionRequest) -> PredictionResponse:
    if not STATE:
        raise HTTPException(503, "Model is not ready.")
    values = make_features(request.features())
    prediction = max(0.0, float(STATE["model"].predict(pd.DataFrame([values]))[0]))
    low, high = STATE["metadata"].get("demand_thresholds", [0, float("inf")])
    level = "lower" if prediction < low else "higher" if prediction >= high else "typical"
    return PredictionResponse(predicted_rentals_per_hour=prediction, demand_level=level,
                              model_version=STATE["metadata"]["model_version"],
                              data_period=STATE["metadata"].get("data_period", "2011–2012"),
                              warnings=_warnings(values, STATE["metadata"]))


@asynccontextmanager
async def lifespan(_: FastAPI):
    config = load_config(os.getenv("RIDECAST_CONFIG", "config.yaml"))
    source = os.getenv("RIDECAST_MODEL_SOURCE", "local")
    release = os.getenv("RIDECAST_MODEL_DIR")
    if source != "local" or not release:
        raise RuntimeError("API requires RIDECAST_MODEL_SOURCE=local and RIDECAST_MODEL_DIR for local serving.")
    model, metadata = load_release(release)
    STATE.update(model=model, metadata=metadata, config=config)
    yield
    STATE.clear()


app = FastAPI(title="RideCast API", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok" if STATE else "starting", "model_ready": bool(STATE),
            "model_version": STATE.get("metadata", {}).get("model_version")}


@app.get("/model-info")
def model_info() -> dict:
    if not STATE:
        raise HTTPException(503, "Model is not ready.")
    return {key: STATE["metadata"].get(key) for key in
            ("model_version", "data_period", "selected_model", "demand_thresholds", "source_manifest")}


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> PredictionResponse:
    return _predict(request)


@app.post("/predict-batch", response_model=BatchResponse)
def predict_batch(request: BatchRequest) -> BatchResponse:
    return BatchResponse(predictions=[_predict(item) for item in request.instances])
