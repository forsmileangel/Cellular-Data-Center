import os
import unittest

from uxm_report.serverctl import _alive
from uxm_report.review import _page
from uxm_report.web import HOME_PAGE, PAGE


class WebPageTests(unittest.TestCase):
    def test_home_is_cards_not_import_form(self):
        self.assertIn("Cellular Specifications and Reporting Analysis Center", HOME_PAGE)
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
        self.assertIn("data_folder", PAGE)

    def test_orig_dock_and_hotkey_in_shell(self):
        html = _page("t", '<label class="orig-sw"><input type="checkbox" id="showOrig"> 顯示規格原文</label>')
        self.assertIn("origDock", html)
        self.assertIn("Ctrl+Shift+E", html)
        self.assertIn("Ctrl+Shift+D", html)
        self.assertNotIn("Ctrl+T", html)

    def test_db_index_export_uses_file_checkboxes(self):
        from uxm_report.catalog import index_page
        from uxm_report.store import Store

        html = index_page(Store(":memory:"))
        self.assertIn("exportSid", html)
        self.assertIn("selectedExportIds", html)
        self.assertIn("請至少勾選一個檔", html)
        self.assertIn("reportTitle", html)
        self.assertIn("incProject", html)
        self.assertIn("incImei", html)
        self.assertIn("buildReportName", html)

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
