#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_FILE="${SCRIPT_DIR}/deployment-template.yaml"
RENDERED_FILE="${SCRIPT_DIR}/deployment.yaml"

if ! command -v gcloud >/dev/null 2>&1; then
  echo "Error: gcloud CLI is required." >&2
  exit 1
fi

if ! command -v envsubst >/dev/null 2>&1; then
  echo "Error: envsubst is required. Install gettext-base (Ubuntu: sudo apt-get install -y gettext-base)." >&2
  exit 1
fi

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || true)}"
DEPLOYMENT_NAME="${DEPLOYMENT_NAME:-ltsm-t4}"
ZONE="${ZONE:-us-central1-a}"
MACHINE_TYPE="${MACHINE_TYPE:-n1-standard-8}"
DISK_SIZE_GB="${DISK_SIZE_GB:-200}"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "Error: PROJECT_ID is empty. Set it or run: gcloud config set project <PROJECT_ID>" >&2
  exit 1
fi

export DEPLOYMENT_NAME ZONE MACHINE_TYPE DISK_SIZE_GB
envsubst < "${TEMPLATE_FILE}" > "${RENDERED_FILE}"

echo "Creating deployment ${DEPLOYMENT_NAME} in project ${PROJECT_ID}..."
gcloud deployment-manager deployments create "${DEPLOYMENT_NAME}" \
  --config "${RENDERED_FILE}" \
  --project "${PROJECT_ID}"

echo ""
echo "Infra created. Useful commands:"
echo "gcloud compute ssh ${DEPLOYMENT_NAME}-vm --zone ${ZONE} --project ${PROJECT_ID}"
echo "./destroy_infra.sh"
