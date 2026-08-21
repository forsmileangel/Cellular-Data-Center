import unittest

from uxm_report.analysis import (
    AnalysisCohort,
    MeasurementGroup,
    Point,
    decorate,
    from_row,
    is_unset_value,
    limit_float,
    measurement_state,
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

    def test_double_limit_has_window_ratio(self):
        p = decorate(
            Point(
                value=12,
                lsl=10,
                usl=30,
                unit="dBm",
                pf="Pass",
                test_case="t",
                item="i",
                band="N1",
                condition="",
            )
        )
        self.assertAlmostEqual(p.margin_ratio, 0.1)

    def test_single_limit_keeps_native_margin_only(self):
        p = decorate(
            Point(
                value=8,
                lsl=None,
                usl=10,
                unit="%",
                pf="Pass",
                test_case="t",
                item="i",
                band="N1",
                condition="",
            )
        )
        self.assertEqual(p.nearest, 2)
        self.assertIsNone(p.margin_ratio)
        self.assertIsNone(p.pos)

    def test_measurement_state_separates_sentinel_and_derived(self):
        self.assertEqual(measurement_state("-9.91e+37", "NR Power"), "unset")
        self.assertEqual(measurement_state("1.2", "GeneralWorstMargin"), "derived")
        self.assertEqual(measurement_state("abc", "NR Power"), "invalid")

    def test_scope_and_group_tokens_roundtrip(self):
        scope = AnalysisCohort("P1", "TA20")
        self.assertEqual(AnalysisCohort.from_token(scope.token), scope)
        group = MeasurementGroup(
            "6.4.2.1",
            "PUSCH EVM",
            "N78",
            "100MHz",
            "30kHz",
            "QAM256",
            "273@0",
            "",
            "%",
            "",
            "3.5",
        )
        self.assertEqual(MeasurementGroup.from_token(group.token), group)
