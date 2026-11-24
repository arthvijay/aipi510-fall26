"""Small endpoint smoke test."""
import argparse
import json
from pathlib import Path
import requests

parser = argparse.ArgumentParser()
parser.add_argument("--base-url", required=True)
args = parser.parse_args()
base = args.base_url.rstrip("/")
request = json.loads(Path("examples/predict_request.json").read_text())
for method, path, payload in [("get", "/health", None), ("get", "/model-info", None),
                              ("post", "/predict", request), ("post", "/predict-batch", {"instances": [request]})]:
    response = getattr(requests, method)(base + path, json=payload, timeout=(5, 60))
    response.raise_for_status()
    print(path, response.status_code, response.json())
