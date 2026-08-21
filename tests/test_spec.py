import unittest

from uxm_report.spec import (
    classify_channels,
    default_lmh,
    nr_arfcn_to_mhz,
    nr_range_class,
)


class SpecTests(unittest.TestCase):
    def test_n1_10mhz(self):
        lmh = default_lmh("NR", "n1", 10)
        self.assertAlmostEqual(lmh.low, 2115.0, places=3)
        self.assertAlmostEqual(lmh.mid, 2140.0, places=3)
        self.assertAlmostEqual(lmh.high, 2165.0, places=3)
        mapped = classify_channels([423000, 428000, 433000], "NR", "n1", 10)
        self.assertEqual(mapped, {423000: "Low", 428000: "Mid", 433000: "High"})

    def test_n8_10mhz(self):
        mapped = classify_channels([186000, 188500, 191000], "NR", "n8", 10)
        self.assertEqual(mapped, {186000: "Low", 188500: "Mid", 191000: "High"})

    def test_n41_10mhz(self):
        self.assertAlmostEqual(nr_arfcn_to_mhz(500202), 2501.01, places=2)
        mapped = classify_channels([500202, 518598, 537000], "NR", "n41", 10)
        self.assertEqual(mapped, {500202: "Low", 518598: "Mid", 537000: "High"})

    def test_n78_100mhz(self):
        mapped = classify_channels([623334, 636666, 650000], "NR", "n78", 100)
        self.assertEqual(mapped, {623334: "Low", 636666: "Mid", 650000: "High"})

    def test_n78_10mhz_low_high_only(self):
        mapped = classify_channels([620334, 653000], "NR", "n78", 10)
        self.assertEqual(mapped, {620334: "Low", 653000: "High"})

    def test_n79_40mhz(self):
        mapped = classify_channels([694668, 713334, 732000], "NR", "n79", 40)
        self.assertEqual(mapped, {694668: "Low", 713334: "Mid", 732000: "High"})

    def test_nr_range_class(self):
        self.assertEqual(nr_range_class("NR_n5"), "Low-band")
        self.assertEqual(nr_range_class("NR_n8"), "Low-band")
        self.assertEqual(nr_range_class("B28"), "Low-band")
        self.assertEqual(nr_range_class("NR_n1"), "Mid-band")
        self.assertEqual(nr_range_class("NR_n3"), "Mid-band")
        self.assertEqual(nr_range_class("B1"), "Mid-band")
        self.assertEqual(nr_range_class("NR_n7"), "High-band")
        self.assertEqual(nr_range_class("NR_n41"), "High-band")
        self.assertEqual(nr_range_class("NR_n78"), "High-band")
        self.assertEqual(nr_range_class("NR_n79"), "High-band")
        self.assertEqual(nr_range_class("B7"), "High-band")
        self.assertEqual(nr_range_class("n257"), "Ultra-high")


if __name__ == "__main__":
    unittest.main()
