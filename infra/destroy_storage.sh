#!/usr/bin/env bash
set -euo pipefail

if ! command -v gcloud >/dev/null 2>&1; then
  echo "Error: gcloud CLI is required." >&2
  exit 1
fi

BUCKET_NAME="${BUCKET_NAME:-}"

if [[ -z "${BUCKET_NAME}" ]]; then
  echo "Error: BUCKET_NAME is required." >&2
  echo "Example: BUCKET_NAME=dirhunter-t-lstm-artifacts ./destroy_storage.sh" >&2
  exit 1
fi

echo "Deleting bucket gs://${BUCKET_NAME} and all objects..."
gcloud storage rm --recursive "gs://${BUCKET_NAME}"
gcloud storage buckets delete "gs://${BUCKET_NAME}"

echo "Bucket deleted: gs://${BUCKET_NAME}"
