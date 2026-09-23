#!/usr/bin/env bash
# Box-side: after Mac raw/html land under /workspace/.../coverage/incoming/,
# render coverage-grid and stage files into publish/ for gh deploy.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COV="$ROOT/coverage"
PUB="$ROOT/publish"
IN="$COV/incoming"
mkdir -p "$IN" "$COV"

STAMP="${STAMP:-}" # optional override

if [[ -f "$IN/coverage-grid-raw.json" ]]; then
  # Rotate: current raw -> prev (if exists and different)
  if [[ -f "$COV/coverage-grid-raw.json" ]]; then
    cp "$COV/coverage-grid-raw.json" "$COV/coverage-grid-prev.json"
  fi
  cp "$IN/coverage-grid-raw.json" "$COV/coverage-grid-raw.json"
fi

ARGS=(--raw "$COV/coverage-grid-raw.json" --out "$PUB/coverage-grid.html")
if [[ -f "$COV/coverage-grid-prev.json" ]]; then
  ARGS+=(--prev "$COV/coverage-grid-prev.json")
fi
if [[ -n "$STAMP" ]]; then
  ARGS+=(--stamp "$STAMP")
fi
python3 "$COV/render_coverage_grid.py" "${ARGS[@]}"

# Also keep JSON SoT in publish for next agents / transparency
cp "$COV/coverage-grid-raw.json" "$PUB/coverage-grid-raw.json"
cp "$COV/coverage-grid-prev.json" "$PUB/coverage-grid-prev.json" 2>/dev/null || true

if [[ -f "$IN/fill-status.html" ]]; then
  cp "$IN/fill-status.html" "$PUB/fill-status.html"
fi
if [[ -f "$IN/fill-status-history.json" ]]; then
  cp "$IN/fill-status-history.json" "$PUB/fill-status-history.json"
fi

echo "Staged under $PUB:"
ls -la "$PUB"/coverage-grid.html "$PUB"/fill-status.html 2>/dev/null || true
