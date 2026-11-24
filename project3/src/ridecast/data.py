"""Download, clean, validate, and publish the UCI hourly dataset."""
from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

import pandas as pd

from .features import source_to_canonical

REQUIRED = {"dteday", "hr", "holiday", "weathersit", "temp", "hum", "windspeed", "cnt"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_source(config: dict, source_zip_path: str | None = None) -> tuple[bytes, str]:
    if source_zip_path:
        payload = Path(source_zip_path).read_bytes()
    else:
        try:
            with urlopen(config["data"]["source_zip"], timeout=60) as response:
                payload = response.read()
        except Exception as exc:
            raise RuntimeError(f"Unable to download UCI archive: {exc}") from exc
    return payload, hashlib.sha256(payload).hexdigest()


def clean_dataset(config: dict, source_zip_path: str | None = None) -> tuple[Path, dict]:
    root = Path(config["_root"])
    workdir = root / config["data"]["workdir"]
    workdir.mkdir(parents=True, exist_ok=True)
    payload, zip_hash = download_source(config, source_zip_path)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = set(archive.namelist())
        member = config["data"]["source_member"]
        if member not in names or "Readme.txt" not in names:
            raise ValueError("Archive must contain hour.csv and Readme.txt.")
        csv_bytes = archive.read(member)
        (workdir / "Readme.txt").write_bytes(archive.read("Readme.txt"))
    raw = pd.read_csv(io.BytesIO(csv_bytes))
    missing = REQUIRED - set(raw.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")
    raw["timestamp"] = pd.to_datetime(raw["dteday"], format="%Y-%m-%d") + pd.to_timedelta(raw["hr"], unit="h")
    if not raw["timestamp"].is_monotonic_increasing:
        raw = raw.sort_values("timestamp", kind="mergesort")
    duplicates = int(raw.duplicated().sum())
    raw = raw.drop_duplicates()
    conflicting = raw.groupby("timestamp")["cnt"].nunique()
    if int((conflicting > 1).sum()):
        raise ValueError("Rows sharing a timestamp disagree on cnt.")
    if not raw["hr"].between(0, 23).all() or (raw["cnt"] < 0).any():
        raise ValueError("Invalid hour or negative target encountered.")
    if not raw["weathersit"].isin([1, 2, 3, 4]).all():
        raise ValueError("Unknown weather category encountered.")
    converted = raw.apply(lambda row: source_to_canonical(row["temp"], row["hum"], row["windspeed"]), axis=1)
    raw[["temperature_c", "humidity_pct", "wind_speed_kmh"]] = pd.DataFrame(converted.tolist(), index=raw.index)
    raw["month"] = raw["timestamp"].dt.month
    raw["hour"] = raw["hr"].astype(int)
    raw["weekday"] = raw["timestamp"].dt.weekday
    raw["is_holiday"] = raw["holiday"].astype(bool)
    raw["is_workingday"] = (raw["weekday"] < 5) & ~raw["is_holiday"]
    raw["weather_category"] = raw["weathersit"].astype(int)
    columns = ["timestamp", "month", "hour", "weekday", "is_holiday", "is_workingday",
               "weather_category", "temperature_c", "humidity_pct", "wind_speed_kmh", "cnt"]
    cleaned = raw[columns].sort_values("timestamp", kind="mergesort")
    output = workdir / "cleaned.csv"
    cleaned.to_csv(output, index=False)
    quality = {
        "row_count": len(cleaned), "columns": columns, "duplicate_rows_removed": duplicates,
        "date_min": cleaned["timestamp"].min().isoformat(), "date_max": cleaned["timestamp"].max().isoformat(),
        "target_min": int(cleaned["cnt"].min()), "target_max": int(cleaned["cnt"].max()),
        "missing_values": cleaned.isna().sum().to_dict(), "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source_zip_sha256": zip_hash, "source_csv_sha256": hashlib.sha256(csv_bytes).hexdigest(),
    }
    (workdir / "data_quality.json").write_text(json.dumps(quality, indent=2), encoding="utf-8")
    manifest = {**quality, "schema_version": config["data"]["schema_version"],
                "source_url": config["data"]["source_zip"], "cleaned_csv_sha256": _sha256(output),
                "cleaned_csv": str(output)}
    manifest_path = workdir / "data_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (root / "docs").mkdir(exist_ok=True)
    return output, manifest


def upload_data(config: dict, manifest: dict) -> str:
    from google.cloud import storage
    bucket_name = __import__("os").environ.get("RIDECAST_GCS_BUCKET")
    if not bucket_name:
        raise RuntimeError("Set RIDECAST_GCS_BUCKET before upload-data.")
    client = storage.Client(project=config["deployment"]["project_id"])
    bucket = client.bucket(bucket_name)
    digest = manifest["cleaned_csv_sha256"]
    prefix = f'{config["data"]["cleaned_prefix"]}/v1/{digest}'
    for filename in ("cleaned_csv", "data_quality.json"):
        source = Path(manifest["cleaned_csv"]).parent / (Path(filename).name if filename != "cleaned_csv" else "cleaned.csv")
        blob = bucket.blob(f"{prefix}/{source.name}")
        if blob.exists():
            raise RuntimeError(f"Refusing to overwrite published object {blob.name}.")
        blob.upload_from_filename(str(source))
    csv_blob = bucket.blob(f"{prefix}/cleaned.csv")
    csv_blob.reload()
    manifest["gcs_csv_uri"] = f"gs://{bucket_name}/{prefix}/cleaned.csv"
    manifest["gcs_generation"] = str(csv_blob.generation)
    manifest["gcs_quality_uri"] = f"gs://{bucket_name}/{prefix}/data_quality.json"
    manifest_blob = bucket.blob(f"{prefix}/data_manifest.json")
    manifest_blob.upload_from_string(json.dumps(manifest, indent=2), content_type="application/json")
    return f"gs://{bucket_name}/{prefix}/data_manifest.json"


def load_ingested_data(config: dict, source: str = "gcs", force_download: bool = False) -> tuple[pd.DataFrame, dict]:
    if source == "local":
        manifest_path = Path(config["data"]["workdir"]) / "data_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return pd.read_csv(manifest["cleaned_csv"], parse_dates=["timestamp"]), manifest
    from google.cloud import storage
    uri = __import__("os").environ.get("RIDECAST_DATA_MANIFEST_URI")
    if not uri or not uri.startswith("gs://"):
        raise RuntimeError("Set RIDECAST_DATA_MANIFEST_URI to a gs:// manifest for GCS ingestion.")
    _, rest = uri.split("gs://", 1)
    bucket_name, blob_name = rest.split("/", 1)
    blob = storage.Client(project=config["deployment"]["project_id"]).bucket(bucket_name).blob(blob_name)
    manifest = json.loads(blob.download_as_bytes())
    cache = Path(config["data"]["workdir"]) / "gcs_cleaned.csv"
    if force_download or not cache.exists():
        storage.Client(project=config["deployment"]["project_id"]).bucket(bucket_name).blob(
            manifest["gcs_csv_uri"].split("/", 3)[-1]
        ).download_to_filename(str(cache))
    if _sha256(cache) != manifest["cleaned_csv_sha256"]:
        raise RuntimeError("Downloaded GCS dataset hash does not match its manifest.")
    return pd.read_csv(cache, parse_dates=["timestamp"]), manifest
