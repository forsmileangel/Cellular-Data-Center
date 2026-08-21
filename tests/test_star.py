import unittest

from uxm_report.aggregate import star_result


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


if __name__ == "__main__":
    unittest.main()
