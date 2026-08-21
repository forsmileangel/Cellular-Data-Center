"""HTML review of stored sessions and first-pass 3GPP interpretation."""

from __future__ import annotations

from collections import defaultdict
from html import escape
from urllib.parse import quote

from .lineage import build_links
from .store import Store

NAV_GROUPS = (
    (
        "工作流程",
        (
            ("/", "首頁"),
            ("/import", "報告匯入"),
            ("/db", "測試資料庫"),
            ("/review", "資料審核"),
            ("/analysis", "資料分析"),
        ),
    ),
    (
        "規格知識",
        (
            ("/spec", "測試規格對照"),
            ("/ref", "3GPP法規參考"),
        ),
    ),
)
NAV_ITEMS = tuple(item for _group, items in NAV_GROUPS for item in items)


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
    suffix = f'<span class="context-extra">{extra}</span>' if extra else ""
    return (
        '<header class="top-context">'
        f'<span class="context-current">{escape(current or "工作台")}</span>{suffix}'
        "</header>"
    )

CSS = """
:root {
  --paper:#fffdf9; --paper-soft:#f8f4ed; --canvas:#eee9df; --ink:#292c29;
  --muted:#6c706a; --line:#ded8ce; --line-strong:#cbc3b6;
  --green:#496b57; --green-deep:#355341; --green-soft:#e9f0e9;
  --fail:#a14f43; --fail-soft:#f8e9e5; --skip:#8a6a2f; --skip-soft:#f6eedb;
  --pass:#4d7152; --shadow:0 14px 34px rgba(69,58,43,.08);
  --radius:14px; --radius-sm:9px;
}
* { box-sizing:border-box; }
html { background:var(--canvas); }
body {
  margin:0; font-family:Segoe UI, Microsoft JhengHei, sans-serif;
  color:var(--ink); background:var(--canvas); line-height:1.55;
}
button, input, select { font:inherit; }
a { color:var(--green-deep); text-underline-offset:3px; }
a:hover { color:#253f31; }
a:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible,
summary:focus-visible { outline:3px solid rgba(73,107,87,.28); outline-offset:2px; }
.app-shell { min-height:100vh; display:grid; grid-template-columns:248px minmax(0,1fr); }
.sidebar {
  position:sticky; top:0; height:100vh; padding:26px 20px 20px;
  background:#e7e1d6; border-right:1px solid var(--line-strong);
  display:flex; flex-direction:column; overflow-y:auto;
}
.brand { display:flex; gap:11px; align-items:center; text-decoration:none; color:var(--ink); margin-bottom:30px; }
.brand-mark {
  width:38px; height:38px; border-radius:12px; display:grid; place-items:center;
  background:var(--green-deep); color:#fffdf9; font-weight:700; letter-spacing:.04em;
}
.brand strong { display:block; font-size:12px; line-height:1.35; }
.brand small { display:block; color:var(--muted); font-size:11px; margin-top:1px; }
.side-group { margin:0 0 22px; }
.side-label {
  margin:0 10px 7px; color:#7c776e; font-size:10px; font-weight:700;
  letter-spacing:.14em; text-transform:uppercase;
}
.side-nav { display:flex; flex-direction:column; gap:3px; }
.side-nav a {
  display:flex; align-items:center; gap:9px; min-height:38px; padding:8px 10px;
  border-radius:9px; text-decoration:none; color:#4b4e49; font-size:13px;
}
.side-nav a::before { content:""; width:6px; height:6px; border-radius:50%; background:#b9b1a5; }
.side-nav a:hover { background:rgba(255,253,249,.65); color:var(--green-deep); }
.side-nav a.active { background:var(--paper); color:var(--green-deep); box-shadow:0 5px 14px rgba(69,58,43,.06); font-weight:650; }
.side-nav a.active::before { background:var(--green); }
.workspace {
  width:min(1380px, calc(100% - 48px)); margin:24px auto; min-width:0;
  background:var(--paper); border:1px solid var(--line); border-radius:18px;
  box-shadow:var(--shadow); padding:26px 30px 38px;
}
h1 { margin:0 0 8px; font-size:clamp(24px,2.3vw,34px); color:var(--ink); letter-spacing:-.025em; line-height:1.2; }
h2 { color:#343834; letter-spacing:-.012em; }
h3 { color:#3d423d; }
.top-context {
  display:flex; align-items:center; justify-content:space-between; gap:16px;
  min-height:34px; margin:-8px 0 20px; padding-bottom:12px; border-bottom:1px solid var(--line);
  color:var(--muted); font-size:12px;
}
.context-current { color:var(--green-deep); font-weight:700; }
.context-extra { display:flex; gap:8px; align-items:center; }
.note {
  background:var(--green-soft); border:1px solid #ccd9ce; border-radius:var(--radius-sm);
  padding:12px 14px; font-size:13px; margin:12px 0 18px;
}
.note.warning { background:var(--skip-soft); border-color:#e1d1aa; }
table { border-collapse:separate; border-spacing:0; width:100%; font-size:13px; }
th, td { border-bottom:1px solid var(--line); padding:9px 10px; text-align:left; vertical-align:top; }
th {
  position:sticky; top:0; z-index:1; background:#f1ede5; color:#52564f;
  font-size:11px; letter-spacing:.025em; white-space:nowrap;
}
tr:hover td { background:#fbf8f2; }
.fail { color:var(--fail); font-weight:650; }
.skip { color:var(--skip); }
.pass { color:var(--pass); }
.err { color:var(--fail); }
.ok { color:var(--pass); }
.muted { color:var(--muted); font-size:12px; }
.name-box { margin-top:12px; display:flex; flex-wrap:wrap; gap:10px 16px; align-items:center; }
.name-box input[type=text] { display:block; margin-top:4px; min-width:240px; }
.name-box .chk { font-weight:normal; font-size:13px; }
#namePreview { width:100%; margin:0; }
.file-drop { margin:12px 0; padding:8px 10px; border:1px solid var(--line); background:#fff; }
.file-list { display:flex; flex-direction:column; gap:4px; max-height:240px; overflow:auto; margin-top:8px; }
.file-pick { font-weight:normal; font-size:13px; }
.meta { font-size:14px; margin:0 0 12px; }
.filters a { margin-right:10px; }
.bar { display:inline-block; position:relative; width:90px; height:10px; background:#eee9df; border:1px solid var(--line-strong); vertical-align:middle; }
.bar .fill { position:absolute; top:-3px; width:6px; height:14px; background:var(--green); margin-left:-3px; }
.super { color:#777; }
.super .fail { color:#a66; font-weight:normal; }
input[type=text], input[type=search], select {
  min-height:38px; padding:7px 10px; border:1px solid var(--line-strong);
  border-radius:8px; color:var(--ink); background:var(--paper); max-width:100%;
}
button, .button {
  display:inline-flex; align-items:center; justify-content:center; min-height:38px;
  padding:8px 14px; border:1px solid var(--green-deep); border-radius:8px;
  background:var(--green-deep); color:#fff; cursor:pointer; text-decoration:none;
  font-size:13px; font-weight:650;
}
button:hover, .button:hover { background:#294534; color:#fff; }
button.secondary, .button.secondary {
  background:transparent; color:var(--green-deep); border-color:var(--line-strong);
}
button.secondary:hover, .button.secondary:hover { background:var(--green-soft); color:var(--green-deep); }
button.danger { background:transparent; color:var(--fail); border-color:#d7aaa2; padding:5px 9px; }
button:disabled, .button.disabled { opacity:.45; pointer-events:none; }
.row { display:flex; flex-wrap:wrap; align-items:center; gap:8px; }
details { color:var(--muted); }
details summary { cursor:pointer; color:var(--ink); }
.cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:14px; margin:18px 0; }
.card {
  display:block; min-width:0; padding:18px; border:1px solid var(--line);
  border-radius:var(--radius); background:var(--paper); color:var(--ink);
  text-decoration:none; box-shadow:0 5px 16px rgba(69,58,43,.04);
}
.card:hover { border-color:#afbeaf; transform:translateY(-1px); }
.card h2 { margin:2px 0 7px; color:var(--green-deep); font-size:19px; }
.card p { margin:0; color:var(--muted); font-size:13px; }
.eyebrow {
  display:block; margin:0 0 5px; color:var(--green); font-size:10px;
  font-weight:750; letter-spacing:.13em; text-transform:uppercase;
}
.page-heading, .section-heading {
  display:flex; align-items:flex-start; justify-content:space-between; gap:22px;
}
.page-heading { margin:6px 0 20px; }
.page-heading > p, .section-heading > p { max-width:430px; margin:5px 0 0; color:var(--muted); font-size:13px; text-align:right; }
.section-heading { align-items:center; margin-bottom:14px; }
.section-heading h2 { margin:0; font-size:20px; }
.context-strip { display:flex; flex-wrap:wrap; gap:8px; align-items:center; color:var(--muted); font-size:12px; margin:-4px 0 18px; }
.panel {
  margin:18px 0; padding:18px; border:1px solid var(--line);
  border-radius:var(--radius); background:var(--paper);
}
.table-scroll { width:100%; overflow:auto; border:1px solid var(--line); border-radius:10px; }
.table-scroll table { min-width:720px; }
.table-scroll th:last-child, .table-scroll td:last-child { border-right:0; }
.empty-state { padding:22px; border:1px dashed var(--line-strong); border-radius:10px; color:var(--muted); text-align:center; background:var(--paper-soft); }
.sub { margin:-2px 0 20px; color:var(--muted); }
.home-cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:14px; margin:20px 0; }
.home-card {
  display:block; min-height:118px; padding:20px; border:1px solid var(--line);
  border-radius:var(--radius); background:var(--paper-soft); color:var(--ink);
  text-decoration:none; transition:transform .15s ease,border-color .15s ease;
}
.home-card:hover { transform:translateY(-2px); border-color:#afbeaf; }
.home-card strong { display:block; margin-bottom:7px; color:var(--green-deep); font-size:17px; }
.home-card span { display:block; color:var(--muted); font-size:12px; line-height:1.55; }
.import-step { margin:16px 0; padding:20px; border:1px solid var(--line); border-radius:var(--radius); background:var(--paper); }
.import-step.action-step { background:var(--green-soft); border-color:#cdd9ce; }
.step-heading { display:flex; gap:12px; align-items:flex-start; padding-bottom:13px; margin-bottom:8px; border-bottom:1px solid var(--line); }
.step-heading > span {
  display:grid; place-items:center; flex:0 0 34px; height:34px; border-radius:10px;
  background:#e7e1d6; color:var(--green-deep); font-size:12px; font-weight:750;
}
.step-heading h2 { margin:1px 0 2px; font-size:17px; }
.step-heading p { margin:0; color:var(--muted); font-size:12px; }
.import-step > label { display:block; margin:13px 0 5px; font-size:13px; font-weight:650; }
.import-step select, .import-step > input { width:100%; }
.hint { color:var(--muted); font-size:12px; margin-top:4px; }
#preview { margin-top:12px; padding:12px; border-radius:9px; background:var(--paper-soft); }
#status { margin-top:12px; font-weight:650; }
.analysis-filters {
  margin:18px 0; padding:16px; border:1px solid var(--line);
  border-radius:var(--radius); background:var(--paper-soft);
}
.filter-grid { display:grid; grid-template-columns:repeat(5,minmax(130px,1fr)); gap:12px; }
.filter-grid label, .group-picker label { font-size:12px; font-weight:650; color:#51554f; }
.filter-grid select, .group-picker select { display:block; width:100%; margin-top:5px; }
.filter-actions { display:flex; gap:8px; margin-top:14px; }
.scope-picker { margin-top:14px; padding-top:12px; border-top:1px solid var(--line); }
.scope-picker summary { font-weight:650; }
.scope-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:8px; margin-top:10px; }
.scope-option {
  display:flex; gap:9px; align-items:flex-start; padding:9px 10px;
  border:1px solid var(--line); border-radius:9px; background:var(--paper);
}
.scope-option input { margin-top:4px; }
.scope-option span, .scope-option small { display:block; }
.scope-option small { color:var(--muted); font-weight:400; margin-top:2px; }
.cohort-cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:12px; margin:16px 0; }
.cohort-card { padding:15px; border:1px solid var(--line); border-radius:12px; background:#fbf8f2; }
.cohort-card h3 { margin:0 0 8px; font-size:16px; }
.cohort-card p { margin:5px 0; }
.status-bar { height:8px; display:flex; overflow:hidden; border-radius:20px; background:#ddd7cc; margin:10px 0; }
.status-bar span { display:block; height:100%; }
.bar-pass { background:#7b9b80; }
.bar-fail { background:#c7796c; }
.cohort-counts { display:flex; flex-wrap:wrap; gap:10px; font-size:11px; }
.status-chip { display:inline-flex; padding:2px 8px; border-radius:20px; background:#ece7dd; color:#5d605b; font-size:11px; font-weight:750; white-space:nowrap; }
.status-chip.pass { background:var(--green-soft); color:var(--pass); }
.status-chip.fail { background:var(--fail-soft); color:var(--fail); }
.status-chip.skip { background:var(--skip-soft); color:var(--skip); }
.layer-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:13px; margin:18px 0; }
.layer-card { padding:17px; border:1px solid var(--line); border-radius:var(--radius); background:var(--paper); }
.layer-card.fact { border-top:4px solid #66728a; }
.layer-card.spec { border-top:4px solid var(--green); }
.layer-card.judgement { border-top:4px solid #a78257; }
.layer-card h3 { margin:4px 0 9px; font-size:16px; }
.layer-card p { font-size:13px; }
.group-picker { margin:8px 0 16px; }
.group-picker select { min-width:min(720px,100%); }
.pagination { display:flex; align-items:center; justify-content:center; gap:12px; margin:14px 0; color:var(--muted); font-size:12px; }
.pagination .button { min-height:32px; padding:5px 10px; }
.split-charts { display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:14px; }
.split-chart { min-width:0; padding:14px; border:1px solid var(--line); border-radius:11px; background:var(--paper-soft); }
.split-chart h3 { margin-top:0; }
.srv-off { margin-top:auto; padding-top:14px; font-size:11px; color:#8b867e; }
.srv-off summary { cursor:pointer; list-style:none; color:#8b867e; user-select:none; }
.srv-off summary::-webkit-details-marker { display:none; }
.srv-off[open] { background:rgba(255,253,249,.6); border:1px solid var(--line); border-radius:8px; padding:7px 9px; }
.srv-off a { display:block; margin-top:6px; color:var(--fail); text-decoration:none; }
.orig-dock { position:fixed; top:52px; right:10px; z-index:19; width:128px;
  background:var(--paper); border:1px solid var(--line); border-radius:9px; padding:8px 8px 6px; font-size:12px; box-shadow:var(--shadow); }
.orig-dock[hidden] { display:none; }
.orig-dock-item { display:flex; flex-direction:column; gap:2px; margin:0 0 8px;
  color:#444; font-weight:normal; cursor:pointer; }
.orig-dock-item:last-child { margin-bottom:0; }
.orig-dock-item input { margin:0 4px 0 0; vertical-align:middle; }
.orig-dock-item span { color:var(--green-deep); }
.orig-dock-item kbd { font-size:10px; color:#888; font-family:inherit; font-weight:normal; }
.orig-sw-moved { position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0,0,0,0); }
body.orig-dock-on .workspace { padding-right:156px; }
@media (max-width: 1080px) {
  .app-shell { grid-template-columns:218px minmax(0,1fr); }
  .sidebar { padding-left:14px; padding-right:14px; }
  .workspace { width:calc(100% - 28px); margin:14px; padding:22px; }
  .filter-grid { grid-template-columns:repeat(3,minmax(130px,1fr)); }
  .layer-grid { grid-template-columns:1fr; }
}
@media (max-width: 760px) {
  .app-shell { display:block; }
  .sidebar { position:static; width:100%; height:auto; padding:14px; border-right:0; border-bottom:1px solid var(--line-strong); }
  .brand { margin-bottom:12px; }
  .side-group { margin:7px 0; }
  .side-label { display:none; }
  .side-nav { flex-direction:row; overflow-x:auto; padding-bottom:3px; }
  .side-nav a { flex:0 0 auto; }
  .workspace { width:calc(100% - 20px); margin:10px; padding:18px 15px 28px; border-radius:13px; }
  .filter-grid { grid-template-columns:1fr 1fr; }
  .page-heading, .section-heading { display:block; }
  .page-heading > p, .section-heading > p { text-align:left; }
  .pagination { flex-wrap:wrap; }
  .srv-off { display:none; }
  .orig-dock { top:auto; bottom:12px; right:10px; }
  body.orig-dock-on .workspace { padding-right:15px; padding-bottom:96px; }
}
@media (max-width: 500px) {
  .filter-grid { grid-template-columns:1fr; }
  .cohort-cards, .cards { grid-template-columns:1fr; }
}
"""


