"""First-pass interpretation of UXM rows. Marked for review, not final truth."""

from __future__ import annotations

import re
from dataclasses import dataclass

# TS 38.521-1 clause titles (NR SA RF). Notes are draft — confirm on the HTML page.
NR_SA: dict[str, tuple[str, str]] = {
    "6.2.1": ("TS 38.521-1 6.2.1", "UE Maximum Output Power。細節列常帶 (PC3)。"),
    "6.2.2": ("TS 38.521-1 6.2.2", "MPR。依調變／RB 允許降功率。"),
    "6.2.3": (
        "TS 38.521-1 6.2.3 / 38.101-1 6.2.3",
        "A-MPR。只在有 NS（Network Signalling，細節列 Condition 如 NS_100、NS_05）時適用。測試計畫常在 Mid 標 Skip。",
    ),
    "6.2.4": ("TS 38.521-1 6.2.4", "Configured transmitted power（PCMAX）。"),
    "6.3.1": ("TS 38.521-1 6.3.1", "Minimum Output Power。"),
    "6.3.2": ("TS 38.521-1 6.3.2", "Transmit OFF Power。"),
    "6.3.3.2": ("TS 38.521-1 6.3.3.2", "General ON/OFF time mask。"),
    "6.3.3.4": (
        "TS 38.521-1 6.3.3.4",
        "PRACH time mask。名稱後的 -118 / -124 是 preamble RX target power (dBm)，不是頻段。",
    ),
    "6.3.3.6": ("TS 38.521-1 6.3.3.6", "SRS time mask。"),
    "6.3.4.2": ("TS 38.521-1 6.3.4.2", "Absolute power tolerance。"),
    "6.3.4.4": ("TS 38.521-1 6.3.4.4", "Aggregate power tolerance。"),
    "6.4.1": ("TS 38.521-1 6.4.1", "Frequency error。"),
    "6.4.2.1": ("TS 38.521-1 6.4.2.1", "EVM（PRACH / PUCCH / PUSCH）。"),
    "6.4.2.2": ("TS 38.521-1 6.4.2.2", "Carrier leakage。"),
    "6.4.2.3": ("TS 38.521-1 6.4.2.3", "In-band emissions。"),
    "6.4.2.4": ("TS 38.521-1 6.4.2.4", "EVM equalizer spectrum flatness。"),
    "6.4.2.5": ("TS 38.521-1 6.4.2.5", "Pi/2-BPSK spectrum flatness。"),
    "6.5.1": ("TS 38.521-1 6.5.1", "Occupied bandwidth。"),
    "6.5.2.2": ("TS 38.521-1 6.5.2.2", "Spectrum Emission Mask。"),
    "6.5.2.3": (
        "TS 38.521-1 6.5.2.3",
        "Additional SEM。只在有 extra NS 頻譜要求時適用，常 Skip。",
    ),
    "6.5.2.4.1": ("TS 38.521-1 6.5.2.4.1", "NR ACLR。"),
    "6.5.2.4.2": (
        "TS 38.521-1 6.5.2.4.2",
        "UTRA ACLR。相鄰是 UTRA 才要求；TDD／部分 channel 常 Skip。",
    ),
    "7.3.2": (
        "TS 38.521-1 7.3.2",
        "Reference sensitivity。N1X2 / N1X4 是接收天線組態（1×2 / 1×4），不是 n1 頻段。",
    ),
    "7.4": ("TS 38.521-1 7.4", "Maximum input level。"),
}


@dataclass(frozen=True)
class Meaning:
    clause: str
    spec: str
    note: str
    skip_hint: str
    confidence: str  # high / draft


def clause_of(test_name: str) -> str:
    m = re.match(r"^\s*(\d+(?:\.\d+)*)\b", test_name)
    if m:
        return m.group(1)
    if "sensitivity Search" in test_name:
        return "7.3.2-search"
    return ""


def meaning_of(test_name: str) -> Meaning:
    clause = clause_of(test_name)
    if clause in NR_SA:
        spec, note = NR_SA[clause]
        skip = ""
        if clause in {"6.2.3", "6.5.2.3", "6.5.2.4.2"}:
            skip = "摘要列 Skip 多半是測項不適用，不是量到失敗。待核對。"
        return Meaning(clause, spec, note, skip, "draft")
    if clause == "7.3.2-search":
        return Meaning(
            "7.3.2",
            "TS 38.521-1 7.3.2（搜尋）",
            "Sensitivity search。細節列常有一串 NotSet（掃功率），最後一點才是結果。",
            "",
            "draft",
        )
    return Meaning(clause or "?", "待補", "尚未對到 3GPP 條款。", "", "draft")


def skip_note(test_name: str, verdict: str) -> str:
    if (verdict or "").lower() != "skip":
        return ""
    m = meaning_of(test_name)
    return m.skip_hint or "摘要列 Skip：此 channel／band 未執行或標為不適用。待核對。"


def detail_pf_note(pf: str) -> str:
    p = (pf or "").strip()
    if p == "NotSet":
        return "搜尋／中間點，通常不計入摘要 Verdict。"
    if p == "Skip":
        return "此量測點不適用。"
    return ""
