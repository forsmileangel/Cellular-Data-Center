import unittest
from pathlib import Path

from uxm_report.parse import parse_csv


class DetailParseTests(unittest.TestCase):
    def test_retry_file_has_detail_rows(self):
        p = Path(
            r"C:\My-project\UXM Report\FN990B Module Test Report"
            r"\351138790009917_N3_Full_Test_2026-03-24_09-44-56_Fail(Retry Failed Item Pass).csv"
        )
        if not p.exists():
            self.skipTest("sample CSV missing")
        session = parse_csv(p)
        self.assertGreaterEqual(len(session.details), 10)
        self.assertTrue(any(d.pf == "Fail" for d in session.details))
        self.assertTrue(any("PRACH" in d.test_case for d in session.details))

    def test_parse_text_roundtrip(self):
        from uxm_report.parse import parse_text

        p = Path(
            r"C:\My-project\UXM Report\FN990B Module Test Report"
            r"\351138790009917_N8_Full Test _2026-03-24_15-08-23_Pass.csv"
        )
        if not p.exists():
            self.skipTest("sample CSV missing")
        session = parse_text(p.read_text(encoding="utf-8", errors="replace"), p.name)
        self.assertEqual(session.filename, p.name)
        self.assertTrue(session.modes)
        self.assertEqual(session.modes[0].display_band, "NR_n8")
