#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${ROOT_DIR}/.env"
  set +a
fi

IMAGE_REF="${1:-}"
if [[ -z "${IMAGE_REF}" ]]; then
  echo "usage: scripts/build-image.sh <image-ref> [--platform linux/arm64|linux/amd64|linux/amd64,linux/arm64] [--push]" >&2
  exit 1
fi

shift

DEFAULT_PLATFORM="linux/arm64"
PUBLISH_PLATFORM="linux/amd64,linux/arm64"
PLATFORM="${DEFAULT_PLATFORM}"
PUSH_FLAG=""
PLATFORM_WAS_SET=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --platform)
      PLATFORM="${2:?missing value for --platform}"
      PLATFORM_WAS_SET=1
      shift 2
      ;;
    --push)
      PUSH_FLAG="--push"
      shift
      ;;
    *)
      echo "unknown option: $1" >&2
      exit 1
      ;;
  esac
done

: "${RUNNER_VERSION:=2.333.0}"

if [[ -n "${PUSH_FLAG}" && "${PLATFORM_WAS_SET}" -eq 0 ]]; then
  PLATFORM="${PUBLISH_PLATFORM}"
fi

cd "${ROOT_DIR}"

docker buildx build \
  --platform "${PLATFORM}" \
  --build-arg "RUNNER_VERSION=${RUNNER_VERSION}" \
  -f docker/Dockerfile \
  -t "${IMAGE_REF}" \
  ${PUSH_FLAG:+"${PUSH_FLAG}"} \
  .
