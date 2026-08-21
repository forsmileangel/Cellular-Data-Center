"""HTML review of stored sessions and first-pass 3GPP interpretation."""

from __future__ import annotations

from collections import defaultdict
from html import escape
from urllib.parse import quote

from .lineage import build_links
from .store import Store

NAV_ITEMS = (
    ("/", "首頁"),
    ("/import", "報告匯入"),
    ("/db", "測試資料庫"),
    ("/review", "資料審核"),
    ("/analysis", "資料分析"),
    ("/spec", "測試規格對照"),
    ("/ref", "3GPP法規參考"),
)


def nav_parts(current: str = "", extra: str = "") -> str:
    bits = []
    for href, label in NAV_ITEMS:
        if label == current:
            bits.append(f"<b>{label}</b>")
        else:
            bits.append(f'<a href="{href}">{label}</a>')
    text = " · ".join(bits)
    if extra:
        text += " · " + extra
    return text


def site_nav(current: str = "", extra: str = "") -> str:
    return f'<div class="nav">{nav_parts(current, extra)}</div>'

CSS = """
:root { --green:#008787; --ink:#222; --muted:#666; --line:#ccc; --bg:#f6f6f6; --fail:#8b0000; --skip:#8a6d00; }
* { box-sizing:border-box; }
body { margin:0; font-family:Segoe UI, Microsoft JhengHei, sans-serif; color:var(--ink); background:var(--bg); }
main { max-width:1200px; margin:24px auto; background:#fff; border:1px solid var(--line); padding:24px 28px; }
h1 { margin:0 0 8px; font-size:22px; color:var(--green); }
a { color:var(--green); }
.nav { margin-bottom:16px; font-size:14px; }
.nav b { font-weight:700; }
.note { background:#f3faf9; border:1px solid #c5e3e0; padding:10px 12px; font-size:13px; margin:12px 0 18px; }
table { border-collapse:collapse; width:100%; font-size:13px; }
th, td { border:1px solid var(--line); padding:5px 7px; text-align:left; vertical-align:top; }
th { background:#eef6f6; }
.fail { color:var(--fail); font-weight:600; }
.skip { color:var(--skip); }
.pass { color:#1a6b1a; }
.err { color:#8b0000; }
.ok { color:#008787; }
.muted { color:var(--muted); font-size:12px; }
.meta { font-size:14px; margin:0 0 12px; }
.filters a { margin-right:10px; }
.bar { display:inline-block; position:relative; width:90px; height:10px; background:#eee; border:1px solid #ccc; vertical-align:middle; }
.bar .fill { position:absolute; top:-3px; width:6px; height:14px; background:#008787; margin-left:-3px; }
.super { color:#777; }
.super .fail { color:#a66; font-weight:normal; }
button.danger { background:#fff; color:#8b0000; border:1px solid #8b0000; padding:4px 8px; cursor:pointer; font-size:12px; }
.srv-off { position:fixed; top:6px; right:10px; z-index:20; font-size:11px; color:#aaa; max-width:160px; }
.srv-off summary { cursor:pointer; list-style:none; color:#bbb; user-select:none; text-align:right; }
.srv-off summary::-webkit-details-marker { display:none; }
.srv-off[open] { background:#fff; border:1px solid #ddd; padding:6px 8px; }
.srv-off a { display:block; margin-top:6px; color:#999; text-decoration:none; }
.srv-off a:hover { color:#8b0000; }
.orig-dock { position:fixed; top:52px; right:10px; z-index:19; width:128px;
  background:#fff; border:1px solid var(--line); padding:8px 8px 6px; font-size:12px; }
.orig-dock[hidden] { display:none; }
.orig-dock-item { display:flex; flex-direction:column; gap:2px; margin:0 0 8px;
  color:#444; font-weight:normal; cursor:pointer; }
.orig-dock-item:last-child { margin-bottom:0; }
.orig-dock-item input { margin:0 4px 0 0; vertical-align:middle; }
.orig-dock-item span { color:#008787; }
.orig-dock-item kbd { font-size:10px; color:#888; font-family:inherit; font-weight:normal; }
.orig-sw-moved { position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0,0,0,0); }
body.orig-dock-on main { padding-right:156px; }
@media (max-width: 720px) {
  .orig-dock { top:auto; bottom:12px; right:10px; }
  body.orig-dock-on main { padding-right:28px; padding-bottom:96px; }
}
"""


