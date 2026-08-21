"""Spec families shown on the 3GPP reference hub.

A family is the main number (38.521, 38.508, 38.213). Part suffixes
(-1, -2, …) stay on the same family page.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_DIR = ROOT / "3GPP SPEC"


@dataclass(frozen=True)
class SpecFile:
    name: str
    label: str
    note: str = ""


@dataclass(frozen=True)
class SpecFamily:
    slug: str
    number: str
    title_zh: str
    title_en: str
    href: str
    blurb: str
    scope_zh: str
    scope_en: str
    files: tuple[SpecFile, ...] = ()
    parts: tuple[tuple[str, str], ...] = ()
    present: bool = True


FAMILIES: tuple[SpecFamily, ...] = (
    SpecFamily(
        slug="38.521",
        number="TS 38.521",
        title_zh="UE 射頻符合性（發射／接收怎麼量）",
        title_en="NR; User Equipment (UE) conformance specification; Radio transmission and reception",
        href="/ref/38.521",
        blurb="RAN5 測法。限值本體在 38.101；這裡寫怎麼量、過不過。本中心已展開的是 38.521-1 第 6／7 章。",
        scope_zh=(
            "本文件規定 NR UE 射頻發射與接收的符合性測法。"
            "第 1 部分是 FR1 獨立作業；第 2 部分是 FR2；第 3 部分是與其他無線電互通；第 4 部分是效能。"
            "它不是功率公式本身。PUSCH／PUCCH／PRACH 該打多少 dBm，在 38.213；這裡量的是打出來的功率、mask、EVM 有沒有落在 38.101 的限值裡。"
        ),
        scope_en=(
            "The present document specifies the RF test methods for NR UE transmitter and receiver "
            "conformance. Part 1 covers FR1 standalone; Part 2 FR2; Part 3 interworking with other radios; "
            "Part 4 performance. It is not the uplink power-control procedure. How the UE computes "
            "PUSCH / PUCCH / PRACH power is specified in TS 38.213. This specification checks the "
            "radiated or conducted result against TS 38.101 limits."
        ),
        files=(
            SpecFile("ts_13852101v180500p.pdf", "38.521-1 V18.5.0", "本中心主檔"),
            SpecFile("ts_13852101v170500p.pdf", "38.521-1 V17.5.0", "備援；差異用「R17:」"),
        ),
        parts=(
            ("38.521-1", "FR1 SA 射頻。資料夾裡有 V18／V17。第 6／7 章已展開。"),
            ("38.521-2", "FR2 SA 射頻。資料夾尚未放 PDF。"),
            ("38.521-3", "與其他無線電互通（例如 EN-DC）。資料夾尚未放 PDF。"),
            ("38.521-4", "效能（解調）。資料夾尚未放 PDF。"),
        ),
    ),
    SpecFamily(
        slug="38.508",
        number="TS 38.508",
        title_zh="UE 符合性共用測試環境",
        title_en="5GS; User Equipment (UE) conformance specification; Common test environment",
        href="/ref/38.508",
        blurb="RAN5 測環境。頻點、適用條件、訊息內容。38.521 各條測案會引用這裡，不是另一本射頻限值。",
        scope_zh=(
            "本文件定義 5G 系統的測試環境，涵蓋 NG-RAN、5GC，以及 5GS 與 EPS 互通，供 UE 符合性測試使用。"
            "第 1 部分是共用測試環境；第 2 部分是 ICS 聲明表。"
        ),
        scope_en=(
            "The present document defines the test environment for the 5G System. "
            "This specification covers all aspects, including NG-RAN, 5GC and interworking between "
            "5GS and EPS used for conformance tests of User Equipment (UE). "
            "3GPP TS 38.508-1: Common test environment (the present document). "
            "3GPP TS 38.508-2: Common Implementation Conformance Statement (ICS) proforma."
        ),
        files=(
            SpecFile("38.508/ts_13850801v170600p.pdf", "38.508-1 V17.6.0", "主檔"),
            SpecFile("38.508/ts_13850801v150400p (Note).pdf", "38.508-1 V15.4.0", "備註／較舊"),
        ),
        parts=(
            ("38.508-1", "共用測試環境（頻點、組態、訊息）。資料夾有 V17／V15。"),
            ("38.508-2", "ICS 聲明表。資料夾尚未放 PDF。"),
        ),
    ),
    SpecFamily(
        slug="38.213",
        number="TS 38.213",
        title_zh="NR 實體層控制程序（含 UL 功率怎麼算）",
        title_en="NR; Physical layer procedures for control",
        href="/ref/38.213",
        blurb="RAN1 程序。PUSCH／PUCCH／PRACH／SRS 的發射功率公式在第 7 章。不是 38.521 的射頻測法。",
        scope_zh="本文件規定並確立 5G-NR 控制運作的實體層程序特性。",
        scope_en="The present document specifies and establishes the characteristics of the physical layer procedures for control operations in 5G-NR.",
        files=(
            SpecFile("38.213/ts_138213v170300p.pdf", "38.213 V17.3.0", "主檔（5G-NR）"),
            SpecFile("38.213/ts_138213v150800p.pdf", "38.213 V15.8.0", "對照 V17"),
            SpecFile("38.213/ETSI-TS-138-213-V18-4-0-2024-10-.pdf", "38.213 V18.4.0", "不完整（14 頁），只標註"),
            SpecFile("38.213/ts_136213v150500p(note).pdf", "36.213 V15.5.0", "LTE 對照，不是 NR"),
        ),
        parts=(
            ("38.213", "NR 控制程序。主檔 V17.3.0。"),
            ("36.213", "LTE／E-UTRA 實體層程序。功率在 5.1 章。"),
        ),
    ),
)


def family_by_slug(slug: str) -> SpecFamily | None:
    for fam in FAMILIES:
        if fam.slug == slug:
            return fam
    return None


def resolve_file(rel: str) -> Path:
    return SPEC_DIR / rel
