"""Server-rendered analysis workspace.

The overview reads summary Verdict rows only. Detail rows are fetched after a
user opens one summary test, one exact measurement group and one 100-row page.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import replace
from html import escape
from math import ceil
from urllib.parse import urlencode

from .analysis import (
    AnalysisCohort,
    AnalysisFilter,
    MeasurementGroup,
    PAGE_SIZE,
    Point,
    SpecInsight,
    clause_of,
    from_row,
    measurement_state,
)
from .charts import svg_comparison, svg_lmh
from .lineage import build_links, event_key, latest_verdict
from .review import _page, _vclass, site_nav
from .store import Store
from .ts38521 import BY_ID, SPEC_DOC, SPEC_VERSION
from .ts38521_details import detail_of

SUMMARY_PAGE_SIZE = 80


def parse_analysis_filter(qs: dict[str, list[str]]) -> AnalysisFilter:
    scopes = []
    seen = set()
    for token in qs.get("scope") or []:
        cohort = AnalysisCohort.from_token(token)
        if cohort and cohort not in seen:
            scopes.append(cohort)
            seen.add(cohort)
    try:
        page = int((qs.get("page") or ["1"])[0])
    except (TypeError, ValueError):
        page = 1
    return AnalysisFilter(
        module=(qs.get("module") or qs.get("name") or [""])[0].strip(),
        scopes=tuple(scopes),
        imei=(qs.get("imei") or [""])[0].strip(),
        band=(qs.get("band") or [""])[0].strip(),
        clause=(qs.get("clause") or [""])[0].strip(),
        status=(qs.get("status") or [""])[0].strip(),
        mode=(qs.get("mode") or ["latest"])[0].strip(),
        page=page,
    )


def _analysis_url(filters: AnalysisFilter, page: int | None = None) -> str:
    pairs: list[tuple[str, str]] = []
    if filters.module:
        pairs.append(("module", filters.module))
    pairs.extend(("scope", scope.token) for scope in filters.scopes)
    for key in ("imei", "band", "clause", "status"):
        value = getattr(filters, key)
        if value:
            pairs.append((key, value))
    if filters.mode == "history":
        pairs.append(("mode", "history"))
    target_page = filters.page if page is None else page
    if target_page > 1:
        pairs.append(("page", str(target_page)))
    return "/analysis" + ("?" + urlencode(pairs) if pairs else "")


def _detail_url(row: dict, scopes: tuple[AnalysisCohort, ...] = ()) -> str:
    pairs = [
        ("id", str(row["session_id"])),
        ("clause", row.get("clause") or clause_of(row.get("test_name") or "")),
        ("test", row.get("test_name") or ""),
        ("lmh", row.get("lmh") or str(row.get("channel") or "")),
    ]
    pairs.extend(("scope", scope.token) for scope in scopes)
    return "/analysis/detail?" + urlencode(pairs)


def _compare_url(
    filters: AnalysisFilter,
    test_name: str,
    band: str,
    lmh: str,
) -> str:
    pairs = [("module", filters.module)]
    pairs.extend(("scope", scope.token) for scope in filters.scopes)
    pairs.extend((("test", test_name), ("band", band), ("lmh", lmh)))
    return "/analysis/compare?" + urlencode(pairs)


def _option(value: str, label: str, current: str) -> str:
    selected = " selected" if value == current else ""
    return f'<option value="{escape(value)}"{selected}>{escape(label)}</option>'


def _status(value: str) -> str:
    text = (value or "Unknown").strip()
    return f'<span class="status-chip {_vclass(text)}">{escape(text)}</span>'


def _natural_clause(value: str) -> tuple:
    bits = []
    for bit in (value or "").split("."):
        number = "".join(ch for ch in bit if ch.isdigit())
        suffix = bit[len(number) :]
        bits.append((int(number or 0), suffix))
    return tuple(bits)


def _select_default_scope(store: Store, filters: AnalysisFilter) -> tuple[AnalysisFilter, list[dict]]:
    available = store.analysis_scopes(filters.module)
    allowed = {row["cohort"] for row in available}
    selected = tuple(scope for scope in filters.scopes if scope in allowed)
    if not selected and available:
        selected = (available[0]["cohort"],)
    return replace(filters, scopes=selected), available


def _event_rows(store: Store, filters: AnalysisFilter) -> tuple[list[dict], list[dict]]:
    facet_rows = store.analysis_events(filters.module, filters.scopes)
    rows = store.analysis_events(
        filters.module,
        filters.scopes,
        imei=filters.imei,
        band=filters.band,
        clause=filters.clause,
    )
    if filters.mode == "latest":
        rows = list(latest_verdict(rows).values())
    if filters.status:
        wanted = filters.status.lower()
        rows = [row for row in rows if (row.get("verdict") or "").lower() == wanted]
    rows.sort(
        key=lambda row: (
            row.get("project") or "",
            row.get("data_folder") or "",
            _natural_clause(row.get("clause") or ""),
            row.get("band") or "",
            row.get("test_name") or "",
            row.get("lmh") or "",
            row.get("start_time") or "",
        )
    )
    return rows, facet_rows


def _module_cards(store: Store) -> str:
    cards = []
    for module in store.list_modules():
        href = _analysis_url(AnalysisFilter(module=module["model"]))
        cards.append(
            f'<a class="card analysis-card" href="{href}">'
            f'<span class="eyebrow">模組</span><h2>{escape(module["model"])}</h2>'
            f'<p>{module["projects"]} 個專案 · {module["duts"]} 個 IMEI · '
            f'{module["sessions"]} 份 session</p></a>'
        )
    body = f"""
{site_nav("資料分析")}
<div class="page-heading">
  <div><p class="eyebrow">Analysis workspace</p><h1>量測分析</h1></div>
  <p>先選模組，再從最新資料夾狀態開始；需要時可加入其他資料夾比較。</p>
