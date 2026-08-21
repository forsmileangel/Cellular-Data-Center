"""Module → project index and UXM report export from the database."""

from __future__ import annotations

from collections import defaultdict
from html import escape
from urllib.parse import urlencode

from .analysis import MeasurementGroup, measurement_group_from_row
from .charts import CHARTS, svg_comparison, svg_lmh
from .review import _page, _vclass, site_nav
from .spec import NR_RANGE_ORDER, nr_range_class
from .parse import plan_label
from .store import Store


def _as_list(value: str | list[str] | tuple[str, ...] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    return [item for item in value if item]


def _hidden_multi(name: str, values: list[str]) -> str:
    return "".join(
        f'<input type="hidden" name="{escape(name)}" value="{escape(item)}">'
        for item in values
    )


def _work_url(
    module: str,
    project: str | list[str] = "",
    data_folder: str | list[str] = "",
    imei: str | list[str] = "",
    tab: str = "report",
    band: str = "",
    chart: str = "",
    color_by: str = "",
) -> str:
    q: list[tuple[str, str]] = [("module", module)]
    for item in _as_list(project):
        q.append(("project", item))
    for item in _as_list(data_folder):
        q.append(("data_folder", item))
    for item in _as_list(imei):
        q.append(("imei", item))
    if tab and tab != "report":
        q.append(("tab", tab))
    if band:
        q.append(("band", band))
    if chart:
        q.append(("chart", chart))
    if color_by:
        q.append(("color_by", color_by))
    return "/db/work?" + urlencode(q)


def _tabs(
    module: str,
    project: str,
    data_folder: str,
    imei: str,
    current: str,
) -> str:
    report = _work_url(module, project, data_folder, imei, "report")
    charts = _work_url(module, project, data_folder, imei, "charts")
    rcls = "tab on" if current == "report" else "tab"
    ccls = "tab on" if current == "charts" else "tab"
    return (
        '<p class="tabs">'
        f'<a class="{rcls}" href="{report}">報告總覽</a>'
        f'<a class="{ccls}" href="{charts}">統計圖表</a>'
        "</p>"
        "<style>"
        ".tabs { margin:12px 0 18px; }"
        ".tab { display:inline-block; padding:6px 14px; border:1px solid #ccc; "
        "margin-right:6px; text-decoration:none; color:#222; }"
        ".tab.on { background:var(--green-deep); color:#fff; border-color:var(--green-deep); }"
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


def _report_name_box() -> str:
    return """
<div class="name-box">
  <label>自填檔名
    <input id="reportTitle" type="text" placeholder="例如 SA Full Test" autocomplete="off">
  </label>
  <label class="chk"><input type="checkbox" id="incProject"> 帶入專案名稱</label>
  <label class="chk"><input type="checkbox" id="incImei"> 帶入 IMEI</label>
  <p class="muted" id="namePreview">預覽：會先放模組名稱，再依選項接專案、IMEI，最後是自填檔名。</p>
</div>
"""


def _report_name_script() -> str:
    return r"""
function uniqueData(selector, attr) {
  const seen = [];
  document.querySelectorAll(selector).forEach((el) => {
    const v = (el.getAttribute(attr) || "").trim();
    if (v && !seen.includes(v)) seen.push(v);
  });
  return seen;
}
function sanitizePart(s) {
  return String(s || "").replace(/[\\/:*?"<>|]+/g, "_").replace(/_+/g, "_").replace(/^[.\s_]+|[.\s_]+$/g, "");
}
function buildReportName() {
  const raw = (document.getElementById("reportTitle") || {}).value || "";
  const custom = sanitizePart(raw.replace(/\.xlsx$/i, "")) || "Excel Report";
  const exportSel = "input[name=exportSid]:checked";
  const fileSel = document.querySelectorAll("input[name=exportSid]").length ? exportSel : "input[name=sid]";
  const parts = [];
  const mods = (typeof moduleName === "string" && moduleName) ? [moduleName] : uniqueData(fileSel, "data-module");
  if (mods.length) parts.push(mods.length === 1 ? mods[0] : mods.join("-"));
  if (document.getElementById("incProject") && document.getElementById("incProject").checked) {
    const ps = (typeof projectName === "string" && projectName) ? [projectName] : uniqueData(fileSel, "data-project");
    if (ps.length) parts.push(ps.length === 1 ? ps[0] : ps.join("-"));
  }
  if (document.getElementById("incImei") && document.getElementById("incImei").checked) {
    const imeis = uniqueData(fileSel, "data-imei");
    if (imeis.length) parts.push(imeis.length === 1 ? imeis[0] : imeis.join("-"));
  }
  parts.push(custom);
  return sanitizePart(parts.join("_")) + ".xlsx";
}
function refreshNamePreview() {
  const el = document.getElementById("namePreview");
  if (el) el.textContent = "預覽：" + buildReportName();
}
["reportTitle", "incProject", "incImei"].forEach((id) => {
  const el = document.getElementById(id);
  if (!el) return;
  el.addEventListener("input", refreshNamePreview);
  el.addEventListener("change", refreshNamePreview);
});
document.querySelectorAll("input[name=exportSid]").forEach((el) => el.addEventListener("change", refreshNamePreview));
refreshNamePreview();
"""


def _msel(name: str, selected: list[str], options: list[str], all_label: str) -> str:
    chosen = [item for item in selected if item]
    shown = list(options)
    for item in chosen:
        if item not in shown:
            shown.append(item)
    picked = set(chosen)
    if not picked:
        summary = all_label
    elif len(picked) == 1:
        summary = next(iter(picked))
    else:
        summary = f"{len(picked)} 項"
    checks = []
    for option in shown:
        ck = " checked" if option in picked else ""
        checks.append(
            f'<label><input type="checkbox" name="{escape(name)}" value="{escape(option)}"{ck}> '
            f"{escape(option)}</label>"
        )
    inner = "".join(checks) or '<p class="muted">沒有選項</p>'
    return (
        f'<details class="msel">'
        f"<summary>{escape(summary)}</summary>"
        f'<div class="msel-panel">'
        f'<p class="msel-actions">'
        f'<button type="button" class="secondary msel-all">全選</button>'
        f'<button type="button" class="secondary msel-none">全不選</button>'
        f'<button type="button" class="secondary msel-inv">反選</button>'
        f"</p>"
        f"{inner}"
        f"</div></details>"
    )


def index_page(store: Store, **_unused) -> str:
    mods = store.list_modules()
    cards = []
    for m in mods:
        href = _work_url(m["model"])
        cards.append(
            f'<a class="card" href="{href}">'
            f"<h2>{escape(m['model'])}</h2>"
            f"<p>{m['projects']} 個專案 · {m['duts']} 個 IMEI · {m['sessions']} 份 session</p>"
            "</a>"
        )
    body = f"""
{_nav()}
<h1>測試資料庫</h1>
<p class="muted">先選模組（點卡片）。進去之後才有<strong>報告總覽</strong>和<strong>統計圖表</strong>；可再篩專案、資料夾、IMEI。</p>
<div class="cards">{''.join(cards) or '<p>還沒有資料。請先匯入或新增模組。</p>'}</div>
<h2>新增模組</h2>
<p class="row">
  <input id="newModule" type="text" placeholder="輸入新模組型號，例如 FN990A" style="max-width:280px">
  <button type="button" id="addModule">新增模組</button>
</p>
<form method="get" action="/db/work" class="row" style="margin-top:18px">
  <input name="imei" type="search" placeholder="用 IMEI 直接進入該模組工作區" style="max-width:280px">
  <button type="submit" class="secondary">找 IMEI</button>
</form>
<style>
.cards {{ display:flex; flex-wrap:wrap; gap:12px; margin-top:16px; }}
.card {{ display:block; min-width:220px; padding:16px 18px; border:1px solid #ccc; text-decoration:none; color:#222; }}
.card:hover {{ border-color:#afbeaf; }}
.card h2 {{ margin:0 0 6px; font-size:18px; color:var(--green-deep); }}
.card p {{ margin:0; color:#666; font-size:13px; }}
</style>
<script>
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
  location = "/db/work?module=" + encodeURIComponent(name);
}};
</script>
"""
    return _page("測試資料庫", body)


def _resolve_module(store: Store, module: str, imei: str | list[str]) -> str:
    if module:
        return module
    picked = _as_list(imei)
    if not picked:
        return ""
    mods: list[str] = []
    for r in store.filter_sessions(imei=picked):
        m = r.get("module") or ""
        if m and m not in mods:
            mods.append(m)
    return mods[0] if mods else ""


def work_page(
    store: Store,
    module: str = "",
    project: str | list[str] = "",
    data_folder: str | list[str] = "",
    imei: str | list[str] = "",
    tab: str = "report",
    band: str = "",
    chart_id: str = "",
    chart_group: str = "",
    color_by: str = "",
) -> str:
    module = _resolve_module(store, module, imei)
    if not module:
        return _page(
            "測試資料庫",
            f'{_nav()}<p>請先從<a href="/db">測試資料庫</a>選一個模組。</p>',
        )
    tab = "charts" if tab == "charts" else "report"
    selected_projects = _as_list(project)
    selected_folders = _as_list(data_folder)
    selected_imeis = _as_list(imei)
    project_names = [p["name"] for p in store.list_projects(module)]
    folder_names: list[str] = []
    for name in selected_projects or project_names:
        for folder in store.list_folders(module, name):
            if folder not in folder_names:
                folder_names.append(folder)
    scoped = store.filter_sessions(module, selected_projects, selected_folders)
    imei_names = sorted({r["imei"] for r in scoped if r.get("imei")})
    rows = store.filter_sessions(module, selected_projects, selected_folders, selected_imeis)
    if not selected_projects:
        title = module
        crumb_tail = ""
    elif len(selected_projects) == 1:
        title = f"{module} · {selected_projects[0]}"
        crumb_tail = f" / {escape(selected_projects[0])}"
    else:
        title = f"{module} · {len(selected_projects)} 個專案"
        crumb_tail = f" / {len(selected_projects)} 個專案"
    crumb = (
        f'{_nav()}<p class="muted"><a href="/db">測試資料庫</a> / {escape(module)}'
        + crumb_tail
        + "</p>"
    )
    keep = ""
    if tab == "charts":
        if band:
            keep += f'<input type="hidden" name="band" value="{escape(band)}">'
        if chart_id:
            keep += f'<input type="hidden" name="chart" value="{escape(chart_id)}">'
        if chart_group:
            keep += f'<input type="hidden" name="group" value="{escape(chart_group)}">'
        if color_by:
            keep += f'<input type="hidden" name="color_by" value="{escape(color_by)}">'
    admin_project = selected_projects[0] if len(selected_projects) == 1 else ""
    filt = f"""
<form method="get" action="/db/work" class="filters">
  <input type="hidden" name="module" value="{escape(module)}">
  <input type="hidden" name="tab" value="{escape(tab)}">
  {keep}
  <label>專案 {_msel("project", selected_projects, project_names, "全部專案")}</label>
  <label>資料夾 {_msel("data_folder", selected_folders, folder_names, "全部資料夾")}</label>
  <label>IMEI {_msel("imei", selected_imeis, imei_names, "全部 IMEI")}</label>
  <button type="submit">套用篩選</button>
</form>
"""
    if tab == "charts":
        inner = _charts_panel(
            store,
            module,
            selected_projects,
            selected_folders,
            selected_imeis,
            band,
            chart_id,
            chart_group,
            color_by,
            rows,
        )
    else:
        inner = _report_panel(store, module, admin_project, "", "", rows)
    body = f"""
{crumb}
<h1>{escape(title)}</h1>
{filt}
{_tabs(module, selected_projects, selected_folders, selected_imeis, tab)}
{inner}
<style>
.filters {{ display:flex; flex-wrap:wrap; gap:12px 18px; margin:14px 0; align-items:end; }}
.filters label {{ font-size:13px; }}
.filters select {{ display:block; margin-top:4px; min-width:160px; }}
.msel {{ position:relative; display:block; margin-top:4px; }}
.msel summary {{ cursor:pointer; min-width:160px; padding:4px 8px; border:1px solid #ccc;
  background:#fff; list-style:none; }}
.msel summary::-webkit-details-marker {{ display:none; }}
.msel-panel {{ position:absolute; z-index:6; background:#fff; border:1px solid #ccc;
  padding:8px; min-width:220px; max-height:260px; overflow:auto;
  box-shadow:0 2px 8px rgba(0,0,0,.08); }}
.msel-panel label {{ display:block; font-size:13px; margin:4px 0; }}
.msel-actions {{ display:flex; gap:6px; margin:0 0 8px; }}
</style>
<script>
document.querySelectorAll("details.msel").forEach((box) => {{
  const panel = box.querySelector(".msel-panel");
  if (!panel) return;
  const boxes = () => panel.querySelectorAll('input[type=checkbox]');
  panel.querySelector(".msel-all")?.addEventListener("click", () => {{
    boxes().forEach((el) => {{ el.checked = true; }});
  }});
  panel.querySelector(".msel-none")?.addEventListener("click", () => {{
    boxes().forEach((el) => {{ el.checked = false; }});
  }});
  panel.querySelector(".msel-inv")?.addEventListener("click", () => {{
    boxes().forEach((el) => {{ el.checked = !el.checked; }});
  }});
}});
</script>
"""
    return _page(title, body)


def _report_panel(
    store: Store,
    module: str,
    project: str,
    data_folder: str,
    imei: str,
    rows: list[dict],
) -> str:
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
            f'<tr class="range-head"><td colspan="2">'
            f'<label><input type="checkbox" class="range-all" data-range="{escape(cls)}" checked> '
            f"<b>{escape(cls)}</b></label></td></tr>"
            + "".join(rows_html)
            + "</tbody>"
        )
    file_rows = []
    existing = store.list_projects(module)
    options = []
    for p in existing:
        label = p["name"] + ("（目前）" if p["name"] == project else "")
        sel = " selected" if p["name"] == project else ""
        options.append(f'<option value="{escape(p["name"])}"{sel}>{escape(label)}</option>')
    for s in rows:
        kind = (s.get("report_kind") or "uxm").lower()
        checked = " checked" if kind == "uxm" else ""
        kind_label = kind.upper()
        file_rows.append(
            "<tr>"
            f"<td><input type=\"checkbox\" name=\"exportSid\" value=\"{s['id']}\"{checked}"
            f" data-module=\"{escape(s.get('module') or '')}\""
            f" data-project=\"{escape(s.get('project') or '')}\""
            f" data-imei=\"{escape(s.get('imei') or '')}\""
            f" data-kind=\"{escape(kind)}\"></td>"
            f"<td>{escape(s.get('filename') or '')}</td>"
            f"<td>{escape(s.get('data_folder') or '')}</td>"
            f"<td>{escape(s.get('imei') or '')}</td>"
            f"<td>{escape(s.get('bands') or '')}</td>"
            f"<td>{escape(kind_label)}</td>"
            f"<td class=\"{_vclass(s.get('overall_result') or '')}\">{escape(s.get('overall_result') or '')}</td>"
            "</tr>"
        )
    admin = ""
    if project:
        admin = f"""
<details>
<summary>專案管理（改名、刪除、改掛檔）</summary>
<form class="row" onsubmit="return renameProject(event)">
  <input id="newProject" type="text" value="{escape(project)}" style="max-width:280px">
  <button type="submit">儲存專案名</button>
</form>
<p><button type="button" class="danger" id="delProject">刪除這個專案</button></p>
<p class="row">
  <select id="moveExisting" style="min-width:200px">
    <option value="">選擇已有專案</option>
    {''.join(options)}
  </select>
  <input id="moveTo" type="text" placeholder="輸入新專案名稱" style="max-width:220px">
  <input id="moveFolder" type="text" placeholder="資料夾（空白則沿用）" style="max-width:180px">
  <button type="button" class="secondary" id="moveBtn">把勾選的檔改掛過去</button>
</p>
</details>
"""
    return f"""
<div class="note">
這份 Excel 屬於 <b>UXM</b> 報告。CMW500 檔會標型式且預設不勾；請不要跟 UXM 混成同一份 Excel。
connection test 仍會列入並在 Excel 獨立標註。
</div>
<h2>符合的檔</h2>
<p class="muted">{len(rows)} 個檔。UXM 預設勾選；可勾掉不要的檔再出報告。</p>
<p class="row">
  <button type="button" class="secondary" id="fileAll">全選 UXM</button>
  <button type="button" class="secondary" id="fileNone">全不選</button>
</p>
<table>
<tr><th></th><th>檔名</th><th>資料夾</th><th>IMEI</th><th>Band</th><th>型式</th><th>Overall</th></tr>
{''.join(file_rows) or '<tr><td colspan="7">沒有檔案。</td></tr>'}
</table>
<h2>依Band產出Excel Report</h2>
<p><label><input type="checkbox" id="groupBands" checked> 依 NR 低／中／高／超高頻分組</label></p>
<table>
<thead><tr><th>Band</th><th>檔數</th></tr></thead>
{''.join(band_blocks) or '<tbody><tr><td colspan="2">沒有 band 資料。</td></tr></tbody>'}
</table>
<p style="margin-top:12px"><button type="button" id="exportBands">依Band產出Excel Report</button></p>
{_report_name_box()}
<div id="status"></div>
{admin}
<script>
const moduleName = {module!r};
const projectName = {project!r};
function selectedExportIds() {{
  return Array.from(document.querySelectorAll('input[name=exportSid]:checked')).map((el) => Number(el.value));
}}
const fileAll = document.getElementById("fileAll");
const fileNone = document.getElementById("fileNone");
if (fileAll) fileAll.onclick = () => {{
  document.querySelectorAll('input[name=exportSid]').forEach((el) => {{
    el.checked = (el.getAttribute("data-kind") || "uxm") === "uxm";
  }});
  refreshNamePreview();
}};
if (fileNone) fileNone.onclick = () => {{
  document.querySelectorAll('input[name=exportSid]').forEach((el) => {{ el.checked = false; }});
  refreshNamePreview();
}};
document.querySelectorAll("input.range-all").forEach((box) => {{
  box.onchange = () => {{
    const cls = box.dataset.range;
    document.querySelectorAll('input[name=band][data-range="' + cls + '"]').forEach((el) => {{
      el.checked = box.checked;
    }});
  }};
}});
const groupBox = document.getElementById("groupBands");
if (groupBox) {{
  groupBox.onchange = () => {{
    document.querySelectorAll("tr.range-head").forEach((tr) => {{
      tr.style.display = groupBox.checked ? "" : "none";
    }});
  }};
}}
document.getElementById("exportBands").onclick = async () => {{
  const bands = Array.from(document.querySelectorAll("input[name=band]:checked")).map((el) => el.value);
  const ids = selectedExportIds();
  const status = document.getElementById("status");
  if (!ids.length) {{ status.textContent = "請至少勾選一個檔"; status.className="err"; return; }}
  if (!bands.length) {{ status.textContent = "請至少選一個 band"; status.className="err"; return; }}
  status.className = "";
  status.textContent = "從資料庫產生 Excel Report…";
  const filename = buildReportName();
  const r = await fetch("/api/report", {{
    method: "POST",
    headers: {{"Content-Type": "application/json"}},
    body: JSON.stringify({{module: moduleName, project: projectName, bands, ids, filename}})
  }});
  if (!r.ok) {{
    const j = await r.json().catch(() => ({{error:"失敗"}}));
    status.className = "err";
    status.textContent = j.error || "產生失敗";
    return;
  }}
  const name = filename || r.headers.get("X-Filename") || "Excel Report.xlsx";
  const blob = await r.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  URL.revokeObjectURL(a.href);
  status.className = "ok";
  status.textContent = "已下載 " + name;
}};
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
    location = "/db/work?module=" + encodeURIComponent(moduleName) + "&project=" + encodeURIComponent(name);
  }});
  return false;
}}
const delProject = document.getElementById("delProject");
if (delProject) delProject.onclick = async () => {{
  if (!confirm("刪除專案「" + projectName + "」以及底下全部 session？\\n不會刪磁碟上的檔。")) return;
  const r = await post("/api/delete-project", {{module: moduleName, project: projectName}});
  const j = await r.json();
  if (!r.ok) {{ alert(j.error || "刪除失敗"); return; }}
  location = "/db/work?module=" + encodeURIComponent(moduleName);
}};
const moveBtn = document.getElementById("moveBtn");
if (moveBtn) moveBtn.onclick = async () => {{
  const typed = document.getElementById("moveTo").value.trim();
  const picked = document.getElementById("moveExisting").value.trim();
  const dest = typed || picked;
  const ids = selectedExportIds();
  if (!dest) {{ alert("請選擇已有專案，或輸入新專案名稱"); return; }}
  if (!ids.length) {{ alert("請勾選檔案"); return; }}
  const destFolder = document.getElementById("moveFolder").value.trim();
  const r = await post("/api/move-sessions", {{module: moduleName, ids, project: dest, data_folder: destFolder}});
  const j = await r.json();
  if (!r.ok) {{ alert(j.error || "移動失敗"); return; }}
  location.reload();
}};
{_report_name_script()}
</script>
"""


def _color_key(row: dict, mode: str) -> str:
    if mode == "project":
        return row.get("project") or "（無專案）"
    if mode == "folder":
        return row.get("data_folder") or "UNKNOWN"
    return row.get("imei") or "（無 IMEI）"


def _auto_color_mode(rows: list[dict]) -> str:
    for mode, field in (("imei", "imei"), ("folder", "data_folder"), ("project", "project")):
        if len({(row.get(field) or "") for row in rows}) > 1:
            return mode
    return ""


def _plot_rows(rows: list[dict], ylabel: str, color_by: str) -> str:
    mode = color_by if color_by in ("imei", "folder", "project") else _auto_color_mode(rows)
    if not mode:
        return svg_lmh(rows, ylabel)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[_color_key(row, mode)].append(row)
    series = [(label, grouped[label]) for label in sorted(grouped)]
    if len(series) <= 1:
        return svg_lmh(rows, ylabel)
    return svg_comparison(series, ylabel)


def _charts_panel(
    store: Store,
    module: str,
    project: str | list[str],
    data_folder: str | list[str],
    imei: str | list[str],
    band: str,
    chart_id: str,
    chart_group: str,
    color_by: str,
    sessions: list[dict],
) -> str:
    import time

    bands = []
    for s in sessions:
        for b in (s.get("bands") or "").split(","):
            if b and b not in bands:
                bands.append(b)
    if not band and bands:
        band = bands[0]
    spec = next((c for c in CHARTS if c["id"] == chart_id), CHARTS[0])
    t0 = time.perf_counter()
    rows = (
        store.chart_points(
            module,
            project,
            band,
            spec["test_like"],
            spec["item"],
            data_folder=data_folder,
            imei=imei,
        )
        if band
        else []
    )
    ms = (time.perf_counter() - t0) * 1000
    buckets: dict[tuple[str, ...], list[dict]] = defaultdict(list)
    templates: dict[tuple[str, ...], MeasurementGroup] = {}
    for row in rows:
        group = measurement_group_from_row(row)
        buckets[group.signature].append(row)
        templates[group.signature] = group
    groups = [
        MeasurementGroup(*signature, count=len(buckets[signature]))
        for signature in sorted(buckets)
    ]
    requested = MeasurementGroup.from_token(chart_group) if chart_group else None
    selected = next(
        (group for group in groups if requested and group.signature == requested.signature),
        groups[0] if groups else None,
    )
    selected_rows = buckets.get(selected.signature, []) if selected else []
    plot = (
        _plot_rows(selected_rows, spec["ylabel"], color_by)
        if selected_rows
        else '<p class="muted">這個 band 沒有此測項的數字。</p>'
    )
    group_opts = []
    for group in groups:
        context = " · ".join(
            value
            for value in (
                group.bandwidth,
                group.scs,
                group.modulation,
                group.rb,
                group.condition,
            )
            if value
        )
        limits = f"[{group.lower_limit or '—'}, {group.upper_limit or '—'}] {group.unit}".strip()
        label = f"{context or '一般條件'} · {limits} · {group.count} 筆"
        selected_attr = " selected" if selected and group.signature == selected.signature else ""
        group_opts.append(
            f'<option value="{group.token}"{selected_attr}>{escape(label)}</option>'
        )
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
    chart_opts = []
    last_group = None
    for c in CHARTS:
        group = c.get("group") or c.get("spec") or ""
        if group != last_group:
            if last_group is not None:
                chart_opts.append("</optgroup>")
            chart_opts.append(f'<optgroup label="{escape(group)}">')
            last_group = group
        sel = " selected" if c["id"] == spec["id"] else ""
        chart_opts.append(
            f'<option value="{escape(c["id"])}"{sel}>{escape(c["title"])}</option>'
        )
    if last_group is not None:
        chart_opts.append("</optgroup>")
    chart_opts = "".join(chart_opts)
    color_mode = color_by if color_by in ("imei", "folder", "project") else "auto"
    color_opts = []
    for value, label in (("auto", "自動"), ("imei", "IMEI"), ("folder", "資料夾"), ("project", "專案")):
        sel = " selected" if value == color_mode else ""
        color_opts.append(f'<option value="{escape(value)}"{sel}>{escape(label)}</option>')
    hidden = (
        f'<input type="hidden" name="module" value="{escape(module)}">'
        f'<input type="hidden" name="tab" value="charts">'
        + _hidden_multi("project", _as_list(project))
        + _hidden_multi("data_folder", _as_list(data_folder))
        + _hidden_multi("imei", _as_list(imei))
    )
    return f"""
<div class="note">
圖跟報告用同一組篩選（模組／專案／資料夾／IMEI，可複選比較）。一次一個 band、一個測項。
這次查到 {len(rows)} 列；目前精確條件組 {len(selected_rows)} 列、{ms:.0f} ms。系統不平均不同 LSL／USL。
多個來源時用顏色區分。點一下資料點可把數值留在圖上。
</div>
<form method="get" action="/db/work" class="row">
  {hidden}
  <label>Band <select name="band" onchange="this.form.submit()">{''.join(band_opt_html)}</select></label>
  <label>測項 <select name="chart" onchange="this.form.submit()">{chart_opts}</select></label>
  <label>精確條件 <select name="group" onchange="this.form.submit()">{''.join(group_opts)}</select></label>
  <label>來源著色 <select name="color_by" onchange="this.form.submit()">{''.join(color_opts)}</select></label>
</form>
<h2>{escape(spec["title"])} <span class="muted">{escape(spec["spec"])} · {escape(band or "")}</span></h2>
{plot}
"""


def module_page(store: Store, module: str) -> str:
    return work_page(store, module=module)


def project_page(store: Store, module: str, project: str) -> str:
    return work_page(store, module=module, project=project, tab="report")


def charts_page(store: Store, module: str, project: str, band: str, chart_id: str) -> str:
    return work_page(
        store,
        module=module,
        project=project,
        tab="charts",
        band=band,
        chart_id=chart_id,
    )
