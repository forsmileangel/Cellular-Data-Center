import unittest
from pathlib import Path

from uxm_report.aggregate import build_report
from uxm_report.parse import parse_folder

ROOT = Path(r"C:\My-project\UXM Report")
FN = ROOT / "FN990B Module Test Report"


class Fn990bAggregateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sessions = parse_folder(FN)
        cls.model = build_report(cls.sessions, module_model="FN990B", project="UNKNOWN")

    def test_file_count_and_order(self):
        self.assertEqual(len(self.model.columns), 16)
        self.assertTrue(self.model.columns[0].filename.startswith("351138790009917_Full Test N41"))
        self.assertTrue(self.model.columns[15].filename.startswith("351138790009917_N8_Full Test"))

    def test_durations(self):
        expected = [
            "137m29s",
            "137m11s",
            "158m1s",
            "148m4s",
            "128m36s",
            "8m33s",
            "122m27s",
            "160m59s",
            "14m8s",
            "74m18s",
            "36m42s",
            "166m58s",
            "118m47s",
            "115m22s",
            "7m4s",
            "129m59s",
        ]
        self.assertEqual([c.duration for c in self.model.columns], expected)

    def test_overall_results(self):
        expected = [
            "Pass*",
            "Fail*",
            "Fail*",
            "Pass*",
            "Fail*",
            "Fail",
            "Pass*",
            "Fail*",
            "Pass",
            "Pass*",
            "Pass*",
            "Fail*",
            "Fail*",
            "Fail*",
            "Fail",
            "Pass*",
        ]
        self.assertEqual([c.summary for c in self.model.columns], expected)

    def test_n1_prach118_fail_items(self):
        n1 = self.model.columns[2]
        self.assertEqual(n1.mode.display_band, "NR_n1")
        self.assertEqual(
            n1.fail_items,
            " 6.3.3.4 PRACH time mask -118_Low\n 6.3.3.4 PRACH time mask -118_Mid",
        )

    def test_data_n78_retry_mid_only(self):
        col = self.model.columns[10]  # File 11 mid
        self.assertEqual(col.by_test["6.2.1 UE Maximum Output Power"], {"Mid": "Pass"})

    def test_data_n78_low_high_only(self):
        col = self.model.columns[9]  # File 10
        self.assertEqual(
            set(col.by_test["6.2.1 UE Maximum Output Power"]),
            {"Low", "High"},
        )

    def test_imei(self):
        self.assertEqual(self.model.imeis, ["351138790009917"])

    def test_ta_version(self):
        self.assertEqual(self.model.columns[0].ta_version, "24.30.0.3251")
        self.assertEqual(self.model.columns[0].rfa_version, "14.0.9430.19673")


if __name__ == "__main__":
    unittest.main()