</div>
<div class="note">
狀態只採用 Keysight 摘要列 Verdict。細節量測負責說明 Value、限值與條件，不會重新判定整個測項 Pass／Fail。
</div>
<div class="cards">{''.join(cards) or '<div class="empty-state">尚無資料，請先匯入報告。</div>'}</div>
"""
    return _page("量測分析", body)


def _filters(
    filters: AnalysisFilter,
    available: list[dict],
    facet_rows: list[dict],
) -> str:
    imeis = sorted({row.get("imei") or "" for row in facet_rows if row.get("imei")})
    bands = sorted({row.get("band") or "" for row in facet_rows if row.get("band")})
    clauses = sorted(
        {row.get("clause") or clause_of(row.get("test_name") or "") for row in facet_rows}
        - {""},
        key=_natural_clause,
    )
    selected = set(filters.scopes)
    scope_boxes = []
    for meta in available:
        cohort = meta["cohort"]
        checked = " checked" if cohort in selected else ""
        scope_boxes.append(
            f'<label class="scope-option"><input type="checkbox" name="scope" '
            f'value="{escape(cohort.token)}"{checked}>'
            f'<span><b>{escape(cohort.project)}</b><small>{escape(cohort.data_folder)} · '
            f'{meta["sessions"]} sessions</small></span></label>'
        )
    imei_opts = [_option("", "全部 IMEI", filters.imei)]
    imei_opts.extend(_option(value, value, filters.imei) for value in imeis)
    band_opts = [_option("", "全部 Band", filters.band)]
    band_opts.extend(_option(value, value, filters.band) for value in bands)
    clause_opts = [_option("", "全部條款", filters.clause)]
    clause_opts.extend(_option(value, value, filters.clause) for value in clauses)
    return f"""
