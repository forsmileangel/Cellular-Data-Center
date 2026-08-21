"""Module → project index and UXM report export from the database."""

from __future__ import annotations

from collections import defaultdict
from html import escape
from urllib.parse import quote

from .charts import CHARTS, svg_lmh
from .review import _page, _vclass, site_nav
from .spec import NR_RANGE_ORDER, nr_range_class
from .parse import plan_label
from .store import Store


def _tabs(module: str, project: str, current: str) -> str:
    report = "/db/project?module=" + quote(module) + "&project=" + quote(project)
    charts = "/db/charts?module=" + quote(module) + "&project=" + quote(project)
    rcls = "tab on" if current == "report" else "tab"
    ccls = "tab on" if current == "charts" else "tab"
    return (
        '<p class="tabs">'
        f'<a class="{rcls}" href="{report}">報告</a>'
        f'<a class="{ccls}" href="{charts}">圖</a>'
        "</p>"
        "<style>"
        ".tabs { margin:12px 0 18px; }"
        ".tab { display:inline-block; padding:6px 14px; border:1px solid #ccc; "
        "margin-right:6px; text-decoration:none; color:#222; }"
        ".tab.on { background:#008787; color:#fff; border-color:#008787; }"
        "</style>"
    )


def _nav() -> str:
    return site_nav("測試資料庫")


def _rat_label(rat: str, bands: str) -> str:
    if rat == "NR":
        return "5G / NR"
    if rat == "LTE":
        return "4G / LTE"
    parts = [b for b in (bands or "").split(",") if b]
    if parts and all(p.startswith("NR_") for p in parts):
        return "5G / NR"
    if parts and all(p.startswith("B") for p in parts):
        return "4G / LTE"
    if rat == "mixed":
        return "4G+5G"
    return rat or "未標"


def _sel(name: str, current: str, options: list[str], all_label: str) -> str:
    bits = [f'<option value="">{escape(all_label)}</option>']
    for o in options:
        sel = " selected" if o == current else ""
        bits.append(f'<option value="{escape(o)}"{sel}>{escape(o)}</option>')
    return f'<select name="{name}" onchange="this.form.submit()">{"".join(bits)}</select>'


