# Submission checklist

| Requirement | Status | Evidence |
|---|---|---|
| UCI real dataset and target | Implemented | [data card](data_card.md) |
| GCS cleaned data and ingestion | Verified | Private bucket, GCS manifest, and local GCS-backed pipeline run |
| Reproducible pipeline/config | Verified locally | `config.yaml`, package CLI |
| MLflow experiments | Three local runs verified | [tracking.py](../src/ridecast/tracking.py), `workdir/tracking/` |
| Docker training/serving | Verified locally | Full-project and slim linux/amd64 images built; slim image pushed |
| JSON API | Implemented locally | [api.py](../src/ridecast/api.py) |
| Cloud API and public UI | Verified public | [Cloud Run and Streamlit deployment](deployment.md) |
| Tests and CI | Implemented | `tests/`, `.github/workflows/ci.yml` |
| Solo PR evidence | Verified | [PR #5](https://github.com/arthvijay/aipi510-fall26/pull/5), [PR #6](https://github.com/arthvijay/aipi510-fall26/pull/6), [collaboration](collaboration.md) |