<form class="analysis-filters" method="get" action="/analysis">
  <input type="hidden" name="module" value="{escape(filters.module)}">
  <div class="filter-grid">
    <label>IMEI<select name="imei">{''.join(imei_opts)}</select></label>
    <label>Band<select name="band">{''.join(band_opts)}</select></label>
    <label>條款<select name="clause">{''.join(clause_opts)}</select></label>
    <label>狀態<select name="status">
      {_option("", "全部狀態", filters.status)}
      {_option("Fail", "Fail", filters.status)}
      {_option("Pass", "Pass", filters.status)}
      {_option("Skip", "Skip", filters.status)}
    </select></label>
    <label>結果版本<select name="mode">
      {_option("latest", "目前最新狀態", filters.mode)}
      {_option("history", "包含歷史結果", filters.mode)}
    </select></label>
  </div>
  <details class="scope-picker"{" open" if len(filters.scopes) > 1 else ""}>
    <summary>資料範圍：已選 {len(filters.scopes)} 個專案／資料夾</summary>
    <p class="muted">選一個是日常檢視；選兩個以上會進入 cohort 比較，不會互相關閉 Fail。</p>
    <div class="scope-grid">{''.join(scope_boxes)}</div>
  </details>
  <div class="filter-actions">
    <button type="submit">套用篩選</button>
    <a class="button secondary" href="/analysis?module={escape(filters.module)}">回到預設</a>
  </div>
</form>
"""


def _cohort_stats(rows: list[dict], scopes: tuple[AnalysisCohort, ...]) -> str:
    by_scope: dict[tuple[str, str], Counter] = defaultdict(Counter)
    for row in rows:
        key = (row.get("project") or "", row.get("data_folder") or "")
        value = (row.get("verdict") or "Other").strip().capitalize()
        by_scope[key][value] += 1
    cards = []
    for scope in scopes:
        counts = by_scope[(scope.project, scope.data_folder)]
        total = sum(counts.values())
        passed = counts["Pass"]
        failed = counts["Fail"]
        skipped = counts["Skip"]
        pass_width = (passed / total * 100) if total else 0
        fail_width = (failed / total * 100) if total else 0
        cards.append(
            '<section class="cohort-card">'
            f'<p class="eyebrow">{escape(scope.project)}</p><h3>{escape(scope.data_folder)}</h3>'
            f'<p><b>{total}</b> 個摘要狀態</p>'
            f'<div class="status-bar" aria-label="Pass {passed}, Fail {failed}, Skip {skipped}">'
            f'<span class="bar-pass" style="width:{pass_width:.2f}%"></span>'
            f'<span class="bar-fail" style="width:{fail_width:.2f}%"></span></div>'
            f'<p class="cohort-counts"><span class="pass">Pass {passed}</span>'
            f'<span class="fail">Fail {failed}</span><span class="skip">Skip {skipped}</span></p>'
            "</section>"
        )
    return '<div class="cohort-cards">' + "".join(cards) + "</div>"


def _comparison_table(rows: list[dict], filters: AnalysisFilter) -> str:
    if len(filters.scopes) < 2 or filters.mode != "latest":
        return ""
    by_test: dict[tuple[str, str, str], dict[tuple[str, str], dict]] = defaultdict(dict)
    for row in rows:
        key = (
            row.get("band") or "",
            row.get("test_name") or "",
            row.get("lmh") or str(row.get("channel") or ""),
        )
        cohort = (row.get("project") or "", row.get("data_folder") or "")
        by_test[key][cohort] = row
    trs = []
    for (band, test_name, lmh), values in sorted(
        by_test.items(), key=lambda item: (item[0][0], _natural_clause(clause_of(item[0][1])), item[0][1], item[0][2])
    ):
        cells = []
        for scope in filters.scopes:
            row = values.get((scope.project, scope.data_folder))
            cells.append(
                f'<td><a href="{_detail_url(row, filters.scopes)}">{_status(row.get("verdict") or "")}</a></td>'
                if row
                else '<td class="muted">—</td>'
            )
        compare = _compare_url(filters, test_name, band, lmh)
        trs.append(
            f'<tr><td>{escape(band)}</td><td>{escape(test_name)}</td><td>{escape(lmh)}</td>'
            + "".join(cells)
            + f'<td><a href="{compare}">比較量測</a></td></tr>'
        )
    heads = "".join(f"<th>{escape(scope.data_folder)}</th>" for scope in filters.scopes)
    return f"""
