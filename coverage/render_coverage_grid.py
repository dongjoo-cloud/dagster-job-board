#!/usr/bin/env python3
"""Render coverage-grid.html from raw JSON (+ optional prev for per-cell deltas).

Usage:
  python3 render_coverage_grid.py \\
    --raw coverage-grid-raw.json \\
    --prev coverage-grid-prev.json \\
    --out coverage-grid.html \\
    [--stamp "2026-09-23 14:30 KST"]
"""
from __future__ import annotations

import argparse
import html
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parent))
from site_nav import site_nav_html
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
BANDS = ["2_10-50k", "3_50-200k", "4_200k+"]  # exclude 1_under10k
CO_GROUPS = [("US", ["US"]), ("KR", ["KR"]), ("기타·미기재", ["기타", "(국가없음)"])]
PLATFORMS = [("instagram", "Instagram"), ("tiktok", "TikTok")]


def load_rows(path: Path) -> list[list]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data["rows"]
    return data


def index_rows(rows: list[list]) -> dict[tuple, tuple[int, int]]:
    """key -> (n, skin_n). Merges 기타+(국가없음)."""
    acc: dict[tuple, list[int]] = defaultdict(lambda: [0, 0])
    for platform, cat, co, band, n, skin_n in rows:
        if co in ("기타", "(국가없음)"):
            co_key = "기타·미기재"
        else:
            co_key = co
        key = (platform, cat, co_key, band)
        acc[key][0] += int(n)
        acc[key][1] += int(skin_n)
    return {k: (v[0], v[1]) for k, v in acc.items()}


def color_class(n: int) -> str:
    if n <= 0:
        return "c0"
    if n < 50:
        return "c1"
    if n < 300:
        return "c2"
    if n < 900:
        return "c3"
    return "c4"


def fmt_num(n: int) -> str:
    return f"{n:,}"


def fmt_cell(n: int, prev: int | None, show_delta: bool) -> str:
    """Absolute + optional delta. Omit delta when 0 or no baseline."""
    base = fmt_num(n)
    if not show_delta or prev is None:
        return base
    d = n - prev
    if d == 0:
        return base
    # use proper minus sign − for negative
    if d > 0:
        return f"{base} (+{d:,})"
    return f"{base} (−{abs(d):,})"


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def platform_cats(idx: dict, platform: str) -> list[str]:
    totals: dict[str, int] = defaultdict(int)
    for (plat, cat, co, band), (n, _) in idx.items():
        if plat != platform:
            continue
        if band == "1_under10k":
            continue
        totals[cat] += n
    return [c for c, _ in sorted(totals.items(), key=lambda x: (-x[1], x[0]))]


def cell_n(idx: dict, platform: str, cat: str, co_label: str, band: str) -> int:
    return idx.get((platform, cat, co_label, band), (0, 0))[0]


def skin_n(idx: dict, platform: str, co_label: str, band: str) -> int:
    total = 0
    for (plat, cat, co, b), (_, sn) in idx.items():
        if plat == platform and co == co_label and b == band:
            total += sn
    return total


def render_platform_table(
    platform: str,
    title: str,
    idx: dict,
    prev_idx: dict | None,
    show_delta: bool,
) -> str:
    cats = platform_cats(idx, platform)
    # also include cats that only exist in prev? skip — current snapshot defines rows
    head = (
        '<table><tr><th rowspan=2>카테고리</th>'
        '<th colspan=3 class="cg">미국</th>'
        '<th colspan=3 class="cg">한국</th>'
        '<th colspan=3 class="cg">기타·미기재</th>'
        '<th rowspan=2>합계</th></tr><tr>'
        + "".join('<th class="bh">1만~5만</th><th class="bh">5만~20만</th><th class="bh">20만+</th>' for _ in range(3))
        + "</tr>"
    )
    body = []
    for cat in cats:
        cells = [f'<td class="cat">{esc(cat)}</td>']
        row_tot = 0
        for co_label, _ in CO_GROUPS:
            for band in BANDS:
                n = cell_n(idx, platform, cat, co_label, band)
                row_tot += n
                prev = None
                if prev_idx is not None:
                    prev = cell_n(prev_idx, platform, cat, co_label, band)
                cls = color_class(n)
                cells.append(f'<td class="{cls}">{fmt_cell(n, prev, show_delta)}</td>')
        cells.append(f'<td class="tot">{fmt_num(row_tot)}</td>')
        body.append("<tr>" + "".join(cells) + "</tr>")
    return f"<h2>{esc(title)}</h2><div class=card>{head}{''.join(body)}</table></div>"


