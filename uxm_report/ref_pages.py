"""HTML: full TS 38.521-1 chapter 6 / 7 reference index."""

from __future__ import annotations

from html import escape
from urllib.parse import quote

from .prose import prose_html
from .review import _page, site_nav
from .ts38521 import SPEC_DOC, SPEC_ETSI, SPEC_FILE, SPEC_VERSION
from .ts38521_ref import (
    BY_REF,
    CH6_SECTIONS,
    CH7_SECTIONS,
    SECTION_FAMILIES,
    SUFFIXES,
    RefNode,
    has_rfa,
    original_of,
)
from .ts38521_details import detail_of
from .ts38521_figures import figures_for, no_figure_reason
from .ts38521_tables import tables_for

REF521 = "/ref/38.521"


def ref_page(node_id: str = "", chapter: str = "") -> str:
    node = BY_REF.get(node_id) if node_id else None
    if node is None:
        return _index(chapter)
    if node.kind == "chapter":
        return _index(node.id)
    return _detail(node)


def _index(chapter: str) -> str:
    show6 = chapter != "7"
    show7 = chapter != "6"
    body = f"""
{site_nav("3GPP法規參考")}
<p class="muted"><a href="/ref">3GPP法規參考</a> · 38.521</p>
<h1>TS 38.521　UE 射頻符合性　{escape(SPEC_DOC)}</h1>
<div class="note">
這是 <b>38.521</b> 系列（RAN5 怎麼量），不是 <a href="/ref/38.213">38.213</a>（RAN1 功率怎麼算），也不是 <a href="/ref/38.508">38.508</a>（測案環境）。<br>
-1 FR1 射頻（本頁已展開第 6／7 章）· -2 FR2 · -3 互通 · -4 效能。後三本資料夾還沒放 PDF。<br>
{escape(SPEC_ETSI)} · <code>{escape(SPEC_FILE)}</code>。頁碼是印刷頁。<br>
這一頁把<b>第 6 章發射</b>與<b>第 7 章接收</b>整章攤開。數字表能重用「測試規格對照」的就重用。<br>
<b>圖：</b>38.521-1 的 Figure 幾乎都是向量線條，不是內嵌照片，所以不能用抽圖檔的方式取出。有 Figure 的條款已從 V18 PDF 原頁裁出。第 7 章整章沒有 Figure，改寫較細的說明並保留原表；必要時附「示意」（會標明不是原圖）。<br>
沒有字母後綴＝單載波 SA 本體。A–L 是同一測項換組態，見下方對照。<br>
<a href="/spec">測試規格對照</a>只收你 RFA 有跑的條款，並可連資料庫摘要。
</div>
<p class="ch-sw">
  <a{" class='on'" if chapter == "" else ""} href="{REF521}">全部</a>
  <a{" class='on'" if chapter == "6" else ""} href="{REF521}?ch=6">第 6 章　發射</a>
  <a{" class='on'" if chapter == "7" else ""} href="{REF521}?ch=7">第 7 章　接收</a>
</p>
<label class="orig-sw"><input type="checkbox" id="showOrig"> 顯示規格原文</label>
<p class="muted">詳細規格（說明、原圖、表）預設打開。原文用右側懸浮開關，或 Ctrl+Shift+E。</p>
{_suffix_box()}
{"".join(_section_block(sid) for sid in (CH6_SECTIONS if show6 else ()))}
{"".join(_section_block(sid) for sid in (CH7_SECTIONS if show7 else ()))}
{_guide_slot()}
{_css()}
"""
    return _page("3GPP法規參考", body)


def _detail(node: RefNode) -> str:
    orig = original_of(node)
    kids = [BY_REF[c] for c in node.children if c in BY_REF]
    fam = [BY_REF[c] for c in SECTION_FAMILIES.get(node.id, ()) if c in BY_REF]
    rfa = has_rfa(node.id)
    parent = _parent_of(node.id)
    crumb = []
    if node.chapter in BY_REF:
        crumb.append(f'<a href="{REF521}?ch={node.chapter}">第 {node.chapter} 章</a>')
    if parent and parent.id != node.id:
        crumb.append(f'<a href="{REF521}?id={quote(parent.id)}">{escape(parent.id)}</a>')
    crumb.append(escape(node.id))

    child_html = ""
    if kids:
        child_html = "<h3>底下條款</h3><ul class=\"clause-list\">" + "".join(
            _clause_row(c) for c in kids
        ) + "</ul>"
    fam_html = _family_line(fam) if fam else ""
    orig_html = ""
    if orig:
        orig_html = (
            '<div class="spec-orig">'
            f'<p class="muted">TS 38.521-1 V{escape(SPEC_VERSION)} · {escape(node.id)} · 印刷頁 {node.page}</p>'
            f"<pre>{escape(orig)}</pre></div>"
        )
    rfa_html = ""
    if rfa:
        rfa_html = (
            f'<p><a href="/spec?clause={quote(node.id)}">這條在測試規格對照裡</a>'
            "　可連已匯入的 RFA 摘要。</p>"
        )
    body = f"""
{site_nav("3GPP法規參考")}
<p class="muted">{' · '.join(crumb)}</p>
<h1>{escape(node.id)}　{escape(node.title)}</h1>
<p class="muted">{escape(SPEC_DOC)} {escape(SPEC_VERSION)} · 印刷頁 {node.page}</p>
<label class="orig-sw"><input type="checkbox" id="showOrig"> 顯示規格原文</label>
{prose_html(node.brief, "spec-prose spec-brief")}
{_detail_html(node.id)}
{orig_html}
{_figures_html(node.id)}
{_tables_html(node.id)}
{child_html}
{fam_html}
{rfa_html}
{_guide_slot()}
<p class="muted"><a href="{REF521}?ch={node.chapter}">回到第 {node.chapter} 章索引</a>
　·　<a href="/ref">規格號一覽</a></p>
{_css()}
"""
    return _page(f"{node.id} 3GPP法規參考", body)


