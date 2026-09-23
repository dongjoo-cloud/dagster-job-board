#!/usr/bin/env bash
# Run existing fill-status.py ON USER MAC.
set -euo pipefail
LOCK="${LOCK_DIR:-/Users/dongjoonamgung/Desktop/STORIKA-pipeline-lock}"
MONO="${MONO_DIR:-/Users/dongjoonamgung/storika-mono}"
cd "$MONO"
set -a
# shellcheck disable=SC1091
source .env
set +a
uv run --project python/data-pipeline python "$LOCK/fill-status.py"
echo "OK: expect $LOCK/fill-status.html (+ history if updated)"
