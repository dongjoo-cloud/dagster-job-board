# Coverage grid + fill-status — weekday refresh

SoT for viewing: GitHub Pages on `dongjoo-cloud/dagster-job-board` (`main` `/`).
Do **not** treat Mac Desktop HTML as the product. Temp Mac outputs under
`~/Desktop/STORIKA-pipeline-lock/` are OK for Spanner runs.

Cadence (parent routine): weekdays **09:00 & 15:00 KST** with the job board.

## Completeness definition (rolling 90d)

Creator is complete when all hold:
1. `Creator` card exists
2. `CreatorPost` rows ≥ 10
3. `MAX(PostedAt) ≥ today − 90d`
4. posts with `Embedding IS NOT NULL` ≥ 10
5. posts with `ARRAY_LENGTH(Categories) > 0` ≥ 5

Table rules: exclude band `1_under10k`; merge `기타` + `(국가없음)` → **기타·미기재**.
Color bands: 0=c0, 1–49=c1, 50–299=c2, 300–899=c3, 900+=c4; target **300/cell**.
Subtitle must say **최근 90일 게시** (never "6월 이후 게시").
Per-cell deltas vs previous snapshot: `1,473 (+12)` / `0 (−3)`; omit when delta=0.

## Machines

| Step | Where |
|------|--------|
| Spanner query (`query_coverage_grid.py`, `fill-status.py`) | **User Mac only** · machineId `6e14aeec-0070-4297-8d0e-daab4ca53214` |
| Render HTML + `gh` deploy | Box (`/workspace/dagster-job-board`) |

Creds: Mac `/Users/dongjoonamgung/storika-mono/google_credentials.json` via `.env`.
**Never** paste credentials into chat or copy them to the box.

## A. Mac — coverage Spanner query (~1–3 min, timeout 1800)

```bash
# Prefer script already in lock folder, or CopyToBox from box:
#   /workspace/dagster-job-board/coverage/query_coverage_grid.py
#   → /Users/dongjoonamgung/Desktop/STORIKA-pipeline-lock/query_coverage_grid.py

cd /Users/dongjoonamgung/storika-mono && set -a && source .env && set +a && \
  uv run --project python/data-pipeline python \
    /Users/dongjoonamgung/Desktop/STORIKA-pipeline-lock/query_coverage_grid.py \
    --out /Users/dongjoonamgung/Desktop/STORIKA-pipeline-lock/coverage-grid-raw.json
```

Or: `bash /workspace/dagster-job-board/coverage/run_mac_query.sh` **after** that script is on the Mac (or run the copy inside `run_mac_query.sh` from a box→Mac CopyToBox of `coverage/`).

Then **CopyFromBox** (Mac → box):
- `.../STORIKA-pipeline-lock/coverage-grid-raw.json` → `/workspace/dagster-job-board/coverage/incoming/coverage-grid-raw.json`

## B. Mac — fill-status (~few min; Spanner + optional MART/Linear)

```bash
cd /Users/dongjoonamgung/storika-mono && set -a && source .env && set +a && \
  uv run --project python/data-pipeline python \
    /Users/dongjoonamgung/Desktop/STORIKA-pipeline-lock/fill-status.py
```

If Linear/MART fail, still accept Spanner-funnel HTML.

CopyFromBox:
- `fill-status.html` → `/workspace/dagster-job-board/coverage/incoming/fill-status.html`
- `fill-status-history.json` (if updated) → same `incoming/`

## C. Box — render + stage + deploy

```bash
bash /workspace/dagster-job-board/coverage/refresh_and_stage.sh
# optional: STAMP="2026-09-23 15:05 KST" bash .../refresh_and_stage.sh

cd /workspace/dagster-job-board/publish
git add coverage-grid.html coverage-grid-raw.json coverage-grid-prev.json \
        fill-status.html fill-status-history.json 2>/dev/null || true
# also keep scripts/docs in sync if changed:
#   from repo root workspace copy coverage/*.py and COVERAGE_REFRESH.md into publish if desired
git status -sb
git commit -m "$(cat <<'EOF'
refresh coverage-grid + fill-status (KST weekday board)

EOF
)"
git push origin main
```

Live URLs (expect HTTP 200, subtitle 최근 90일, fresh stamp):
- https://dongjoo-cloud.github.io/dagster-job-board/coverage-grid.html
- https://dongjoo-cloud.github.io/dagster-job-board/fill-status.html

## D. When to ping the user

Ping (Slack/user) only when:
1. Any cell flips **0 ↔ nonzero**
2. Any cell **|delta| ≥ 100**
3. Spanner / fill-status / deploy **failure**

Otherwise silent; report paths/KPIs to parent only. Do **not** SendToUser / Slack / change Dagster toggles from the refresh agent unless the routine says so.

## E. Taxonomy timing note

`PrimarySubcategories` rollup runs taxonomy_sync **06:30 / 18:30 KST**. Prefer measuring skincare cells after **07:00 or 19:00 KST**.

## First-publish baseline

`coverage-grid-raw.json` / `coverage-grid-prev.json` seeded from 2026-09-23 **09:16 KST** Spanner snapshot (rolling 90d). Next successful Mac query should show per-cell deltas vs that prev.
