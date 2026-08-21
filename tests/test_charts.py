import unittest

from uxm_report.charts import assign_lmh, svg_lmh


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
