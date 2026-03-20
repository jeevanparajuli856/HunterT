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
  echo "Error: envsubst is required. Install: sudo apt-get install -y gettext-base" >&2
  exit 1
fi

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || true)}"
DEPLOYMENT_NAME="${DEPLOYMENT_NAME:-lstm-v100-transformer}"
MACHINE_TYPE="${MACHINE_TYPE:-custom-12-46080}"
GPU_TYPE="${GPU_TYPE:-nvidia-tesla-v100}"
DISK_SIZE_GB="${DISK_SIZE_GB:-200}"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "Error: PROJECT_ID is empty. Run: gcloud config set project <PROJECT_ID>" >&2
  exit 1
fi

# V100 Spot fallback zones — tried in order until one has capacity.
if [[ -n "${ZONE:-}" ]]; then
  ZONES=("${ZONE}")
else
  ZONES=(
    us-central1-b
    us-central1-a
    us-central1-c
    us-east1-c
    us-east1-d
    europe-west4-a
    europe-west4-b
    asia-east1-a
  )
fi

export DEPLOYMENT_NAME MACHINE_TYPE GPU_TYPE DISK_SIZE_GB

for ZONE in "${ZONES[@]}"; do
  echo "Trying V100 Spot in ${ZONE}..."
  export ZONE
  envsubst < "${TEMPLATE_FILE}" > "${RENDERED_FILE}"

  # Clean up any previous failed deployment
  if gcloud deployment-manager deployments describe "${DEPLOYMENT_NAME}" \
       --project "${PROJECT_ID}" &>/dev/null; then
    gcloud deployment-manager deployments delete "${DEPLOYMENT_NAME}" \
      --project "${PROJECT_ID}" --quiet 2>/dev/null || true
  fi

  if gcloud deployment-manager deployments create "${DEPLOYMENT_NAME}" \
       --config "${RENDERED_FILE}" \
       --project "${PROJECT_ID}" 2>&1 | tee /tmp/dm_create.log; then
    echo ""
    echo "VM created: V100 Spot in ${ZONE}"
    echo ""
    echo "SSH (wait ~2 min for startup script):"
    echo "  gcloud compute ssh ${DEPLOYMENT_NAME}-vm --zone ${ZONE} --project ${PROJECT_ID}"
    echo ""
    echo "Destroy when done:  ./destroy_infra.sh"
    exit 0
  fi

  if grep -qE "ZONE_RESOURCE_POOL_EXHAUSTED|QUOTA_EXCEEDED" /tmp/dm_create.log; then
    echo "  No capacity in ${ZONE}, trying next..."
    gcloud deployment-manager deployments delete "${DEPLOYMENT_NAME}" \
      --project "${PROJECT_ID}" --quiet 2>/dev/null || true
    continue
  fi

  echo "Unexpected error — see output above." >&2
  exit 1
done

echo ""
echo "Error: No V100 Spot capacity found in any zone. Try again later." >&2
exit 1
