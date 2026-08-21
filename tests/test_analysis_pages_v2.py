import tempfile
import unittest
from pathlib import Path

from uxm_report.analysis import AnalysisCohort, AnalysisFilter
from uxm_report.analysis_pages import (
    analysis_compare,
    analysis_index,
    analysis_session,
    spec_insight,
)
from uxm_report.store import Store


class AnalysisWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "analysis.db")
        self.module_id = self.store.upsert_module("M1")
        self.project_id = self.store.upsert_project(self.module_id, "P1")
        self.dut_id = self.store.upsert_dut(self.module_id, "123")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def _session(self, folder, filename, start, verdict):
        folder_id = self.store.upsert_folder(self.project_id, folder)
        cur = self.store.conn.execute(
            """
            INSERT INTO sessions(
                project_id, folder_id, dut_id, filename, start_time,
                overall_result, raw_csv
            ) VALUES (?,?,?,?,?,?,?)
            """,
            (self.project_id, folder_id, self.dut_id, filename, start, verdict, ""),
        )
        session_id = int(cur.lastrowid)
        self.store.conn.execute(
            """
            INSERT INTO test_rows(
                session_id, test_name, band, scs, bw, channel, verdict,
                time_s, lmh, spec_ref, interpret_note
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                session_id,
                "6.2.1 UE Maximum Output Power",
                "NR_n78",
                "30K",
                "B100M",
                640000,
                verdict,
                1.0,
                "Mid",
                "TS 38.521-1 6.2.1",
                "summary note",
            ),
        )
        self.store.conn.commit()
        return session_id

    def _details(self, session_id, count, detail_pf="Pass"):
        for index in range(count):
            self.store.conn.execute(
                """
                INSERT INTO detail_rows(
                    session_id, time, test_case, band, bandwidth, scs, arfcn,
                    modulation, rb, condition, item, lower_limit, value,
                    upper_limit, unit, pf
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    session_id,
                    str(index),
                    "6.2.1 UE Maximum Output Power(PC3)",
                    "N78",
                    "100MHz",
                    "30kHz",
                    "620000",
                    "QPSK",
                    "273@0",
                    "",
                    "NR Power",
                    "20",
                    str(22 + index / 1000),
                    "25",
                    "dBm",
                    detail_pf,
                ),
            )
        self.store.conn.commit()

    def test_detail_query_is_paginated_at_100(self):
        session_id = self._session("TA17", "a.csv", "2026-01-01", "Pass")
        self._details(session_id, 150)
        group = self.store.analysis_measurement_groups(session_id, "6.2.1")[0]
        first, total, page = self.store.analysis_detail_page(
            session_id, "6.2.1", group, 1
        )
        second, total2, page2 = self.store.analysis_detail_page(
            session_id, "6.2.1", group, 2
        )
        self.assertEqual((len(first), total, page), (100, 150, 1))
        self.assertEqual((len(second), total2, page2), (50, 150, 2))
        self.assertTrue({row["detail_id"] for row in first}.isdisjoint(
            {row["detail_id"] for row in second}
        ))

    def test_overview_never_calls_measure_rows(self):
        self._session("TA17", "a.csv", "2026-01-01", "Pass")

        def forbidden(*_args, **_kwargs):
            raise AssertionError("overview materialized detail rows")

        self.store.measure_rows = forbidden
        html = analysis_index(
            self.store,
            AnalysisFilter(
                module="M1",
                scopes=(AnalysisCohort("P1", "TA17"),),
            ),
        )
        self.assertIn("Summary verdict", html)

    def test_summary_verdict_remains_authoritative(self):
        session_id = self._session("TA17", "fail.csv", "2026-01-01", "Fail")
        self._details(session_id, 3, detail_pf="Pass")
        html = analysis_session(
            self.store,
            session_id,
            "6.2.1",
            "6.2.1 UE Maximum Output Power",
            "Mid",
        )
        self.assertIn("摘要 Verdict：Fail", html)
        self.assertIn("細節 P/F 是儀器證據，不覆寫", html)

    def test_comparison_keeps_folder_cohorts_visible(self):
        self._session("TA17", "fail.csv", "2026-01-01", "Fail")
        self._session("TA20", "pass.csv", "2026-01-02", "Pass")
        html = analysis_index(
            self.store,
            AnalysisFilter(
                module="M1",
                scopes=(
                    AnalysisCohort("P1", "TA17"),
                    AnalysisCohort("P1", "TA20"),
                ),
            ),
        )
        self.assertIn("資料夾並列", html)
        self.assertIn("TA17", html)
        self.assertIn("TA20", html)
        self.assertIn("Fail", html)
        self.assertIn("Pass", html)

        compare = analysis_compare(
            self.store,
            AnalysisFilter(
                module="M1",
                scopes=(
                    AnalysisCohort("P1", "TA17"),
                    AnalysisCohort("P1", "TA20"),
                ),
            ),
            "6.2.1 UE Maximum Output Power",
            "NR_n78",
            "Mid",
        )
        self.assertIn("精確條件比較", compare)
        self.assertIn("未疊圖", compare)

    def test_missing_grok_content_is_safe_fallback(self):
        insight = spec_insight("9.9.9")
        self.assertFalse(insight.available)
        self.assertEqual(insight.clause, "9.9.9")


if __name__ == "__main__":
    unittest.main()