def render_skin_table(idx: dict, prev_idx: dict | None, show_delta: bool) -> str:
    rows_spec = [
        ("instagram", "US", "Instagram · 미국"),
        ("instagram", "KR", "Instagram · 한국"),
        ("tiktok", "US", "TikTok · 미국"),
        ("tiktok", "KR", "TikTok · 한국"),
    ]
    head = (
        '<table><tr><th>플랫폼 · 국가</th>'
        '<th class="bh">1만~5만</th><th class="bh">5만~20만</th><th class="bh">20만+</th></tr>'
    )
    body = []
    for plat, co, label in rows_spec:
        cells = [f'<td class="cat">{esc(label)}</td>']
        for band in BANDS:
            n = skin_n(idx, plat, co, band)
            prev = skin_n(prev_idx, plat, co, band) if prev_idx is not None else None
            cls = color_class(n)
            cells.append(f'<td class="{cls}">{fmt_cell(n, prev, show_delta)}</td>')
        body.append("<tr>" + "".join(cells) + "</tr>")
    note = (
        '<div class=note>카드 세부 분류에 skin이 들어간 사람만 셈. TikTok이 낮은 것은 분류 잡이 '
        "어제 착지한 라벨을 아직 카드에 올리지 않았기 때문(06:30·18:30에만 실행). "
        "갱신은 taxonomy_sync 이후(07:00 또는 19:00 KST 이후)가 맞다.</div>"
    )
    return (
        "<h2>스킨케어만 따로 (설화수 같은 브리프가 실제로 보는 칸)</h2>"
        f"<div class=card>{head}{''.join(body)}</table>{note}</div>"
    )


def total_excluding_under10k(idx: dict) -> tuple[int, int, int]:
    ig = tt = 0
    for (plat, cat, co, band), (n, _) in idx.items():
        if band == "1_under10k":
            continue
        if plat == "instagram":
            ig += n
        elif plat == "tiktok":
            tt += n
    return ig + tt, ig, tt


