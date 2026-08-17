#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="timesheet-f82fa"
SERVICE_NAME="timesheet"
REGION="us-east1"

gcloud config set project "$PROJECT_ID"
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com

SECRET_NAME="timesheet-admin-password"
ADMIN_EMAIL="rodrigo.bermudez@kellyeducation.com"
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
RUNTIME_SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

if ! gcloud secrets describe "$SECRET_NAME" --project "$PROJECT_ID" >/dev/null 2>&1; then
  read -r -s -p "Create the administrator password: " ADMIN_PASSWORD
  echo
  printf '%s' "$ADMIN_PASSWORD" | gcloud secrets create "$SECRET_NAME" \
    --project "$PROJECT_ID" \
    --replication-policy automatic \
    --data-file=-
  unset ADMIN_PASSWORD
fi

gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
  --project "$PROJECT_ID" \
  --member="serviceAccount:$RUNTIME_SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor" >/dev/null

gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --region "$REGION" \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars "ADMIN_EMAIL=$ADMIN_EMAIL" \
  --set-secrets "ADMIN_PASSWORD=$SECRET_NAME:latest" \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 3

gcloud run services describe "$SERVICE_NAME" \
  --region "$REGION" \
  --format='value(status.url)'
