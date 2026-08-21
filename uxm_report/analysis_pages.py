"""HTML for limit-margin analysis. Not Cpk until many IMEIs exist."""

from __future__ import annotations

from html import escape

from .analysis import Point, from_row, summarize
from .lineage import build_links, latest_verdict
from .review import _page, _vclass, nav_parts, site_nav
from .store import Store


def _bar(pos: float | None) -> str:
    if pos is None:
        return '<span class="muted">單邊限</span>'
    pct = max(0, min(100, pos * 100))
    return (
        '<span class="bar" title="0=下限 100=上限">'
        f'<span class="fill" style="left:{pct:.1f}%"></span>'
        "</span>"
        f' <span class="muted">{pct:.0f}%</span>'
    )


def _fmt(x: float | None) -> str:
    if x is None:
        return ""
    return f"{x:.3g}"


def _table(points: list[Point], limit: int = 40) -> str:
    rows = []
    for p in points[:limit]:
        rows.append(
            "<tr>"
            f"<td>{escape(p.test_case)}</td>"
            f"<td>{escape(p.item)}</td>"
            f"<td>{escape(p.band)}</td>"
            f"<td>{_fmt(p.lsl)}</td>"
            f"<td>{_fmt(p.value)}</td>"
            f"<td>{_fmt(p.usl)} {escape(p.unit)}</td>"
            f"<td>{_fmt(p.nearest)}</td>"
            f"<td>{escape(p.side)}</td>"
            f"<td>{_bar(p.pos)}</td>"
            f"<td class=\"{_vclass(p.pf)}\">{escape(p.pf)}</td>"
            "</tr>"
        )
    if not rows:
        return "<p class=\"muted\">沒有可算上下限的量測點。</p>"
    return (
        "<table><tr>"
        "<th>測項</th><th>Item</th><th>Band</th><th>LSL</th><th>Value</th>"
        "<th>USL</th><th>margin</th><th>較近哪邊</th><th>在窗裡的位置</th><th>P/F</th>"
        "</tr>"
        + "".join(rows)
        + "</table>"
    )


def _load(store: Store, session_id: int | None = None, module: str | None = None) -> list[Point]:
    points: list[Point] = []
    for row in store.measure_rows(session_id=session_id, module=module):
        point = from_row(row)
        if point:
            points.append(point)
    return points


def analysis_index(store: Store) -> str:
    sessions = store.list_sessions()
    modules = sorted({r["module"] for r in sessions})
    links = "".join(
        f'<li><a href="/analysis/module?name={escape(m)}">{escape(m)}</a></li>' for m in modules
    )
    slinks = "".join(
        f'<li><a href="/analysis/session?id={r["id"]}">{escape(r["filename"])}</a> '
        f'({escape(r["overall_result"] or "")})</li>'
        for r in sessions
    )
    body = f"""
{site_nav("資料分析")}
<h1>對 3GPP 上下限的位置（初版）</h1>
<div class="note">
伺服器已經把量測寫進 SQLite。這頁不重算 Pass/Fail，只看 <b>Value 落在 [LSL, USL] 的哪裡</b>。<br>
<b>Cpk 現在不算。</b>Cpk 要多顆獨立 IMEI（不同 DUT）。同一顆模組掃 2000 個測點，那是測試條件的分佈，不是製程能力。<br>
位置條：左=下限、右=上限。偏左＝貼下限，偏右＝貼上限。Pass 的點也會列，才能看出設計鬆緊。
</div>
<h2>依模組</h2>
<ul>{links or "<li>資料庫是空的</li>"}</ul>
<h2>依 session</h2>
<ul>{slinks}</ul>
"""
    return _page("資料分析", body)


def _retry_note(point: Point, links) -> str:
    for (sid, name, _lmh), link in links.items():
        if sid == point.session_id and link.superseded and name in (point.test_case or ""):
            return f"已重測過 → {link.later_filename}"
    return "未結"


def _report(title: str, nav: str, points: list[Point], extra: str = "", links=None) -> str:
    bias = summarize(points)
    tight = sorted(
        [p for p in points if p.nearest is not None],
        key=lambda p: p.nearest,
    )[:25]
    fails = [p for p in points if p.pf == "Fail"]
    links = links or {}
    open_f, closed_f = [], []
    for p in fails:
        if _retry_note(p, links).startswith("已重測"):
            closed_f.append(p)
        else:
            open_f.append(p)
    body = f"""
<div class="nav">{nav}</div>
<h1>{escape(title)}</h1>
<div class="note">
可定位的雙邊限點 <b>{bias.usable}</b>：
偏下限 {bias.lower}、中段 {bias.mid}、偏上限 {bias.upper}。
細節 Fail {bias.fail}（未結 {len(open_f)}／已重測過 {len(closed_f)}）。
窗寬 10% 以內（偏緊）{bias.tight}。<br>
同一 IMEI＋band＋測項＋LMH，後來 Pass 會把前面 Fail 標成已重測，<b>不要用單次 Fail 當最終結論</b>。<br>
這是已匯入樣本的位置統計，還不是 Cpk。
</div>
{extra}
<h2>最貼限的 25 點（含 Pass）</h2>
<p class="muted">margin 愈小愈危險。用來找「過了但很貼」的設計風險。</p>
{_table(tight, 25)}
<h2>未結的 Fail</h2>
{_table(open_f, 40)}
<h2>已重測過的 Fail（後來有 Pass，僅供追溯）</h2>
{_table(closed_f, 40)}
"""
    return _page(title, body)


def analysis_module(store: Store, name: str) -> str:
    points = _load(store, module=name)
    events = store.lineage_events(module=name)
    links = build_links(events)
    latest = latest_verdict(events)
    open_keys = [
        ev for ev in latest.values() if (ev.get("verdict") or "").lower() == "fail"
    ]
    rows = []
    for ev in open_keys:
        rows.append(
            "<tr>"
            f"<td>{escape(ev.get('imei') or '')}</td>"
            f"<td>{escape(ev.get('band') or '')}</td>"
            f"<td>{escape(ev.get('test_name') or '')}</td>"
            f"<td>{escape(ev.get('lmh') or '')}</td>"
            f"<td>{escape(ev.get('filename') or '')}</td>"
            "</tr>"
        )
    extra = (
        "<h2>重測之後仍未過的摘要項</h2>"
        "<p class=\"muted\">每個 IMEI＋band＋測項＋LMH 只留時間最晚的那一筆。這裡才比較接近「整體還有沒有掛著」。</p>"
        + (
            "<table><tr><th>IMEI</th><th>Band</th><th>測項</th><th>LMH</th><th>最後出現於</th></tr>"
            + "".join(rows)
            + "</table>"
            if rows
            else "<p class=\"muted\">沒有未結的摘要 Fail。</p>"
        )
    )
    nav = nav_parts("資料分析")
    return _report(f"模組 {name}", nav, points, extra=extra, links=links)


def analysis_session(store: Store, session_id: int) -> str:
    head = store.session_header(session_id)
    if not head:
        return _page("找不到", "<p>沒有這個 session。</p>")
    points = _load(store, session_id=session_id)
    links = build_links(store.lineage_events(module=head["module"]))
    nav = nav_parts("資料分析", extra=f'<a href="/review/session?id={session_id}">原始列</a>')
    return _report(head["filename"], nav, points, links=links)