def index_page(
    store: Store,
    module: str = "",
    project: str = "",
    data_folder: str = "",
    imei: str = "",
) -> str:
    mods = store.list_modules()
    cards = []
    for m in mods:
        href = "/db?module=" + quote(m["model"])
        cards.append(
            f'<a class="card" href="{href}">'
            f"<h2>{escape(m['model'])}</h2>"
            f"<p>{m['projects']} 個專案 · {m['duts']} 個 IMEI · {m['sessions']} 份 session</p>"
            f"<span class=\"muted\">管理專案：</span>"
            f'<a href="/db/module?name={quote(m["model"])}">開啟</a>'
            "</a>"
        )
    projects = [p["name"] for p in store.list_projects(module)] if module else []
    folders = store.list_folders(module, project) if module and project else []
    imeis = sorted({r["imei"] for r in store.filter_sessions(module=module) if r.get("imei")})
    rows = store.filter_sessions(module, project, data_folder, imei)
    by_band: dict[str, list[dict]] = defaultdict(list)
    for s in rows:
        for band in [b for b in (s.get("bands") or "").split(",") if b]:
            by_band[band].append(s)
    grouped: dict[str, list[str]] = defaultdict(list)
    for band in by_band:
        grouped[nr_range_class(band)].append(band)
    band_blocks = []
    for cls in NR_RANGE_ORDER:
        names = sorted(grouped.get(cls, []))
        if not names:
            continue
        rows_html = []
        for band in names:
            files = by_band[band]
            sources: list[str] = []
            for f in files:
                lab = plan_label(f.get("filename") or "")
                if lab and lab not in sources:
                    sources.append(lab)
            ntxt = str(len(files))
            if sources:
                ntxt = f"{len(files)}（{', '.join(sources)}）"
            rows_html.append(
                "<tr>"
                f"<td><label><input type=\"checkbox\" name=\"band\" value=\"{escape(band)}\" "
                f"data-range=\"{escape(cls)}\" checked> {escape(band)}</label></td>"
                f"<td>{escape(ntxt)}</td>"
                "</tr>"
            )
        band_blocks.append(
            f'<tbody class="band-group">'
            f'<tr class="range-head"><td colspan="2"><b>{escape(cls)}</b></td></tr>'
            + "".join(rows_html)
            + "</tbody>"
        )
    file_rows = []
    for s in rows:
        file_rows.append(
            "<tr>"
            f"<td><input type=\"checkbox\" name=\"exportSid\" value=\"{s['id']}\" checked></td>"
            f"<td>{escape(s.get('module') or '')}</td>"
            f"<td>{escape(s.get('project') or '')}</td>"
            f"<td>{escape(s.get('data_folder') or '')}</td>"
            f"<td>{escape(s.get('imei') or '')}</td>"
            f"<td>{escape(s.get('filename') or '')}</td>"
            f"<td>{escape(s.get('bands') or '')}</td>"
            f"<td class=\"{_vclass(s.get('overall_result') or '')}\">{escape(s.get('overall_result') or '')}</td>"
            "</tr>"
        )
    body = f"""
{_nav()}
<h1>測試資料庫</h1>
<p class="muted">用篩選縮小範圍後，依 band 產出 Excel Report。匯入只是進庫；出報告在這裡做。</p>
<form method="get" action="/db" class="filters">
  <label>模組 {_sel("module", module, [m["model"] for m in mods], "全部模組")}</label>
  <label>專案 {_sel("project", project, projects, "全部專案")}</label>
  <label>資料夾 {_sel("data_folder", data_folder, folders, "全部資料夾")}</label>
  <label>IMEI {_sel("imei", imei, imeis, "全部 IMEI")}</label>
</form>
<p class="muted">{len(rows)} 個檔符合目前篩選。預設全勾，可勾掉不要進報告的檔。</p>

<h2>符合的檔</h2>
<p class="row">
  <button type="button" class="secondary" id="fileAll">全選檔</button>
  <button type="button" class="secondary" id="fileNone">全不選</button>
</p>
<table>
<tr><th></th><th>模組</th><th>專案</th><th>資料夾</th><th>IMEI</th><th>檔名</th><th>Band</th><th>Overall</th></tr>
{''.join(file_rows) or '<tr><td colspan="8">沒有檔案。</td></tr>'}
</table>

<h2>依Band產出Excel Report</h2>
<p class="muted">只會用上面仍勾選的檔。band 列表來自目前篩選；勾掉檔之後，沒有資料的 band 不會進 Excel。</p>
<table>
<thead><tr><th>Band</th><th>檔數</th></tr></thead>
{''.join(band_blocks) or '<tbody><tr><td colspan="2">沒有資料。請先匯入或放寬篩選。</td></tr></tbody>'}
</table>
<p style="margin-top:12px"><button type="button" id="exportBands">依Band產出Excel Report</button></p>
<div id="status"></div>

<h2>模組</h2>
<p class="row">
  <input id="newModule" type="text" placeholder="輸入新模組型號，例如 FN990A" style="max-width:280px">
  <button type="button" id="addModule">新增模組</button>
</p>
<div class="cards">{''.join(cards) or '<p>還沒有資料。請先匯入或新增模組。</p>'}</div>
<style>
.filters {{ display:flex; flex-wrap:wrap; gap:12px 18px; margin:14px 0; align-items:end; }}
.filters label {{ font-size:13px; }}
.filters select {{ display:block; margin-top:4px; min-width:160px; }}
.cards {{ display:flex; flex-wrap:wrap; gap:12px; margin-top:16px; }}
.card {{ display:block; min-width:220px; padding:16px 18px; border:1px solid #ccc; text-decoration:none; color:#222; }}
.card:hover {{ border-color:#008787; }}
.card h2 {{ margin:0 0 6px; font-size:18px; color:#008787; }}
.card p {{ margin:0 0 8px; color:#666; font-size:13px; }}
</style>
<script>
const moduleName = {module!r};
const projectName = {project!r};
function selectedExportIds() {{
  return Array.from(document.querySelectorAll('input[name=exportSid]:checked')).map((el) => Number(el.value));
}}
const fileAll = document.getElementById("fileAll");
const fileNone = document.getElementById("fileNone");
if (fileAll) fileAll.onclick = () => document.querySelectorAll('input[name=exportSid]').forEach((el) => {{ el.checked = true; }});
if (fileNone) fileNone.onclick = () => document.querySelectorAll('input[name=exportSid]').forEach((el) => {{ el.checked = false; }});
document.getElementById("addModule").onclick = async () => {{
  const name = document.getElementById("newModule").value.trim();
  if (!name) {{ alert("請輸入新模組型號"); return; }}
  const r = await fetch("/api/create-module", {{
    method: "POST",
    headers: {{"Content-Type": "application/json"}},
    body: JSON.stringify({{name}})
  }});
  const j = await r.json();
  if (!r.ok) {{ alert(j.error || "新增失敗"); return; }}
  location = "/db?module=" + encodeURIComponent(name);
}};
document.getElementById("exportBands").onclick = async () => {{
  const bands = Array.from(document.querySelectorAll("input[name=band]:checked")).map((el) => el.value);
  const ids = selectedExportIds();
  const status = document.getElementById("status");
  if (!ids.length) {{ status.textContent = "請至少勾選一個檔"; status.className="err"; return; }}
  if (!bands.length) {{ status.textContent = "請至少選一個 band"; status.className="err"; return; }}
  status.className = "";
  status.textContent = "從資料庫產生 Excel Report…";
  const r = await fetch("/api/report", {{
    method: "POST",
    headers: {{"Content-Type": "application/json"}},
    body: JSON.stringify({{module: moduleName, project: projectName, bands, ids}})
  }});
  if (!r.ok) {{
    const j = await r.json().catch(() => ({{error:"失敗"}}));
    status.className = "err";
    status.textContent = j.error || "產生失敗";
    return;
  }}
  const name = r.headers.get("X-Filename") || "Excel Report.xlsx";
  const blob = await r.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  URL.revokeObjectURL(a.href);
  status.className = "ok";
  status.textContent = "已下載 " + name;
}};
</script>
"""
    return _page("測試資料庫", body)


