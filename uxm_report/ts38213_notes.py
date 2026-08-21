"""Longer notes for TS 38.213 power-control terms (engineer, not primer)."""

from __future__ import annotations

from .gloss import gloss_note

# V17.3.0 clause 7: unified TCI remaps q_d / P0 / α / closed-loop with the indicated state.

UNIFIED_TCI = (
    "Rel-15／16 把下行波束與上行空間濾波拆成兩套指令。"
    "下行用 TCI-State（QCL-TypeA／D）管 PDCCH／PDSCH／CSI-RS；上行用 spatialRelationInfo 或 SRI 分別管 PUCCH、SRS、PUSCH。"
    "FR2 波束一多，MAC-CE／RRC 要改好幾處，DL QCL 跟 UL spatial filter 還容易不同步。"
    "Rel-17 unified TCI（38.214 指示、38.331 的 dl-OrJoint-TCIStateList-r17／UL-TCIState、38.213 第 7 章套用）把「現在這條鏈路用哪一個 TCI」收成一次指示。"
    "兩種用法：joint TCI 假設上下行波束對應，一個 indicated state 同時管收（PDCCH／PDSCH／CSI-RS）與發（PUSCH／PUCCH／SRS）；"
    "separate UL TCI 在對應不成立時，上行另指一個 UL-TCIState。"
    "指示路徑通常是：RRC 配一池 → MAC-CE 啟動子集 → DCI 給 index_new。"
    "38.213 寫：排 PUSCH 且 NDI 翻轉的那次 PDCCH 最後一個符號之後再數 28 個符號，才改用新 TCI 的 QCL／空間濾波。"
    "對功率才是重點：q_d 不再是每個 SCell 寫死的 pathlossReferenceRS。"
    "改從 indicated TCIState（或 UL-TCIState）帶的 PL-RS 取路徑損耗。"
    "若有配 p0AlphaSetforPUSCH／PUCCH／SRS，P0、α、閉環狀態跟著同一個 ul-powerControlId 走。"
    "換 TCI 等於換開環工作點：PL-RS 一換，PL 估計就換；網路若把不同 P0／α 綁在不同 TCI，算出來的 P_PUSCH 會跳，不是只轉波束。"
    "RFA 單波束、沒開 unified TCI 時，用 V15 那組 PUSCH-PowerControl 就解得開報表。"
    "FR2、多 TRP、或 Rel-17 UE 真的在用 unified TCI 時，量測當下 indicated TCI 是哪一個，必須跟 P0／α／PL-RS 一起記，否則會用錯開環。"
)

SRS2 = (
    "Rel-16／17 允許 codebook 或 nonCodebook 各掛兩套 SRS-ResourceSet，對兩條 UL 空間鏈（常見是兩個 TRP 或兩塊面板）。"
    "DCI 0_1／0_2 可以有兩個 SRI，再加上 SRS resource set indicator：00 只用第一套、01 只用第二套、10／11 兩套都用。"
    "開環因此有兩份：p0-PUSCH-Alpha 對第一套，p0-PUSCH-Alpha2（以及 p0-PUSCH-SetList／List2）對第二套。"
    "同一 slot 兩筆 PUSCH（SDM／FDM）可以落在兩個不同的 P0／α，閉環 l 仍可以是共用或兩套，看 twoPUSCH-PC-AdjustmentStates。"
    "V15 公式形狀沒變，但 V15 沒有第二套 SRI→P0 的對照。"
    "報表若出現兩組 UL grant 或兩套 SRS，不要把兩筆功率都套同一組 P0。"
)

MSGA = (
    "兩步 RACH（Rel-16）的 MsgA 是 preamble 加一段 PUSCH，不是連上之後的 7.1 那套 connected PUSCH。"
    "38.213 把這段開環放在 j＝0 附近：O_NOMINAL 用 O_PRE 加 MsgA 偏移時，α 先看 msgA-Alpha；"
    "否則退回 msg3-Alpha；再沒有就 α＝1。"
    "目標電平跟 preambleReceivedTargetPower／msgA-PreambleReceivedTargetPower 走，不是 p0-NominalWithoutGrant。"
    "RFA 若量的是連線後 PUSCH／PUCCH，MsgA 這組用不上。"
    "若量 2-step RACH 或 MsgA PUSCH EVM／功率，要用 V16／V17 這段，V15 只有 Msg3。"
)

REDCAP_P0 = (
    "RedCap 沒有另寫一條 P_PUSCH 公式。"
    "第 7 章同一形狀，第 17 章限制哪些 7.x 程序適用（頻寬、天線、TCI／SRS 能力較窄）。"
    "真正改數字的是 M_RB：BWP 小，10log10(2^μ·M_RB) 變小，同樣 P0／α／PL 算出來的功率比較低。"
    "PCMAX 多半仍是 6.2I 沿用的 Power Class 3，跟一般模組同一張 23 dBm 表。"
    "多數也不會上第二套 SRS 或完整 unified TCI 池，所以 P0／α 通常還是單一 P0-PUSCH-AlphaSet。"
    "一般模組引進不是 RedCap SKU 就不必用 7.3I／6.2I 去解 RFA 功率。"
)

V15_V17_READ = (
    "RFA 報表上的 PUSCH／PUCCH／PRACH「目標」多半是單一 BWP、單一 PL-RS、一套 P0／α。"
    "這正是 V15 7.1–7.4 的模型：min(PCMAX, P0 + 10log10(2^μ M) + αPL + ΔTF + 閉環)。"
    "V17 沒改這個形狀。"
    "V17 要問的是：量測當下，UE 到底選了哪一套開環。"
    "unified TCI 把 PL-RS 與可選的 P0／α 綁在 indicated TCI 上；換波束就可能換工作點。"
    "第二套 SRS 讓同一 slot 兩筆 PUSCH 用 p0-PUSCH-Alpha 與 Alpha2。"
    "MsgA 用 O_PRE／msgA-Alpha，跟連線後 PUSCH 不是同一組。"
    "RedCap 公式不變，但 M_RB 與第 17 章適用範圍會改算出來的值。"
    "單波束 FR1 DVT：V15 夠用。"
    "報表出現兩套 SRS、TCI 指示、MsgA 或 RedCap 頻寬時，才需要對 V17 問「現在用的是哪一組 P0／α」。"
)


def panels_html() -> str:
    return "".join(
        (
            gloss_note("unified-tci", "unified TCI（Rel-17）跟功率怎麼綁", UNIFIED_TCI),
            gloss_note("srs2", "第二套 SRS resource set 與兩組 P0／α", SRS2),
            gloss_note("msga", "MsgA 功率（兩步 RACH）", MSGA),
            gloss_note("redcap-p0", "RedCap 會不會改 P0／α", REDCAP_P0),
            gloss_note("v15-v17-read", "看功率時 V15 與 V17 各解什麼", V15_V17_READ),
        )
    )
