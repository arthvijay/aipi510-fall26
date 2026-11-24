# Deployment

Training, MLflow, tests, and Docker builds are local. `scripts/deploy_gcp.sh`
builds only the `api` target for linux/amd64 and deploys one request-billed
Cloud Run service in `us-central1` with 0.5 vCPU, 512 MiB, concurrency 1, and
0–1 instances. The bucket remains private; only the prediction service is
public. Run `gcloud` and `docker` only after local authentication and Docker
integration are available. Cloud Build is a fallback, not the default.

To clean up only RideCast resources, inspect first with `gcloud run services
list`, `gcloud artifacts docker images list`, and `gcloud storage ls`; do not
delete shared resources automatically.
