"""Local import UI: pick a CSV folder, fill module/project, download Excel."""

from __future__ import annotations

import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .parse import list_report_files
from .pipeline import run_build, run_ingest, run_report_from_db
from .analysis_pages import analysis_index, analysis_module, analysis_session
from .catalog import index_page as db_index, work_page as db_work
from .review import list_page, session_page, site_nav
from .spec_pages import spec_page
from .store import Store
from .ts38521_figures import ASSET_DIR as SPEC_FIG_DIR

ROOT = Path(__file__).resolve().parents[1]

HOME_PAGE = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cellular Specifications and Reporting Analysis Center</title>
<style>
  :root { --green:#008787; --ink:#222; --muted:#666; --line:#ccc; --bg:#f6f6f6; }
  * { box-sizing:border-box; }
  body { margin:0; font-family:Segoe UI, Microsoft JhengHei, sans-serif; color:var(--ink); background:var(--bg); }
  main { max-width:860px; margin:40px auto; background:#fff; border:1px solid var(--line); padding:28px 32px; }
  h1 { margin:0 0 6px; font-size:20px; color:var(--green); line-height:1.3; }
  .sub { color:var(--muted); margin:0 0 20px; font-size:14px; }
  .home-cards { display:grid; grid-template-columns:repeat(auto-fill,minmax(170px,1fr)); gap:12px; }
  .home-card { display:block; padding:16px 16px 14px; border:1px solid var(--line); text-decoration:none; color:var(--ink); background:#fff; min-height:96px; }
  .home-card:hover { border-color:var(--green); }
  .home-card strong { display:block; color:var(--green); font-size:15px; margin-bottom:6px; }
  .home-card span { display:block; color:var(--muted); font-size:12px; line-height:1.4; }
  .srv-off { position:fixed; top:6px; right:10px; z-index:20; font-size:11px; color:#aaa; max-width:160px; margin:0; }
  .srv-off summary { cursor:pointer; list-style:none; color:#bbb; user-select:none; text-align:right; }
  .srv-off summary::-webkit-details-marker { display:none; }
  .srv-off[open] { background:#fff; border:1px solid #ddd; padding:6px 8px; }
  .srv-off a { display:block; margin-top:6px; color:#999; text-decoration:none; }
  .srv-off a:hover { color:#8b0000; }
</style>
</head>
<body>
<details class="srv-off">
  <summary>本機</summary>
  <a href="#" onclick="uxmShutdown();return false">關閉本地伺服器</a>
</details>
<main>
  <h1>Cellular Specifications and Reporting Analysis Center</h1>
  <p class="sub">選一個功能進入。</p>
  <div class="home-cards">
    <a class="home-card" href="/import"><strong>報告匯入</strong><span>把 UXM CSV 放進測試資料庫，或順便出 Excel</span></a>
    <a class="home-card" href="/db"><strong>測試資料庫</strong><span>篩選後依 Band 產出 Excel Report</span></a>
    <a class="home-card" href="/review"><strong>資料審核</strong><span>依模組／專案查匯入紀錄</span></a>
    <a class="home-card" href="/analysis"><strong>資料分析</strong><span>量測相對 LSL／USL 的位置</span></a>
    <a class="home-card" href="/spec"><strong>測試規格對照</strong><span>RFA 測項對 38.521-1</span></a>
    <a class="home-card" href="/ref"><strong>3GPP法規參考</strong><span>依規格號：38.521、38.508、38.213</span></a>
  </div>
</main>
<script>
async function uxmShutdown() {
  if (!confirm("關閉本地伺服器？關閉後請雙擊「開啟介面.bat」再開。")) return;
  await fetch("/api/shutdown", {method: "POST"});
  document.body.innerHTML = "<main><p>本地伺服器已關閉。要用時請雙擊專案資料夾裡的「開啟介面.bat」。</p></main>";
}
</script>
</body>
</html>
"""

PAGE = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cellular Specifications and Reporting Analysis Center</title>
<style>
  :root { --green:#008787; --ink:#222; --muted:#666; --line:#ccc; --bg:#f6f6f6; }
  * { box-sizing:border-box; }
  body { margin:0; font-family:Segoe UI, Microsoft JhengHei, sans-serif; color:var(--ink); background:var(--bg); }
  main { max-width:860px; margin:40px auto; background:#fff; border:1px solid var(--line); padding:28px 32px; }
  h1 { margin:0 0 6px; font-size:20px; color:var(--green); line-height:1.3; }
  .sub { color:var(--muted); margin:0 0 16px; font-size:14px; }
  .home-cards { display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:10px; margin:0 0 26px; }
  .home-card { display:block; padding:14px 14px 12px; border:1px solid var(--line); text-decoration:none; color:var(--ink); background:#fff; }
  .home-card:hover { border-color:var(--green); }
  .home-card strong { display:block; color:var(--green); font-size:15px; margin-bottom:4px; }
  .home-card span { display:block; color:var(--muted); font-size:12px; line-height:1.4; }
  label { display:block; font-weight:600; margin:14px 0 6px; }
  .req { color:#a00; }
  input[type=text], input[type=search], select { width:100%; padding:8px 10px; border:1px solid var(--line); font-size:14px; }
  .row { display:flex; gap:8px; }
  .pick-new { margin-top:8px; }
  .row input { flex:1; }
  button { background:var(--green); color:#fff; border:0; padding:8px 14px; cursor:pointer; font-size:14px; }
  button.secondary { background:#fff; color:var(--green); border:1px solid var(--green); }
  button:disabled { opacity:.5; cursor:default; }
  .hint { color:var(--muted); font-size:12px; margin-top:4px; }
  #preview { margin-top:10px; font-size:13px; white-space:pre-wrap; }
  #status { margin-top:16px; font-size:14px; }
  #status.err { color:#a00; }
  #status.ok { color:var(--green); }
  details { margin-top:28px; color:var(--muted); font-size:13px; }
  details summary { cursor:pointer; color:var(--ink); }
  .srv-off { position:fixed; top:6px; right:10px; z-index:20; font-size:11px; color:#aaa; max-width:160px; margin:0; }
  .srv-off summary { cursor:pointer; list-style:none; color:#bbb; user-select:none; text-align:right; }
  .srv-off summary::-webkit-details-marker { display:none; }
  .srv-off[open] { background:#fff; border:1px solid #ddd; padding:6px 8px; }
  .srv-off a { display:block; margin-top:6px; color:#999; text-decoration:none; }
  .srv-off a:hover { color:#8b0000; }
  table { border-collapse:collapse; margin-top:8px; width:100%; }
  td, th { border:1px solid var(--line); padding:6px 8px; text-align:left; }
  .nav { margin-bottom:16px; font-size:14px; }
  .nav a { color:var(--green); }
</style>
</head>
<body>
<details class="srv-off">
  <summary>本機</summary>
  <a href="#" onclick="uxmShutdown();return false">關閉本地伺服器</a>
</details>
<main>
NAV_SLOT
  <h1>報告匯入</h1>
  <p class="sub">把 CSV 放進庫。要出 Excel，也可在這裡做，或進資料庫：模組 → 專案 → 勾 band。</p>

  <label>模組型號 <span class="req">*</span></label>
  <select id="modulePick">
    <option value="">（請選擇已有模組）</option>
    <option value="__new__">＋ 新增模組型號…</option>
  </select>
  <div id="moduleNewWrap" class="pick-new" hidden>
    <input id="moduleNew" type="text" placeholder="輸入新模組型號，例如 FN990B">
  </div>
  <div class="hint">必填。有現成的請下拉選；沒有才新增。同一型號可有多個 IMEI。</div>

  <label>專案</label>
  <input id="projectSearch" type="search" placeholder="搜尋已有專案" autocomplete="off">
  <select id="projectPick">
    <option value="">不指定（UNKNOWN）</option>
    <option value="__new__">＋ 新增專案…</option>
  </select>
  <div id="projectNewWrap" class="pick-new" hidden>
    <input id="projectNew" type="text" placeholder="輸入新專案名稱">
  </div>
  <div class="hint">選填。先搜尋或下拉選已有專案；沒有才新增。都不填則存 UNKNOWN。</div>

  <label>資料夾</label>
  <input id="dataFolderSearch" type="search" placeholder="搜尋已有資料夾" autocomplete="off">
  <select id="dataFolderPick">
    <option value="">不指定（UNKNOWN）</option>
    <option value="__new__">＋ 新增資料夾…</option>
  </select>
  <div id="dataFolderNewWrap" class="pick-new" hidden>
    <input id="dataFolderNew" type="text" placeholder="例如 TA17、TA20、e-test、pre-DVT">
  </div>
  <div class="hint">專案底下再分一層，避免 TA17／TA20 或 e-test／pre-DVT 混在一起。選既有或新增；空白則 UNKNOWN。</div>

  <label>報告檔所在路徑 <span class="req">*</span></label>
  <div class="row">
    <input id="folder" type="text" placeholder="選擇或貼上本機資料夾路徑">
    <button type="button" class="secondary" id="browse">瀏覽</button>
  </div>
  <div class="hint">列出第一層 *.csv 與 *.pdf（略過 BandCombinations）。請勾選要進資料庫的檔；測錯留檔不要勾，以免汙染統計。PDF 沒有原 CSV 時會還原並標註折行／缺欄。</div>
  <div id="preview"></div>

  <p style="margin-top:22px">
    <button type="button" id="ingest">只匯入選取檔</button>
    <button type="button" id="build">匯入並產生 Excel</button>
  </p>
  <div id="status"></div>

  <details>
    <summary>Result 星號怎麼標</summary>
    <p>星號來自 CSV 摘要列的 <b>Skip</b>，不是任意加上去的。Keysight RFA 對 3GPP 不適用的測項（例如部分 band 的 A-MPR、Additional SEM、UTRA ACLR）會標 Skip。</p>
    <table>
      <tr><th>結果</th><th>條件</th></tr>
      <tr><td>Pass</td><td>有跑的測項全過，且沒有 Skip</td></tr>
      <tr><td>Pass*</td><td>有跑的測項全過，但有 Skip（不適用／未執行）</td></tr>
      <tr><td>Fail</td><td>至少一筆 Fail，且沒有 Skip</td></tr>
      <tr><td>Fail*</td><td>至少一筆 Fail，且同時有 Skip</td></tr>
    </table>
    <p>所以 File 9 只重測 6.2.2 且全過、沒有 Skip → Pass。File 6 重測失敗、沒有 Skip → Fail。Full Test 常有 Skip → Pass* 或 Fail*。</p>
  </details>
</main>
<script>
const $ = (id) => document.getElementById(id);
let catalog = {modules: []};
function selectedFiles() {
  return Array.from(document.querySelectorAll('#preview input[type=checkbox]:checked')).map((el) => el.value);
}
function chosenModule() {
  const pick = $('modulePick').value;
  if (pick === '__new__') return $('moduleNew').value.trim();
  return pick.trim();
}
function chosenProject() {
  const pick = $('projectPick').value;
  if (pick === '__new__') return $('projectNew').value.trim();
  return pick.trim();
}
function chosenDataFolder() {
  const pick = $('dataFolderPick').value;
  if (pick === '__new__') return $('dataFolderNew').value.trim();
  return pick.trim();
}
function fillModuleSelect(keep) {
  const sel = $('modulePick');
  const cur = keep || sel.value;
  sel.innerHTML = '';
  const ph = document.createElement('option');
  ph.value = '';
  ph.textContent = catalog.modules.length ? '（請選擇已有模組）' : '（尚無模組，請新增）';
  sel.appendChild(ph);
  catalog.modules.forEach((m) => {
    const o = document.createElement('option');
    o.value = m.model;
    o.textContent = m.model;
    sel.appendChild(o);
  });
  const nw = document.createElement('option');
  nw.value = '__new__';
  nw.textContent = '＋ 新增模組型號…';
  sel.appendChild(nw);
  if ([...sel.options].some((o) => o.value === cur)) sel.value = cur;
  else if (!catalog.modules.length) sel.value = '__new__';
  toggleNew('module');
}
function projectNamesFor(module) {
  const m = catalog.modules.find((x) => x.model === module);
  return m ? m.projects.slice() : [];
}
function fillProjectSelect(keep) {
  const module = $('modulePick').value;
  const names = (module && module !== '__new__') ? projectNamesFor(module) : [];
  const q = $('projectSearch').value.trim().toLowerCase();
  const filtered = q ? names.filter((n) => n.toLowerCase().includes(q)) : names;
  const sel = $('projectPick');
  const cur = keep || sel.value;
  sel.innerHTML = '';
  const ph = document.createElement('option');
  ph.value = '';
  ph.textContent = '不指定（UNKNOWN）';
  sel.appendChild(ph);
  filtered.forEach((n) => {
    const o = document.createElement('option');
    o.value = n;
    o.textContent = n;
    sel.appendChild(o);
  });
  const nw = document.createElement('option');
  nw.value = '__new__';
  nw.textContent = '＋ 新增專案…';
  sel.appendChild(nw);
  if ([...sel.options].some((o) => o.value === cur)) sel.value = cur;
  toggleNew('project');
}
function toggleNew(kind) {
  const pick = $(kind + 'Pick').value === '__new__';
  $(kind + 'NewWrap').hidden = !pick;
  if (pick) $(kind + 'New').focus();
}
function folderNamesFor(module, project) {
  const m = catalog.modules.find((x) => x.model === module);
  if (!m || !m.folders || !project) return [];
  return (m.folders[project] || []).slice();
}
function fillDataFolderSelect(keep) {
  const module = $('modulePick').value;
  const project = chosenProject();
  const names = (module && module !== '__new__' && project && project !== '__new__')
    ? folderNamesFor(module, project) : [];
  const q = $('dataFolderSearch').value.trim().toLowerCase();
  const filtered = q ? names.filter((n) => n.toLowerCase().includes(q)) : names;
  const sel = $('dataFolderPick');
  const cur = keep || sel.value;
  sel.innerHTML = '';
  const ph = document.createElement('option');
  ph.value = '';
  ph.textContent = '不指定（UNKNOWN）';
  sel.appendChild(ph);
  filtered.forEach((n) => {
    const o = document.createElement('option');
    o.value = n;
    o.textContent = n;
    sel.appendChild(o);
  });
  const nw = document.createElement('option');
  nw.value = '__new__';
  nw.textContent = '＋ 新增資料夾…';
  sel.appendChild(nw);
  if ([...sel.options].some((o) => o.value === cur)) sel.value = cur;
  toggleNew('dataFolder');
}
async function loadCatalog() {
  const r = await fetch('/api/catalog');
  catalog = await r.json();
  if (!catalog.modules) catalog = {modules: []};
  fillModuleSelect($('modulePick').value);
  fillProjectSelect($('projectPick').value);
  fillDataFolderSelect($('dataFolderPick').value);
}
$('modulePick').addEventListener('change', () => {
  toggleNew('module');
  $('projectSearch').value = '';
  fillProjectSelect('');
  fillDataFolderSelect('');
});
$('projectPick').addEventListener('change', () => {
  toggleNew('project');
  $('dataFolderSearch').value = '';
  fillDataFolderSelect('');
});
$('projectSearch').addEventListener('input', () => fillProjectSelect($('projectPick').value));
$('dataFolderPick').addEventListener('change', () => toggleNew('dataFolder'));
$('dataFolderSearch').addEventListener('input', () => fillDataFolderSelect($('dataFolderPick').value));
loadCatalog();
async function preview() {
  const folder = $('folder').value.trim();
  $('preview').innerHTML = '';
  if (!folder) return;
  const r = await fetch('/api/preview?folder=' + encodeURIComponent(folder));
  const j = await r.json();
  if (!r.ok) { $('preview').textContent = j.error || '預覽失敗'; return; }
  const box = document.createElement('div');
  box.innerHTML = '<p>找到 ' + (j.csv_count||0) + ' 個 CSV、' + (j.pdf_count||0) + ' 個 PDF。'
    + '<button type="button" class="secondary" id="all">全選</button> '
    + '<button type="button" class="secondary" id="none">全不選</button></p>';
  j.files.forEach((name) => {
    const lab = document.createElement('label');
    lab.style.fontWeight = 'normal';
    lab.style.display = 'block';
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.value = name;
    cb.checked = true;
    lab.appendChild(cb);
    lab.appendChild(document.createTextNode(' ' + name));
    box.appendChild(lab);
  });
  $('preview').appendChild(box);
  $('all').onclick = () => document.querySelectorAll('#preview input[type=checkbox]').forEach((el) => { el.checked = true; });
  $('none').onclick = () => document.querySelectorAll('#preview input[type=checkbox]').forEach((el) => { el.checked = false; });
}
$('browse').onclick = async () => {
  const r = await fetch('/api/browse');
  const j = await r.json();
  if (j.path) { $('folder').value = j.path; preview(); }
};
$('folder').addEventListener('change', preview);
async function postJson(url, body) {
  return fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
}
$('ingest').onclick = async () => {
  const module = chosenModule();
  const project = chosenProject();
  const folder = $('folder').value.trim();
  const files = selectedFiles();
  const status = $('status');
  status.className = '';
  if (!module) { status.className='err'; status.textContent='模組型號必填：請選擇已有模組或新增'; return; }
  if (!folder) { status.className='err'; status.textContent='請選擇報告資料夾'; return; }
  if (!files.length) { status.className='err'; status.textContent='請至少勾選一個檔案'; return; }
  $('ingest').disabled = true;
  status.textContent = '匯入資料庫中…';
  try {
    const r = await postJson('/api/ingest', {module, project, data_folder: chosenDataFolder(), folder, files});
    const j = await r.json();
    if (!r.ok) { status.className='err'; status.textContent = j.error || '匯入失敗'; return; }
    status.className='ok';
    status.textContent = '已匯入 ' + j.sessions + ' 個檔、細節 ' + j.details + ' 列。可到資料審核查。';
    await loadCatalog();
    $('modulePick').value = module;
    fillProjectSelect(project || '');
  } catch (e) {
    status.className='err'; status.textContent = String(e);
  } finally { $('ingest').disabled = false; }
};
$('build').onclick = async () => {
  const module = chosenModule();
  const project = chosenProject();
  const folder = $('folder').value.trim();
  const files = selectedFiles();
  const status = $('status');
  status.className = '';
  if (!module) { status.className='err'; status.textContent='模組型號必填：請選擇已有模組或新增'; return; }
  if (!folder) { status.className='err'; status.textContent='請選擇報告資料夾'; return; }
  if (!files.length) { status.className='err'; status.textContent='請至少勾選一個檔案'; return; }
  $('build').disabled = true;
  status.textContent = '產生中（會呼叫 Excel，約數十秒）…';
  try {
    const r = await postJson('/api/build', {module, project, data_folder: chosenDataFolder(), folder, files});
    if (!r.ok) {
      const j = await r.json().catch(()=>({error:'產生失敗'}));
      status.className='err';
      status.textContent = j.error || ('HTTP '+r.status);
      return;
    }
    const name = r.headers.get('X-Filename') || (module + ' Module Test Report.xlsx');
    const blob = await r.blob();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = name;
    a.click();
    URL.revokeObjectURL(a.href);
    const note = r.headers.get('X-Note') || '';
    status.className='ok';
    status.textContent = '已下載 ' + name + (note ? '。' + note : '');
    await loadCatalog();
    $('modulePick').value = module;
    fillProjectSelect(project || '');
  } catch (e) {
    status.className='err';
    status.textContent = String(e);
  } finally {
    $('build').disabled = false;
  }
};
async function uxmShutdown() {
  if (!confirm("關閉本地伺服器？關閉後請雙擊「開啟介面.bat」再開。")) return;
  await fetch("/api/shutdown", {method: "POST"});
  document.body.innerHTML = "<main><p>本地伺服器已關閉。要用時請雙擊專案資料夾裡的「開啟介面.bat」。</p></main>";
}
</script>
</body>
</html>
"""


def catalog_payload(store: Store) -> dict:
    modules = []
    for m in store.list_modules():
        projects = [p["name"] for p in store.list_projects(m["model"])]
        folders = {p: store.list_folders(m["model"], p) for p in projects}
        modules.append({"model": m["model"], "projects": projects, "folders": folders})
    return {"modules": modules}


def _json(handler: BaseHTTPRequestHandler, code: int, payload: dict) -> None:
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def _pick_folder() -> str:
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askdirectory(title="選擇 UXM CSV 資料夾")
    root.destroy()
    return path or ""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        print("[ui]", fmt % args)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            raw = HOME_PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if parsed.path.startswith("/spec-fig/"):
            name = Path(parsed.path).name
            dest = (SPEC_FIG_DIR / name).resolve()
            root = SPEC_FIG_DIR.resolve()
            if dest.parent != root or dest.suffix.lower() != ".png" or not dest.is_file():
                self.send_error(404)
                return
            raw = dest.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Cache-Control", "public, max-age=86400")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if parsed.path == "/import":
            raw = PAGE.replace("NAV_SLOT", site_nav("報告匯入")).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if parsed.path == "/db":
            store = Store(ROOT / "uxm.db")
            try:
                html = db_index(store)
            finally:
                store.close()
            raw = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if parsed.path in ("/db/work", "/db/module", "/db/project", "/db/charts"):
            qs = parse_qs(parsed.query)
            module = (qs.get("module") or qs.get("name") or [""])[0]
            project = (qs.get("project") or [""])[0]
            data_folder = (qs.get("data_folder") or [""])[0]
            imei = (qs.get("imei") or [""])[0]
            tab = (qs.get("tab") or [""])[0]
            if parsed.path == "/db/charts":
                tab = "charts"
            elif parsed.path == "/db/project":
                tab = "report"
            band = (qs.get("band") or [""])[0]
            chart = (qs.get("chart") or ["621-power"])[0]
            store = Store(ROOT / "uxm.db")
            try:
                html = db_work(
                    store,
                    module,
                    project,
                    data_folder,
                    imei,
                    tab,
                    band,
                    chart,
                )
            finally:
                store.close()
            raw = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if parsed.path == "/review":
            qs = parse_qs(parsed.query)
            store = Store(ROOT / "uxm.db")
            try:
                html = list_page(
                    store,
                    (qs.get("module") or [""])[0],
                    (qs.get("project") or [""])[0],
                )
            finally:
                store.close()
            raw = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if parsed.path == "/review/session":
            qs = parse_qs(parsed.query)
            try:
                sid = int((qs.get("id") or ["0"])[0])
            except ValueError:
                sid = 0
            pf = (qs.get("pf") or [None])[0]
            test = (qs.get("test") or [None])[0]
            store = Store(ROOT / "uxm.db")
            try:
                html = session_page(store, sid, pf, test)
            finally:
                store.close()
            raw = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if parsed.path == "/ref" or parsed.path.startswith("/ref/"):
            from .ref_hub import ref_dispatch

            qs = parse_qs(parsed.query)
            slug = parsed.path[len("/ref") :].strip("/")
            # Old bookmarks /ref?id=6.2.1 still open the 38.521 page.
            if not slug and (qs.get("id") or qs.get("ch")):
                slug = "38.521"
            html = ref_dispatch(
                slug,
                (qs.get("id") or [""])[0],
                (qs.get("ch") or [""])[0],
            )
            raw = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if parsed.path == "/spec":
            qs = parse_qs(parsed.query)
            module = (qs.get("module") or [""])[0]
            project = (qs.get("project") or [""])[0]
            clause = (qs.get("clause") or ["6.2.1"])[0]
            store = Store(ROOT / "uxm.db")
            try:
                html = spec_page(store, module, project, clause)
            finally:
                store.close()
            raw = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if parsed.path == "/analysis":
            store = Store(ROOT / "uxm.db")
            try:
                html = analysis_index(store)
            finally:
                store.close()
            raw = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if parsed.path == "/analysis/module":
            qs = parse_qs(parsed.query)
            name = (qs.get("name") or [""])[0]
            applied = (qs.get("applied") or [""])[0] == "1"
            ids: list[int] = []
            for x in qs.get("id") or []:
                try:
                    ids.append(int(x))
                except (TypeError, ValueError):
                    continue
            store = Store(ROOT / "uxm.db")
            try:
                html = analysis_module(store, name, session_ids=ids if applied else None)
            finally:
                store.close()
            raw = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if parsed.path == "/analysis/session":
            try:
                sid = int((parse_qs(parsed.query).get("id") or ["0"])[0])
            except ValueError:
                sid = 0
            store = Store(ROOT / "uxm.db")
            try:
                html = analysis_session(store, sid)
            finally:
                store.close()
            raw = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if parsed.path == "/api/catalog":
            store = Store(ROOT / "uxm.db")
            try:
                payload = catalog_payload(store)
            finally:
                store.close()
            _json(self, 200, payload)
            return
        if parsed.path == "/api/browse":
            _json(self, 200, {"path": _pick_folder()})
            return
        if parsed.path == "/api/preview":
            qs = parse_qs(parsed.query)
            folder = (qs.get("folder") or [""])[0]
            path = Path(folder)
            if not path.is_dir():
                _json(self, 400, {"error": f"找不到資料夾: {folder}"})
                return
            files = list_report_files(path)
            names = [p.name for p in files]
            n_csv = sum(1 for p in files if p.suffix.lower() == ".csv")
            n_pdf = sum(1 for p in files if p.suffix.lower() == ".pdf")
            _json(self, 200, {"csv_count": n_csv, "pdf_count": n_pdf, "files": names})
            return
        self.send_error(404)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        if self.path == "/api/delete":
            try:
                sid = int(body.get("id") or 0)
            except (TypeError, ValueError):
                sid = 0
            store = Store(ROOT / "uxm.db")
            try:
                ok = store.delete_session(sid)
            finally:
                store.close()
            if not ok:
                _json(self, 404, {"error": "找不到這個 session"})
                return
            _json(self, 200, {"deleted": sid})
            return
        if self.path == "/api/delete-many":
            raw_ids = body.get("ids") or []
            ids = []
            for x in raw_ids:
                try:
                    ids.append(int(x))
                except (TypeError, ValueError):
                    continue
            store = Store(ROOT / "uxm.db")
            try:
                n = store.delete_sessions(ids)
            finally:
                store.close()
            _json(self, 200, {"deleted": n})
            return
        if self.path == "/api/ingest":
            files = body.get("files") or []
            if not isinstance(files, list):
                files = []
            try:
                n_sess, n_det = run_ingest(
                    body.get("folder") or "",
                    body.get("module") or "",
                    body.get("project") or "",
                    files=[str(x) for x in files],
                    data_folder=body.get("data_folder") or "",
                )
            except Exception as exc:
                _json(self, 400, {"error": str(exc)})
                return
            _json(self, 200, {"sessions": n_sess, "details": n_det})
            return
        if self.path == "/api/shutdown":
            httpd = getattr(Handler, "httpd", None)
            if httpd:
                threading.Thread(target=httpd.shutdown, daemon=True).start()
            _json(self, 200, {"ok": True})
            return
        if self.path == "/api/create-module":
            name = (body.get("name") or "").strip()
            if not name:
                _json(self, 400, {"error": "請輸入新模組型號"})
                return
            store = Store(ROOT / "uxm.db")
            try:
                store.upsert_module(name)
                store.conn.commit()
            finally:
                store.close()
            _json(self, 200, {"name": name})
            return
        if self.path == "/api/delete-project":
            store = Store(ROOT / "uxm.db")
            try:
                n = store.delete_project(
                    (body.get("module") or "").strip(),
                    (body.get("project") or "").strip(),
                )
            except Exception as exc:
                _json(self, 400, {"error": str(exc)})
                return
            finally:
                store.close()
            _json(self, 200, {"deleted_sessions": n})
            return
        if self.path == "/api/rename-project":
            store = Store(ROOT / "uxm.db")
            try:
                store.rename_project(
                    (body.get("module") or "").strip(),
                    (body.get("old") or "").strip(),
                    (body.get("new") or "").strip(),
                )
            except Exception as exc:
                _json(self, 400, {"error": str(exc)})
                return
            finally:
                store.close()
            _json(self, 200, {"ok": True})
            return
        if self.path == "/api/move-sessions":
            store = Store(ROOT / "uxm.db")
            try:
                module = (body.get("module") or "").strip()
                dest = (body.get("project") or "").strip()
                dest_folder = (body.get("data_folder") or "").strip()
                for sid in body.get("ids") or []:
                    store.move_session_project(int(sid), module, dest, dest_folder)
            except Exception as exc:
                _json(self, 400, {"error": str(exc)})
                return
            finally:
                store.close()
            _json(self, 200, {"ok": True})
            return
        if self.path == "/api/report":
            module = (body.get("module") or "").strip()
            project = (body.get("project") or "").strip()
            bands = [str(x) for x in (body.get("bands") or [])]
            explicit = body.get("ids") or []
            store = Store(ROOT / "uxm.db")
            try:
                if explicit:
                    ids = []
                    for x in explicit:
                        try:
                            ids.append(int(x))
                        except (TypeError, ValueError):
                            continue
                else:
                    rows = store.project_sessions(module, project)
                    ids = []
                    want = set(bands)
                    for row in rows:
                        if (row.get("report_kind") or "uxm") != "uxm":
                            continue
                        have = {b for b in (row.get("bands") or "").split(",") if b}
                        if have & want:
                            ids.append(int(row["id"]))
            finally:
                store.close()
            store = Store(ROOT / "uxm.db")
            try:
                kinds = store.session_report_kinds(ids)
            finally:
                store.close()
            mixed = [k for k in kinds.values() if k not in ("", "uxm")]
            if mixed:
                _json(self, 400, {"error": "UXM 與 CMW500 不能混成同一份 Excel Report"})
                return
            try:
                result = run_report_from_db(
                    module,
                    project,
                    ids,
                    bands=bands,
                    filename=body.get("filename") or "",
                )
            except Exception as exc:
                _json(self, 400, {"error": str(exc)})
                return
            data = result.output.read_bytes()
            name = result.output.name
            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            self.send_header("Content-Disposition", f'attachment; filename="{name}"')
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Filename", name)
            self.end_headers()
            self.wfile.write(data)
            return
        if self.path != "/api/build":
            self.send_error(404)
            return
        module = (body.get("module") or "").strip()
        project = (body.get("project") or "").strip()
        folder = (body.get("folder") or "").strip()
        files = body.get("files") or []
        if not isinstance(files, list):
            files = []
        try:
            result = run_build(
                folder,
                module,
                project,
                files=[str(x) for x in files] or None,
                data_folder=body.get("data_folder") or "",
            )
        except Exception as exc:
            _json(self, 400, {"error": str(exc)})
            return
        data = result.output.read_bytes()
        name = result.output.name
        note = f"CSV {result.csv_count}，測項 {len(result.model.test_names)}"
        self.send_response(200)
        self.send_header(
            "Content-Type",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.send_header("Content-Disposition", f'attachment; filename="{name}"')
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Filename", name)
        self.send_header("X-Note", note)
        self.end_headers()
        self.wfile.write(data)


def serve(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True) -> None:
    from .serverctl import clear_pid, write_pid

    httpd = ThreadingHTTPServer((host, port), Handler)
    Handler.httpd = httpd
    url = f"http://{host}:{port}/"
    write_pid(port)
    print(f"UXM Report UI {url}")
    print("關閉：關掉這個視窗、雙擊 關閉介面.bat，或網頁右上角「本機」→ 關閉本地伺服器。")
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    finally:
        clear_pid()
        Handler.httpd = None