def module_page(store: Store, module: str) -> str:
    projects = store.list_projects(module)
    rows = []
    for p in projects:
        href = "/db/project?module=" + quote(module) + "&project=" + quote(p["name"])
        rows.append(
            "<tr>"
            f"<td><a href=\"{href}\">{escape(p['name'])}</a></td>"
            f"<td>{p['sessions']}</td>"
            f"<td><button class=\"danger\" data-del-project=\"{escape(p['name'])}\">刪除專案</button></td>"
            "</tr>"
        )
    body = f"""
{_nav()}
<p class="muted"><a href="/db">測試資料庫</a> / {escape(module)}</p>
<h1>{escape(module)}</h1>
<p class="muted">同一個模組型號下，用專案分開不同案子。UNKNOWN 可在專案頁改名。</p>
<table>
<tr><th>專案</th><th>session</th><th></th></tr>
{''.join(rows) or '<tr><td colspan="3">這個模組還沒有專案。</td></tr>'}
</table>
<p class="muted">刪除專案會連同底下已匯入的 session 一併從資料庫移除，不會刪磁碟上的 CSV。</p>
<script>
const moduleName = {module!r};
document.querySelectorAll("button[data-del-project]").forEach((btn) => {{
  btn.onclick = async () => {{
    const name = btn.dataset.delProject;
    if (!confirm("刪除專案「" + name + "」以及底下全部 session？\\n不會刪你磁碟上的 CSV。")) return;
    const r = await fetch("/api/delete-project", {{
      method: "POST",
      headers: {{"Content-Type": "application/json"}},
      body: JSON.stringify({{module: moduleName, project: name}})
    }});
    const j = await r.json();
    if (!r.ok) {{ alert(j.error || "刪除失敗"); return; }}
    location.reload();
  }};
}});
</script>
"""
    return _page(module, body)


