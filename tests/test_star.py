import unittest
from pathlib import Path

from uxm_report.aggregate import build_report, star_result
from uxm_report.parse import Session, TestMode, TestRow, is_connection_test, plan_label


class StarResultTests(unittest.TestCase):
    def test_pass_clean(self):
        self.assertEqual(star_result(["Pass", "Pass"]), "Pass")

    def test_pass_star_when_skip(self):
        self.assertEqual(star_result(["Pass", "Skip", "Pass"]), "Pass*")

    def test_fail_clean(self):
        self.assertEqual(star_result(["Pass", "Fail", "Pass"]), "Fail")

    def test_fail_star_when_skip(self):
        self.assertEqual(star_result(["Fail", "Skip", "Pass"]), "Fail*")

    def test_skip_only(self):
        self.assertEqual(star_result(["Skip", "Skip"]), "Pass*")


def _mode(display: str, band_id: str, channel: int) -> TestMode:
    return TestMode(
        raw=f"SAFR1 {display} SCS15K_DFT_B20M",
        rat="NR",
        band_id=band_id,
        display_band=display,
        scs="15K",
        bw="B20M",
        rows=[
            TestRow(
                "6.2.1 UE Maximum Output Power",
                f"{display}A",
                channel,
                "B20M",
                "Pass",
                1.0,
            )
        ],
    )


class FileNumberTests(unittest.TestCase):
    def test_multi_band_file_keeps_one_file_number(self):
        one = Session(
            Path("n1.pdf"),
            "n1.pdf",
            {"IMEI": "1", "TA Version": "17.0"},
            [_mode("NR_n1", "n1", 424000)],
        )
        conn = Session(
            Path("connection_test.pdf"),
            "connection_test.pdf",
            {"IMEI": "1", "TA Version": "17.0"},
            [
                _mode("NR_n1", "n1", 424000),
                _mode("NR_n28", "n28", 156100),
            ],
        )
        model = build_report([one, conn], "FN990", "demo")
        self.assertEqual(
            [c.file_label for c in model.columns],
            ["File 1", "File 2 (connection test)", "File 2 (connection test)"],
        )
        self.assertEqual([c.mode.display_band for c in model.columns], ["NR_n1", "NR_n1", "NR_n28"])
        self.assertEqual(
            [row[0] for row in model.file_rows[1:]],
            ["File 1", "File 2 (connection test)"],
        )
        self.assertEqual(model.overall_rows[2][4], "File 2 (connection test)")
        self.assertEqual(model.overall_rows[2][5], "connection test")
        self.assertIsNone(model.overall_rows[1][5])


class PlanLabelTests(unittest.TestCase):
    def test_connection_and_full(self):
        self.assertTrue(is_connection_test("3599_connection_test_2022_Pass.pdf"))
        self.assertTrue(is_connection_test("x.csv", "connection test"))
        self.assertFalse(is_connection_test("Full Test N1_Fail.pdf"))
        self.assertEqual(plan_label("3599_Full Test N1_Fail.pdf"), "Full Test N1")
        self.assertEqual(
            plan_label("3599_connection_test_2022_Pass.pdf"),
            "connection test",
        )
        self.assertEqual(plan_label("N1_Full_Test.csv"), "Full Test")


if __name__ == "__main__":
    unittest.main()
