#!/usr/bin/env bash
set -euo pipefail

if ! command -v gcloud >/dev/null 2>&1; then
  echo "Error: gcloud CLI is required." >&2
  exit 1
fi

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || true)}"
BUCKET_NAME="${BUCKET_NAME:-}"
BUCKET_LOCATION="${BUCKET_LOCATION:-US}"
STORAGE_CLASS="${STORAGE_CLASS:-STANDARD}"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "Error: PROJECT_ID is empty. Set it or run: gcloud config set project <PROJECT_ID>" >&2
  exit 1
fi

if [[ -z "${BUCKET_NAME}" ]]; then
  echo "Error: BUCKET_NAME is required (globally unique)." >&2
  echo "Example: BUCKET_NAME=dirhunter-t-lstm-artifacts ./create_storage.sh" >&2
  exit 1
fi

echo "Creating bucket gs://${BUCKET_NAME} in project ${PROJECT_ID}..."
gcloud storage buckets create "gs://${BUCKET_NAME}" \
  --project "${PROJECT_ID}" \
  --location "${BUCKET_LOCATION}" \
  --default-storage-class "${STORAGE_CLASS}" \
  --uniform-bucket-level-access

echo "Bucket created: gs://${BUCKET_NAME}"
echo "Use this sync command in training:"
echo "--sync-cmd \"gsutil -m rsync -r ./saved_models gs://${BUCKET_NAME}/lstm/saved_models && gsutil -m rsync -r ./results gs://${BUCKET_NAME}/lstm/results\""
