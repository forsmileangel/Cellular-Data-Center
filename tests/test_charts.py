import unittest

from uxm_report.charts import CHARTS, assign_lmh, svg_comparison, svg_lmh


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
        self.assertIn("data-tip", html)
        self.assertIn("23", html)
        self.assertIn("釘在圖上", html)

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

    def test_svg_comparison_colors_sources_and_has_tip(self):
        def row(value, imei):
            return {
                "session_id": 1 if imei == "A" else 2,
                "arfcn": "385000",
                "value": value,
                "lower_limit": "20",
                "upper_limit": "26",
                "pf": "Pass",
                "lmh": "Low",
                "unit": "dBm",
                "imei": imei,
            }

        html = svg_comparison(
            [("IMEI-A", [row("23", "A")]), ("IMEI-B", [row("24", "B")])],
            "dBm",
        )
        self.assertIn("<svg", html)
        self.assertIn("data-tip", html)
        self.assertIn("IMEI-A", html)
        self.assertIn("IMEI-B", html)
        self.assertIn("#496b57", html)
        self.assertIn("#9a6c42", html)

    def test_plot_rows_overlays_two_imeis(self):
        from uxm_report.catalog import _plot_rows

        def row(value, imei, sid):
            return {
                "session_id": sid,
                "arfcn": "385000",
                "value": value,
                "lower_limit": "20",
                "upper_limit": "26",
                "pf": "Pass",
                "lmh": "Low",
                "unit": "dBm",
                "imei": imei,
            }

        html = _plot_rows([row("23", "111", 1), row("24", "222", 2)], "dBm", "imei")
        self.assertIn("111", html)
        self.assertIn("222", html)
        self.assertIn("data-tip", html)
