    #!/usr/bin/env bash
    set -euo pipefail

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
