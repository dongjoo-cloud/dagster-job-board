"""Shared top nav for job board / coverage grid / fill-status Pages."""
from __future__ import annotations

import re

NAV_ITEMS = (
    ("index.html", "Dagster 현황"),
    ("coverage-grid.html", "완전체 분포"),
    ("fill-status.html", "완전체 총원"),
)

ACTIVE = "#2563eb"
INACTIVE = "#c2652a"

# Matches our shared nav (classed or the older unclassed twin on index).
_NAV_RE = re.compile(
    r'<div(?:\s+class="site-nav")?\s+style="font:500 12\.5px/1\.4 system-ui,sans-serif;'
    r'padding:8px 16px;background:#fff;border-bottom:1px solid #e2e6eb;'
    r'display:flex;gap:14px;align-items:center">.*?</div>\s*',
    re.S,
)
_OLD_COPPER_NAV_RE = re.compile(
    r'<div class="nav"><a href="index\.html">← 잡 보드</a>.*?</div>\s*',
    re.S,
)


def site_nav_html(active: str) -> str:
    links = []
    for href, label in NAV_ITEMS:
        color = ACTIVE if href == active else INACTIVE
        links.append(
            f'<a href="{href}" style="color:{color};text-decoration:none">{label}</a>'
        )
    return (
        '<div class="site-nav" style="font:500 12.5px/1.4 system-ui,sans-serif;'
        "padding:8px 16px;background:#fff;border-bottom:1px solid #e2e6eb;"
        "display:flex;gap:14px;align-items:center;"
        "position:sticky;top:0;z-index:100\">"
        + "".join(links)
        + "</div>"
    )


def _strip_navs(html: str) -> str:
    html = _NAV_RE.sub("", html)
    html = _OLD_COPPER_NAV_RE.sub("", html)
    # leftover site-nav blocks
    html = re.sub(r'<div class="site-nav"[^>]*>.*?</div>\s*', "", html, flags=re.S)
    return html


def _ensure_document(html: str, title: str) -> str:
    """Wrap fragment pages (fill-status) into a minimal HTML document."""
    low = html.lower()
    if "<html" in low and "<body" in low:
        return html
    # Extract existing title if present
    m = re.search(r"<title>(.*?)</title>", html, flags=re.S | re.I)
    if m:
        title = re.sub(r"<.*?>", "", m.group(1)).strip() or title
        # keep styles/links; drop duplicate title later by wrapping body content only
    # If fragment starts with <title>..., treat whole thing as head+body content
    if re.match(r"\s*<title", html, flags=re.I):
        # split head-ish vs rest: title+link+style until first content div/h1
        head_end = re.search(r"</style>\s*", html, flags=re.I)
        if head_end:
            head = html[: head_end.end()]
            body = html[head_end.end() :]
        else:
            head = f"<title>{title}</title>"
            body = html
        return (
            "<!doctype html><html lang=ko><head><meta charset=utf-8>"
            f"{head}</head><body>{body}</body></html>"
        )
    return (
        "<!doctype html><html lang=ko><head><meta charset=utf-8>"
        f"<title>{title}</title></head><body>{html}</body></html>"
    )



_STAMP_RE = re.compile(
    r"실측\s*(?:<span[^>]*>)?([0-9]{4}-[0-9]{2}-[0-9]{2}\s+[0-9]{2}:[0-9]{2}\s*KST)",
    re.I,
)


def _extract_stamp(html: str) -> str | None:
    m = _STAMP_RE.search(html)
    return m.group(1).strip() if m else None


def ensure_refresh_stamp(html: str, active: str) -> str:
    """Put job-board-style top-right '생성 … KST' on coverage / fill-status."""
    if active == "index.html":
        return html
    stamp = _extract_stamp(html)
    if not stamp:
        return html
    gen = f'<div class="gen">생성 {stamp}</div>'
    if ".hdr-top{" not in html and ".hdr-top {" not in html:
        css = (
            ".hdr-top{display:flex;flex-wrap:wrap;align-items:baseline;"
            "gap:10px 18px;justify-content:space-between}"
            ".gen{color:var(--mute,var(--muted,#5f6b7a));font-size:.85rem}"
        )
        html = re.sub(r"(</style>)", css + r"\1", html, count=1, flags=re.I)
    # drop prior gen blocks (avoid dup on reinject)
    html = re.sub(r'<div class="gen">.*?</div>\s*', "", html, flags=re.S)
    html = re.sub(r"<div class=gen>.*?</div>\s*", "", html, flags=re.S)
    if re.search(r'<div class="hdr-top">|<div class=hdr-top>', html):
        html = re.sub(
            r'(<div class="?hdr-top"?>\s*<h1[^>]*>.*?</h1>)',
            r"\1" + gen,
            html,
            count=1,
            flags=re.S,
        )
        return html

    def wrap_h1(m: re.Match[str]) -> str:
        return f'<div class="hdr-top">{m.group(0)}{gen}</div>'

    return re.sub(r"<h1[^>]*>.*?</h1>", wrap_h1, html, count=1, flags=re.S)



def _rename_page_copy(html: str, active: str) -> str:
    """Keep human-facing titles aligned with NAV_ITEMS after regenerations."""
    if active == "coverage-grid.html":
        html = re.sub(r"<title>.*?</title>", "<title>완전체 분포</title>", html, count=1, flags=re.S | re.I)
        html = re.sub(
            r'(<div class=eyebrow>)[^<]*(</div>)',
            r"\1Storika · Discovery · 완전체 분포\2",
            html,
            count=1,
        )
        html = re.sub(
            r'(<div class="eyebrow">)[^<]*(</div>)',
            r"\1Storika · Discovery · 완전체 분포\2",
            html,
            count=1,
        )
    elif active == "fill-status.html":
        html = re.sub(r"<title>.*?</title>", "<title>완전체 총원</title>", html, count=1, flags=re.S | re.I)
        html = re.sub(
            r"(<h1[^>]*>).*?(</h1>)",
            r"\1완전체 총원\2",
            html,
            count=1,
            flags=re.S,
        )
        html = re.sub(
            r'(<div class=eyebrow>)[^<]*(</div>)',
            r"\1Storika · Discovery · 완전체 총원\2",
            html,
            count=1,
        )
        html = re.sub(
            r'(<div class="eyebrow">)[^<]*(</div>)',
            r"\1Storika · Discovery · 완전체 총원\2",
            html,
            count=1,
        )
    return html


def inject_site_nav(html: str, active: str, title: str | None = None) -> str:
    titles = {
        "index.html": "Dagster 현황",
        "coverage-grid.html": "완전체 분포",
        "fill-status.html": "완전체 총원",
    }
    html = _strip_navs(html)
    html = _ensure_document(html, title or titles.get(active, "Storika"))
    nav = site_nav_html(active)
    m = re.search(r"(<body[^>]*>)", html, flags=re.I)
    if not m:
        return f"<!doctype html><html lang=ko><body>{nav}{html}</body></html>"
    i = m.end()
    html = html[:i] + nav + html[i:]
    html = ensure_refresh_stamp(html, active)
    return _rename_page_copy(html, active)