def project_page(store: Store, module: str, project: str) -> str:
    existing = store.list_projects(module)
    sessions = store.project_sessions(module, project)
    by_band: dict[str, list[dict]] = defaultdict(list)
    for s in sessions:
        for band in [b for b in (s.get("bands") or "").split(",") if b]:
            by_band[band].append(s)
    grouped: dict[str, list[str]] = defaultdict(list)
    for band in by_band:
        grouped[nr_range_class(band)].append(band)
    band_blocks = []
    for cls in NR_RANGE_ORDER:
        names = sorted(grouped.get(cls, []))
        if not names:
            continue
        hint = {
            "Low-band": "低於 1 GHz（約 450–960 MHz，如 n5/n8、B8/B28）",
            "Mid-band": "1–2.2 GHz（如 n1/n3、B1/B3）",
            "High-band": "2.2 GHz 以上（n7/n41、n78/n79、B7/B41）",
            "Ultra-high": "FR2 mmWave（n257 起）",
            "其他": "尚未對到頻段表",
        }.get(cls, "")
        rows_html = []
        for band in names:
            files = by_band[band]
            rats = {_rat_label(f.get("rat") or "", band) for f in files}
            kinds = {f.get("report_kind") or "uxm" for f in files}
            sources: list[str] = []
            for f in files:
                lab = plan_label(f.get("filename") or "", f.get("test_plan") or "")
                if lab and lab not in sources:
                    sources.append(lab)
            ntxt = str(len(files))
            if sources:
                ntxt = f"{len(files)}（{', '.join(sources)}）"
            rows_html.append(
                "<tr>"
                f"<td><label><input type=\"checkbox\" name=\"band\" value=\"{escape(band)}\" "
                f"data-range=\"{escape(cls)}\" checked> {escape(band)}</label></td>"
                f"<td>{escape(', '.join(sorted(rats)))}</td>"
                f"<td>{escape(', '.join(sorted(kinds))).upper()}</td>"
                f"<td>{escape(ntxt)}</td>"
                "</tr>"
            )
        band_blocks.append(
            f'<tbody class="band-group" data-range="{escape(cls)}">'
            f'<tr class="range-head"><td colspan="4">'
            f'<label><input type="checkbox" class="range-all" data-range="{escape(cls)}" checked> '
            f"<b>{escape(cls)}</b> <span class=\"muted\">{escape(hint)}</span></label>"
            f"</td></tr>"
            + "".join(rows_html)
            + "</tbody>"
        )
    options = []
    for p in existing:
        label = p["name"] + ("（目前）" if p["name"] == project else "")
        sel = " selected" if p["name"] == project else ""
        options.append(f'<option value="{escape(p["name"])}"{sel}>{escape(label)}</option>')
    file_rows = []
    for s in sessions:
        file_rows.append(
            "<tr>"
            f"<td><input type=\"checkbox\" name=\"sid\" value=\"{s['id']}\"></td>"
            f"<td>{escape(s['filename'])}</td>"
            f"<td>{escape(s.get('data_folder') or '')}</td>"
            f"<td>{escape(s['imei'])}</td>"
            f"<td>{escape(s.get('bands') or '')}</td>"
            f"<td>{escape(_rat_label(s.get('rat') or '', s.get('bands') or ''))}</td>"
            f"<td>{escape((s.get('report_kind') or 'uxm').upper())}</td>"
            f"<td class=\"{_vclass(s.get('overall_result') or '')}\">{escape(s.get('overall_result') or '')}</td>"
            "</tr>"
        )
    body = f"""
{_nav()}
<p class="muted"><a href="/db">測試資料庫</a> / <a href="/db/module?name={quote(module)}">{escape(module)}</a> / {escape(project)}</p>
<h1>{escape(module)} · {escape(project)}</h1>
{_tabs(module, project, "report")}
<div class="note">
這份 Excel 屬於 <b>UXM</b> 報告型式（Keysight UXM / RFA）。5G（NR）只會走 UXM。
4G 現在若從 UXM 匯入也用同一套表；以後 CMW500 的 4G 會另標 <b>CMW500</b>，不會跟 UXM 混成同一種報告。
</div>
<h2>專案名稱</h2>
<form class="row" onsubmit="return renameProject(event)">
  <input id="newProject" type="text" value="{escape(project)}" style="max-width:280px">
  <button type="submit">儲存專案名</button>
</form>
<p class="muted">可把 UNKNOWN 改成真實專案代號。只改這個模組底下的這個專案。</p>
<p><button type="button" class="danger" id="delProject">刪除這個專案</button></p>
<p class="muted">會刪除此專案底下全部已匯入 session，不會刪磁碟 CSV。</p>

<h2>依Band產出Excel Report</h2>
<p class="muted">勾選要進報告的 band。同一 band 若有多次量測（含重測）都會列入。檔數會標 Full Test 或 connection test；connection test 會進 Excel，並在 File／Note 獨立標出，不是完整 RF。</p>
<p><label><input type="checkbox" id="groupBands" checked> 依 NR 低／中／高／超高頻分組</label>
<span class="muted">（Low &lt;1 GHz、Mid 1–2.2 GHz、High ≥2.2 GHz 含 n78/n79、Ultra-high 僅 FR2）</span></p>
<table>
<thead><tr><th>Band</th><th>世代</th><th>報告型式</th><th>檔數</th></tr></thead>
{''.join(band_blocks) or '<tbody><tr><td colspan="4">沒有 band 資料，請先匯入。</td></tr></tbody>'}
</table>
<p style="margin-top:12px"><button type="button" id="exportBands">依Band產出Excel Report</button></p>
<div id="status"></div>

<h2>檔案（可改掛到別的專案）</h2>
<table>
<tr><th></th><th>檔名</th><th>資料夾</th><th>IMEI</th><th>Band</th><th>世代</th><th>型式</th><th>Overall</th></tr>
{''.join(file_rows)}
</table>
<p class="row" style="margin-top:12px">
  <select id="moveExisting" style="min-width:200px">
    <option value="">選擇已有專案</option>
    {''.join(options)}
  </select>
  <input id="moveTo" type="text" placeholder="輸入新專案名稱" style="max-width:220px">
  <input id="moveFolder" type="text" placeholder="資料夾（空白則沿用）" style="max-width:180px">
  <button type="button" class="secondary" id="moveBtn">把勾選的檔改掛過去</button>
</p>
<p class="muted">可改專案與資料夾。資料夾空白則沿用原資料夾名（在目標專案底下建立同名）。</p>

<script>
const moduleName = {module!r};
const projectName = {project!r};
const status = document.getElementById("status");
const groupBox = document.getElementById("groupBands");
function syncGroupHeads() {{
  document.querySelectorAll("tr.range-head").forEach((tr) => {{
    tr.style.display = groupBox && groupBox.checked ? "" : "none";
  }});
}}
if (groupBox) {{
  groupBox.onchange = syncGroupHeads;
  syncGroupHeads();
}}
document.querySelectorAll("input.range-all").forEach((box) => {{
  box.onchange = () => {{
    const cls = box.dataset.range;
    document.querySelectorAll('input[name=band][data-range="' + cls + '"]').forEach((el) => {{
      el.checked = box.checked;
    }});
  }};
}});
async function post(url, body) {{
  return fetch(url, {{method:"POST", headers:{{"Content-Type":"application/json"}}, body: JSON.stringify(body)}});
}}
function renameProject(ev) {{
  ev.preventDefault();
  const name = document.getElementById("newProject").value.trim();
  if (!name) {{ alert("專案名不可空白"); return false; }}
  post("/api/rename-project", {{module: moduleName, old: projectName, new: name}}).then(async (r) => {{
    const j = await r.json();
    if (!r.ok) {{ alert(j.error || "改名失敗"); return; }}
    location = "/db/project?module=" + encodeURIComponent(moduleName) + "&project=" + encodeURIComponent(name);
  }});
  return false;
}}
document.getElementById("exportBands").onclick = async () => {{
  const bands = Array.from(document.querySelectorAll("input[name=band]:checked")).map((el) => el.value);
  if (!bands.length) {{ status.textContent = "請至少選一個 band"; status.className="err"; return; }}
  status.className = "";
  status.textContent = "從資料庫產生 Excel Report…";
  const r = await post("/api/report", {{module: moduleName, project: projectName, bands}});
  if (!r.ok) {{
    const j = await r.json().catch(() => ({{error:"失敗"}}));
    status.className = "err";
    status.textContent = j.error || "產生失敗";
    return;
  }}
  const name = r.headers.get("X-Filename") || "UXM Report.xlsx";
  const blob = await r.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  URL.revokeObjectURL(a.href);
  status.className = "ok";
  status.textContent = "已下載 " + name;
}};
document.getElementById("delProject").onclick = async () => {{
  if (!confirm("刪除專案「" + projectName + "」以及底下全部 session？\\n不會刪磁碟上的 CSV。")) return;
  const r = await post("/api/delete-project", {{module: moduleName, project: projectName}});
  const j = await r.json();
  if (!r.ok) {{ alert(j.error || "刪除失敗"); return; }}
  location = "/db/module?name=" + encodeURIComponent(moduleName);
}};
document.getElementById("moveBtn").onclick = async () => {{
  const typed = document.getElementById("moveTo").value.trim();
  const picked = document.getElementById("moveExisting").value.trim();
  const dest = typed || picked;
  const ids = Array.from(document.querySelectorAll("input[name=sid]:checked")).map((el) => Number(el.value));
  if (!dest) {{ alert("請選擇已有專案，或輸入新專案名稱"); return; }}
  if (!ids.length) {{ alert("請勾選檔案"); return; }}
  const destFolder = document.getElementById("moveFolder").value.trim();
  const r = await post("/api/move-sessions", {{module: moduleName, ids, project: dest, data_folder: destFolder}});
  const j = await r.json();
  if (!r.ok) {{ alert(j.error || "移動失敗"); return; }}
  location.reload();
}};
</script>
"""
    return _page(f"{module} {project}", body)