def _section_block(sid: str) -> str:
    node = BY_REF[sid]
    kids = [BY_REF[c] for c in node.children if c in BY_REF]
    fam = [BY_REF[c] for c in SECTION_FAMILIES.get(sid, ()) if c in BY_REF]
    links = []
    if node.kind != "section" or not kids:
        links.append(_clause_row(node))
    for c in kids:
        links.append(_clause_row(c))
    orig = original_of(node)
    orig_html = ""
    if orig:
        orig_html = (
            '<div class="spec-orig">'
            f"<pre>{escape(orig)}</pre></div>"
        )
    return f"""
<section class="sec">
  <h2><a href="{REF521}?id={quote(node.id)}">{escape(node.id)}　{escape(node.title)}</a>
    <span class="muted">p.{node.page}</span></h2>
  {prose_html(node.brief, "spec-prose spec-brief")}
  {_detail_html(node.id)}
  {orig_html}
  <ul class="clause-list">{''.join(links)}</ul>
  {_family_line(fam)}
</section>
"""


def _clause_row(node: RefNode) -> str:
    badge = ' <span class="rfa">RFA</span>' if has_rfa(node.id) else ""
    return (
        f'<li><a href="{REF521}?id={quote(node.id)}"><code>{escape(node.id)}</code>'
        f"　{escape(node.title)}</a>"
        f'{badge}　<span class="muted">p.{node.page}</span></li>'
    )


def _family_line(fam: list[RefNode]) -> str:
    if not fam:
        return ""
    rows = "".join(_clause_row(n) for n in fam)
    return (
        '<p class="fam"><b>組態變體</b>　字母條款有自己的加總方式、參考點與適用條件，'
        "點進去看，不是本體的一句話摘要。</p>"
        f'<ul class="clause-list fam-list">{rows}</ul>'
    )


def _suffix_box() -> str:
    rows = "".join(
        f"<tr><td>{escape(s or '（無）')}</td><td>{escape(m)}</td><td>{escape(d)}</td></tr>"
        for s, m, d in SUFFIXES
    )
    return f"""
<details class="suf">
<summary>條款編號後面的字母（A–L）是什麼（不是把本體再抄一次）</summary>
<table>
<tr><th>後綴</th><th>組態</th><th></th></tr>
{rows}
</table>
</details>
"""


def _collect_tables(clause_id: str):
    seen: set[str] = set()
    out = []
    ids = [clause_id]
    node = BY_REF.get(clause_id)
    if node:
        ids.extend(node.children)
    for cid in ids:
        for tab in tables_for(cid):
            if tab.tid in seen:
                continue
            seen.add(tab.tid)
            out.append(tab)
    return out


def _detail_html(clause_id: str) -> str:
    return prose_html(detail_of(clause_id), "spec-prose spec-detail")


def _figures_html(clause_id: str) -> str:
    figs = list(figures_for(clause_id))
    node = BY_REF.get(clause_id)
    if node:
        for cid in node.children:
            for fig in figures_for(cid):
                if all(fig.fid != f.fid for f in figs):
                    figs.append(fig)
    if not figs:
        return (
            '<div class="spec-figs">'
            f'<p class="muted">{escape(no_figure_reason(clause_id))}'
            "限值看下面的表與「顯示規格原文」。</p></div>"
        )
    chunks = ['<div class="spec-figs">']
    for fig in figs:
        if fig.is_original:
            src = "/spec-fig/" + fig.png
            body = (
                f'<img src="{escape(src)}" alt="Figure {escape(fig.fid)}" '
                'class="pdf-fig">'
            )
            origin = "從 V18 PDF 原頁裁出"
        else:
            body = fig.svg
            origin = "示意，不是 PDF 原圖"
        chunks.append(
            f'<figure><figcaption>Figure {escape(fig.fid)}　{escape(fig.title)}'
            f'　（印刷頁 {fig.page} · {origin}）</figcaption>{body}'
        )
        if fig.note:
            chunks.append(f'<p class="muted">{escape(fig.note)}</p>')
        chunks.append("</figure>")
    chunks.append("</div>")
    return "".join(chunks)


