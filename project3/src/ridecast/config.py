"""Validated configuration and environment handling."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when configuration cannot safely be used."""


def load_config(path: str | Path = "config.yaml") -> dict[str, Any]:
    root = Path(path).resolve().parent
    with Path(path).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ConfigError("Configuration must be a YAML mapping.")
    config["_root"] = str(root)
    split = config["split"]
    dates = [split["train_end_exclusive"], split["validation_end_exclusive"], split["test_end_exclusive"]]
    if dates != sorted(dates):
        raise ConfigError("Chronological split boundaries must be increasing.")
    if config["deployment"]["project_id"] != os.getenv("RIDECAST_GCP_PROJECT", config["deployment"]["project_id"]):
        raise ConfigError("RIDECAST_GCP_PROJECT conflicts with the configured project.")
    for section in ("tracking", "artifacts"):
        for key in ("sqlite_path", "artifact_dir") if section == "tracking" else ("local_dir",):
            if key in config[section]:
                config[section][key] = str((root / config[section][key]).resolve())
    return config


def config_hash(config: dict[str, Any]) -> str:
    clean = {k: v for k, v in config.items() if k != "_root"}
    return hashlib.sha256(json.dumps(clean, sort_keys=True).encode()).hexdigest()


def env_or_config(config: dict[str, Any], env_name: str, default: str | None = None) -> str | None:
    return os.getenv(env_name, default)

