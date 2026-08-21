"""HTML: 38.521-1 clause guide mapped to RFA items and imported verdicts."""

from __future__ import annotations

from html import escape
from urllib.parse import quote

from .prose import prose_html
from .review import _page, site_nav
from .store import Store
from .ts38521 import (
    BY_ID,
    CHAPTERS,
    CLAUSES,
    SPEC_DIR,
    SPEC_DOC,
    SPEC_ETSI,
    SPEC_FALLBACK_FILE,
    SPEC_FALLBACK_VERSION,
    SPEC_FILE,
    SPEC_VERSION,
    clauses_in,
    spec_folder,
)
from .ts38521_details import detail_of
from .ts38521_figures import figures_for, no_figure_reason
from .ts38521_tables import tables_for


def _nav() -> str:
    return site_nav("測試規格對照")


def spec_page(store: Store, module: str, project: str, clause_id: str) -> str:
    spec = BY_ID.get(clause_id, CLAUSES[0])
    folder = spec_folder()
    mods = store.list_modules()
    projects = store.list_projects(module) if module else []
    stats = store.clause_stats(module, project) if module and project else []
    live = _live_for(spec, stats) if stats else []

    chap_html = []
    for chap in CHAPTERS:
        links = []
        for c in clauses_in(chap):
            href = _href(module, project, c.id)
            on = ' class="on"' if c.id == spec.id else ""
            links.append(f'<a{on} href="{href}">{escape(c.id)}</a>')
        chap_html.append(
            f"<p class=\"clause-nav\"><b>{escape(chap)}</b><br>{' '.join(links)}</p>"
        )

    extra_note = ""
    if folder.extra:
        extra_note = (
            "<br>備援："
            + escape("、".join(p.name for p in folder.extra))
            + "。條款與表格以 "
            + escape(SPEC_FILE)
            + "（"
            + SPEC_VERSION
            + "）為準；新版找不到的才回看 "
            + escape(SPEC_FALLBACK_FILE)
            + "（"
            + SPEC_FALLBACK_VERSION
            + "）。有差異的格子用「R17:」註記。"
        )
    if not folder.expected.is_file():
        extra_note += (
            "<br><b>找不到預期檔名 "
            + escape(SPEC_FILE)
            + "。</b>條款卡仍可用，但請把目前那本放到 "
            + escape(str(SPEC_DIR))
            + "。"
        )

    mod_opts = ['<option value="">（不連資料庫）</option>']
    for m in mods:
        sel = " selected" if m["model"] == module else ""
        mod_opts.append(
            f'<option value="{escape(m["model"])}"{sel}>{escape(m["model"])}</option>'
        )
    proj_opts = ['<option value="">選擇專案</option>']
    for p in projects:
        sel = " selected" if p["name"] == project else ""
        proj_opts.append(
            f'<option value="{escape(p["name"])}"{sel}>{escape(p["name"])}</option>'
        )

    tests = "".join(f"<li>{escape(t)}</li>" for t in spec.rfa_tests)
    items = "".join(f"<li>{escape(i)}</li>" for i in spec.items)

    skip = f"<p><b>Skip</b>　{escape(spec.skip)}</p>" if spec.skip else ""
    watch = f"<p><b>以後分析時先看</b>　{escape(spec.watch)}</p>" if spec.watch else ""

    body = f"""
{_nav()}
<h1>測試規格對照　{escape(SPEC_DOC)}</h1>
<div class="note">
來源：<code>{escape(str(SPEC_DIR))}</code> 裡的 <b>{escape(SPEC_FILE)}</b>。<br>
版本 {escape(SPEC_ETSI)}。頁碼是 PDF 印在頁腳的印刷頁。<br>
這裡只對你 RFA 有跑的單載波 SA 條款，並可連到已匯入的摘要結果。<br>
第六章／第七章完整索引在 <a href="/ref/38.521">TS 38.521</a>。功率公式在 <a href="/ref/38.213">TS 38.213</a>。
{extra_note}
</div>
<form method="get" action="/spec" class="row">
  <input type="hidden" name="clause" value="{escape(spec.id)}">
  <label>模組 <select name="module" onchange="this.form.submit()">{''.join(mod_opts)}</select></label>
  <label>專案 <select name="project" onchange="this.form.submit()">{''.join(proj_opts)}</select></label>
  <label class="orig-sw"><input type="checkbox" id="showOrig"> 顯示規格原文</label>
  <label class="orig-sw"><input type="checkbox" id="showTables"> 顯示詳細規格</label>
</form>
<div class="spec-wrap">
  <aside>{''.join(chap_html)}</aside>
  <section>
    <h2>{escape(spec.id)}　{escape(spec.title)}</h2>
    <p class="muted">{escape(spec.chapter)} · {escape(SPEC_DOC)} {escape(SPEC_VERSION)} · 印刷頁 {spec.page}</p>
    {prose_html(spec.purpose, "spec-prose spec-brief")}
    <div class="spec-orig">
      <p class="muted">TS 38.521-1 V{escape(SPEC_VERSION)} · {escape(spec.id)} · 印刷頁 {spec.page}（Test purpose／必要適用條件，非整章）</p>
      <pre>{escape(spec.original)}</pre>
    </div>
    {_detail_html(spec.id)}
    {_figures_html(spec.id)}
    {_tables_html(spec.id)}
    {skip}
    {watch}
    <p class="muted">{escape(spec.extra)}</p>
    <h3>對到的 RFA 測項</h3>
    <ul>{tests}</ul>
    <h3>細節列常見 Item</h3>
    <ul>{items}</ul>
    {_stats_table(spec, live, module, project)}
  </section>
</div>
<style>
.spec-wrap {{ display:flex; gap:28px; align-items:flex-start; }}
aside {{ min-width:200px; max-width:240px; font-size:13px; }}
.clause-nav {{ margin:0 0 12px; }}
.clause-nav a {{ display:inline-block; margin:2px 4px 2px 0; padding:2px 6px;
  border:1px solid #ccc; text-decoration:none; color:#222; font-size:12px; }}
.clause-nav a.on {{ background:#008787; color:#fff; border-color:#008787; }}
.row label {{ margin-right:12px; }}
.orig-sw {{ font-weight:normal; color:#666; font-size:13px; margin-left:8px; }}
.spec-orig {{ display:none; border-left:3px solid #008787; background:#f3faf9;
  padding:8px 12px; margin:12px 0; }}
.spec-orig pre {{ white-space:pre-wrap; font-family:Segoe UI, Microsoft JhengHei, sans-serif;
  font-size:13px; margin:8px 0 0; color:#222; }}
body:has(#showOrig:checked) .spec-orig {{ display:block; }}
.spec-tables {{ display:none; margin:16px 0; }}
.spec-tables table {{ font-size:12px; }}
.spec-tables caption {{ text-align:left; font-weight:600; padding:8px 0 4px; color:#008787; }}
body:has(#showTables:checked) .spec-tables {{ display:block; }}
.spec-figs .pdf-fig {{ display:block; max-width:100%; height:auto; border:1px solid #ddd; background:#fff; }}
.spec-prose {{ max-width:40em; margin:8px 0 16px; color:#222; }}
.spec-prose p {{ margin:0 0 0.75em; line-height:1.75; }}
.spec-prose p:last-child {{ margin-bottom:0; }}
.spec-detail {{ padding:10px 14px 12px; background:#f7fafa; border-left:3px solid #008787; }}
</style>
"""
    return _page(f"{spec.id} 測試規格對照", body)