def _page(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title><style>{CSS}</style></head>
<body>
<details class="srv-off">
  <summary>本機</summary>
  <a href="#" onclick="uxmShutdown();return false">關閉本地伺服器</a>
</details>
<div id="origDock" class="orig-dock" hidden></div>
<main>{body}</main>
<script>
async function uxmShutdown() {{
  if (!confirm("關閉本地伺服器？關閉後請雙擊「開啟介面.bat」再開。")) return;
  await fetch("/api/shutdown", {{method: "POST"}});
  document.body.innerHTML = "<main><p>本地伺服器已關閉。要用時請雙擊專案資料夾裡的「開啟介面.bat」。</p></main>";
}}
(function () {{
  var dock = document.getElementById("origDock");
  if (!dock) return;
  function wire(id, label, hint) {{
    var src = document.getElementById(id);
    if (!src) return false;
    var item = document.createElement("label");
    item.className = "orig-dock-item";
    var name = document.createElement("span");
    name.textContent = label;
    var kbd = document.createElement("kbd");
    kbd.textContent = hint;
    item.appendChild(src);
    item.appendChild(name);
    item.appendChild(kbd);
    dock.appendChild(item);
    return true;
  }}
  var any = false;
  if (wire("showOrig", "原文", "Ctrl+Shift+E")) any = true;
  if (wire("showTables", "詳細規格", "Ctrl+Shift+D")) any = true;
  if (!any) return;
  document.querySelectorAll(".orig-sw").forEach(function (el) {{
    el.classList.add("orig-sw-moved");
  }});
  dock.hidden = false;
  document.body.classList.add("orig-dock-on");
  function toggle(id) {{
    var el = document.getElementById(id);
    if (!el) return;
    el.checked = !el.checked;
    el.dispatchEvent(new Event("change", {{ bubbles: true }}));
  }}
  document.addEventListener("keydown", function (e) {{
    if (!e.ctrlKey || !e.shiftKey || e.altKey || e.metaKey) return;
    var k = (e.key || "").toLowerCase();
    if (k === "e" && document.getElementById("showOrig")) {{
      e.preventDefault();
      toggle("showOrig");
    }}
    if (k === "d" && document.getElementById("showTables")) {{
      e.preventDefault();
      toggle("showTables");
    }}
  }});
}})();
</script>
</body></html>"""


def _vclass(v: str) -> str:
    x = (v or "").lower()
    if x == "fail":
        return "fail"
    if x == "skip":
        return "skip"
    if x == "pass":
        return "pass"
    return ""


def _fail_counts(store: Store) -> tuple[dict[int, int], dict[int, int]]:
    links = build_links(store.lineage_events())
    opened: dict[int, int] = {}
    closed: dict[int, int] = {}
    for (sid, _name, _lmh), link in links.items():
        if link.superseded:
            closed[sid] = closed.get(sid, 0) + 1
        else:
            opened[sid] = opened.get(sid, 0) + 1
    return opened, closed


def _del_script() -> str:
    return """
<script>
async function postDel(body) {
  const r = await fetch("/api/delete-many", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(body)
  });
  const j = await r.json();
  if (!r.ok) { alert(j.error || "刪除失敗"); return; }
  location.reload();
}
function checkedIds() {
  return Array.from(document.querySelectorAll('input[name=sid]:checked')).map((el) => Number(el.value));
}
function allIds() {
  return Array.from(document.querySelectorAll('input[name=sid]')).map((el) => Number(el.value));
}
document.querySelectorAll("button[data-del]").forEach((btn) => {
  btn.onclick = async () => {
    if (!confirm("從資料庫刪除：\\n" + btn.dataset.name + "\\n（不刪你磁碟上的檔）")) return;
    const r = await fetch("/api/delete", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({id: Number(btn.dataset.del)})
    });
    const j = await r.json();
    if (!r.ok) { alert(j.error || "刪除失敗"); return; }
    location.reload();
  };
});
const selAll = document.getElementById("selAll");
const selNone = document.getElementById("selNone");
const delChecked = document.getElementById("delChecked");
const delAll = document.getElementById("delAll");
if (selAll) selAll.onclick = () => document.querySelectorAll('input[name=sid]').forEach((el) => { el.checked = true; });
if (selNone) selNone.onclick = () => document.querySelectorAll('input[name=sid]').forEach((el) => { el.checked = false; });
if (delChecked) delChecked.onclick = async () => {
  const ids = checkedIds();
  if (!ids.length) { alert("請先勾選要刪的檔"); return; }
  if (!confirm("從資料庫刪除勾選的 " + ids.length + " 筆？\\n不刪磁碟檔。")) return;
  await postDel({ids});
};
if (delAll) delAll.onclick = async () => {
  const ids = allIds();
  if (!ids.length) { alert("這一頁沒有檔"); return; }
  if (!confirm("將刪除這個專案目前列表的 " + ids.length + " 筆（僅資料庫）。下一步還要輸入「刪除」。")) return;
  const typed = prompt("請輸入「刪除」以確認全部刪除：");
  if (typed !== "刪除") { alert("已取消"); return; }
  await postDel({ids});
};
</script>
"""


def list_page(store: Store, module: str = "", project: str = "") -> str:
    rows = store.list_sessions()
    if not module:
        return _review_modules(rows)
    if not project:
        return _review_projects(rows, module)
    return _review_sessions(store, rows, module, project)


def _review_modules(rows: list[dict]) -> str:
    by_mod: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_mod[r["module"] or "?"].append(r)
    cards = []
    for name in sorted(by_mod):
        items = by_mod[name]
        projs = {r["project"] for r in items}
        href = "/review?module=" + quote(name)
        cards.append(
            f'<a class="card" href="{href}">'
            f"<h2>{escape(name)}</h2>"
            f"<p>{len(projs)} 個專案 · {len(items)} 筆匯入紀錄</p>"
            "</a>"
        )
    body = f"""
{site_nav("資料審核")}
<h1>資料審核</h1>
<p class="muted">先選模組，再進專案看匯入紀錄。匯入時間會留著，方便日後查核。</p>
<div class="cards">{''.join(cards) or '<p>還沒有資料。請先到報告匯入帶入 CSV。</p>'}</div>
<style>
.cards {{ display:flex; flex-wrap:wrap; gap:12px; margin-top:16px; }}
.card {{ display:block; min-width:220px; padding:16px 18px; border:1px solid #ccc; text-decoration:none; color:#222; }}
.card:hover {{ border-color:#008787; }}
.card h2 {{ margin:0 0 6px; font-size:18px; color:#008787; }}
.card p {{ margin:0; color:#666; font-size:13px; }}
</style>
"""
    return _page("資料審核", body)


def _review_projects(rows: list[dict], module: str) -> str:
    items = [r for r in rows if r["module"] == module]
    by_proj: dict[str, list[dict]] = defaultdict(list)
    for r in items:
        by_proj[r["project"] or "?"].append(r)
    cards = []
    for name in sorted(by_proj):
        recs = by_proj[name]
        href = "/review?module=" + quote(module) + "&project=" + quote(name)
        cards.append(
            f'<a class="card" href="{href}">'
            f"<h2>{escape(name)}</h2>"
            f"<p>{len(recs)} 筆匯入紀錄</p>"
            "</a>"
        )
    body = f"""
{site_nav("資料審核")}
<p class="muted"><a href="/review">資料審核</a> / {escape(module)}</p>
<h1>{escape(module)}</h1>
<p class="muted">選專案看該專案的匯入紀錄。</p>
<div class="cards">{''.join(cards) or '<p>這個模組還沒有匯入紀錄。</p>'}</div>
<style>
.cards {{ display:flex; flex-wrap:wrap; gap:12px; margin-top:16px; }}
.card {{ display:block; min-width:220px; padding:16px 18px; border:1px solid #ccc; text-decoration:none; color:#222; }}
.card:hover {{ border-color:#008787; }}
.card h2 {{ margin:0 0 6px; font-size:18px; color:#008787; }}
.card p {{ margin:0; color:#666; font-size:13px; }}
</style>
"""
    return _page(f"{module} 資料審核", body)


def _review_sessions(store: Store, rows: list[dict], module: str, project: str) -> str:
    opened, closed = _fail_counts(store)
    items = [r for r in rows if r["module"] == module and r["project"] == project]
    trs = []
    for r in items:
        href = f"/review/session?id={r['id']}"
        trs.append(
            "<tr>"
            f"<td><input type=\"checkbox\" name=\"sid\" value=\"{r['id']}\"></td>"
            f"<td>{escape(r.get('imported_at') or '—')}</td>"
            f"<td>{escape(r['start_time'] or '')}</td>"
            f"<td>{escape(r.get('data_folder') or '')}</td>"
            f"<td>{escape(r['imei'])}</td>"
            f"<td><a href=\"{href}\">{escape(r['filename'])}</a> "
            f"<a class=\"muted\" href=\"/analysis/session?id={r['id']}\">資料分析</a></td>"
            f"<td>TA {escape(r.get('ta_major') or '—')}</td>"
            f"<td>{escape(r.get('source_kind') or '')}</td>"
            f"<td class=\"{_vclass(r['overall_result'])}\">{escape(r['overall_result'] or '')}</td>"
            f"<td>{r['n_sum']}</td><td>{r['n_det']}</td>"
            f"<td>{opened.get(r['id'], 0)} 未結"
            + (f" / {closed.get(r['id'], 0)} 已重測過" if closed.get(r["id"]) else "")
            + "</td>"
            f"<td><button class=\"danger\" data-del=\"{r['id']}\" data-name=\"{escape(r['filename'])}\">刪除</button></td>"
            "</tr>"
        )
    body = f"""
{site_nav("資料審核")}
<p class="muted"><a href="/review">資料審核</a> / <a href="/review?module={quote(module)}">{escape(module)}</a> / {escape(project)}</p>
<h1>{escape(module)} · {escape(project)}</h1>
<div class="note">
同一 IMEI、同一 band、同一測項、同一 Low/Mid/High，若<b>較晚的 session 已 Pass</b>，較早的 Fail 算「已重測過」。<br>
「匯入時間」是進庫時間；「測試時間」是 CSV 裡的 Start Time。舊資料若還沒有匯入時間會顯示 —。
</div>
<p class="muted">{len(items)} 筆匯入紀錄。</p>
<p class="row">
  <button type="button" class="secondary" id="selAll">全選</button>
  <button type="button" class="secondary" id="selNone">全不選</button>
  <button type="button" class="danger" id="delChecked">刪除勾選</button>
  <button type="button" class="danger" id="delAll">全部刪除</button>
</p>
<p class="muted">刪除只從資料庫拿掉，不刪磁碟檔。全部刪除只針對這個專案，要確認兩次。</p>
<table>
<tr><th></th><th>匯入時間</th><th>測試時間</th><th>資料夾</th><th>IMEI</th><th>檔名</th><th>TA</th><th>來源</th><th>Overall</th><th>摘要</th><th>細節</th><th>Fail</th><th></th></tr>
{''.join(trs) or '<tr><td colspan="13">這個專案還沒有匯入紀錄。</td></tr>'}
</table>
{_del_script()}
"""
    return _page(f"{module} {project} 資料審核", body)


def session_page(store: Store, session_id: int, pf: str | None, test: str | None) -> str:
    head = store.session_header(session_id)
    if not head:
        return _page("找不到", "<p>沒有這個 session。</p>")
    tests = store.session_tests(session_id)
    details = store.session_details(session_id, pf=pf, test_case=test, limit=400)
    links = build_links(store.lineage_events())
    trows = []
    for t in tests:
        lmh = t.get("lmh") or str(t.get("channel") or "")
        link = links.get((session_id, t["test_name"], lmh))
        extra = ""
        row_cls = ""
        if link and (t.get("verdict") or "").lower() == "fail":
            if link.superseded:
                row_cls = "super"
                extra = (
                    f'後續已 Pass：<a href="/review/session?id={link.later_session_id}">'
                    f"{escape(link.later_filename)}</a> ({escape(link.later_start)})"
                )
            else:
                extra = "未結：沒有較晚的同項 Pass"
        trows.append(
            f"<tr class=\"{row_cls}\">"
            f"<td>{escape(t['test_name'])}</td>"
            f"<td>{escape(t['band'] or '')}</td>"
            f"<td>{escape(str(t['channel'] or ''))}</td>"
            f"<td>{escape(t['lmh'] or '')}</td>"
            f"<td class=\"{_vclass(t['verdict'])}\">{escape(t['verdict'] or '')}</td>"
            f"<td>{t['time_s'] if t['time_s'] is not None else ''}</td>"
            f"<td>{escape(t['spec_ref'] or '')}</td>"
            f"<td class=\"muted\">{escape(t['interpret_note'] or '')} {extra}</td>"
            "</tr>"
        )
    drows = []
    for d in details:
        drows.append(
            "<tr>"
            f"<td>{escape(d['time'] or '')}</td>"
            f"<td>{escape(d['test_case'] or '')}</td>"
            f"<td>{escape(d['arfcn'] or '')} {escape(d['freq_mhz'] or '')}</td>"
            f"<td>{escape(d['item'] or '')}</td>"
            f"<td>{escape(d['condition'] or '')}</td>"
            f"<td>{escape(d['lower_limit'] or '')}</td>"
            f"<td>{escape(d['value'] or '')}</td>"
            f"<td>{escape(d['upper_limit'] or '')} {escape(d['unit'] or '')}</td>"
            f"<td class=\"{_vclass(d['pf'])}\">{escape(d['pf'] or '')}</td>"
            "</tr>"
        )
    sid = head["id"]
    body = f"""
{site_nav("資料審核", extra=f'<a href="/analysis/session?id={sid}">資料分析</a> · session {sid}')}
<h1>{escape(head['filename'])}</h1>
<p class="meta">
模組 <b>{escape(head['module'])}</b> ·
專案 <b>{escape(head['project'])}</b> ·
IMEI <b>{escape(head['imei'])}</b> ·
測試 {escape(head['start_time'] or '')} → {escape(head['stop_time'] or '')} ·
匯入 {escape(head.get('imported_at') or '—')}<br>
TestPlan {escape(head['test_plan'] or '')} ·
Overall <span class="{_vclass(head['overall_result'])}">{escape(head['overall_result'] or '')}</span> ·
資料夾 {escape(head.get('data_folder') or 'UNKNOWN')} ·
TA {escape(head.get('ta_major') or '—')}
（{escape(head['ta_version'] or '')}） ·
來源 {escape(head.get('source_kind') or 'csv')} ·
RFA {escape(head['rfa_version'] or '')}
</p>
{('<div class="note"><b>PDF 還原註記</b><br>' + escape(head.get('parse_notes') or '').replace(chr(10), '<br>') + '</div>') if head.get('parse_notes') else ''}
<div class="note">
<b>初版假設（請核對）</b><br>
1. 摘要列的 Channel 是 DL NR-ARFCN；6.2.x 細節列 ARFCN 多半是 UL（例如 n1 摘要 423000、細節 385000）。<br>
2. Low/Mid/High 用 TS 38.101-1 頻段邊界 + TS 38.508-1（F_low+CBW/2、中心、F_high-CBW/2）。<br>
3. 6.2.3 Condition 的 NS_100 / NS_05 對應 38.101-1 additional emission / A-MPR。<br>
4. 細節 P/F=NotSet 多半是搜尋中間點，不應覆寫摘要 Verdict。<br>
5. PRACH -118/-124 是 preamble 目標功率，不是頻段編號。<br>
6. 同一 IMEI＋band＋測項＋LMH，較晚的 Pass 會把這份裡的 Fail 標成「已重測過」（刪除線）。該檔 Overall 仍是當次結果，最終判定請看未結 Fail。
</div>
<h2>摘要列（給 Excel 的那層）</h2>
<table>
<tr><th>測項</th><th>Band</th><th>Channel</th><th>LMH</th><th>Verdict</th><th>s</th><th>規格（初版）</th><th>解讀</th></tr>
{''.join(trows)}
</table>
<h2>細節量測</h2>
<p class="filters muted">
篩選：
<a href="/review/session?id={sid}">全部（最多 400）</a>
<a href="/review/session?id={sid}&amp;pf=Fail">只看 Fail</a>
<a href="/review/session?id={sid}&amp;pf=Skip">Skip</a>
<a href="/review/session?id={sid}&amp;pf=NotSet">NotSet</a>
{f'· 目前測項過濾：{escape(test)}' if test else ''}
</p>
<table>
<tr><th>Time</th><th>Test Case</th><th>ARFCN / Freq</th><th>Item</th><th>Condition</th><th>Lower</th><th>Value</th><th>Upper</th><th>P/F</th></tr>
{''.join(drows) or '<tr><td colspan="9">沒有細節列。請用匯入頁再匯一次，才會寫入 detail_rows。</td></tr>'}
</table>
"""
    return _page(head["filename"], body)