def _page(title: str, body: str) -> str:
    groups = []
    for label, items in NAV_GROUPS:
        links = "".join(
            f'<a href="{href}" data-nav="{href}">{escape(text)}</a>'
            for href, text in items
        )
        groups.append(
            f'<section class="side-group"><p class="side-label">{escape(label)}</p>'
            f'<nav class="side-nav" aria-label="{escape(label)}">{links}</nav></section>'
        )
    sidebar = "".join(groups)
    return f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title><style>{CSS}</style></head>
<body>
<div class="app-shell">
  <aside class="sidebar">
    <a class="brand" href="/">
      <span><strong>Cellular Specifications and Reporting Analysis Center</strong></span>
    </a>
    {sidebar}
    <details class="srv-off">
      <summary>本機服務</summary>
      <a href="#" onclick="uxmShutdown();return false">關閉本地伺服器</a>
    </details>
  </aside>
  <main class="workspace">
    <div id="origDock" class="orig-dock" hidden></div>
    {body}
  </main>
</div>
<script>
async function uxmShutdown() {{
  if (!confirm("關閉本地伺服器？關閉後請雙擊「開啟介面.bat」再開。")) return;
  await fetch("/api/shutdown", {{method: "POST"}});
  document.body.innerHTML = '<main class="workspace"><div class="empty-state">本地伺服器已關閉。要用時請雙擊專案資料夾裡的「開啟介面.bat」。</div></main>';
}}
(function () {{
  var path = window.location.pathname || "/";
  document.querySelectorAll("[data-nav]").forEach(function (link) {{
    var href = link.getAttribute("data-nav");
    var active = href === "/" ? path === "/" : (path === href || path.indexOf(href + "/") === 0);
    if (active) {{
      link.classList.add("active");
      link.setAttribute("aria-current", "page");
    }}
  }});
}})();
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
.card:hover {{ border-color:#afbeaf; }}
.card h2 {{ margin:0 0 6px; font-size:18px; color:var(--green-deep); }}
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
.card:hover {{ border-color:#afbeaf; }}
.card h2 {{ margin:0 0 6px; font-size:18px; color:var(--green-deep); }}
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
只有同一專案、同一資料夾、同一 IMEI、同一 band、同一測項、同一 Low/Mid/High，
若<b>較晚的 session 已 Pass</b>，較早的 Fail 才算「已重測過」。<br>
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
6. 只有同專案＋同資料夾＋同 IMEI＋band＋測項＋LMH，較晚的 Pass 才會把這份裡的 Fail 標成「已重測過」（刪除線）。該檔 Overall 仍是當次結果，最終判定請看未結 Fail。
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