<section class="panel">
  <div class="section-heading"><div><p class="eyebrow">Cohort comparison</p><h2>資料夾並列</h2></div>
  <p>每欄獨立計算目前狀態。</p></div>
  <div class="table-scroll"><table>
    <thead><tr><th>Band</th><th>測項</th><th>LMH</th>{heads}<th>量測</th></tr></thead>
    <tbody>{''.join(trs) or '<tr><td colspan="6">沒有可比較的摘要項。</td></tr>'}</tbody>
  </table></div>
</section>
"""


def _summary_table(rows: list[dict], filters: AnalysisFilter) -> str:
    total = len(rows)
    pages = max(1, ceil(total / SUMMARY_PAGE_SIZE))
    page = min(filters.page, pages)
    shown = rows[(page - 1) * SUMMARY_PAGE_SIZE : page * SUMMARY_PAGE_SIZE]
    trs = []
    show_scope = len(filters.scopes) > 1
    for row in shown:
        link = _detail_url(row, filters.scopes)
        scope = (
            f'<td>{escape(row.get("project") or "")}<br><span class="muted">'
            f'{escape(row.get("data_folder") or "")}</span></td>'
            if show_scope
            else ""
        )
        when = (
            f'<td>{escape(row.get("start_time") or "")}<br><span class="muted">'
            f'{escape(row.get("filename") or "")}</span></td>'
            if filters.mode == "history"
            else ""
        )
        trs.append(
            "<tr>"
            + scope
            + f'<td>{escape(row.get("band") or "")}</td>'
            f'<td><a href="{link}">{escape(row.get("test_name") or "")}</a>'
            f'<br><span class="muted">{escape(row.get("clause") or "")}</span></td>'
            f'<td>{escape(row.get("lmh") or str(row.get("channel") or ""))}</td>'
            f'<td>{_status(row.get("verdict") or "")}</td>'
            f'<td>{escape(row.get("imei") or "")}</td>'
            + when
            + "</tr>"
        )
    prev_link = (
        f'<a class="button secondary" href="{_analysis_url(filters, page - 1)}">上一頁</a>'
        if page > 1
        else '<span class="button secondary disabled">上一頁</span>'
    )
    next_link = (
        f'<a class="button secondary" href="{_analysis_url(filters, page + 1)}">下一頁</a>'
        if page < pages
        else '<span class="button secondary disabled">下一頁</span>'
    )
    scope_head = "<th>範圍</th>" if show_scope else ""
    when_head = "<th>時間／來源</th>" if filters.mode == "history" else ""
    return f"""
<section class="panel">
  <div class="section-heading"><div><p class="eyebrow">Summary verdict</p><h2>測項狀態</h2></div>
  <p>{total} 筆 · 第 {page}/{pages} 頁</p></div>
  <div class="table-scroll"><table>
    <thead><tr>{scope_head}<th>Band</th><th>測項</th><th>LMH</th><th>Verdict</th><th>IMEI</th>{when_head}</tr></thead>
    <tbody>{''.join(trs) or '<tr><td colspan="8">沒有符合條件的摘要結果。</td></tr>'}</tbody>
  </table></div>
  <nav class="pagination">{prev_link}<span>第 {page} / {pages} 頁</span>{next_link}</nav>
</section>
"""


def analysis_index(store: Store, filters: AnalysisFilter | None = None) -> str:
    filters = filters or AnalysisFilter()
    if not filters.module:
        return _module_cards(store)
    filters, available = _select_default_scope(store, filters)
    rows, facet_rows = _event_rows(store, filters)
    title = filters.module
    body = f"""
{site_nav("資料分析")}
<div class="context-strip"><a href="/analysis">量測分析</a><span>/</span><b>{escape(filters.module)}</b>
  <span>/</span><span>{'比較模式' if len(filters.scopes) > 1 else '目前狀態'}</span></div>
<div class="page-heading">
  <div><p class="eyebrow">Module analysis</p><h1>{escape(title)}</h1></div>
  <p>摘要狀態、規格依據與工程判讀分開呈現。</p>
