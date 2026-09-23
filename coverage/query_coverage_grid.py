#!/usr/bin/env python3
"""Query Spanner for completeness coverage grid. MUST run on user's Mac from storika-mono root.

Usage (on Mac):
  cd /Users/dongjoonamgung/storika-mono && set -a && source .env && set +a \\
    && uv run --project python/data-pipeline python \\
       /Users/dongjoonamgung/Desktop/STORIKA-pipeline-lock/query_coverage_grid.py

Writes coverage-grid-raw.json next to this script (or --out).
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from google.cloud import spanner

SQL = """
WITH p AS (
  SELECT ProfileId, COUNT(*) n, MAX(PostedAt) last,
         COUNTIF(Embedding IS NOT NULL) emb,
         COUNTIF(ARRAY_LENGTH(Categories)>0) lab
  FROM CreatorPost GROUP BY 1
), cc AS (
  SELECT c.Platform,
    IFNULL(c.PrimaryCategory,'(분류없음)') cat,
    CASE WHEN c.Country='US' OR c.ResidenceCountry='US' THEN 'US'
         WHEN c.Country='KR' OR c.ResidenceCountry='KR' THEN 'KR'
         WHEN c.Country IS NULL AND c.ResidenceCountry IS NULL THEN '(국가없음)'
         ELSE '기타' END co,
    CASE WHEN c.FollowersCount<10000 THEN '1_under10k'
         WHEN c.FollowersCount<50000 THEN '2_10-50k'
         WHEN c.FollowersCount<200000 THEN '3_50-200k'
         ELSE '4_200k+' END band,
    EXISTS(SELECT 1 FROM UNNEST(c.PrimarySubcategories) s WHERE LOWER(s) LIKE '%skin%') skin
  FROM Creator c JOIN p USING(ProfileId)
  WHERE c.Platform IN ('instagram','tiktok')
    AND p.n>=10
    AND p.last>=TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
    AND p.emb>=10 AND p.lab>=5
)
SELECT Platform, cat, co, band, COUNT(*) n, COUNTIF(skin) skin_n
FROM cc GROUP BY 1,2,3,4 ORDER BY 1,2,3,4
"""

PROJECT = "storika-455708"
INSTANCE = "prediction-engine"
DATABASE = "knowledge-graph"
KST = ZoneInfo("Asia/Seoul")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out",
        default=str(Path(__file__).resolve().parent / "coverage-grid-raw.json"),
        help="Output JSON path",
    )
    args = ap.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Prefer relocating to repo root if GOOGLE_APPLICATION_CREDENTIALS is relative
    cred = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    if cred and not os.path.isabs(cred):
        mono = Path.home() / "storika-mono"
        if (mono / cred).exists():
            os.chdir(mono)
            print(f"chdir {mono} for relative credentials", flush=True)

    client = spanner.Client(project=PROJECT)
    db = client.instance(INSTANCE).database(DATABASE)
    rows: list[list] = []
    print("executing coverage SQL (timeout=1800s)...", flush=True)
    with db.snapshot() as snap:
        result = snap.execute_sql(SQL, timeout=1800)
        for r in result:
            platform, cat, co, band, n, skin_n = r
            rows.append([platform, cat, co, band, int(n), int(skin_n)])

    stamp = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    payload = {
        "queried_at_kst": stamp,
        "definition": "card+posts>=10+MAX(PostedAt)>=today-90d+emb>=10+lab>=5",
        "rows": rows,
    }
    # Also support bare list for renderers that expect [[...], ...]
    # Hand-off format: bare list. Keep meta alongside via sidecar? Prefer bare list
    # per handoff, plus write meta file.
    out.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    meta = out.with_name(out.stem + "-meta.json")
    meta.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out} rows={len(rows)} queried_at={stamp}", flush=True)
    print(f"wrote {meta}", flush=True)


if __name__ == "__main__":
    main()
