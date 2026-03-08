#!/usr/bin/env bash
set -euo pipefail

# Poll the metadata preemption endpoint and trigger artifact sync when preempted.
POLL_SECONDS="${POLL_SECONDS:-5}"
SYNC_CMD="${SYNC_CMD:-${LTSM_SYNC_CMD:-}}"
LOG_FILE="${LOG_FILE:-./preempt_watch.log}"

METADATA_URL="http://metadata.google.internal/computeMetadata/v1/instance/preempted"

log() {
  local msg="$1"
  printf '%s %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$msg" | tee -a "$LOG_FILE"
}

log "preempt_watch started (poll=${POLL_SECONDS}s)"
if [[ -n "$SYNC_CMD" ]]; then
  log "sync command configured"
else
  log "warning: no SYNC_CMD or LTSM_SYNC_CMD configured; only logging events"
fi

while true; do
  # Endpoint returns TRUE shortly before Spot preemption shutdown.
  if status=$(curl -fsS -H "Metadata-Flavor: Google" "$METADATA_URL" 2>/dev/null); then
    if [[ "$status" == "TRUE" ]]; then
      log "preemption notice received"
      if [[ -n "$SYNC_CMD" ]]; then
        log "running emergency sync"
        if bash -lc "$SYNC_CMD"; then
          log "emergency sync completed"
        else
          log "emergency sync failed"
        fi
      fi
      log "watcher exiting after preemption signal"
      exit 0
    fi
  else
    log "metadata endpoint not reachable yet; retrying"
  fi

  sleep "$POLL_SECONDS"
done
