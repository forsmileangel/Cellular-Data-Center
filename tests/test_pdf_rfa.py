import tempfile
import unittest
from pathlib import Path

from uxm_report.parse import list_report_files, parse_selected, ta_major
from uxm_report.store import Store

SA = Path(r"C:\Google Drive\WORK\TRD\模組驗證\(驗證候選)Telit\FN990\SA")
N1 = SA / "359918920023868_Full Test N1_2022-12-22_16-23-42_Fail.pdf"
TA20 = SA / "TA version 20" / "359918920023868_Full Test N1_2023-02-22_12-56-44_Fail.pdf"
RETRY = (
    SA
    / "TA version 20"
    / "359918920023868_Full Test N1_2023-02-22_13-49-50_Pass_Retry_Loop1.pdf"
)


class TaMajorTests(unittest.TestCase):
    def test_major(self):
        self.assertEqual(ta_major("17.21.5.7071"), "17")
        self.assertEqual(ta_major("20.0.14.11031"), "20")
        self.assertEqual(ta_major("24.30.0.3251"), "24")
        self.assertEqual(ta_major(""), "")


class ListReportFilesTests(unittest.TestCase):
    def test_skips_bandcombinations(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "a.csv").write_text("IMEI, 1\n", encoding="utf-8")
        (tmp / "b.pdf").write_bytes(b"%PDF-1.4\n")
        (tmp / "BandCombinations_1,3,5.csv").write_text("x", encoding="utf-8")
        names = [p.name for p in list_report_files(tmp)]
        self.assertEqual(names, ["a.csv", "b.pdf"])
        self.assertEqual(parse_selected(tmp, ["BandCombinations_1,3,5.csv"]), [])


class PdfRfaTests(unittest.TestCase):
    def test_n1_ta17(self):
        if not N1.is_file():
            self.skipTest("FN990 SA N1 PDF missing")
        from uxm_report.pdf_rfa import parse_pdf

        session = parse_pdf(N1)
        self.assertEqual(session.source_kind, "pdf")
        self.assertEqual(session.header.get("IMEI"), "359918920023868")
        self.assertEqual(session.header.get("TestPlan"), "Full Test N1")
        self.assertEqual(session.header.get("TA Version"), "17.21.5.7071")
        self.assertEqual(session.header.get("Start Time"), "2022-12-22_16-23-42")
        self.assertEqual(session.header.get("Overall Result"), "Fail")
        self.assertEqual(ta_major(session.header.get("TA Version") or ""), "17")
        n = sum(len(m.rows) for m in session.modes)
        self.assertEqual(n, 81)
        self.assertTrue(session.modes)
        self.assertIn("NR_n1", session.modes[0].display_band)
        self.assertTrue(any(d.item == "NR Power" for d in session.details))
        self.assertTrue(any(d.pf in {"Pass", "Fail"} for d in session.details))
        self.assertTrue(session.raw_text.startswith("SourceKind"))
        self.assertIn("折行", session.parse_notes)

    def test_ta20_and_retry(self):
        if not TA20.is_file() or not RETRY.is_file():
            self.skipTest("FN990 SA TA20 PDF missing")
        from uxm_report.pdf_rfa import parse_pdf

        full = parse_pdf(TA20)
        self.assertEqual(ta_major(full.header.get("TA Version") or ""), "20")
        self.assertEqual(sum(len(m.rows) for m in full.modes), 60)
        retry = parse_pdf(RETRY)
        self.assertEqual(retry.header.get("Overall Result"), "Pass")
        self.assertGreaterEqual(sum(len(m.rows) for m in retry.modes), 50)
        self.assertTrue(any("PRACH" in d.test_case for d in retry.details))

    def test_store_ta_major_and_raw_not_pdf_binary(self):
        if not N1.is_file():
            self.skipTest("FN990 SA N1 PDF missing")
        from uxm_report.pdf_rfa import parse_pdf

        session = parse_pdf(N1)
        db = Path(tempfile.mkdtemp()) / "t.db"
        store = Store(db)
        try:
            sid = store.import_session(session, "FN990A", "SA-PDF")
            store.conn.commit()
            head = store.session_header(sid)
            self.assertEqual(head["ta_major"], "17")
            self.assertEqual(head["source_kind"], "pdf")
            self.assertTrue(head["parse_notes"])
            raw = store.conn.execute(
                "SELECT raw_csv FROM sessions WHERE id=?", (sid,)
            ).fetchone()[0]
            self.assertTrue(raw.startswith("SourceKind"))
            self.assertNotIn("%PDF", raw[:20])
        finally:
            store.close()