def _detail_html(clause_id: str) -> str:
    return prose_html(detail_of(clause_id), "spec-tables spec-prose spec-detail")


def _figures_html(clause_id: str) -> str:
    figs = list(figures_for(clause_id))
    if not figs:
        return (
            '<div class="spec-tables spec-figs">'
            f'<p class="muted">{escape(no_figure_reason(clause_id))}</p></div>'
        )
    chunks = ['<div class="spec-tables spec-figs">']
    for fig in figs:
        if fig.is_original:
            body = (
                f'<img src="/spec-fig/{escape(fig.png)}" '
                f'alt="Figure {escape(fig.fid)}" class="pdf-fig">'
            )
            origin = "從 V18 PDF 原頁裁出"
        else:
            body = fig.svg
            origin = "示意，不是 PDF 原圖"
        chunks.append(
            f'<figure><figcaption>Figure {escape(fig.fid)}　{escape(fig.title)}'
            f'　（印刷頁 {fig.page} · {origin}）</figcaption>{body}</figure>'
        )
        if fig.note:
            chunks.append(f'<p class="muted">{escape(fig.note)}</p>')
    chunks.append("</div>")
    return "".join(chunks)


def _tables_html(clause_id: str) -> str:
    tabs = tables_for(clause_id)
    if not tabs:
        return (
            '<div class="spec-tables">'
            '<p class="muted">這一條還沒有抽出數值表。限值請先對 PDF 或開「顯示規格原文」。'
            "之後換版再補。</p></div>"
        )
    chunks = [
        '<div class="spec-tables">',
        f'<p class="muted">以下數值從 TS 38.521-1 V{escape(SPEC_VERSION)} 印刷表逐格抄入。空白＝該格未規定。'
        f"與 V{escape(SPEC_FALLBACK_VERSION)} 不同的地方用「R17:」註記。仍以 PDF 為準。</p>",
    ]
    for tab in tabs:
        notes = "".join(f"<li>{escape(n)}</li>" for n in tab.notes)
        head = "".join(f"<th>{escape(h)}</th>" for h in tab.headers)
        body = []
        for row in tab.rows:
            tds = "".join(f"<td>{escape(c)}</td>" for c in row)
            body.append(f"<tr>{tds}</tr>")
        chunks.append(
            f"<table><caption>Table {escape(tab.tid)}　{escape(tab.title)}　"
            f"（印刷頁 {tab.page}）</caption>"
            f"<tr>{head}</tr>{''.join(body)}</table>"
        )
        if notes:
            chunks.append(f"<ul class=\"muted\">{notes}</ul>")
    chunks.append("</div>")
    return "".join(chunks)


