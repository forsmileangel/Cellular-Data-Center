import os
import unittest

from uxm_report.serverctl import _alive
from uxm_report.review import _page
from uxm_report.web import HOME_PAGE, PAGE


class WebPageTests(unittest.TestCase):
    def test_home_is_cards_not_import_form(self):
        self.assertIn("Cellular Specifications and Reporting Analysis Center", HOME_PAGE)
        self.assertNotIn("UXM 測試報告工作台", HOME_PAGE)
        self.assertNotIn(">UR</span>", HOME_PAGE)
        self.assertNotIn("UXM Report", HOME_PAGE)
        self.assertIn("home-card", HOME_PAGE)
        self.assertIn("/import", HOME_PAGE)
        self.assertIn("報告匯入", HOME_PAGE)
        self.assertNotIn('id="module"', HOME_PAGE)
        self.assertNotIn('id="ingest"', HOME_PAGE)

    def test_form_has_required_fields(self):
        self.assertIn('id="modulePick"', PAGE)
        self.assertIn('id="projectPick"', PAGE)
        self.assertIn('id="projectSearch"', PAGE)
        self.assertIn('id="moduleNew"', PAGE)
        self.assertIn('id="projectNew"', PAGE)
        self.assertIn("/api/catalog", PAGE)
        self.assertIn('id="folder"', PAGE)
        self.assertIn('id="build"', PAGE)
        self.assertIn('id="ingest"', PAGE)
        self.assertIn("模組型號", PAGE)
        self.assertIn("Skip", PAGE)
        self.assertIn("selectedFiles", PAGE)
        self.assertIn("報告匯入", PAGE)
        self.assertIn("*.pdf", PAGE)
        self.assertIn("dataFolderPick", PAGE)

    def test_shared_shell_is_warm_sidebar_workspace(self):
        self.assertIn('class="app-shell"', HOME_PAGE)
        self.assertIn('class="sidebar"', HOME_PAGE)
        self.assertIn("--paper:#fffdf9", HOME_PAGE)
        self.assertIn("工作流程", HOME_PAGE)
        self.assertIn("規格知識", HOME_PAGE)

    def test_import_is_three_step_flow(self):
        self.assertIn("01</span>", PAGE)
        self.assertIn("歸檔資訊", PAGE)
        self.assertIn("選擇來源", PAGE)
        self.assertIn("03</span>", PAGE)
        self.assertIn("執行", PAGE)
        self.assertIn("data_folder", PAGE)

    def test_orig_dock_and_hotkey_in_shell(self):
        html = _page("t", '<label class="orig-sw"><input type="checkbox" id="showOrig"> 顯示規格原文</label>')
        self.assertIn("origDock", html)
        self.assertIn("Ctrl+Shift+E", html)
        self.assertIn("Ctrl+Shift+D", html)
        self.assertNotIn("Ctrl+T", html)

    def test_db_index_is_module_cards_only(self):
        from uxm_report.catalog import index_page
        from uxm_report.store import Store

        html = index_page(Store(":memory:"))
        self.assertIn("/db/work", html)
        self.assertNotIn("exportSid", html)
        self.assertNotIn("依Band產出Excel Report", html)
        self.assertNotIn("管理專案", html)
        self.assertNotIn(">開啟</a>", html)

    def test_work_page_has_report_and_chart_tabs(self):
        from uxm_report.catalog import work_page
        from uxm_report.store import Store

        store = Store(":memory:")
        mid = store.upsert_module("FN990")
        store.upsert_project(mid, "DEMO")
        html = work_page(store, module="FN990")
        self.assertIn("報告總覽", html)
        self.assertIn("統計圖表", html)
        self.assertIn("依Band產出Excel Report", html)
        self.assertIn("exportSid", html)
        self.assertIn("reportTitle", html)
        html_c = work_page(store, module="FN990", tab="charts")
        self.assertIn("統計圖表", html_c)
        self.assertIn('class="msel"', html)
        self.assertIn("套用篩選", html)
        self.assertIn("來源著色", html_c)
        self.assertIn('name="project"', html)
        self.assertIn("點一下資料點可把數值留在圖上", html_c)

    def test_catalog_payload_lists_module_projects(self):
        from uxm_report.store import Store
        from uxm_report.web import catalog_payload

        store = Store(":memory:")
        store.upsert_module("FN990B")
        mid = store.upsert_module("FN990B")
        store.upsert_project(mid, "模組引進")
        store.conn.commit()
        payload = catalog_payload(store)
        store.close()
        models = [m["model"] for m in payload["modules"]]
        self.assertIn("FN990B", models)
        fn = next(m for m in payload["modules"] if m["model"] == "FN990B")
        self.assertIn("模組引進", fn["projects"])

    def test_alive_detects_this_process(self):
        self.assertTrue(_alive(os.getpid()))
        self.assertFalse(_alive(0))
        self.assertFalse(_alive(999_999_999))
