"""Local MLflow tracking helpers."""
from __future__ import annotations

from pathlib import Path


def configure_tracking(config: dict) -> None:
    import mlflow
    tracking_path = Path(config["tracking"]["sqlite_path"])
    artifact_dir = Path(config["tracking"]["artifact_dir"]).resolve()
    tracking_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(f"sqlite:///{tracking_path}")
    name = config["tracking"]["experiment_name"]
    try:
        experiment = mlflow.get_experiment_by_name(name)
        if experiment is None:
            mlflow.create_experiment(name, artifact_location=artifact_dir.as_uri())
    except Exception:
        # A fresh local database can be initialized by set_experiment below.
        pass
    mlflow.set_experiment(name)


def log_run(config: dict, name: str, params: dict, metrics: dict, model, artifacts: dict) -> str:
    import mlflow
    configure_tracking(config)
    with mlflow.start_run(run_name=name) as run:
        mlflow.log_params(params)
        mlflow.log_metrics(metrics)
        for key, value in artifacts.items():
            path = Path(value)
            if path.exists():
                mlflow.log_artifact(str(path), artifact_path=key)
        try:
            mlflow.sklearn.log_model(model, "model", input_example=[{
                "month": 9, "hour": 8, "weekday": 1, "is_holiday": False,
                "is_workingday": True, "weather_category": 1,
                "temperature_c": 22.0, "humidity_pct": 55.0, "wind_speed_kmh": 12.0,
            }])
        except Exception:
            mlflow.log_text("Model logging unavailable for this MLflow version.", "model.txt")
        return run.info.run_id
