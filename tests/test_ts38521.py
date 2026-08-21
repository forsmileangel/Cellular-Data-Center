import unittest

from uxm_report.ts38521 import BY_ID, CLAUSES, SPEC_FILE, SPEC_VERSION, clause_of, match_clause
from uxm_report.ts38521_ref import BY_REF, CH6_SECTIONS, CH7_SECTIONS
from uxm_report.ts38521_tables import tables_for
from uxm_report.ts38521_figures import ASSET_DIR, figures_for
from uxm_report.prose import split_sentences
from uxm_report.ref_pages import ref_page
from uxm_report.ref_hub import hub_page, page_38213, page_38508, ref_dispatch
from uxm_report.spec_pages import spec_page
from uxm_report.store import Store


class Ts38521Tests(unittest.TestCase):
    def test_rfa_names_map(self):
        self.assertEqual(clause_of("6.2.1 UE Maximum Output Power"), "6.2.1")
        self.assertEqual(clause_of("6.3.3.4 PRACH time mask -118"), "6.3.3.4")
        self.assertEqual(clause_of("Reference sensitivity Search(N1X2)"), "7.3.2")
        self.assertEqual(match_clause("6.5.2.4.1 NR ACLR").id, "6.5.2.4.1")

    def test_catalog_covers_fn990b_set(self):
        needed = {
            "6.2.1",
            "6.2.2",
            "6.2.3",
            "6.2.4",
            "6.3.1",
            "6.3.2",
            "6.3.3.2",
            "6.3.3.4",
            "6.3.3.6",
            "6.3.4.2",
            "6.3.4.4",
            "6.4.1",
            "6.4.2.1",
            "6.4.2.2",
            "6.4.2.3",
            "6.4.2.4",
            "6.4.2.5",
            "6.5.1",
            "6.5.2.2",
            "6.5.2.3",
            "6.5.2.4.1",
            "6.5.2.4.2",
            "7.3.2",
            "7.4",
        }
        self.assertEqual(needed, set(BY_ID))
        self.assertEqual(SPEC_VERSION, "18.5.0")
        self.assertEqual(SPEC_FILE, "ts_13852101v180500p.pdf")
        self.assertTrue(all(c.page > 0 and c.purpose and c.original for c in CLAUSES))

    def test_spec_page_mentions_pdf_and_rfa(self):
        store = Store(":memory:")
        html = spec_page(store, "", "", "6.2.1")
        self.assertIn("ts_13852101v180500p.pdf", html)
        self.assertIn("6.2.1", html)
        self.assertIn("NR Power", html)
        self.assertIn("N1X2", spec_page(store, "", "", "7.3.2"))
        self.assertIn('id="showOrig"', html)
        self.assertIn("顯示規格原文", html)
        self.assertEqual(html.count('id="showOrig"'), 1)
        self.assertIn("origDock", html)
        self.assertIn("Ctrl+Shift+E", html)
        self.assertIn("maximum output power", html)
        self.assertIn("spec-orig", html)
        self.assertIn('id="showTables"', html)
        self.assertEqual(html.count('id="showTables"'), 1)
        self.assertIn("顯示詳細規格", html)
        self.assertIn("6.2.1.3-1", html)
        html732 = spec_page(store, "", "", "7.3.2")
        self.assertIn("-100.0", html732)
        self.assertIn("10log10", html732)
        self.assertIn("R17:", html732)
        self.assertIn("測試規格對照", html)
        self.assertIn("3GPP法規參考", html)
        store.close()

    def test_key_table_values_from_pdf(self):
        pc = {row[0]: row for row in tables_for("6.2.1")[0].rows}
        self.assertEqual(pc["n1"][5], "23")
        self.assertEqual(pc["n1"][3], "26")
        self.assertEqual(pc["n78"][1], "31⁶")
        self.assertEqual(pc["n78"][3], "26")
        self.assertEqual(pc["n78"][5], "23")
        self.assertEqual(pc["n78"][6], "+2/-3")
        evm = {row[0]: row[2] for row in tables_for("6.4.2.1")[0].rows}
        self.assertEqual(evm["QPSK"], "17.5")
        self.assertEqual(evm["256 QAM"], "3.5")
        aclr = tables_for("6.5.2.4.1")[0].rows[0]
        self.assertEqual(aclr[-1], "30 dB")
        self.assertEqual(len(aclr), 4)
        n1_15 = next(r for r in tables_for("7.3.2")[0].rows if r[0] == "n1" and r[1] == "15")
        self.assertEqual(n1_15[3], "-100.0")
        self.assertEqual(n1_15[4], "-96.8")
        n79_15 = next(r for r in tables_for("7.3.2")[1].rows if r[0].startswith("n79") and r[1] == "15")
        self.assertIn("NRB/52", n79_15[3])
        notes = " ".join(tables_for("7.3.2")[1].notes)
        self.assertIn("R17", notes)
        self.assertIn("NRB/216", notes)

    def test_ref_index_covers_chapter_6_and_7(self):
        html = ref_page()
        self.assertIn("3GPP法規參考", html)
        self.assertIn("第 6 章", html)
        self.assertIn("第 7 章", html)
        self.assertIn("6.2.1", html)
        self.assertIn("7.5", html)
        self.assertIn("7.6.2", html)
        self.assertIn("7.9", html)
        self.assertIn("6.2A", html)
        self.assertIn("新手導覽", html)
        self.assertIn("預留", html)
        self.assertIn('id="showOrig"', html)
        self.assertEqual(html.count('id="showOrig"'), 1)
        self.assertIn("origDock", html)
        self.assertIn("Ctrl+Shift+E", html)
        for sid in CH6_SECTIONS + CH7_SECTIONS:
            self.assertIn(sid, BY_REF)
        self.assertIn("載波聚合", html)
        self.assertIn("UE maximum output power", html)
        self.assertIn("Reference sensitivity power level", html)
        self.assertIn("clause-list", html)
        self.assertNotIn('id="showTables"', html)
        self.assertIn("/ref/38.521", html)
        hub = hub_page()
        self.assertIn("TS 38.521", hub)
        self.assertIn("TS 38.508", hub)
        self.assertIn("TS 38.213", hub)
        self.assertIn("/ref/38.213", hub)
        self.assertNotIn("6.2.1.3-1", hub)
        p213 = page_38213()
        self.assertIn("P_PUSCH", p213)
        self.assertIn("36.213", p213)
        self.assertIn("V17.3.0", p213)
        self.assertIn("不是 38.521", p213)
        self.assertIn("/ref/38.521?id=6.2.4", p213)
        self.assertIn("2^μ", p213)
        self.assertIn("unified TCI", p213)
        self.assertIn("14 頁", p213)
        self.assertIn("顯示規格原文", p213)
        self.assertIn('data-gloss="unified-tci"', p213)
        self.assertIn("p0AlphaSetforPUSCH", p213)
        self.assertIn("28 個符號", p213)
        self.assertIn("msgA-Alpha", p213)
        self.assertIn("Escape", p213)
        self.assertIn("gloss-box", p213)
        p508 = page_38508()
        self.assertIn("共用測試環境", p508)
        self.assertIn("38.508-2", p508)
        self.assertEqual(ref_dispatch("", "", ""), hub)
        self.assertIn("6.2.1.3-1", ref_dispatch("38.521", "6.2.1", ""))
        detail = ref_page("6.2.1")
        self.assertIn("6.2.1.3-1", detail)
        self.assertIn("測試規格對照", detail)
        self.assertIn("maximum output power", detail)
        self.assertIn("spec-tables", detail)
        acs = ref_page("7.5")
        self.assertIn("33 dB", acs)
        self.assertIn("Adjacent channel selectivity", acs)
        self.assertIn("<svg", acs)
        self.assertIn("第 7 章整章沒有 Figure", acs)
        self.assertIn("不是 PDF 原圖", acs)
        ibe = ref_page("6.4.2.3")
        self.assertIn("IQ Image", ibe)
        self.assertIn("沒有 Figure", ibe)
        oob = ref_page("7.6.3")
        self.assertIn("Range 1", oob)
        self.assertTrue(tables_for("6.5.3"))
        self.assertTrue(tables_for("7.9"))
        onoff = ref_page("6.3.3.2")
        self.assertIn("/spec-fig/6.3.3.2.3-1.png", onoff)
        self.assertIn("從 V18 PDF 原頁裁出", onoff)
        self.assertIn("6.2.1.3-1", ref_page("6.2.1"))
        self.assertTrue(tables_for("6.3.4.4"))
        self.assertIn("2.5", tables_for("6.3.4.4")[0].rows[0][2])
        idx = ref_page()
        self.assertIn("向量線條", idx)
        self.assertTrue((ASSET_DIR / "6.3.3.2.3-1.png").is_file())
        self.assertTrue(figures_for("6.3.3.2")[0].is_original)
        self.assertFalse(figures_for("7.5")[0].is_original)
        ca = ref_page("6.2A")
        self.assertIn("兩個接頭相加", ca)
        self.assertIn("CA_n1A-n3A", ca)
        self.assertNotIn("同一類量測", ca)
        mimo = ref_page("6.2D")
        self.assertIn("ULFPTx", mimo)
        self.assertIn("0／14／18", mimo)
        v2x = ref_page("6.2E")
        self.assertIn("PSSCH", v2x)
        self.assertIn("n47", v2x)
        refs = ref_page("7.3A")
        self.assertIn("每個 CC", refs)
        self.assertIn("ΔRIB,c", refs)
        redcap = ref_page("7.3I")
        self.assertIn("排除 RedCap", redcap)
        acs_ca = ref_page("7.5A")
        self.assertIn("CA bandwidth class", acs_ca)
        self.assertIn("聚合後", acs_ca)
        self.assertGreaterEqual(ca.count("<p>"), 4)
        self.assertIn("spec-prose", ca)
        sents = split_sentences("第一句。第二句。尾巴")
        self.assertEqual(sents, ["第一句。", "第二句。", "尾巴"])