def render(raw: Path, prev: Path | None, out: Path, stamp: str | None) -> dict:
    rows = load_rows(raw)
    idx = index_rows(rows)
    prev_idx = None
    show_delta = False
    if prev and prev.exists():
        prev_idx = index_rows(load_rows(prev))
        show_delta = True

    if not stamp:
        stamp = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")

    total, ig, tt = total_excluding_under10k(idx)
    sub = (
        "완전체 = 카드 + 게시물 10개↑ + 최근 90일 게시 + 벡터 10개↑ + 라벨 5개↑ · "
        f"실측 {stamp} · Spanner 직접 조회 · 총 {total:,}명 (1만 미만 제외"
        f" · IG {ig:,} / TT {tt:,})"
    )
    if show_delta:
        sub += " · 칸 옆 숫자는 직전 스냅샷 대비 증감"

    css = """
:root{--paper:#f3f5f8;--card:#fff;--ink:#1a1f2b;--mute:#5f6b7a;--line:#dfe3e9;--copper:#c2652a}
*{box-sizing:border-box} body{margin:0;background:var(--paper);color:var(--ink);font:14px/1.6 "IBM Plex Sans KR",system-ui,sans-serif}
.wrap{max-width:1240px;margin:0 auto;padding:24px 20px 60px}
.eyebrow{font:600 11px/1 "IBM Plex Mono",monospace;letter-spacing:.14em;text-transform:uppercase;color:var(--copper);margin-bottom:6px}
.hdr-top{display:flex;flex-wrap:wrap;align-items:baseline;gap:10px 18px;justify-content:space-between}h1{font-size:23px;margin:0} .gen{color:var(--mute);font-size:.85rem} .sub{color:var(--mute);font-size:12.5px;margin:8px 0 16px}
h2{font-size:15px;margin:26px 0 10px;padding-left:10px;border-left:3px solid var(--copper)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;overflow-x:auto}
table{border-collapse:collapse;font-size:12.5px;width:100%}
th,td{padding:5px 7px;border:1px solid var(--line);text-align:center;font-variant-numeric:tabular-nums;font-family:"IBM Plex Mono",monospace}
th{background:#eef1f5;color:var(--mute);font:600 11px "IBM Plex Sans KR",sans-serif}
th.cg{background:#e4e9f0;color:#1a1f2b} th.bh{font-size:10.5px}
td.cat{text-align:left;font:500 12px "IBM Plex Sans KR",sans-serif;white-space:nowrap}
td.tot{background:#f4f6f9;font-weight:700}
.c0{background:#fbe9e7;color:#b3392e;font-weight:700} .c1{background:#fdeee0;color:#b3622e}
.c2{background:#fdf6e3;color:#8a6d1f} .c3{background:#eef7f0;color:#2e8b57} .c4{background:#dcf0e4;color:#1f6b41;font-weight:600}
.note{font-size:12.5px;color:var(--mute);margin-top:10px}
.legend span{display:inline-block;padding:2px 9px;border-radius:6px;margin-right:6px;font:600 11.5px "IBM Plex Mono",monospace}
""".strip()

    parts = [
        "<!doctype html><html lang=ko><head><meta charset=utf-8>",
        "<title>완전체 분포</title>",
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;700&family=IBM+Plex+Mono:wght@400;600&display=swap">',
        f"<style>\n{css}\n</style></head><body>",
        site_nav_html("coverage-grid.html"),
        "<div class=wrap>",
        '<div class=eyebrow>Storika · Discovery · 완전체 분포</div>',
        '<div class=hdr-top>',
        "<h1>완전체가 실제로 어디에 있나</h1>",
        f'<div class=gen>생성 {esc(stamp)}</div>',
        '</div>',
        f'<div class=sub>{esc(sub)}</div>',
        '<div class="note legend">칸당 제안 목표 <b>300명</b> · '
        '<span class=c0>0</span><span class=c1>~49</span><span class=c2>50~299</span>'
        '<span class=c3>300~899</span><span class=c4>900+</span></div>',
    ]
    for plat, title in PLATFORMS:
        parts.append(render_platform_table(plat, title, idx, prev_idx, show_delta))
    parts.append(render_skin_table(idx, prev_idx, show_delta))
    parts.append(
        "<h2>읽는 법</h2><div class=card><div class=note>"
        "총량은 목표 3만에 가깝지만 <b>칸으로 쪼개면 빈 곳이 드러난다</b>. "
        "결손을 총량이 아니라 이 격자의 빈 칸으로 계산하면, 배관이 무엇이 부족한지 스스로 알고 그 칸만 채우러 간다.<br><br>"
        "칸당 목표 300명은 제안값이다. 근거: 2026-09-16 실측에서 후보 45명을 심층 판단해 강한 적합이 5명(11%)이었으므로 "
        "브리프 하나에 10명을 주려면 후보 100명 안팎이 필요하고, 여유를 3배로 잡았다.<br><br>"
        "선행 조건 두 가지: TikTok 카드의 국가 공백(약 1만 명)과 세부 분류 미반영. 이 둘을 채우기 전에는 격자가 실제보다 나쁘게 보인다."
        "</div></div>"
    )
    parts.append("</div></body></html>")
    out.write_text("".join(parts), encoding="utf-8")
    return {
        "stamp": stamp,
        "total": total,
        "ig": ig,
        "tt": tt,
        "show_delta": show_delta,
        "out": str(out),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--prev", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--stamp", default="")
    args = ap.parse_args()
    info = render(
        Path(args.raw),
        Path(args.prev) if args.prev else None,
        Path(args.out),
        args.stamp or None,
    )
    print(json.dumps(info, ensure_ascii=False))


if __name__ == "__main__":
    main()