</div>
<div class="note">
目前狀態鍵：專案＋資料夾＋IMEI＋Band＋測項＋LMH。較晚 Pass 只會關閉同一鍵的舊 Fail。
</div>
{_filters(filters, available, facet_rows)}
{_cohort_stats(rows, filters.scopes)}
{_comparison_table(rows, filters)}
{_summary_table(rows, filters)}
"""
    return _page(f"{title} 量測分析", body)


def analysis_module(store: Store, name: str, session_ids: list[int] | None = None) -> str:
    scopes = []
    if session_ids:
        for session_id in session_ids:
            head = store.session_header(session_id)
            if not head or head.get("module") != name:
                continue
            cohort = AnalysisCohort(head["project"], head.get("data_folder") or "UNKNOWN")
            if cohort not in scopes:
                scopes.append(cohort)
    return analysis_index(store, AnalysisFilter(module=name, scopes=tuple(scopes)))


def spec_insight(clause: str) -> SpecInsight:
    spec = BY_ID.get(clause)
    if not spec:
        return SpecInsight(clause=clause)
    return SpecInsight(
        clause=clause,
        title=spec.title,
        version=SPEC_VERSION,
        page=spec.page,
        purpose=spec.purpose,
        watch=spec.watch,
        extra=spec.extra,
        detail=detail_of(clause),
        available=True,
    )


def _group_label(group: MeasurementGroup) -> str:
    context = " · ".join(
        value for value in (group.band, group.bandwidth, group.scs, group.modulation, group.rb, group.condition) if value
    )
    limits = f"[{group.lower_limit or '—'}, {group.upper_limit or '—'}] {group.unit}".strip()
    return f"{group.item or '未命名 Item'} · {context or '一般條件'} · {limits} · {group.count} 筆"


def _margin(point: Point | None) -> str:
    if not point or point.state != "measured":
        return "—"
    if point.nearest is None:
        return "無有效限值"
    native = f"{point.nearest:.3g} {point.unit}".strip()
    if point.margin_ratio is not None:
        return f"{native}（窗寬 {point.margin_ratio * 100:.1f}%）"
    return f"{native}（單邊限）"


def _state_label(state: str) -> str:
    return {
        "measured": "有效量測",
        "unset": "未量到／儀器判定",
        "derived": "衍生 Item（不列貼限排行）",
        "invalid": "非數值／格式異常",
    }.get(state, state)


def _detail_pager(
    session_id: int,
    clause: str,
    test_name: str,
    lmh: str,
    group: MeasurementGroup | None,
    page: int,
    total: int,
) -> str:
    pages = max(1, ceil(total / PAGE_SIZE))
    base = [("id", str(session_id)), ("clause", clause), ("test", test_name), ("lmh", lmh)]
    if group:
        base.append(("group", group.token))

    def link(target: int, label: str) -> str:
        if target < 1 or target > pages:
            return f'<span class="button secondary disabled">{label}</span>'
        return f'<a class="button secondary" href="/analysis/detail?{urlencode(base + [("page", str(target))])}">{label}</a>'

    return (
        '<nav class="pagination">'
        + link(page - 1, "上一頁")
        + f"<span>第 {page} / {pages} 頁 · 共 {total} 筆 · 每頁最多 {PAGE_SIZE} 筆</span>"
        + link(page + 1, "下一頁")
        + "</nav>"
    )


def analysis_session(
    store: Store,
    session_id: int,
    clause: str = "",
    test_name: str = "",
    lmh: str = "",
    group_token: str = "",
    page: int = 1,
) -> str:
    head = store.session_header(session_id)
    if not head:
        return _page("找不到", f'{site_nav("資料分析")}<div class="empty-state">沒有這個 session。</div>')
    tests = store.session_tests(session_id)
    summary = next(
        (
            row
            for row in tests
            if (not test_name or row["test_name"] == test_name)
            and (not lmh or (row.get("lmh") or str(row.get("channel") or "")) == lmh)
            and (not clause or clause_of(row["test_name"]) == clause)
        ),
        tests[0] if tests else None,
    )
    if summary:
        test_name = summary["test_name"]
        clause = clause or clause_of(test_name)
        lmh = lmh or summary.get("lmh") or str(summary.get("channel") or "")
    groups = store.analysis_measurement_groups(session_id, clause) if clause else []
    requested = MeasurementGroup.from_token(group_token) if group_token else None
    selected = next((group for group in groups if requested and group.signature == requested.signature), None)
    if selected is None and groups:
        selected = groups[0]
    rows, total, page = store.analysis_detail_page(session_id, clause, selected, page) if clause else ([], 0, 1)
    points = [point for point in (from_row(row) for row in rows) if point]
    chart_rows = [dict(row, lmh=lmh) for row in rows if measurement_state(row.get("value"), row.get("item") or "") == "measured"]
    chart = svg_lmh(chart_rows, selected.unit if selected else "") if chart_rows else '<div class="empty-state">這個條件組沒有可畫的有效數值。</div>'
    links = build_links(store.lineage_events(module=head["module"]))
    retry = links.get((session_id, test_name, lmh)) if summary else None
    current_note = "目前最新結果"
    if retry and retry.superseded:
        current_note = f"歷史 Fail；後續已由 {retry.later_filename} Pass"
    insight = spec_insight(clause)
    options = "".join(
        f'<option value="{group.token}"{" selected" if selected and group.signature == selected.signature else ""}>'
        f'{escape(_group_label(group))}</option>'
        for group in groups
    )
    detail_rows = []
    for row in rows:
        state = measurement_state(row.get("value"), row.get("item") or "")
        point = from_row(row)
        detail_rows.append(
            "<tr>"
            f'<td>{escape(row.get("time") or "")}</td>'
            f'<td>{escape(row.get("item") or "")}<br><span class="muted">{escape(row.get("description") or "")}</span></td>'
            f'<td>{escape(row.get("arfcn") or "")}<br><span class="muted">{escape(row.get("freq_mhz") or "")}</span></td>'
            f'<td>{escape(row.get("value") or "")} {escape(row.get("unit") or "")}</td>'
            f'<td>{escape(row.get("lower_limit") or "—")}</td><td>{escape(row.get("upper_limit") or "—")}</td>'
            f'<td>{escape(_margin(point))}</td><td>{escape(_state_label(state))}</td>'
            f'<td>{_status(row.get("pf") or "NotSet")}</td></tr>'
        )
    spec_block = (
        f'<h3>{escape(SPEC_DOC)} {escape(clause)} · {escape(insight.title)}</h3>'
        f'<p>{escape(insight.purpose)}</p>'
        f'<p class="muted">V{escape(insight.version)} · PDF 印刷頁 {insight.page}。'
        f'測法來源 38.521-1；限值本體依 38.101-1 對應條款。</p>'
        f'<p><a href="/spec?{urlencode({"module": head["module"], "project": head["project"], "clause": clause})}">開啟測試規格對照</a></p>'
        if insight.available
        else f'<h3>{escape(clause or "未辨識條款")}</h3><p>規格來源已保留；Grok 解讀整理中。</p>'
    )
    engineering = (
        "".join(
            f"<p>{escape(text)}</p>"
            for text in (insight.watch, insight.extra, insight.detail)
            if text
        )
        if insight.available and any((insight.watch, insight.extra, insight.detail))
        else "<p>解讀整理中。此區不即時呼叫模型，也不自行補寫結論。</p>"
    )
    verdict = summary.get("verdict") if summary else ""
    body = f"""
{site_nav("資料分析", extra=f'<a href="/review/session?id={session_id}">原始 session</a>')}
<div class="context-strip"><a href="/analysis">量測分析</a><span>/</span>
  <a href="/analysis?module={escape(head["module"])}">{escape(head["module"])}</a><span>/</span>
  <b>{escape(head["project"])} / {escape(head.get("data_folder") or "UNKNOWN")}</b></div>