def _tables_html(clause_id: str) -> str:
    tabs = _collect_tables(clause_id)
    if not tabs:
        return (
            '<div class="spec-tables">'
            '<p class="muted">這一條沒有獨立限值表（void、只指向本體、或細表按 NS／band 展開太長）。'
            "限值對 PDF 或開「顯示規格原文」。A–L 變體用本體那一條的表。</p></div>"
        )
    chunks = [
        '<div class="spec-tables">',
        f'<p class="muted">數值從 TS 38.521-1 V{escape(SPEC_VERSION)} 抄入。空白＝未規定。與 V17 不同處見「R17:」註。'
        "表格從 PDF 逐格抄入，空白＝未規定。有原圖的條款用上面裁出的 Figure。</p>",
    ]
    for tab in tabs:
        notes = "".join(f"<li>{escape(n)}</li>" for n in tab.notes)
        head = "".join(f"<th>{escape(h)}</th>" for h in tab.headers)
        body = "".join(
            "<tr>" + "".join(f"<td>{escape(c)}</td>" for c in row) + "</tr>"
            for row in tab.rows
        )
        chunks.append(
            f"<table><caption>Table {escape(tab.tid)}　{escape(tab.title)}　（印刷頁 {tab.page}）</caption>"
            f"<tr>{head}</tr>{body}</table>"
        )
        if notes:
            chunks.append(f'<ul class="muted">{notes}</ul>')
    chunks.append("</div>")
    return "".join(chunks)


def _guide_slot() -> str:
    return (
        '<div class="guide-slot">'
        "<b>新手導覽</b>　預留。之後每一條會補一段白話：為什麼要量、量的是哪裡、失敗通常代表哪一塊電路。"
        "</div>"
    )


def _parent_of(nid: str) -> RefNode | None:
    if nid in ("6", "7"):
        return BY_REF[nid]
    if nid in CH6_SECTIONS or nid in CH7_SECTIONS:
        return BY_REF[nid[0]]
    if "." in nid:
        parent_id = nid.rsplit(".", 1)[0]
        return BY_REF.get(parent_id) or BY_REF.get(nid[0])
    return BY_REF.get(nid[0])


def _css() -> str:
    return """
<style>
.ch-sw { margin:12px 0; }
.ch-sw a { display:inline-block; margin:0 8px 0 0; padding:4px 10px; border:1px solid #ccc;
  text-decoration:none; color:#222; font-size:13px; }
.ch-sw a.on { background:#008787; color:#fff; border-color:#008787; }
.orig-sw { font-weight:normal; color:#666; font-size:13px; margin-right:12px; }
.spec-orig { display:none; border-left:3px solid #008787; background:#f3faf9;
  padding:8px 12px; margin:12px 0; }
.spec-orig pre { white-space:pre-wrap; font-family:Segoe UI, Microsoft JhengHei, sans-serif;
  font-size:13px; margin:8px 0 0; color:#222; }
body:has(#showOrig:checked) .spec-orig { display:block; }
.spec-tables { display:block; margin:16px 0; }
.spec-tables table { font-size:12px; }
.spec-tables caption, .spec-figs figcaption { text-align:left; font-weight:600;
  padding:8px 0 4px; color:#008787; }
.spec-figs figure { margin:12px 0 20px; }
.spec-figs .pdf-fig { display:block; max-width:100%; height:auto; border:1px solid #ddd; background:#fff; }
.spec-prose { max-width:40em; margin:8px 0 16px; color:#222; }
.spec-prose p { margin:0 0 0.75em; line-height:1.75; }
.spec-prose p:last-child { margin-bottom:0; }
.spec-prose ul { margin:0 0 0.75em; padding-left:1.3em; line-height:1.75; }
.spec-brief { color:#333; }
.spec-detail { padding:10px 14px 12px; background:#f7fafa; border-left:3px solid #008787; }
.sec { margin:22px 0 28px; padding-top:8px; border-top:1px solid #e5e5e5; }
.sec h2 { font-size:18px; margin:0 0 6px; }
.sec h2 a { text-decoration:none; color:#008787; }
.clause-list { list-style:none; padding:0; margin:8px 0 12px; }
.clause-list li { margin:4px 0; line-height:1.45; }
.clause-list a { text-decoration:none; }
.clause-list code { font-size:13px; }
.rfa { font-size:10px; color:#008787; border:1px solid #008787; padding:0 3px; margin-left:2px; }
.fam { font-size:13px; color:#444; margin:12px 0 0; }
.fam-list { margin-top:4px; }
.suf { margin:12px 0 20px; font-size:13px; color:#444; }
.suf summary { cursor:pointer; color:#008787; }
.kids { font-size:14px; }
.guide-slot { margin:24px 0 8px; padding:10px 12px; border:1px dashed #bbb;
  color:#888; font-size:13px; background:#fafafa; }
</style>
"""
