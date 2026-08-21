import unittest

from uxm_report.analysis import (
    Point,
    decorate,
    from_row,
    is_unset_value,
    limit_float,
    summarize,
    to_float,
)


class AnalysisMathTests(unittest.TestCase):
    def test_sentinel_limits(self):
        self.assertIsNone(limit_float("-999"))
        self.assertIsNone(limit_float("999"))
        self.assertEqual(limit_float("25.7"), 25.7)

    def test_nan_value(self):
        self.assertIsNone(to_float("NaN"))
        p = from_row({"value": "NaN", "lower_limit": "-999", "upper_limit": "-48.5", "pf": "Fail"})
        self.assertIsNotNone(p)
        self.assertTrue(p.unset)

    def test_keysight_unset_not_tight(self):
        self.assertTrue(is_unset_value("-9.91e+37"))
        p = from_row(
            {
                "value": "-9.91E+37",
                "lower_limit": "20.3",
                "upper_limit": "25.7",
                "pf": "Pass",
                "test_case": "6.2.1",
                "item": "NR Power",
                "band": "N1",
            }
        )
        self.assertTrue(p.unset)
        self.assertIsNone(p.nearest)
        bias = summarize([p])
        self.assertEqual(bias.usable, 0)

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
