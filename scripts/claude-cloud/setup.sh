    #!/usr/bin/env bash
    set -euo pipefail

    if ! command -v gh >/dev/null 2>&1; then
  apt-get update
  apt-get install -y gh
fi

if [[ -f package-lock.json ]]; then
  npm ci --prefer-offline --no-audit --no-fund
elif [[ -f pnpm-lock.yaml ]]; then
  corepack enable
  pnpm install --frozen-lockfile
elif [[ -f yarn.lock ]]; then
  corepack enable
  yarn install --immutable
elif [[ -f package.json ]]; then
  npm install --prefer-offline --no-audit --no-fund
fi
