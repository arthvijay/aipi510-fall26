"""HTTP-only RideCast Streamlit interface."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import requests
import streamlit as st


def api_origin() -> str:
    value = os.getenv("RIDECAST_API_URL")
    if not value:
        try:
            value = st.secrets.get("RIDECAST_API_URL")
        except Exception:
            value = None
    if not value:
        path = Path(__file__).with_name("public_config.json")
        if path.exists():
            value = json.loads(path.read_text(encoding="utf-8")).get("api_url")
    if not value or not value.startswith("https://") and not value.startswith("http://"):
        raise RuntimeError("Set RIDECAST_API_URL or frontend/public_config.json to the API HTTPS origin.")
    return value.rstrip("/")


def call_api(path: str, payload: dict | None = None) -> dict:
    try:
        response = requests.post(api_origin() + path, json=payload, timeout=(5, 60)) if payload else requests.get(
            api_origin() + path, timeout=(5, 60))
        response.raise_for_status()
        return response.json()
    except requests.Timeout as exc:
        raise RuntimeError("The API may be starting from a cold start; retry in a moment.") from exc
    except requests.RequestException as exc:
        raise RuntimeError(f"RideCast API request failed: {exc}") from exc


st.set_page_config(page_title="RideCast", page_icon="🚲", layout="wide")
st.title("RideCast")
st.subheader("Explore hourly bike-share demand under different conditions.")
st.info("Historical Capital Bikeshare model, trained on 2011–2012 data.")
one, compare, about = st.tabs(["Predict one hour", "Compare scenarios", "About the model"])
with one:
    with st.form("single"):
        month = st.selectbox("Month", list(range(1, 13)), index=8)
        weekday = st.selectbox("Day of week", list(range(7)), format_func=lambda x: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][x])
        hour = st.slider("Hour", 0, 23, 8)
        holiday = st.checkbox("Holiday")
        weather = st.selectbox("Weather category", [1, 2, 3, 4])
        temp = st.number_input("Temperature (°C)", -8.0, 39.0, 22.0)
        humidity = st.number_input("Humidity (%)", 0.0, 100.0, 55.0)
        wind = st.number_input("Wind speed (km/h)", 0.0, 67.0, 12.0)
        submitted = st.form_submit_button("Predict")
    if submitted:
        try:
            st.session_state["prediction"] = call_api("/predict", {"month": month, "hour": hour, "weekday": weekday, "is_holiday": holiday, "weather_category": weather, "temperature_c": temp, "humidity_pct": humidity, "wind_speed_kmh": wind})
        except RuntimeError as exc:
            st.error(str(exc))
    if "prediction" in st.session_state:
        result = st.session_state["prediction"]
        st.metric("Estimated rentals per hour", f"{result['predicted_rentals_per_hour']:.0f}")
        st.write("Demand level:", result["demand_level"])
        if result["warnings"]:
            st.warning(" ".join(result["warnings"]))
        st.caption("This is systemwide historical demand, not current inventory or station allocation.")
with compare:
    st.write("Profiles hold supplied weather constant while varying the hour.")
    with st.form("comparison"):
        a = st.number_input("Scenario A temperature (°C)", value=22.0)
        b = st.number_input("Scenario B temperature (°C)", value=12.0)
        go = st.form_submit_button("Compare")
    if go:
        base = {"month": 9, "weekday": 1, "is_holiday": False, "weather_category": 1, "humidity_pct": 55.0, "wind_speed_kmh": 12.0}
        instances = [{**base, "hour": h, "temperature_c": t} for t in (a, b) for h in range(24)]
        try:
            result = call_api("/predict-batch", {"instances": instances})
            frame = pd.DataFrame([{"hour": h, "scenario": label, "prediction": p["predicted_rentals_per_hour"]} for label, offset in (("A", 0), ("B", 24)) for h, p in enumerate(result["predictions"][offset:offset+24])])
            st.session_state["comparison"] = frame
        except RuntimeError as exc:
            st.error(str(exc))
    if "comparison" in st.session_state:
        frame = st.session_state["comparison"]
        st.line_chart(frame.pivot(index="hour", columns="scenario", values="prediction"))
        st.download_button("Download predictions", frame.to_csv(index=False), "ridecast_predictions.csv", "text/csv")
with about:
    try:
        st.json(call_api("/model-info"))
    except RuntimeError as exc:
        st.error(str(exc))