def charts_page(store: Store, module: str, project: str, band: str, chart_id: str) -> str:
    import time

    sessions = store.project_sessions(module, project)
    bands = []
    for s in sessions:
        for b in (s.get("bands") or "").split(","):
            if b and b not in bands:
                bands.append(b)
    if not band and bands:
        band = bands[0]
    spec = next((c for c in CHARTS if c["id"] == chart_id), CHARTS[0])
    t0 = time.perf_counter()
    rows = store.chart_points(module, project, band, spec["test_like"], spec["item"]) if band else []
    ms = (time.perf_counter() - t0) * 1000
    plot = svg_lmh(rows, spec["ylabel"]) if rows else '<p class="muted">這個 band 沒有此測項的數字。</p>'
    grouped_opts: dict[str, list[str]] = defaultdict(list)
    for b in bands:
        grouped_opts[nr_range_class(b)].append(b)
    band_opt_html = []
    for cls in NR_RANGE_ORDER:
        names = sorted(grouped_opts.get(cls, []))
        if not names:
            continue
        band_opt_html.append(f'<optgroup label="{escape(cls)}">')
        for b in names:
            sel = " selected" if b == band else ""
            band_opt_html.append(f'<option value="{escape(b)}"{sel}>{escape(b)}</option>')
        band_opt_html.append("</optgroup>")
    band_opts = "".join(band_opt_html)
    chart_opts = "".join(
        f'<option value="{escape(c["id"])}"{" selected" if c["id"] == spec["id"] else ""}>{escape(c["title"])}</option>'
        for c in CHARTS
    )
    body = f"""
{_nav()}
<p class="muted"><a href="/db">測試資料庫</a> / <a href="/db/module?name={quote(module)}">{escape(module)}</a> / {escape(project)}</p>
<h1>{escape(module)} · {escape(project)}</h1>
{_tabs(module, project, "charts")}
<div class="note">
Excel 報告格式不變。這裡只畫<b>已匯入、這個專案</b>的量測對 3GPP 限值。<br>
查詢只取單一 band + 單一 Item，上限 800 點。這次查詢 {len(rows)} 列、{ms:.0f} ms。
報告多了以後請維持「一次一張圖」，不要一次載入全庫。
</div>
<form method="get" action="/db/charts" class="row">
  <input type="hidden" name="module" value="{escape(module)}">
  <input type="hidden" name="project" value="{escape(project)}">
  <label>Band <select name="band" onchange="this.form.submit()">{band_opts}</select></label>
  <label>測項 <select name="chart" onchange="this.form.submit()">{chart_opts}</select></label>
</form>
<h2>{escape(spec["title"])} <span class="muted">{escape(spec["spec"])} · {escape(band or "")}</span></h2>
{plot}
<p class="muted">Low/Mid/High 依該份 CSV 細節列 ARFCN 由低到高（TX 多為 UL）。同一 channel 的多個 RB／調變點都會畫上。</p>
"""
    return _page(f"{module} {project} 圖", body)
