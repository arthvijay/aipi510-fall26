"""Chronological training, evaluation, reports, and release export."""
from __future__ import annotations

import json
import platform
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from .config import config_hash
from .data import load_ingested_data
from .features import FEATURE_COLUMNS
from .tracking import log_run


def split_data(df: pd.DataFrame, config: dict) -> dict[str, pd.DataFrame]:
    boundaries = [pd.Timestamp(config["split"][key]) for key in
                  ("train_end_exclusive", "validation_end_exclusive", "test_end_exclusive")]
    masks = [
        df["timestamp"] < boundaries[0],
        (df["timestamp"] >= boundaries[0]) & (df["timestamp"] < boundaries[1]),
        (df["timestamp"] >= boundaries[1]) & (df["timestamp"] < boundaries[2]),
    ]
    result = dict(zip(("train", "validation", "test"), (df.loc[m] for m in masks)))
    if any(part.empty for part in result.values()):
        raise ValueError("Chronological partitions must all be nonempty.")
    if sum(map(len, result.values())) != len(df):
        raise ValueError("Partitions do not cover the dataset.")
    return result


def make_pipeline(config: dict, estimator) -> Pipeline:
    categorical = config["features"]["categorical"]
    numeric = config["features"]["numeric"]
    transform = ColumnTransformer([
        ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median"))]), numeric),
        ("categorical", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]), categorical),
    ])
    return Pipeline([("preprocess", transform), ("model", estimator)])


def metrics(actual, predicted) -> dict[str, float]:
    return {"mae": float(mean_absolute_error(actual, predicted)),
            "rmse": float(mean_squared_error(actual, predicted) ** 0.5),
            "r2": float(r2_score(actual, predicted))}


def run_pipeline(config: dict, source: str = "gcs", force_download: bool = False) -> dict:
    start = time.monotonic()
    df, manifest = load_ingested_data(config, source, force_download)
    parts = split_data(df, config)
    x_train, y_train = parts["train"][FEATURE_COLUMNS], parts["train"]["cnt"]
    candidates = [("baseline", DummyRegressor(strategy="mean"))]
    for spec in config["model"]["candidates"]:
        candidates.append((spec["name"], RandomForestRegressor(
            n_estimators=spec["n_estimators"], max_depth=spec["max_depth"],
            min_samples_leaf=spec["min_samples_leaf"], random_state=config["project"]["random_seed"],
            n_jobs=config["model"]["n_jobs"])))
    results, fitted = {}, {}
    for name, estimator in candidates:
        model = make_pipeline(config, estimator)
        model.fit(x_train, y_train)
        validation = metrics(parts["validation"]["cnt"], model.predict(parts["validation"][FEATURE_COLUMNS]))
        results[name] = {"validation": validation}
        fitted[name] = model
    selected = min((n for n in fitted if n != "baseline"), key=lambda n: (results[n]["validation"]["mae"], n))
    for name, model in fitted.items():
        results[name]["test"] = metrics(parts["test"]["cnt"], model.predict(parts["test"][FEATURE_COLUMNS]))
        try:
            results[name]["run_id"] = log_run(config, name, {"random_seed": config["project"]["random_seed"]},
                                              results[name]["validation"], model, {})
        except ImportError:
            results[name]["run_id"] = None
    chosen = fitted[selected]
    test_pred = chosen.predict(parts["test"][FEATURE_COLUMNS])
    model_version = f"{selected}-{config_hash(config)[:12]}"
    release_dir = Path(config["artifacts"]["local_dir"]) / model_version
    release_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(chosen, release_dir / "model.joblib")
    thresholds = np.quantile(y_train, config["evaluation"]["demand_quantiles"]).tolist()
    metadata = {"model_version": model_version, "selected_model": selected,
                "data_period": f"{df.timestamp.min().date()} to {df.timestamp.max().date()}",
                "feature_columns": FEATURE_COLUMNS, "demand_thresholds": thresholds,
                "config_hash": config_hash(config), "python": sys.version, "platform": platform.platform(),
                "source_manifest": manifest}
    (release_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")
    (release_dir / "metrics.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    reports = Path(config["_root"], "reports")
    reports.mkdir(exist_ok=True)
    pd.DataFrame({"timestamp": parts["test"]["timestamp"], "actual_count": parts["test"]["cnt"],
                  "prediction": test_pred}).to_csv(reports / "test_predictions.csv", index=False)
    (reports / "metrics.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (release_dir / "release_manifest.json").write_text(json.dumps({
        "schema_version": "1", "model_version": model_version,
        "files": ["model.joblib", "metadata.json", "metrics.json"],
    }, indent=2), encoding="utf-8")
    return {"selected": selected, "model_version": model_version, "release_dir": str(release_dir),
            "metrics": results, "duration_seconds": time.monotonic() - start}
