import unittest

from uxm_report.lineage import build_links, latest_verdict


def ev(
    sid,
    name,
    lmh,
    verdict,
    start,
    imei="1",
    band="NR_n78",
    fn="",
    module="M1",
    project="P1",
    folder="TA17",
):
    return {
        "session_id": sid,
        "test_name": name,
        "lmh": lmh,
        "channel": None,
        "verdict": verdict,
        "start_time": start,
        "imei": imei,
        "band": band,
        "filename": fn or f"f{sid}.csv",
        "module": module,
        "project": project,
        "data_folder": folder,
    }


class LineageTests(unittest.TestCase):
    def test_later_pass_supersedes_fail(self):
        events = [
            ev(1, "6.2.2 MPR", "High", "Fail", "2026-03-19_13-00-00", fn="old.csv"),
            ev(2, "6.2.2 MPR", "High", "Pass", "2026-03-19_17-00-00", fn="retry.csv"),
        ]
        links = build_links(events)
        self.assertTrue(links[(1, "6.2.2 MPR", "High")].superseded)
        self.assertEqual(links[(1, "6.2.2 MPR", "High")].later_filename, "retry.csv")
        self.assertNotIn((2, "6.2.2 MPR", "High"), links)

    def test_open_fail_not_superseded(self):
        events = [ev(1, "6.3.3.4 PRACH", "Mid", "Fail", "2026-03-24_10-00-00")]
        links = build_links(events)
        self.assertFalse(links[(1, "6.3.3.4 PRACH", "Mid")].superseded)

    def test_latest_is_retry_pass(self):
        events = [
            ev(1, "6.2.2 MPR", "High", "Fail", "a"),
            ev(2, "6.2.2 MPR", "High", "Pass", "b"),
        ]
        latest = latest_verdict(events)
        key = ("M1", "P1", "TA17", "1", "NR_n78", "6.2.2 MPR", "High")
        self.assertEqual(latest[key]["verdict"], "Pass")

    def test_pass_in_other_folder_does_not_supersede_fail(self):
        events = [
            ev(1, "6.2.2 MPR", "High", "Fail", "a", folder="TA17"),
            ev(2, "6.2.2 MPR", "High", "Pass", "b", folder="TA20"),
        ]
        links = build_links(events)
        self.assertFalse(links[(1, "6.2.2 MPR", "High")].superseded)

    def test_latest_keeps_project_and_folder_cohorts_separate(self):
        events = [
            ev(1, "6.2.2 MPR", "High", "Fail", "a", project="P1", folder="TA17"),
            ev(2, "6.2.2 MPR", "High", "Pass", "b", project="P1", folder="TA20"),
            ev(3, "6.2.2 MPR", "High", "Pass", "c", project="P2", folder="TA17"),
        ]
        latest = latest_verdict(events)
        self.assertEqual(len(latest), 3)
