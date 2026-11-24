# RideCast

RideCast is a reproducible bike-share demand planning dashboard. It estimates
historical, systemwide hourly Capital Bikeshare rentals under supplied
calendar and weather conditions. It does not estimate current inventory,
station placement, unique riders, or causal effects.

## Status and architecture

The implementation is deployed to Cloud Run and has real GCS ingestion evidence.
Training and MLflow remain local. Cleaned data and the immutable model release
are stored in private regional GCS. The deployed API is at
`https://ridecast-api-oidv2f4u5a-uc.a.run.app`, subject to the project
organization policy described in [deployment.md](docs/deployment.md). The UI is
HTTP-only and intended for Streamlit Community Cloud.

## Quick start

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python -m ridecast prepare-data --config config.yaml
python -m ridecast run-pipeline --config config.yaml --data-source local
RIDECAST_MODEL_DIR=workdir/models/<observed-version> python -m ridecast serve --config config.yaml
```

The official source is the [UCI Bike Sharing dataset](https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset).
Use `RIDECAST_GCS_BUCKET` and `RIDECAST_DATA_MANIFEST_URI` for authenticated
upload and GCS-ingestion runs. Open MLflow with:

```bash
mlflow ui --backend-store-uri sqlite:///workdir/tracking/mlflow.db --default-artifact-root workdir/tracking/artifacts
```

The verified local run selected `rf_standard` release
`rf_standard-7312d6a8de51`. Its held-out test MAE is 88.2332 rentals/hour,
RMSE 128.4624, and R² 0.5939; the mean baseline test MAE is 156.5652.

## API and UI

```bash
curl -X POST http://localhost:8080/predict -H 'content-type: application/json' \
  --data @examples/predict_request.json
python scripts/smoke_test.py --base-url http://localhost:8080
python -m streamlit run frontend/streamlit_app.py
```

The API validates strict inputs, computes `is_workingday`, loads one trusted
pipeline at startup, and supports `/health`, `/model-info`, `/predict`,
`/predict-batch`, and `/docs`.

## Verification and deployment

Run `ruff check src tests frontend` and `pytest`. Build locally with
`docker build --target project -t ridecast:local .`; build the deployed image
with `docker build --platform linux/amd64 --target api -t <image> .`. Follow
[deployment.md](docs/deployment.md), [demo.md](docs/demo.md), and the
[submission checklist](docs/submission_checklist.md). See
[model limitations](docs/model_card.md), [data details](docs/data_card.md),
and [solo workflow](docs/collaboration.md).
