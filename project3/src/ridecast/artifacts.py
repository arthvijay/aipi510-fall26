"""Trusted local model release loading and integrity checks."""
from __future__ import annotations

import json
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
