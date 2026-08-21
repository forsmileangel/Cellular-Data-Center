"""3GPP reference hub and family pages (38.508, 38.213)."""

from __future__ import annotations

from html import escape

from .gloss import gloss_css, gloss_shell, gloss_term
from .prose import prose_html
from .review import _page, site_nav
from .spec_families import FAMILIES, family_by_slug
from .ts38213_notes import panels_html


def ref_dispatch(path: str, node_id: str = "", chapter: str = "") -> str:
    """path is '' (hub), '38.521', '38.508', or '38.213'."""
    slug = (path or "").strip("/")
    if slug in ("", "index"):
        return hub_page()
    if slug == "38.521":
        from .ref_pages import ref_page

        return ref_page(node_id, chapter)
    if slug == "38.508":
        return page_38508()
    if slug == "38.213":
        return page_38213()
    return hub_page()


def hub_page() -> str:
    cards = "".join(_card(f) for f in FAMILIES)
    body = f"""
{site_nav("3GPP法規參考")}
<h1>3GPP法規參考</h1>
<div class="note">
依<b>主要規格號</b>分頁。同一號的 -1／-2／-3／-4 留在同一頁；不同號（38.521、38.508、38.213）分開。
{prose_html("38.521 是 RAN5 射頻怎麼量。38.213 是 RAN1 功率與控制程序怎麼算。38.508 是測案共用環境。三本不要混。資料夾沒有 38.212（通道編碼）；38.213 會引用它。")}
</div>
<div class="fam-cards">{cards}</div>
{_css()}
"""
    return _page("3GPP法規參考", body)


def _card(fam) -> str:
    parts = "".join(
        f"<li><code>{escape(n)}</code>　{escape(d)}</li>" for n, d in fam.parts
    )
    return f"""
<a class="fam-card" href="{escape(fam.href)}">
  <strong>{escape(fam.number)}</strong>
  <span class="t">{escape(fam.title_zh)}</span>
  <span class="b">{escape(fam.blurb)}</span>
  <ul>{parts}</ul>
</a>
"""


def page_38508() -> str:
    fam = family_by_slug("38.508")
    assert fam is not None
    body = f"""
{site_nav("3GPP法規參考")}
<p class="muted"><a href="/ref">3GPP法規參考</a> · 38.508</p>
<h1>TS 38.508　UE 符合性共用測試環境</h1>
<p class="muted">{escape(fam.title_en)}</p>
<label class="orig-sw"><input type="checkbox" id="showOrig"> 顯示規格原文</label>
{prose_html(fam.scope_zh, "spec-prose spec-brief")}
<div class="spec-orig">
  <p class="muted">TS 38.508-1 V17.6.0 · 印刷頁 29 · Scope</p>
  <pre>{escape(fam.scope_en)}</pre>
</div>
{_files(fam)}
<h2>這本跟 38.521、38.213 差在哪</h2>
{prose_html(
    "38.508-1 不寫功率公式，也不寫 SEM／REFSENS 限值。"
    "它規定測案共用的環境：測試頻率、通道頻寬、訊息內容、EN-DC 組合、適用條件。"
    "38.521-1 各條的 Test configuration 會寫「依 38.508-1 子條款 4.x」。"
    "38.508-1 的參考清單也點到 38.521-1～4、38.213、38.101。"
)}
<p><a href="/ref/38.521">打開 TS 38.521</a>　·　<a href="/ref/38.213">打開 TS 38.213</a></p>
<h2>第 1／2 部分</h2>
{prose_html(
    "第 1 部分（本中心有 PDF）：共用測試環境。"
    "第 2 部分：ICS 聲明表，資料夾還沒放。"
    "LTE 對應本是 36.508，不是 38.508。"
)}
<h2>資料夾裡的版本</h2>
{prose_html(
    "主檔用 V17.6.0（2022-10，1247 頁）。"
    "V15.4.0 是較早的 Rel-15（671 頁），封面標 Note。"
    "V17 明顯加厚的是 EN-DC／CA 組合與測點表，不是把 Scope 改掉。"
)}
{_css()}
"""
    return _page("TS 38.508 3GPP法規參考", body)


