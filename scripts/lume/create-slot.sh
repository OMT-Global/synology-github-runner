#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib.sh"

slot=""
config_path="$(default_lume_config_path)"
env_path="$(default_lume_env_path)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --slot)
      slot="$2"
      shift 2
      ;;
    --config)
      config_path="$2"
      shift 2
      ;;
    --env)
      env_path="$2"
      shift 2
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "${slot}" ]]; then
  echo "--slot is required" >&2
  exit 1
fi

load_slot_env "${slot}" "${config_path}" "${env_path}"
mkdir -p "${LUME_SLOT_DIR}" "$(dirname "${LUME_SLOT_LOG_FILE}")"

if vm_exists; then
  log "slot VM ${LUME_VM_NAME} already exists"
  exit 0
fi

log "cloning ${LUME_VM_BASE_NAME} -> ${LUME_VM_NAME}"
lume clone "${LUME_VM_BASE_NAME}" "${LUME_VM_NAME}" $(clone_args) >/dev/null
lume set "${LUME_VM_NAME}" --cpu "${LUME_VM_CPU}" --memory "${LUME_VM_MEMORY}" --disk-size "${LUME_VM_DISK_SIZE}" $(storage_args) >/dev/null

log "starting ${LUME_VM_NAME}"
nohup lume run "${LUME_VM_NAME}" --no-display --network "${LUME_VM_NETWORK}" $(storage_args) >"${LUME_SLOT_VM_LOG_FILE}" 2>&1 &
echo $! > "${LUME_SLOT_VM_PID_FILE}"

wait_for_ssh
log "slot ${LUME_VM_NAME} is reachable over SSH"
