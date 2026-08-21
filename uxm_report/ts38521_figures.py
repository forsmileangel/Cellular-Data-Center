"""Figures for 3GPP reference pages.

38.521-1 figures are almost all vector drawings (lines/text), not embedded
JPEGs, so pdfimages cannot pull them. The PNGs under assets/spec_figures
are cropped from the V18.5.0 PDF page around each Figure caption.

Chapter 7 has no Figure captions at all. Those clauses keep a labelled
sketch so the interference geometry is visible, and the page text says so.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ASSET_DIR = Path(__file__).resolve().parent / "assets" / "spec_figures"


@dataclass(frozen=True)
class SpecFigure:
    fid: str
    title: str
    page: int
    png: str = ""
    svg: str = ""
    note: str = ""

    @property
    def is_original(self) -> bool:
        return bool(self.png) and (ASSET_DIR / self.png).is_file()


def _svg(body: str, w: int = 640, h: int = 220) -> str:
    return (
        f'<svg viewBox="0 0 {w} {h}" width="100%" style="max-width:{w}px;background:#fff;'
        f'border:1px solid #ddd">'
        '<style>text{font-family:Segoe UI,Microsoft JhengHei,sans-serif;font-size:12px;fill:#222}'
        "</style>"
        f"{body}</svg>"
    )


def _pdf(fid: str, title: str, page: int, note: str = "") -> SpecFigure:
    return SpecFigure(fid, title, page, png=f"{fid}.png", note=note)


# --- original crops from ts_13852101v180500p.pdf --------------------------

F_ONOFF = _pdf(
    "6.3.3.2.3-1",
    "General ON/OFF time mask for NR UL transmission in FR1",
    713,
    "OFF 區間不含暫態。預設 tp = 10 µs。",
)
F_PRACH = _pdf(
    "6.3.3.4.3-1",
    "PRACH ON/OFF time mask",
    718,
    "裁切含其上方 preamble 量測時間表（PDF 原表）。",
)
F_SRS1 = _pdf("6.3.3.6.3-1", "Single SRS time mask for NR UL transmission", 723)
F_SRS2 = _pdf(
    "6.3.3.6.3-2",
    "Consecutive SRS time mask when no power change is required",
    724,
)
F_SRS3 = _pdf(
    "6.3.3.6.3-3",
    "Consecutive SRS time mask when power change is required (other than antenna switching)",
    724,
    "PDF 裡這張是內嵌 JPEG，放大會看到原檔的壓縮痕跡。",
)
F_SRS4 = _pdf(
    "6.3.3.6.3-4",
    "Consecutive SRS time mask when power change is required (antenna-switching case)",
    724,
)
F_SRS5 = _pdf(
    "6.3.3.6.3-5",
    "FR1 time mask for 15 kHz and 30 kHz SCS, consecutive SRS",
    724,
)
F_TPC_FDD_UP = _pdf("6.3.4.3.4.2-1", "FDD ramping up test power patterns", 737)
F_TPC_FDD_DN = _pdf("6.3.4.3.4.2-2", "FDD ramping down test power patterns", 738)
F_TPC_TDD_UP = _pdf("6.3.4.3.4.2-3", "TDD ramping up test power patterns", 739)
F_TPC_TDD_DN = _pdf("6.3.4.3.4.2-4", "TDD ramping down test power patterns", 740)
F_TPC_ALT = _pdf("6.3.4.3.4.2-5", "Alternating test power patterns", 741)
F_AGG = _pdf("6.3.4.4.4.2-1", "Test uplink transmission (aggregate power)", 751)
F_EVM_TR = _pdf(
    "6.4.2.1a.4.2-1",
    "Error Vector Magnitude including symbols with transient period",
    1005,
)
F_EVM_RB = _pdf(
    "6.4.2.1a.4.2-2",
    "Test power / RB patterns for EVM including transient symbols",
    1005,
)
F_FLAT_LIM = _pdf(
    "6.4.2.4.3-1",
    "Limits for EVM equalizer spectral flatness (maximum allowed variation)",
    1016,
)
F_FLAT_TEST = _pdf(
    "6.4.2.4.5-1",
    "Test requirements for EVM equalizer spectral flatness",
    1018,
)
F_PI2_LIM = _pdf(
    "6.4.2.5.3-1",
    "EVM equalizer spectral flatness for Pi/2 BPSK (minimum requirement)",
    1020,
)
F_PI2_TEST = _pdf(
    "6.4.2.5.5-1",
    "EVM equalizer spectral flatness for Pi/2 BPSK (test requirement)",
    1022,
)
F_SPEC = _pdf(
    "6.5.0-1",
    "Transmitter RF spectrum",
    1149,
    "通道／ΔfOOB（SEM+ACLR）／雜散三區。",
)

# --- sketches only where the spec itself has no Figure --------------------

F_ACS = SpecFigure(
    "7.5-sketch",
    "ACS 量測配置（示意）",
    1661,
    svg=_svg(
        '<rect x="200" y="60" width="140" height="70" fill="#cfe8e8" stroke="#008787"/>'
        '<text x="220" y="90">Wanted</text>'
        '<text x="215" y="108">REFSENS+14 dB</text>'
        '<rect x="360" y="50" width="140" height="90" fill="#f3c8c8" stroke="#8b0000"/>'
        '<text x="385" y="90">鄰道干擾</text>'
        '<text x="375" y="108">調變 NR 信號</text>'
        '<text x="60" y="180">吞吐仍須 ≥95%。ACS 本身是濾波比，測的是這組電平下過不過。</text>'
    ),
    note="38.521-1 第 7 章沒有 Figure。這張依 Table 7.5.3-1／7.5.3-2 畫，不是 PDF 原圖。",
)
F_BLOCK = SpecFigure(
    "7.6-sketch",
    "In-band / OOB blocking 頻率關係（sub-3 GHz 示意）",
    1714,
    svg=_svg(
        '<rect x="220" y="70" width="200" height="50" fill="#cfe8e8" stroke="#008787"/>'
        '<text x="270" y="100">UE 接收頻段</text>'
        '<rect x="150" y="70" width="70" height="50" fill="#f3e6c8" stroke="#8a6d00"/>'
        '<rect x="420" y="70" width="70" height="50" fill="#f3e6c8" stroke="#8a6d00"/>'
        '<text x="155" y="100">±15 MHz</text>'
        '<text x="80" y="160">7.6.2 in-band：帶內＋兩邊 15 MHz（干擾是 NR 信號）</text>'
        '<text x="80" y="180">7.6.3 OOB：Range1 −44 dBm → Range2 −30 → Range3 −15（CW）</text>'
        '<text x="80" y="200">過不了的離散點改走 7.7 雜散響應</text>'
    ),
    note="38.521-1 沒有 blocking 原圖。這張依 7.6.2／7.6.3 表畫。",
)
F_IMD = SpecFigure(
    "7.8.2-sketch",
    "Wideband IMD 兩個干擾（示意）",
    1851,
    svg=_svg(
        '<rect x="80" y="70" width="100" height="60" fill="#cfe8e8" stroke="#008787"/>'
        '<text x="100" y="105">Wanted</text>'
        '<rect x="260" y="70" width="100" height="60" fill="#f3c8c8" stroke="#8b0000"/>'
        '<text x="275" y="96">干擾 1</text>'
        '<text x="280" y="114">CW −46</text>'
        '<rect x="420" y="70" width="120" height="60" fill="#f3c8c8" stroke="#8b0000"/>'
        '<text x="435" y="96">干擾 2</text>'
        '<text x="430" y="114">調變 −46</text>'
        '<text x="70" y="170">偏移約 ±(BW/2+7.5) MHz 與 2× 該值，差頻落到本信道。</text>'
        '<text x="70" y="190">這是接收互調。發射被 CW 灌進去產 IMD 是 6.5.4。</text>'
    ),
    note="38.521-1 沒有 IMD 原圖。這張依 Table 7.8.2.3-1 畫。",
)

FIGURES: dict[str, tuple[SpecFigure, ...]] = {
    "6.3": (F_ONOFF,),
    "6.3.3": (F_ONOFF,),
    "6.3.3.2": (F_ONOFF,),
    "6.3.3.4": (F_PRACH,),
    "6.3.3.6": (F_SRS1, F_SRS2, F_SRS3, F_SRS4, F_SRS5),
    "6.3.4": (F_TPC_FDD_UP, F_AGG),
    "6.3.4.3": (F_TPC_FDD_UP, F_TPC_FDD_DN, F_TPC_TDD_UP, F_TPC_TDD_DN, F_TPC_ALT),
    "6.3.4.4": (F_AGG,),
    "6.4.2.1a": (F_EVM_TR, F_EVM_RB),
    "6.4.2.4": (F_FLAT_LIM, F_FLAT_TEST),
    "6.4.2.5": (F_PI2_LIM, F_PI2_TEST),
    "6.5": (F_SPEC,),
    "6.5.1": (F_SPEC,),
    "6.5.2.2": (F_SPEC,),
    "6.5.3": (F_SPEC,),
    "6.5.3.1": (F_SPEC,),
    "7.5": (F_ACS,),
    "7.6": (F_BLOCK,),
    "7.6.2": (F_BLOCK,),
    "7.6.3": (F_BLOCK,),
    "7.8": (F_IMD,),
    "7.8.2": (F_IMD,),
}

NO_FIGURE_TEXT = {
    "6.2": "38.521-1 用表規定功率，沒有 Figure。",
    "6.2.1": "38.521-1 用表規定 Power Class，沒有 Figure。",
    "6.2.2": "38.521-1 用表規定 MPR，沒有 Figure。",
    "6.2.3": "A-MPR 是 NS×band 細表，沒有 Figure。",
    "6.2.4": "PCMAX 是公式，沒有 Figure。",
    "6.3.1": "最小功率是一個上限數字，沒有 Figure。",
    "6.3.2": "OFF 功率是一個上限；波形看 6.3.3 的 time mask。",
    "6.3.3.3": "規格標不可測，沒有圖、也沒有表。",
    "6.3.3.7": "規格標不可測，沒有圖、也沒有表。",
    "6.3.4.2": "絕對功率容差是一個 ±dB，沒有 Figure。",
    "6.4.1": "頻率誤差是一個 ppm 數字，沒有 Figure。",
    "6.4.2.1": "EVM 限值在表裡，沒有 Figure。含暫態的圖在 6.4.2.1a。",
    "6.4.2.2": "載波洩漏是 dBc 數字，沒有 Figure。",
    "6.4.2.3": "IBE 是公式，沒有 Figure。",
    "6.4.2.6": "相位連續是相位差數字，沒有 Figure。",
    "6.5.2.3": "加嚴 SEM 按 NS 列表，沒有獨立 Figure。區域看 6.5.0-1。",
    "6.5.2.4.1": "ACLR 是一個比，沒有 Figure。",
    "6.5.2.4.2": "UTRA ACLR 是一個比，沒有 Figure。",
    "6.5.3.2": "共存雜散是按 band 展開的長表，沒有 Figure。",
    "6.5.3.3": "NS 加嚴雜散是表，沒有 Figure。",
    "6.5.4": "發射互調是 dBc 表，沒有 Figure。",
    "7": "38.521-1 第 7 章整章沒有 Figure。",
}


def figures_for(clause_id: str) -> tuple[SpecFigure, ...]:
    return FIGURES.get(clause_id, ())


def no_figure_reason(clause_id: str) -> str:
    if clause_id in NO_FIGURE_TEXT:
        return NO_FIGURE_TEXT[clause_id]
    if clause_id.startswith("7"):
        return "38.521-1 第 7 章整章沒有 Figure。干擾怎麼擺寫在表裡。"
    if any(ch.isalpha() for ch in clause_id):
        return "A–L 變體沿用本體那一條的圖；本條通常不再另畫。"
    return "這一條在 38.521-1 沒有 Figure。"