def page_38213() -> str:
    fam = family_by_slug("38.213")
    assert fam is not None
    tci = gloss_term("unified-tci", "unified TCI")
    srs2 = gloss_term("srs2", "第二套 SRS")
    msga = gloss_term("msga", "MsgA")
    redcap = gloss_term("redcap-p0", "RedCap")
    read_v = gloss_term("v15-v17-read", "V15 與 V17 各解什麼")
    body = f"""
{site_nav("3GPP法規參考")}
<p class="muted"><a href="/ref">3GPP法規參考</a> · 38.213</p>
<h1>TS 38.213　NR 實體層控制程序</h1>
<p class="muted">ETSI TS 138 213 V17.3.0 (2022-09)　·　主檔 <code>ts_138213v170300p.pdf</code></p>
<label class="orig-sw"><input type="checkbox" id="showOrig"> 顯示規格原文</label>
{prose_html(fam.scope_zh, "spec-prose spec-brief")}
<div class="spec-orig">
  <p class="muted">TS 38.213 V17.3.0 · 印刷頁 7 · Scope</p>
  <pre>{escape(fam.scope_en)}</pre>
</div>
<div class="note">
這不是 38.521。38.213 第 7 章告訴 UE「PUSCH／PUCCH／PRACH／SRS 該算出多少 dBm」；
38.521-1 第 6 章量「算出來之後，天線接頭上的功率、mask、TPC 步階過不過」。
PCMAX 的數字在 38.101-1，測法在 <a href="/ref/38.521?id=6.2.4">38.521-1 6.2.4</a>。
資料夾沒有 38.212（Multiplexing and channel coding）；38.213 算層數／SRI 時會引用它。
</div>
{_files(fam)}

<h2>第 7 章　Uplink power control</h2>
{prose_html(
    "V17 印刷頁 20 起。這是本中心要留的功率論述。"
    "公式依 BWP（b）、載波（f）、服務細胞（c）來算，再跟 PCMAX 取較小。"
)}
<table>
<tr><th>條款</th><th>通道</th><th></th></tr>
<tr><td>7.1</td><td>PUSCH</td><td>資料通道。開環 P0＋α·PL，再加 RB 數、ΔTF、閉環 f(i)。</td></tr>
<tr><td>7.2</td><td>PUCCH</td><td>控制通道。路徑損耗通常全補償（沒有 α&lt;1 那一項的同樣寫法），另有格式偏移 ΔF。</td></tr>
<tr><td>7.3</td><td>SRS</td><td>探測。自己的 P0／α／閉環狀態。</td></tr>
<tr><td>7.4</td><td>PRACH</td><td>min(PCMAX, 目標接收功率 + 路徑損耗)。RFA 名稱裡的 −118／−124 就是目標，不是頻段。</td></tr>
<tr><td>7.5</td><td>優先序</td><td>總功率不夠時先砍誰（PRACH／PUCCH／PUSCH／SRS）。</td></tr>
<tr><td>7.6</td><td>雙連線</td><td>EN-DC、NE-DC、NR-DC 兩邊 UL 怎麼分功率。</td></tr>
<tr><td>7.7</td><td>PHR</td><td>Type 1 PUSCH、Type 2 PUCCH、Type 3 SRS 的功率餘裕回報。</td></tr>
</table>

<h3>PUSCH（7.1.1）</h3>
{prose_html(
    "UE 在作用中 UL BWP 上發 PUSCH 時，發射功率是 PCMAX 與開環＋閉環之和的較小值。"
    "開環：標稱 P0（網路目標）加 UE 專用偏移，乘上路徑損耗係數 α，再加上以 2^μ·M_RB 計的頻寬項與調變偏移 ΔTF。"
    "閉環：TPC 累積狀態 f(i,l)，可以有兩套 l。"
    "路徑損耗 PL 來自指定的下行參考（q_d），通常是 SSB 或 CSI-RS，不是 LTE 那種永遠在的 CRS。"
    "PCMAX 定義在 38.101-1／-2／-3，符合性測法見 38.521-1 6.2.4。"
)}
<div class="spec-orig">
  <p class="muted">TS 38.213 V17.3.0 · 7.1.1 · 印刷頁 22（公式結構）</p>
  <pre>P_PUSCH,b,f,c(i,j,q_d,l) = min{{
  P_CMAX,f,c(i),
  P_O_PUSCH,b,f,c(j) + 10log10(2^μ · M_RB,b,f,c(i))
    + α_b,f,c(j) · PL_b,f,c(q_d) + Δ_TF,b,f,c(i) + f_b,f,c(i,l)
}}  [dBm]
P_CMAX,f,c(i) is the UE configured maximum output power defined in
TS 38.101-1 / 38.101-2 / 38.101-3.</pre>
</div>
<p class="cross"><a href="/ref/38.521?id=6.2.4">對照 38.521-1 6.2.4 Configured transmitted power</a>
　·　<a href="/ref/38.521?id=6.3.4">TPC 步階測法 6.3.4</a></p>

<h3>PUCCH（7.2.1）</h3>
{prose_html(
    "結構類似 PUSCH，但用 P_O_PUCCH 與閉環 g(i,l)，並加上 PUCCH 格式偏移 ΔF_PUCCH(F)。"
    "路徑損耗一般按全補償來寫。"
    "格式 0–4 的 ΔF 不同；這是 38.213 的事。38.521 量的是打出來之後 ON/OFF 與功率容差。"
)}
<div class="spec-orig">
  <p class="muted">TS 38.213 V17.3.0 · 7.2.1（公式結構）</p>
  <pre>P_PUCCH,b,f,c(i,q_u,q_d,l) = min{{
  P_CMAX,f,c(i),
  P_O_PUCCH,b,f,c(q_u) + 10log10(2^μ · M_RB,b,f,c(i))
    + PL_b,f,c(q_d) + Δ_F_PUCCH(F) + Δ_TF,b,f,c(i) + g_b,f,c(i,l)
}}  [dBm]</pre>
</div>

<h3>PRACH（7.4）</h3>
{prose_html(
    "前導功率是目標接收電平加路徑損耗，再與 PCMAX 取小。"
    "RFA 測項名稱後面的 −118／−124 是 preambleReceivedTargetPower，不是 n118。"
    "38.521-1 6.3.3.4 量的是這次發射的 time mask，不重算 38.213 的公式。"
)}
<div class="spec-orig">
  <p class="muted">TS 38.213 V17.3.0 · 7.4（公式結構）</p>
  <pre>P_PRACH,b,f,c(i) = min{{ P_CMAX,f,c(i),  P_PRACH,target,f,c + PL_b,f,c }}  [dBm]</pre>
</div>
<p class="cross"><a href="/ref/38.521?id=6.3.3.4">對照 38.521-1 6.3.3.4 PRACH time mask</a></p>

<h2>1. LTE（36.213）跟 5G-NR（38.213）差在哪</h2>
{prose_html(
    "LTE 功率在 TS 36.213 第 5.1 章（本中心檔案 ts_136213v150500p，V15.5.0）。"
    "NR 功率在 TS 38.213 第 7 章。兩本都是實體層程序，都不是射頻符合性。"
)}
<table>
<tr><th></th><th>LTE 36.213</th><th>NR 38.213 V17</th></tr>
<tr><td>條款</td><td>5.1 PUSCH／PUCCH／SRS；PRACH 在第 6 章</td><td>7.1–7.4 把四種通道放在同一章</td></tr>
<tr><td>索引</td><td>多半只有服務細胞 c</td><td>BWP b、載波 f、細胞 c</td></tr>
<tr><td>頻寬項</td><td>10log10(M_PUSCH)，SCS 固定 15 kHz</td><td>10log10(2^μ · M_RB)，μ 隨 SCS 變</td></tr>
<tr><td>路徑損耗</td><td>通常用 CRS</td><td>可選 SSB 或 CSI-RS（q_d）；V17 還可跟 {tci} 綁在一起</td></tr>
<tr><td>開環／閉環</td><td>一套 P0、α、f(i)</td><td>多套 j、兩套閉環 l；還有 SRI、兩組 SRS resource set</td></tr>
<tr><td>PRACH</td><td>preambleInitialReceivedTargetPower 加每次重試遞增</td><td>目標＋PL，再受 7.5 優先序與雙連線 7.6 約束</td></tr>
<tr><td>雙連線</td><td>5.1.4 EUTRA DC Mode 1／2</td><td>7.6 EN-DC／NE-DC／NR-DC</td></tr>
<tr><td>PCMAX</td><td>36.101</td><td>38.101-1／-2／-3，測法 38.521-1 6.2.4</td></tr>
</table>
<div class="spec-orig">
  <p class="muted">TS 36.213 V15.5.0 · 5.1.1（LTE PUSCH 結構）</p>
  <pre>P_PUSCH,c(i) = min{{
  P_CMAX,c(i),
  10log10(M_PUSCH,c(i)) + P_O_PUSCH,c(j) + α_c(j)·PL_c + Δ_TF,c(i) + f_c(i)
}}  [dBm]</pre>
</div>

<h2>2. 38.213 V15 跟 V17 差在哪</h2>
{prose_html(
    "主檔是 V17.3.0（262 頁）。對照本是 V15.8.0（112 頁）。"
    "第 7 章目錄骨架沒變：仍是 7.1 PUSCH … 7.7 PHR。"
    "變厚的是參數怎麼對到 RRC／DCI，不是把 PUSCH 公式改成另一個形狀。"
)}
<table>
<tr><th></th><th>V15.8.0</th><th>V17.3.0</th></tr>
<tr><td>篇幅</td><td>112 頁；功率從印刷頁 14</td><td>262 頁；功率從印刷頁 20</td></tr>
<tr><td>第 7 章骨架</td><td>7.1–7.7 已齊</td><td>同樣 7.1–7.7</td></tr>
<tr><td>PUSCH 公式</td><td>已是 min(PCMAX, P0+10log10(2^μ M)+αPL+ΔTF+f)</td><td>同一形狀；多了 {srs2}、p0-PUSCH-Alpha2、SRI 欄位對兩套 P0</td></tr>
<tr><td>TCI／路徑損耗</td><td>PL-RS 個別設定</td><td>可跟 {tci}（dl-OrJoint-TCIStateList-r17）走同一套 PL-RS／P0</td></tr>
<tr><td>兩步 RACH</td><td>Msg3 為主</td><td>補 msgA-Alpha、O_PRE 等 {msga} 功率</td></tr>
<tr><td>本體後面</td><td>寫到 Rel-15 控制程序</td><td>第 16 章側鏈、第 17 章 RedCap、第 18 章 MBS、第 19 章 RRC_INACTIVE 的 PUSCH</td></tr>
</table>
<p>看功率時：V15 就能解釋 RFA 報表上的 PUSCH／PUCCH／PRACH 目標。
V17 要看的是 {tci}、{srs2}、{msga}、{redcap} 會不會改你用的那一組 P0／α。
{read_v}</p>

<h2>3. 資料夾裡的 V18（先標註）</h2>
{prose_html(
    "ETSI-TS-138-213-V18-4-0-2024-10-.pdf 只有 14 頁，是不完整預覽，不能當主檔。"
    "目錄還看得到第 7 章仍叫 Uplink Power control，並多了 Rel-18 條目。"
    "新東西只先記下，等完整 PDF 再核對內文。"
)}
<table>
<tr><th>目錄上看得到</th><th>先標註</th></tr>
<tr><td>Configured-grant PUSCH in RACH-less LTM cell switch</td><td>Rel-18 LTM 無 RACH 切細胞時的 CG PUSCH</td></tr>
<tr><td>17.1A Second procedures for RedCap UE</td><td>RedCap 第二套程序</td></tr>
<tr><td>16.4A PSCCH in dedicated SL PRS resource pool</td><td>側鏈定位資源</td></tr>
<tr><td>in-device coexistence and co-channel coexistence</td><td>共存從 16.7 加寫</td></tr>
</table>
{prose_html("主檔維持 V17.3.0。V18 完整檔進來後再比第 7 章有沒有改公式。")}

<h2>跟 38.521-1 怎麼對讀</h2>
<table>
<tr><th>38.213 在算</th><th>38.521-1 在量</th></tr>
<tr><td>P_CMAX,f,c</td><td><a href="/ref/38.521?id=6.2.4">6.2.4</a>、上限對 <a href="/ref/38.521?id=6.2.1">6.2.1</a></td></tr>
<tr><td>閉環 TPC f(i)／g(i)</td><td><a href="/ref/38.521?id=6.3.4.2">6.3.4.2</a> 絕對、 <a href="/ref/38.521?id=6.3.4.3">6.3.4.3</a> 相對、 <a href="/ref/38.521?id=6.3.4.4">6.3.4.4</a> 累積</td></tr>
<tr><td>PRACH 目標＋PL</td><td><a href="/ref/38.521?id=6.3.3.4">6.3.3.4</a> time mask</td></tr>
<tr><td>最小／OFF 功率</td><td><a href="/ref/38.521?id=6.3.1">6.3.1</a>、<a href="/ref/38.521?id=6.3.2">6.3.2</a></td></tr>
</table>
<p><a href="/ref/38.508">測案環境見 TS 38.508</a></p>
{panels_html()}
{gloss_shell()}
{_css()}
"""
    return _page("TS 38.213 3GPP法規參考", body)


