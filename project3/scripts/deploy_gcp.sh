#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT3_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${PROJECT3_DIR}/.." && pwd)"
PROJECT="${RIDECAST_GCP_PROJECT:-ridecast-515702}"
REGION="us-central1"
REPO="ridecast"
SERVICE="ridecast-api"
RUNTIME_SA="${RUNTIME_SA:-ridecast-runtime}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/${REPO}/${SERVICE}:$(git -C "$REPO_ROOT" rev-parse --short HEAD)"

gcloud projects describe "$PROJECT" --format='value(projectNumber)' | grep -Fx '121192188296'
gcloud services enable \
  run.googleapis.com artifactregistry.googleapis.com storage.googleapis.com \
  iam.googleapis.com iamcredentials.googleapis.com \
  --project="$PROJECT"
gcloud artifacts repositories describe "$REPO" --location="$REGION" --project="$PROJECT" >/dev/null 2>&1 ||
  gcloud artifacts repositories create "$REPO" --repository-format=docker \
    --location="$REGION" --project="$PROJECT" --quiet
gcloud iam service-accounts describe "${RUNTIME_SA}@${PROJECT}.iam.gserviceaccount.com" \
  --project="$PROJECT" >/dev/null 2>&1 ||
  gcloud iam service-accounts create "$RUNTIME_SA" \
    --project="$PROJECT" --display-name="RideCast runtime"
gcloud storage buckets add-iam-policy-binding "gs://ridecast-data-121192188296" \
  --member="serviceAccount:${RUNTIME_SA}@${PROJECT}.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer" --project="$PROJECT"

docker build --platform linux/amd64 --target api -t "$IMAGE" "$PROJECT3_DIR"
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet --project="$PROJECT"
docker push "$IMAGE"
gcloud run deploy "$SERVICE" --project="$PROJECT" --region="$REGION" --image="$IMAGE" \
  --service-account="${RUNTIME_SA}@${PROJECT}.iam.gserviceaccount.com" \
  --platform=managed --allow-unauthenticated --cpu=0.5 --memory=512Mi \
  --concurrency=1 --min-instances=0 --max-instances=1 --execution-environment=gen1 \
  --set-env-vars="RIDECAST_MODEL_SOURCE=gcs,RIDECAST_MODEL_MANIFEST_URI=${RIDECAST_MODEL_MANIFEST_URI}"
