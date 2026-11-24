# Deployment

Training, MLflow, tests, and Docker builds are local. `scripts/deploy_gcp.sh`
builds only the `api` target for linux/amd64 and deploys one request-billed
Cloud Run service in `us-central1` with 0.5 vCPU, 512 MiB, concurrency 1, and
0–1 instances. The bucket remains private; only the prediction service is
public. Run `gcloud` and `docker` only after local authentication and Docker
integration are available. Cloud Build is a fallback, not the default.

## Current deployment

Project `ridecast-515702` (`121192188296`) is active with billing enabled.
The cleaned dataset is in private bucket
`gs://ridecast-data-121192188296/data/clean/v1/3b29612513f88169a95f7f8dd7de4cc2083eb9ada481ce9f60db82c25396ba4f/`
and the GCS-backed pipeline selected `rf_standard-7312d6a8de51`. The model
release is in `gs://ridecast-data-121192188296/models/rf_standard-7312d6a8de51/`.
The tested Docker image is
`us-central1-docker.pkg.dev/ridecast-515702/ridecast/ridecast-api:ed32c203-gcs`.

Cloud Run service: `https://ridecast-api-oidv2f4u5a-uc.a.run.app`.
The deployed revision is gen1, 0.5 vCPU, 512 MiB, concurrency 1, minimum 0,
maximum 1, and uses the dedicated `ridecast-runtime` service account with
`roles/storage.objectViewer` on the private bucket.

The project effective `iam.allowedPolicyMemberDomains` policy restricts IAM
members to organization domain `C00wrsdu1`, so `allUsers` invocation is
currently blocked. This requires an authorized organization-policy administrator
to allow public IAM members or set an exception. The service is deployed and
ready, but anonymous endpoint verification cannot pass until that policy is
changed.

To clean up only RideCast resources, inspect first with `gcloud run services
list`, `gcloud artifacts docker images list`, and `gcloud storage ls`; do not
delete shared resources automatically.