def _files(fam) -> str:
    rows = "".join(
        f"<tr><td><code>{escape(f.name)}</code></td>"
        f"<td>{escape(f.label)}</td><td>{escape(f.note)}</td></tr>"
        for f in fam.files
    )
    return f"""
<h2>本中心檔案</h2>
<table>
<tr><th>檔名</th><th>版本</th><th></th></tr>
{rows}
</table>
"""


def _css() -> str:
    return """
<style>
.fam-cards { display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:14px; margin:18px 0; }
.fam-card { display:block; padding:16px 16px 12px; border:1px solid #ccc; text-decoration:none;
  color:#222; background:#fff; min-height:168px; }
.fam-card:hover { border-color:#afbeaf; }
.fam-card strong { display:block; color:var(--green-deep); font-size:16px; margin-bottom:4px; }
.fam-card .t { display:block; font-size:14px; margin:0 0 8px; }
.fam-card .b { display:block; color:#666; font-size:12px; line-height:1.45; margin-bottom:8px; }
.fam-card ul { margin:0; padding-left:1.1em; color:#444; font-size:12px; line-height:1.45; }
.orig-sw { font-weight:normal; color:#666; font-size:13px; }
.spec-orig { display:none; border-left:3px solid var(--green); background:var(--green-soft);
  padding:8px 12px; margin:12px 0; }
.spec-orig pre { white-space:pre-wrap; font-family:Segoe UI, Microsoft JhengHei, sans-serif;
  font-size:13px; margin:8px 0 0; color:#222; }
body:has(#showOrig:checked) .spec-orig { display:block; }
.spec-prose { max-width:40em; margin:8px 0 16px; }
.spec-prose p { margin:0 0 0.75em; line-height:1.75; }
.spec-prose p:last-child { margin-bottom:0; }
.cross { font-size:13px; }
table { font-size:13px; }
""" + gloss_css() + """
</style>
"""
