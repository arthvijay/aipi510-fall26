# Submission checklist

| Requirement | Status | Evidence |
|---|---|---|
| UCI real dataset and target | Implemented | [data card](data_card.md) |
| GCS cleaned data and ingestion | Pending cloud auth | [data.py](../src/ridecast/data.py) |
| Reproducible pipeline/config | Implemented | `config.yaml`, package CLI |
| MLflow experiments | Pending real data run | [tracking.py](../src/ridecast/tracking.py) |
| Docker training/serving | Pending Docker integration | `Dockerfile` |
| JSON API | Implemented locally | [api.py](../src/ridecast/api.py) |
| Cloud API and public UI | Pending cloud/hosting access | [deployment](deployment.md) |
| Tests and CI | Implemented | `tests/`, `.github/workflows/ci.yml` |
| Solo PR evidence | Pending branch/PR | [collaboration](collaboration.md) |
