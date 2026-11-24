# Demo

Open the deployed Streamlit app, make one prediction, then use Compare
scenarios to request two 24-hour profiles. Open `/docs` for interactive API
requests and run `python scripts/smoke_test.py --base-url <api-origin>`.
The local MLflow comparison is opened with `mlflow ui --backend-store-uri
sqlite:///workdir/tracking/mlflow.db --default-artifact-root
workdir/tracking/artifacts`. Point the audience to the GCS manifest and the
actual feature-branch PR recorded in `docs/collaboration.md`.
