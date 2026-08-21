"""Small SVG charts vs 3GPP limits. Computed only when the 圖 tab is opened."""

from __future__ import annotations

from collections import defaultdict
from html import escape

from .analysis import limit_float, to_float

# First-wave plots: one Item, numeric limits, maps to 38.521-1.
CHARTS = [
    {
        "id": "621-power",
        "title": "6.2.1 UE Maximum Output Power",
        "spec": "TS 38.521-1 6.2.1",
        "test_like": "6.2.1%",
        "item": "NR Power",
        "ylabel": "NR Power (dBm)",
    },
    {
        "id": "6421-evm",
        "title": "6.4.2.1 PUSCH EVM",
        "spec": "TS 38.521-1 6.4.2.1",
        "test_like": "%PUSCH Error Vector Magnitude%",
        "item": "PUSCH EVM",
        "ylabel": "PUSCH EVM (%)",
    },
    {
        "id": "641-ferr",
        "title": "6.4.1 Frequency error",
        "spec": "TS 38.521-1 6.4.1",
        "test_like": "6.4.1%",
        "item": "Freq Error in Hz",
        "ylabel": "Freq Error (Hz)",
    },
    {
        "id": "65241-aclr-l",
        "title": "6.5.2.4.1 NR ACLR Offset L",
        "spec": "TS 38.521-1 6.5.2.4.1",
        "test_like": "%6.5.2.4.1%",
        "item": "NR Offset L",
        "ylabel": "NR ACLR Offset L (dB)",
    },
    {
        "id": "65241-aclr-u",
        "title": "6.5.2.4.1 NR ACLR Offset U",
        "spec": "TS 38.521-1 6.5.2.4.1",
        "test_like": "%6.5.2.4.1%",
        "item": "NR Offset U",
        "ylabel": "NR ACLR Offset U (dB)",
    },
]

RANGE_X = {"Low": 0, "Mid": 1, "High": 2}


def assign_lmh(rows: list[dict]) -> list[dict]:
    """Low/Mid/High by ARFCN order inside each session (TX detail uses UL ARFCN)."""
    by_sess: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        by_sess[int(row["session_id"])].append(row)
    out = []
    for group in by_sess.values():
        if all(row.get("lmh") in RANGE_X for row in group):
            out.extend(dict(row) for row in group)
            continue
        arfcns = []
        for row in group:
            n = to_float(row.get("arfcn"))
            if n is not None and n not in arfcns:
                arfcns.append(n)
        arfcns.sort()
        labels = {1: ["Mid"], 2: ["Low", "High"], 3: ["Low", "Mid", "High"]}
        names = labels.get(len(arfcns), [])
        mapping = {arfcns[i]: names[i] for i in range(len(names))} if names else {}
        for row in group:
            n = to_float(row.get("arfcn"))
            row = dict(row)
            row["lmh"] = mapping.get(n, "")
            out.append(row)
    return out


def _scale(values: list[float], y0: float, y1: float, lo: float, hi: float) -> list[float]:
    if hi <= lo:
        hi = lo + 1
    return [y1 - (v - lo) / (hi - lo) * (y1 - y0) for v in values]


