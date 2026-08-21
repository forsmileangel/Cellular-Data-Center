import tempfile
import unittest
from pathlib import Path

from uxm_report.parse import parse_csv
from uxm_report.store import Store


class ProjectRenameTests(unittest.TestCase):
    def test_rename_unknown(self):
        sample = Path(
            r"C:\My-project\UXM Report\FN990B Module Test Report"
            r"\351138790009917_N8_Full Test _2026-03-24_15-08-23_Pass.csv"
        )
        if not sample.exists():
            self.skipTest("sample CSV missing")
        tmp = Path(tempfile.mkdtemp()) / "t.db"
        store = Store(tmp)
        try:
            store.import_session(parse_csv(sample), "FN990B", "UNKNOWN")
            store.rename_project("FN990B", "UNKNOWN", "PT-DEMO")
            names = [p["name"] for p in store.list_projects("FN990B")]
            self.assertEqual(names, ["PT-DEMO"])
            rows = store.project_sessions("FN990B", "PT-DEMO")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["instrument"], "uxm")
            self.assertEqual(rows[0]["report_kind"], "uxm")
            n = store.delete_project("FN990B", "PT-DEMO")
            self.assertEqual(n, 1)
            self.assertEqual(store.list_projects("FN990B"), [])
        finally:
            store.close()

    def test_folders_and_filter(self):
        sample = Path(
            r"C:\My-project\UXM Report\FN990B Module Test Report"
            r"\351138790009917_N8_Full Test _2026-03-24_15-08-23_Pass.csv"
        )
        if not sample.exists():
            self.skipTest("sample CSV missing")
        session = parse_csv(sample)
        tmp = Path(tempfile.mkdtemp()) / "t.db"
        store = Store(tmp)
        try:
            a = store.import_session(session, "FN990B", "模組引進", data_folder="TA17")
            b = store.import_session(session, "FN990B", "模組引進", data_folder="TA20")
            self.assertNotEqual(a, b)
            self.assertEqual(store.list_folders("FN990B", "模組引進"), ["TA17", "TA20"])
            t17 = store.filter_sessions("FN990B", "模組引進", "TA17")
            t20 = store.filter_sessions("FN990B", "模組引進", "TA20")
            self.assertEqual(len(t17), 1)
            self.assertEqual(len(t20), 1)
            self.assertEqual(t17[0]["data_folder"], "TA17")
            n = store.delete_sessions([a])
            self.assertEqual(n, 1)
            self.assertEqual(len(store.filter_sessions("FN990B", "模組引進")), 1)
        finally:
            store.close()
