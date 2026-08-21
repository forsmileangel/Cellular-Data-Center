import unittest

from uxm_report.charts import CHARTS, assign_lmh, svg_lmh


class ChartHelperTests(unittest.TestCase):
    def test_assign_three_arfcn(self):
        rows = [
            {"session_id": 1, "arfcn": "385000"},
            {"session_id": 1, "arfcn": "390000"},
            {"session_id": 1, "arfcn": "395000"},
        ]
        out = assign_lmh(rows)
        self.assertEqual({r["arfcn"]: r["lmh"] for r in out}, {
            "385000": "Low",
            "390000": "Mid",
            "395000": "High",
        })

    def test_svg_has_limits(self):
        rows = [
            {
                "session_id": 1,
                "arfcn": "385000",
                "value": "23",
                "lower_limit": "20",
                "upper_limit": "26",
                "pf": "Pass",
            }
        ]
        html = svg_lmh(rows, "dBm")
        self.assertIn("<svg", html)
        self.assertIn("LSL", html)
        self.assertIn("USL", html)

    def test_svg_refuses_to_average_different_limits(self):
        rows = [
            {
                "session_id": 1,
                "arfcn": "385000",
                "value": "2",
                "lower_limit": "0",
                "upper_limit": "3.5",
                "pf": "Pass",
                "lmh": "Low",
            },
            {
                "session_id": 2,
                "arfcn": "385000",
                "value": "4",
                "lower_limit": "0",
                "upper_limit": "8",
                "pf": "Pass",
                "lmh": "Low",
            },
        ]
        html = svg_lmh(rows, "%")
        self.assertNotIn("<svg", html)
        self.assertIn("不會平均限值", html)

    def test_assign_lmh_preserves_explicit_summary_range(self):
        rows = [{"session_id": 1, "arfcn": "385000", "lmh": "High"}]
        self.assertEqual(assign_lmh(rows)[0]["lmh"], "High")

    def test_chart_catalog_covers_more_than_power_evm(self):
        ids = [c["id"] for c in CHARTS]
        self.assertIn("621-power", ids)
        self.assertIn("631-power", ids)
        self.assertIn("6421-pucch", ids)
        self.assertIn("651-obw", ids)
        self.assertGreaterEqual(len(CHARTS), 20)
        blob = " ".join(c["item"] + c["title"] for c in CHARTS).lower()
        self.assertNotIn("worstmargin", blob)
        self.assertNotIn("worst margin", blob)
