#!/usr/bin/env bash
# Run ON USER MAC only (machineId 6e14aeec-0070-4297-8d0e-daab4ca53214).
# Does not copy credentials. Writes raw JSON under Desktop lock folder.
set -euo pipefail
LOCK="${LOCK_DIR:-/Users/dongjoonamgung/Desktop/STORIKA-pipeline-lock}"
MONO="${MONO_DIR:-/Users/dongjoonamgung/storika-mono}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$LOCK"
# Prefer lock-folder copy of query script (durable for Mac runs)
if [[ -f "$SCRIPT_DIR/query_coverage_grid.py" ]]; then
  cp "$SCRIPT_DIR/query_coverage_grid.py" "$LOCK/query_coverage_grid.py"
fi
cd "$MONO"
set -a
# shellcheck disable=SC1091
source .env
set +a
uv run --project python/data-pipeline python "$LOCK/query_coverage_grid.py" \
  --out "$LOCK/coverage-grid-raw.json"
echo "OK: $LOCK/coverage-grid-raw.json"
