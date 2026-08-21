import unittest

from uxm_report.analysis import decorate, from_row, limit_float, summarize, to_float
from uxm_report.analysis import Point


class AnalysisMathTests(unittest.TestCase):
    def test_sentinel_limits(self):
        self.assertIsNone(limit_float("-999"))
        self.assertIsNone(limit_float("999"))
        self.assertEqual(limit_float("25.7"), 25.7)

    def test_nan_value(self):
        self.assertIsNone(to_float("NaN"))
        self.assertIsNone(from_row({"value": "NaN", "lower_limit": "-999", "upper_limit": "-48.5", "pf": "Fail"}))

    def test_position_center(self):
        p = decorate(Point(value=20, lsl=10, usl=30, unit="dBm", pf="Pass", test_case="t", item="i", band="N1", condition=""))
        self.assertAlmostEqual(p.pos, 0.5)
        self.assertEqual(p.side, "mid")
        self.assertAlmostEqual(p.margin_lsl, 10)
        self.assertAlmostEqual(p.margin_usl, 10)

    def test_bias_lower(self):
        p = decorate(Point(value=12, lsl=10, usl=30, unit="dBm", pf="Pass", test_case="t", item="i", band="N1", condition=""))
        self.assertLess(p.pos, 1 / 3)
        self.assertEqual(p.side, "lower")
        bias = summarize([p])
        self.assertEqual(bias.lower, 1)
        self.assertEqual(bias.upper, 0)