def _href(module: str, project: str, clause: str) -> str:
    q = "/spec?clause=" + quote(clause)
    if module:
        q += "&module=" + quote(module)
    if project:
        q += "&project=" + quote(project)
    return q


def _live_for(spec, stats: list[dict]) -> list[dict]:
    out = []
    wanted = set(spec.rfa_tests)
    for row in stats:
        name = row["test_name"]
        if name in wanted or name.startswith(spec.id):
            out.append(row)
    return out


def _stats_table(spec, live: list[dict], module: str, project: str) -> str:
    if not module or not project:
        return (
            "<h3>這個專案的摘要結果</h3>"
            '<p class="muted">上面選模組與專案後，才會用已匯入的摘要列對這一條。</p>'
        )
    if not live:
        return (
            f"<h3>{escape(module)} · {escape(project)}</h3>"
            f'<p class="muted">這個專案的摘要列沒有 {escape(spec.id)}。</p>'
        )
    bands: dict[str, dict[str, int]] = {}
    names: set[str] = set()
    for row in live:
        names.add(row["test_name"])
        bucket = bands.setdefault(row["band"] or "?", {"Pass": 0, "Fail": 0, "Skip": 0, "other": 0})
        v = (row["verdict"] or "").strip()
        key = v if v in bucket else "other"
        bucket[key] += row["n"]
    trs = []
    for band in sorted(bands):
        c = bands[band]
        trs.append(
            "<tr>"
            f"<td>{escape(band)}</td>"
            f"<td class=\"pass\">{c['Pass']}</td>"
            f"<td class=\"fail\">{c['Fail']}</td>"
            f"<td class=\"skip\">{c['Skip']}</td>"
            f"<td class=\"muted\">{c['other']}</td>"
            "</tr>"
        )
    shown = "、".join(sorted(names))
    return f"""
<h3>{escape(module)} · {escape(project)}　摘要列</h3>
<p class="muted">對到：{escape(shown)}。數字是摘要列次數（含 Low／Mid／High 各一列），不是細節點。</p>
<table>
<tr><th>Band</th><th>Pass</th><th>Fail</th><th>Skip</th><th>其他</th></tr>
{''.join(trs)}
</table>
"""