def svg_lmh(rows: list[dict], ylabel: str, width: int = 640, height: int = 260) -> str:
    pts = []
    for row in assign_lmh(rows):
        val = to_float(row.get("value"))
        if val is None or row.get("lmh") not in RANGE_X:
            continue
        pts.append(
            {
                "x": RANGE_X[row["lmh"]],
                "y": val,
                "lsl": limit_float(row.get("lower_limit")),
                "usl": limit_float(row.get("upper_limit")),
                "pf": row.get("pf") or "",
                "lmh": row["lmh"],
            }
        )
    if not pts:
        return '<p class="muted">這個 band／測項沒有可畫的數字點。</p>'
    limit_pairs = {(p["lsl"], p["usl"]) for p in pts}
    if len(limit_pairs) > 1:
        return (
            '<div class="empty-state">這批資料包含多組 LSL／USL。'
            "請先選擇一個精確條件組；系統不會平均限值。</div>"
        )
    ys = [p["y"] for p in pts]
    lsls = [p["lsl"] for p in pts if p["lsl"] is not None]
    usls = [p["usl"] for p in pts if p["usl"] is not None]
    lo = min(ys + lsls)
    hi = max(ys + usls)
    pad = (hi - lo) * 0.12 or 1
    lo, hi = lo - pad, hi + pad
    left, right, top, bottom = 56, width - 16, 16, height - 36
    # x positions
    xs = [left + (right - left) * (0.18 + 0.32 * i) for i in range(3)]
    svg = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" style="max-width:{width}px;background:#fff;border:1px solid #ccc">'
    ]
    # axes
    svg.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#333"/>')
    svg.append(f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#333"/>')
    for i, name in enumerate(("Low", "Mid", "High")):
        svg.append(
            f'<text x="{xs[i]}" y="{height - 10}" text-anchor="middle" font-size="12">{name}</text>'
        )
    svg.append(
        f'<text x="12" y="{top + 10}" font-size="11" fill="#555">{escape(ylabel)}</text>'
    )
    # ticks
    for t in (lo, (lo + hi) / 2, hi):
        y = _scale([t], top, bottom, lo, hi)[0]
        svg.append(f'<text x="{left - 6}" y="{y + 4}" text-anchor="end" font-size="10">{t:.3g}</text>')
    if lsls:
        y = _scale([lsls[0]], top, bottom, lo, hi)[0]
        svg.append(
            f'<line x1="{left}" y1="{y}" x2="{right}" y2="{y}" stroke="#1a6b1a" stroke-dasharray="4 3"/>'
        )
        svg.append(f'<text x="{right}" y="{y - 4}" text-anchor="end" font-size="10" fill="#1a6b1a">LSL</text>')
    if usls:
        y = _scale([usls[0]], top, bottom, lo, hi)[0]
        svg.append(
            f'<line x1="{left}" y1="{y}" x2="{right}" y2="{y}" stroke="#8b0000" stroke-dasharray="4 3"/>'
        )
        svg.append(f'<text x="{right}" y="{y - 4}" text-anchor="end" font-size="10" fill="#8b0000">USL</text>')
    # points with small jitter by index
    counts = {0: 0, 1: 0, 2: 0}
    for p in pts:
        i = p["x"]
        counts[i] += 1
        jitter = ((counts[i] % 7) - 3) * 3
        y = _scale([p["y"]], top, bottom, lo, hi)[0]
        color = "#8b0000" if p["pf"] == "Fail" else "#008787"
        svg.append(
            f'<circle cx="{xs[i] + jitter}" cy="{y}" r="3.5" fill="{color}" fill-opacity="0.8"/>'
        )
    svg.append("</svg>")
    svg.append(
        f'<p class="muted">點數 {len(pts)}（綠=Pass，紅=Fail）。虛線是 3GPP 下限／上限。同一 channel 多點會左右微移以免重疊。</p>'
    )
    return "\n".join(svg)


def svg_comparison(
    series: list[tuple[str, list[dict]]],
    ylabel: str,
    width: int = 760,
    height: int = 300,
) -> str:
    """Overlay cohorts only after the caller proves the exact group is shared."""
    palette = ("#496b57", "#9a6c42", "#66728a", "#82697e")
    pts = []
    for series_index, (label, rows) in enumerate(series):
        for row in assign_lmh(rows):
            value = to_float(row.get("value"))
            if value is None or row.get("lmh") not in RANGE_X:
                continue
            pts.append(
                {
                    "series": series_index,
                    "label": label,
                    "x": RANGE_X[row["lmh"]],
                    "y": value,
                    "lsl": limit_float(row.get("lower_limit")),
                    "usl": limit_float(row.get("upper_limit")),
                    "pf": row.get("pf") or "",
                }
            )
    if not pts:
        return '<div class="empty-state">共同條件組沒有可畫的有效數值。</div>'
    pairs = {(point["lsl"], point["usl"]) for point in pts}
    if len(pairs) != 1:
        return (
            '<div class="empty-state">cohort 的條件或限值不同，已停止疊圖。'
            "請改看下方分圖。</div>"
        )
    values = [point["y"] for point in pts]
    lsl, usl = next(iter(pairs))
    if lsl is not None:
        values.append(lsl)
    if usl is not None:
        values.append(usl)
    lo, hi = min(values), max(values)
    pad = (hi - lo) * 0.12 or 1
    lo, hi = lo - pad, hi + pad
    left, right, top, bottom = 58, width - 20, 34, height - 38
    xs = [left + (right - left) * (0.18 + 0.32 * index) for index in range(3)]
    svg = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" '
        'style="max-width:760px;background:#fffdf9;border:1px solid #ded8ce;border-radius:10px">'
    ]
    svg.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#393b38"/>')
    svg.append(f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#393b38"/>')
    for index, name in enumerate(("Low", "Mid", "High")):
        svg.append(f'<text x="{xs[index]}" y="{height - 12}" text-anchor="middle" font-size="12">{name}</text>')
    svg.append(f'<text x="12" y="{top + 8}" font-size="11" fill="#676b65">{escape(ylabel)}</text>')
    for tick in (lo, (lo + hi) / 2, hi):
        y = _scale([tick], top, bottom, lo, hi)[0]
        svg.append(f'<text x="{left - 6}" y="{y + 4}" text-anchor="end" font-size="10">{tick:.3g}</text>')
    for value, label, color in ((lsl, "LSL", "#496b57"), (usl, "USL", "#a14f43")):
        if value is None:
            continue
        y = _scale([value], top, bottom, lo, hi)[0]
        svg.append(f'<line x1="{left}" y1="{y}" x2="{right}" y2="{y}" stroke="{color}" stroke-dasharray="5 4"/>')
        svg.append(f'<text x="{right}" y="{y - 4}" text-anchor="end" font-size="10" fill="{color}">{label} {value:.3g}</text>')
    counts: dict[tuple[int, int], int] = defaultdict(int)
    for point in pts:
        key = (point["series"], point["x"])
        counts[key] += 1
        offset = (point["series"] - (len(series) - 1) / 2) * 10
        jitter = ((counts[key] % 5) - 2) * 2
        y = _scale([point["y"]], top, bottom, lo, hi)[0]
        color = palette[point["series"] % len(palette)]
        stroke = "#a14f43" if point["pf"] == "Fail" else "#fffdf9"
        svg.append(
            f'<circle cx="{xs[point["x"]] + offset + jitter}" cy="{y}" r="4" '
            f'fill="{color}" stroke="{stroke}" stroke-width="1.5"/>'
        )
    legend_x = left
    for index, (label, _rows) in enumerate(series):
        color = palette[index % len(palette)]
        svg.append(f'<circle cx="{legend_x}" cy="16" r="4" fill="{color}"/>')
        svg.append(f'<text x="{legend_x + 8}" y="20" font-size="11">{escape(label)}</text>')
        legend_x += min(170, 24 + len(label) * 12)
    svg.append("</svg>")
    svg.append('<p class="muted">顏色代表資料夾 cohort；紅色外框代表該細節列由儀器標為 Fail。</p>')
    return "\n".join(svg)
