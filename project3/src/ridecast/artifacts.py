"""Trusted local model release loading and integrity checks."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import joblib


def load_release(path: str | Path) -> tuple[object, dict]:
    release = Path(path).resolve()
    manifest = json.loads((release / "release_manifest.json").read_text(encoding="utf-8"))
    model_path = release / "model.joblib"
    if not model_path.is_file():
        raise RuntimeError(f"Missing model artifact in {release}")
    model = joblib.load(model_path)
    metadata = json.loads((release / "metadata.json").read_text(encoding="utf-8"))
    return model, {**metadata, "manifest": manifest}


def load_gcs_release(manifest_uri: str) -> tuple[object, dict]:
    if not manifest_uri.startswith("gs://"):
        raise RuntimeError("RIDECAST_MODEL_MANIFEST_URI must be a gs:// manifest URI.")

    from google.cloud import storage

    _, rest = manifest_uri.split("gs://", 1)
    bucket_name, blob_name = rest.split("/", 1)
    bucket = storage.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT", "ridecast-515702")).bucket(bucket_name)
    manifest = json.loads(bucket.blob(blob_name).download_as_bytes())
    prefix = blob_name.rsplit("/", 1)[0]
    release = Path(tempfile.mkdtemp(prefix="ridecast-model-"))
    (release / "release_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    for filename in manifest["files"]:
        if filename not in ("model.joblib", "metadata.json", "metrics.json"):
            raise RuntimeError(f"Untrusted model release filename: {filename}")
        bucket.blob(f"{prefix}/{filename}").download_to_filename(str(release / filename))
    if "model.joblib" not in manifest["files"]:
        raise RuntimeError("Model release manifest does not include model.joblib.")
    return load_release(release)