<div class="page-heading">
  <div><p class="eyebrow">{escape(clause)}</p><h1>{escape(test_name or head["filename"])}</h1></div>
  <div>{_status(verdict or "No Verdict")}<p class="muted">{escape(current_note)}</p></div>
</div>
<div class="layer-grid">
  <section class="layer-card fact"><p class="eyebrow">01 量測事實</p>
    <h3>摘要 Verdict：{escape(verdict or "—")}</h3>
    <p>{escape(head["module"])} · {escape(head["project"])} · {escape(head.get("data_folder") or "UNKNOWN")}<br>
    IMEI {escape(head["imei"])} · {escape(summary.get("band") if summary else "")} · {escape(lmh)}</p>
    <p class="muted">{escape(head["filename"])} · {escape(head["start_time"] or "")}</p>
    <p><a href="/review/session?id={session_id}">查看原始摘要與細節列</a></p>
  </section>
  <section class="layer-card spec"><p class="eyebrow">02 規格依據</p>{spec_block}</section>
  <section class="layer-card judgement"><p class="eyebrow">03 工程判讀</p>
    <h3>Grok 已整理內容</h3>{engineering}</section>
</div>
<section class="panel">
  <div class="section-heading"><div><p class="eyebrow">Exact condition group</p><h2>量測條件與圖表</h2></div>
  <p>不同單位或限值不混圖、不混排行。</p></div>
  <form method="get" action="/analysis/detail" class="group-picker">
    <input type="hidden" name="id" value="{session_id}">
    <input type="hidden" name="clause" value="{escape(clause)}">
    <input type="hidden" name="test" value="{escape(test_name)}">
    <input type="hidden" name="lmh" value="{escape(lmh)}">
    <label>精確條件組<select name="group" onchange="this.form.submit()">{options}</select></label>
  </form>
  {chart}
