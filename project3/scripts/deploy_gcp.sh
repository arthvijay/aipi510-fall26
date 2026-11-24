#!/usr/bin/env bash
set -euo pipefail
PROJECT="${RIDECAST_GCP_PROJECT:-ridecast-515702}"
REGION="us-central1"
REPO="ridecast"
SERVICE="ridecast-api"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/${REPO}/${SERVICE}:$(git rev-parse --short HEAD)"
gcloud projects describe "$PROJECT" --format='value(projectNumber)' | grep -Fx '121192188296'
gcloud artifacts repositories describe "$REPO" --location="$REGION" --project="$PROJECT" >/dev/null
docker build --platform linux/amd64 --target api -t "$IMAGE" .
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
docker push "$IMAGE"
gcloud run deploy "$SERVICE" --project="$PROJECT" --region="$REGION" --image="$IMAGE" \
  --platform=managed --allow-unauthenticated --cpu=0.5 --memory=512Mi \
  --concurrency=1 --min-instances=0 --max-instances=1 --execution-environment=gen1 \
  --set-env-vars="RIDECAST_MODEL_SOURCE=gcs,RIDECAST_MODEL_MANIFEST_URI=${RIDECAST_MODEL_MANIFEST_URI}"
