#!/usr/bin/env bash
set -euo pipefail

if ! command -v gcloud >/dev/null 2>&1; then
  echo "Error: gcloud CLI is required." >&2
  exit 1
fi

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || true)}"
DEPLOYMENT_NAME="${DEPLOYMENT_NAME:-lstm-t4}"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "Error: PROJECT_ID is empty. Set it or run: gcloud config set project <PROJECT_ID>" >&2
  exit 1
fi

echo "Deleting deployment ${DEPLOYMENT_NAME} in project ${PROJECT_ID}..."
gcloud deployment-manager deployments delete "${DEPLOYMENT_NAME}" \
  --project "${PROJECT_ID}" \
  --quiet

echo "Infra destroyed."
