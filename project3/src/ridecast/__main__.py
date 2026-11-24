"""RideCast command line interface."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

from .config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(prog="ridecast")
    parser.add_argument("command", choices=["prepare-data", "upload-data", "run-pipeline",
                                            "publish-model", "serve", "ui", "backup-tracking"])
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--data-source", choices=["gcs", "local"], default="gcs")
    parser.add_argument("--source-zip-path")
    parser.add_argument("--force-download", action="store_true")
    parser.add_argument("--release-dir")
    args = parser.parse_args()
    config = load_config(args.config)
    from .data import clean_dataset, upload_data
    if args.command == "prepare-data":
        _, manifest = clean_dataset(config, args.source_zip_path)
        print(json.dumps(manifest, indent=2))
    elif args.command == "upload-data":
        manifest_path = Path(config["data"]["workdir"]) / "data_manifest.json"
        print(upload_data(config, json.loads(manifest_path.read_text())))
    elif args.command == "run-pipeline":
        from .pipeline import run_pipeline
        print(json.dumps(run_pipeline(config, args.data_source, args.force_download), indent=2, default=str))
    elif args.command == "publish-model":
        if not args.release_dir:
            parser.error("--release-dir is required for publish-model")
        print("Model release ready for immutable publication:", Path(args.release_dir).resolve())
    elif args.command == "serve":
        import uvicorn
        uvicorn.run("ridecast.api:app", host=config["api"]["host"],
                    port=int(os.getenv("PORT", config["api"]["default_port"])), workers=1)
    elif args.command == "ui":
        subprocess.run(["python", "-m", "streamlit", "run", "frontend/streamlit_app.py"], check=True)
    elif args.command == "backup-tracking":
        target = Path(config["tracking"]["artifact_dir"]).parent.with_suffix(".tar.gz")
        shutil.make_archive(str(target.with_suffix("")), "gztar", Path(config["tracking"]["artifact_dir"]).parent)
        print(target)


if __name__ == "__main__":
    main()
