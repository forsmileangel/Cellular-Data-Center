"""Crop TS 38.521-1 Figure captions from the V18 PDF into PNG.

Figures are vector drawings, not embedded images. Re-run after replacing
the PDF. Needs PyMuPDF: python -m pip install pymupdf
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "3GPP SPEC" / "ts_13852101v180500p.pdf"
OUT = ROOT / "uxm_report" / "assets" / "spec_figures"

WANT = {
    "6.3.3.2.3-1",
    "6.3.3.4.3-1",
    "6.3.3.6.3-1",
    "6.3.3.6.3-2",
    "6.3.3.6.3-3",
    "6.3.3.6.3-4",
    "6.3.3.6.3-5",
    "6.3.4.3.4.2-1",
    "6.3.4.3.4.2-2",
    "6.3.4.3.4.2-3",
    "6.3.4.3.4.2-4",
    "6.3.4.3.4.2-5",
    "6.3.4.4.4.2-1",
    "6.4.2.1a.4.2-1",
    "6.4.2.1a.4.2-2",
    "6.4.2.4.3-1",
    "6.4.2.4.5-1",
    "6.4.2.5.3-1",
    "6.4.2.5.5-1",
    "6.5.0-1",
}

# TDD ramping figures sit as three disconnected drawings; force a wide clip.
FORCE_CLIP = {
    "6.3.4.3.4.2-3": (70, 88, 520, 472),
    "6.3.4.3.4.2-4": (70, 88, 520, 472),
}


def _cluster(rects, cap_y0, prev_y1, gap=36):
    cand = [r for r in rects if r.y1 <= cap_y0 + 6 and r.y0 >= prev_y1 - 4]
    if not cand:
        return None
    seed = [r for r in cand if r.y1 >= cap_y0 - 55] or [
        min(cand, key=lambda r: cap_y0 - r.y1)
    ]
    used = list(seed)
    changed = True
    while changed:
        changed = False
        u = used[0]
        for r in used[1:]:
            u |= r
        for r in cand:
            if any(r == x for x in used):
                continue
            if r.y1 >= u.y0 - gap and r.y0 <= u.y1 + gap:
                used.append(r)
                changed = True
    u = used[0]
    for r in used[1:]:
        u |= r
    return u


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(PDF)
    by_page: dict[int, list] = defaultdict(list)
    for i in range(700, 1160):
        page = doc[i]
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                s = "".join(sp.get("text", "") for sp in line.get("spans", [])).strip()
                if not s.startswith("Figure "):
                    continue
                rest = s[len("Figure ") :]
                fid = rest.split()[0].rstrip(":")
                title = rest[len(fid) :].lstrip(": ").strip()
                by_page[i].append((fid, title, pymupdf.Rect(line["bbox"])))
    for i in by_page:
        by_page[i].sort(key=lambda t: t[2].y0)

    manifest = []
    seen: set[str] = set()
    for i, items in sorted(by_page.items()):
        page = doc[i]
        rects = []
        for d in page.get_drawings():
            r = d.get("rect")
            if r and r.get_area() >= 30:
                rects.append(r)
        for info in page.get_image_info(xrefs=True):
            r = pymupdf.Rect(info["bbox"])
            if r.get_area() >= 200:
                rects.append(r)
        for idx, (fid, title, cap) in enumerate(items):
            if fid not in WANT or fid in seen:
                continue
            seen.add(fid)
            if fid in FORCE_CLIP:
                clip = pymupdf.Rect(*FORCE_CLIP[fid])
            else:
                prev_y1 = items[idx - 1][2].y1 + 6 if idx else 48
                union = _cluster(rects, cap.y0, prev_y1)
                if union:
                    clip = pymupdf.Rect(
                        max(20, union.x0 - 18),
                        max(prev_y1, union.y0 - 16),
                        min(page.rect.x1 - 20, union.x1 + 18),
                        min(cap.y0 - 1, union.y1 + 12),
                    )
                else:
                    clip = pymupdf.Rect(
                        36, max(prev_y1, cap.y0 - 200), page.rect.x1 - 36, cap.y0 - 2
                    )
            pix = page.get_pixmap(matrix=pymupdf.Matrix(2.2, 2.2), clip=clip, alpha=False)
            dest = OUT / f"{fid}.png"
            pix.save(dest)
            manifest.append(
                {
                    "fid": fid,
                    "title": title,
                    "printed": i,
                    "pdf_page": i + 1,
                    "file": dest.name,
                    "w": pix.width,
                    "h": pix.height,
                }
            )
            print(fid, dest.name, pix.width, pix.height)
    missing = sorted(WANT - seen)
    if missing:
        raise SystemExit(f"missing figures: {missing}")
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print("wrote", len(manifest), "figures")


if __name__ == "__main__":
    main()