</section>
<section class="panel">
  <div class="section-heading"><div><p class="eyebrow">Paged evidence</p><h2>細節量測</h2></div>
  <p>細節 P/F 是儀器證據，不覆寫上方摘要 Verdict。</p></div>
  {_detail_pager(session_id, clause, test_name, lmh, selected, page, total)}
  <div class="table-scroll"><table>
    <thead><tr><th>Time</th><th>Item</th><th>ARFCN／Freq</th><th>Value</th><th>LSL</th><th>USL</th>
    <th>Margin</th><th>量測狀態</th><th>細節 P/F</th></tr></thead>
    <tbody>{''.join(detail_rows) or '<tr><td colspan="9">這個精確條件組沒有細節列。</td></tr>'}</tbody>
  </table></div>
  {_detail_pager(session_id, clause, test_name, lmh, selected, page, total)}
</section>
"""
    return _page(f"{test_name or head['filename']} 分析", body)


def analysis_compare(
    store: Store,
    filters: AnalysisFilter,
    test_name: str,
    band: str,
    lmh: str,
    group_token: str = "",
) -> str:
    filters, _available = _select_default_scope(store, filters)
    back = _analysis_url(filters)
    if len(filters.scopes) < 2:
        return _page(
            "量測比較",
            f'{site_nav("資料分析")}<div class="empty-state">'
            f'請先在<a href="{back}">分析首頁</a>選取至少兩個資料夾。</div>',
        )
    clause = clause_of(test_name)
    events = store.analysis_events(
        filters.module,
        filters.scopes,
        band=band,
        clause=clause,
    )
    events = list(latest_verdict(events).values())
    wanted = {}
    for row in events:
        row_lmh = row.get("lmh") or str(row.get("channel") or "")
        if row.get("test_name") == test_name and row_lmh == lmh:
            wanted[(row.get("project") or "", row.get("data_folder") or "")] = row

    cohort_data = []
    for scope in filters.scopes:
        event = wanted.get((scope.project, scope.data_folder))
        groups = (
            store.analysis_measurement_groups(event["session_id"], clause)
            if event
            else []
        )
        cohort_data.append((scope, event, groups))

    group_sets = [set(group.signature for group in groups) for _scope, event, groups in cohort_data if event]
    all_present = len(group_sets) == len(filters.scopes)
    common = set.intersection(*group_sets) if all_present and group_sets else set()
    requested = MeasurementGroup.from_token(group_token) if group_token else None
    selected_signature = requested.signature if requested and requested.signature in common else None
    if selected_signature is None and common:
        selected_signature = sorted(common)[0]

    status_cards = []
    for scope, event, _groups in cohort_data:
        status_cards.append(
            '<section class="cohort-card">'
            f'<p class="eyebrow">{escape(scope.project)}</p><h3>{escape(scope.data_folder)}</h3>'
            + (
                f'<p>{_status(event.get("verdict") or "")}</p>'
                f'<p class="muted">{escape(event.get("filename") or "")}</p>'
                if event
                else '<p class="muted">這個 cohort 沒有此摘要測項。</p>'
            )
            + "</section>"
        )

    if selected_signature:
        selected_groups = []
        series = []
        for scope, event, groups in cohort_data:
            group = next(group for group in groups if group.signature == selected_signature)
            selected_groups.append(group)
            rows, _total, _page_no = store.analysis_detail_page(
                event["session_id"], clause, group, 1
            )
            series.append(
                (
                    scope.data_folder,
                    [dict(row, lmh=lmh) for row in rows],
                )
            )
        selected = selected_groups[0]
        chart = svg_comparison(series, selected.unit)
        option_groups = [
            next(group for group in cohort_data[0][2] if group.signature == signature)
            for signature in sorted(common)
        ]
        options = "".join(
            f'<option value="{group.token}"'
            f'{" selected" if group.signature == selected_signature else ""}>'
            f'{escape(_group_label(group))}</option>'
            for group in option_groups
        )
        selector = f"""
