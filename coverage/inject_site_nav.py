#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_nav import inject_site_nav

PUB = Path(__file__).resolve().parent.parent / "publish"
# Prefer fresh fill-status fragment from incoming when present
INC = Path(__file__).resolve().parent / "incoming"
if (INC / "fill-status.html").exists():
    (PUB / "fill-status.html").write_text(
        (INC / "fill-status.html").read_text(encoding="utf-8"), encoding="utf-8"
    )

for name, active in (
    ("coverage-grid.html", "coverage-grid.html"),
    ("fill-status.html", "fill-status.html"),
    ("index.html", "index.html"),
):
    p = PUB / name
    if not p.exists():
        continue
    p.write_text(inject_site_nav(p.read_text(encoding="utf-8"), active), encoding="utf-8")
    print("nav injected", name)