<form method="get" action="/analysis/compare" class="group-picker">
  <input type="hidden" name="module" value="{escape(filters.module)}">
  {''.join(f'<input type="hidden" name="scope" value="{escape(scope.token)}">' for scope in filters.scopes)}
  <input type="hidden" name="test" value="{escape(test_name)}">
  <input type="hidden" name="band" value="{escape(band)}">
  <input type="hidden" name="lmh" value="{escape(lmh)}">
  <label>共同精確條件組<select name="group" onchange="this.form.submit()">{options}</select></label>
</form>
"""
        comparison = f"""
<div class="note">所有 cohort 的 Item、Band、BW、SCS、調變、RB、Condition、單位及 LSL／USL 完全一致，因此允許疊圖。</div>
{selector}{chart}
"""
    else:
        panels = []
        for scope, event, groups in cohort_data:
            if not event:
                panels.append(
                    f'<section class="split-chart"><h3>{escape(scope.data_folder)}</h3>'
                    '<div class="empty-state">沒有此摘要測項。</div></section>'
                )
                continue
            if not groups:
                panels.append(
                    f'<section class="split-chart"><h3>{escape(scope.data_folder)}</h3>'
                    '<div class="empty-state">沒有可畫的細節條件組。</div></section>'
                )
                continue
            group = groups[0]
            rows, _total, _page_no = store.analysis_detail_page(
                event["session_id"], clause, group, 1
            )
            plot = svg_lmh([dict(row, lmh=lmh) for row in rows], group.unit)
            panels.append(
                f'<section class="split-chart"><h3>{escape(scope.data_folder)}</h3>'
                f'<p class="muted">{escape(_group_label(group))}</p>{plot}</section>'
            )
        comparison = (
            '<div class="note warning"><b>未疊圖：</b>至少一個 cohort 缺少測項，'
            "或精確條件／限值沒有共同交集。為避免錯誤比較，改用分圖呈現。</div>"
            '<div class="split-charts">' + "".join(panels) + "</div>"
        )

    body = f"""
{site_nav("資料分析")}
<div class="context-strip"><a href="{back}">返回分析</a><span>/</span>
  <b>{escape(filters.module)}</b><span>/</span><span>cohort 比較</span></div>
<div class="page-heading">
  <div><p class="eyebrow">{escape(clause)} · {escape(band)} · {escape(lmh)}</p>
  <h1>{escape(test_name)}</h1></div>
  <p>每個資料夾保留自己的目前狀態。</p>
</div>
<div class="cohort-cards">{''.join(status_cards)}</div>
<section class="panel">
  <div class="section-heading"><div><p class="eyebrow">Measurement comparison</p>
  <h2>精確條件比較</h2></div><p>每個 cohort 最多載入 100 筆圖表點。</p></div>
  {comparison}
</section>
"""
    return _page(f"{test_name} 比較", body)
