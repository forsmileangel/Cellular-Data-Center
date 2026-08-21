"""TS 38.521-1 clause cards curated from the PDF in 3GPP SPEC/.

Primary source is V18.5.0. V17.5.0 is fallback only when a value
is missing from the new PDF. The HTML page does not scrape the
2095-page PDF at request time.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_DIR = ROOT / "3GPP SPEC"
SPEC_DOC = "TS 38.521-1"
SPEC_VERSION = "18.5.0"
SPEC_ETSI = "ETSI TS 138 521-1 V18.5.0 (2025-02)"
SPEC_FILE = "ts_13852101v180500p.pdf"
SPEC_FALLBACK_VERSION = "17.5.0"
SPEC_FALLBACK_ETSI = "ETSI TS 138 521-1 V17.5.0 (2022-09)"
SPEC_FALLBACK_FILE = "ts_13852101v170500p.pdf"
# Printed page in the ETSI PDF (cover is PDF page 1; printed N ≈ PDF N+1).
LIMIT_REF = "限值本體在 TS 38.101-1 對應條款；38.521-1 是符合性測法。"


@dataclass(frozen=True)
class Clause:
    id: str
    chapter: str
    title: str
    page: int
    purpose: str
    rfa_tests: tuple[str, ...]
    items: tuple[str, ...]
    skip: str = ""
    watch: str = ""
    extra: str = ""
    original: str = ""


@dataclass
class SpecFolder:
    expected: Path
    pdfs: list[Path]
    extra: list[Path]


def spec_folder() -> SpecFolder:
    pdfs = sorted(SPEC_DIR.glob("*.pdf")) if SPEC_DIR.is_dir() else []
    expected = SPEC_DIR / SPEC_FILE
    extra = [p for p in pdfs if p.name != SPEC_FILE]
    return SpecFolder(expected=expected, pdfs=pdfs, extra=extra)


def clause_of(test_name: str) -> str:
    name = test_name or ""
    if "sensitivity Search" in name:
        return "7.3.2"
    m = re.match(r"^\s*(\d+(?:\.\d+)*)\b", name)
    return m.group(1) if m else ""


CLAUSES: list[Clause] = [
    Clause(
        "6.2.1",
        "6.2 發射功率",
        "UE maximum output power",
        112,
        "確認 UE 最大輸出功率落在標稱功率與容差內。過大可能干擾鄰信道／其他系統；過小會縮小覆蓋。",
        ("6.2.1 UE Maximum Output Power",),
        ("NR Power",),
        watch="PC3 預設 23 dBm。V18：n1／n2／n3／n7／n8 新增 PC2 26 dBm；n7／n25／n40／n41／n66／n71／n77／n78 等新增 PC1 31 dBm（R17 僅 n14 有 PC1，PC2 僅 n34／n39／n41／n77／n78／n79）。帶緣 4 MHz 內下限可再鬆 1.5 dB（NOTE 3）；n91–n94／n109 另有 NOTE 4 再鬆 0.3 dB。",
        extra=LIMIT_REF + " 規範參考 38.101-1 6.2.1。",
        original=(
            "6.2.1.1 Test purpose\n"
            "To verify that the error of the UE maximum output power does not exceed the range prescribed "
            "by the specified nominal maximum output power and tolerance.\n"
            "An excess maximum output power has the possibility to interfere to other channels or other systems. "
            "A small maximum output power decreases the coverage area.\n"
            "6.2.1.2 Test applicability\n"
            "This test case applies to all types of NR Power Class 1 UE release 15 and forward.\n"
            "This test case applies to all types of NR Power Class 2 and Power Class 3 UE release 15 and forward "
            "that don't support Tx diversity and don't support RedCap."
        ),
    ),
    Clause(
        "6.2.2",
        "6.2 發射功率",
        "UE maximum output power reduction",
        119,
        "高階調變與 RB 配置允許降最大功率（MPR），好讓 ACLR 仍過。Edge／Outer／Inner RB 與 DFT-s／CP-OFDM 的允許降幅不同。",
        ("6.2.2 UE maximum output power reduction",),
        ("NR Power",),
        skip="規格註：若已完整執行 6.5.2.4.1 NR ACLR，本項可不另跑。",
        watch="V18 拆成 PC3／PC2／PC1 三張 MPR 表，另有 ΔMPR（n28／n83 30 MHz 0.5 dB；n40／n97 100 MHz 1 dB）。3 MHz Pi/2 Edge 另加 1 dB（NOTE 3）。Rel-18 powerBoost IEs 仍標 FFS。",
        extra=LIMIT_REF + " 規範參考 38.101-1 6.2.2。",
        original=(
            "6.2.2.1 Test purpose\n"
            "The number of RB identified in Table 6.2.2.3-1 is based on meeting the requirements for "
            "adjacent channel leakage ratio and the maximum power reduction (MPR) due to Cubic Metric (CM).\n"
            "UE is allowed to reduce the maximum output power due to higher order modulations and transmit "
            "bandwidth configurations.\n"
            "NOTE: Test execution is not necessary if TS 38.521-1 6.5.2.4.1 is executed.\n"
            "6.2.2.2 Test applicability\n"
            "This test case applies to all types of NR Power Class 1 UE release 15 and forward.\n"
            "This test case applies to all types of NR Power Class 2 and Power Class 3 UE release 15 and forward "
            "that don't support Tx diversity."
        ),
    ),
    Clause(
        "6.2.3",
        "6.2 發射功率",
        "UE additional maximum output power reduction",
        149,
        "網路用 NS（additionalSpectrumEmission）下額外頻譜要求時，才允許再降功率（A-MPR）。總降幅通常是 max(MPR, A-MPR)。沒有對應 NS 就不適用。",
        ("6.2.3 UE additional maximum output power reduction",),
        ("NR Power",),
        skip="細節列 Condition 沒有 NS_xx，或測項標 Skip，多半是這個 band／channel 沒有額外 NS，不是量失敗。",
        watch="NS_01 是各 band 預設、通常無 A-MPR。你們會碰到的：n1→NS_05／NS_100；n8→NS_43／NS_100；n7→NS_46；n41→NS_04；n2→NS_03／NS_100。n78／n79 在表 6.2.3.3.1-1A 主要是 NS_01。",
        extra="與 6.5.2.3／6.5.2.4.2／6.5.3.3 綁在一起；規格寫若那些已執行，本項可不另跑。",
        original=(
            "6.2.3.1 Test purpose\n"
            "Additional emission requirements can be signalled by the network. Each additional emission "
            "requirement is associated with a unique network signalling (NS) value indicated in RRC signalling "
            "by an NR frequency band number of the applicable operating band and an associated value in the "
            "field additionalSpectrumEmission.\n"
            "To meet the additional requirements, additional maximum power reduction (A-MPR) is allowed for "
            "the maximum output power as specified in Table 6.2.1.3-1. Unless stated otherwise, the total "
            "reduction to UE maximum output power is max(MPR, A-MPR) where MPR is defined in clause 6.2.2.\n"
            "NOTE: Test execution is not necessary if 6.5.2.3, 6.5.2.4.2 and 6.5.3.3 are executed."
        ),
    ),
    Clause(
        "6.2.4",
        "6.2 發射功率",
        "Configured transmitted power",
        323,
        "確認設定發射功率 PCMAX（受 P-Max、MPR、A-MPR 限制後的上限）在容差內，不是再量一次 23 dBm 標稱值。",
        ("6.2.4 Configured transmitted power",),
        ("NR Power", "PCMAX"),
        extra=LIMIT_REF + " 規範參考 38.101-1 6.2.4。",
        original=(
            "6.2.4 Configured transmitted power\n"
            "The configured transmitted power PCMAX is the UE maximum output power after applying the "
            "configured maximum output power P-Max and the allowed reductions (MPR, A-MPR, ΔTIB,c). "
            "The test verifies that the measured output power stays within the configured-power tolerance, "
            "not the nominal 23 dBm power class by itself.\n"
            "The normative reference for this requirement is TS 38.101-1 clause 6.2.4."
        ),
    ),
    Clause(
        "6.3.1",
        "6.3 功率動態",
        "Minimum output power",
        709,
        "功率設到最小時，通道內寬帶功率必須低於表列上限。V18 改成公式：3–20 MHz 為 −40 dBm；更寬則 −40+10log10(BW/20)。R17 是逐 BW 列數字，數值與公式四捨五入後相同，但沒有 3／35 MHz。",
        ("6.3.1 Minimum Output Power",),
        ("NR Power",),
        extra="規範參考 38.101-1 6.3.1。",
        original=(
            "6.3.1.1 Test purpose\n"
            "To verify the UE's ability to transmit with a broadband output power below the value specified "
            "in the test requirement when the power is set to a minimum value.\n"
            "The minimum controlled output power of the UE is defined as the power in the channel bandwidth "
            "for all transmit bandwidth configurations (resource blocks), when the power is set to a minimum value."
        ),
    ),
    Clause(
        "6.3.2",
        "6.3 功率動態",
        "Transmit OFF power",
        711,
        "發射機關閉時通道平均功率必須夠低（測試要求約 −50 dBm+TT）。過高會抬升 RoT、擠壓其他 UE 覆蓋。本項由 6.3.3 time mask 覆蓋。",
        ("6.3.2 Transmit Off Power",),
        ("NR Power", "OFF Power"),
        extra="規範參考 38.101-1 6.3.2。",
        original=(
            "6.3.2.1 Test purpose\n"
            "To verify that the UE transmit OFF power is lower than the value specified in the test requirement.\n"
            "An excess Transmit OFF power potentially increases the Rise Over Thermal (RoT) and therefore "
            "reduces the cell coverage area for other UEs.\n"
            "This test is covered by clause 6.3.3 Transmit ON/OFF time mask."
        ),
    ),
    Clause(
        "6.3.3.2",
        "6.3 功率動態",
        "General ON/OFF time mask",
        713,
        "ON／OFF 之間只允許短暫暫態（預設 10 µs）。量錯功率會干擾別的通道或讓本機 UL 錯誤增加。",
        ("6.3.3.2 General ONOFF time mask",),
        ("NR Power",),
        extra="規範參考 38.101-1 6.3.3.2。",
        original=(
            "6.3.3.2.1 Test purpose\n"
            "To verify that the general ON/OFF time mask meets the requirements given in 6.3.3.2.5.\n"
            "The transmit power time mask for transmit ON/OFF defines the transient period(s) allowed between "
            "transmit OFF power as defined in sub-clause 6.3.2 and transmit ON power symbols (transmit ON/OFF).\n"
            "Transmission of the wrong power increases interference to other channels, or increases transmission "
            "errors in the uplink channel."
        ),
    ),
    Clause(
        "6.3.3.4",
        "6.3 功率動態",
        "PRACH time mask",
        717,
        "發 PRACH 時，OFF→ON→OFF 必須落在 time mask 內。RFA 名稱後的 −118／−124 是 preambleReceivedTargetPower（dBm），不是頻段。",
        (
            "6.3.3.4 PRACH time mask",
            "6.3.3.4 PRACH time mask -118",
            "6.3.3.4 PRACH time mask -124",
        ),
        ("NR Power",),
        extra="規範參考 38.101-1 6.3.3.4。PDF Table 6.3.3.4.4.3-2 可見 −118／−122／−124／−128。",
        original=(
            "6.3.3.4.1 Test purpose\n"
            "To verify that the PRACH time mask meets the requirements given in 6.3.3.4.5.\n"
            "The time mask for PRACH time mask defines the transient period(s) allowed between transmit OFF "
            "power and transmit ON power when transmitting the PRACH.\n"
            "Transmission of the wrong power increases interference to other channels, or increases transmission "
            "errors in the uplink channel.\n"
            "preambleReceivedTargetPower in Table 6.3.3.4.4.3-2 uses values such as −118, −122, −124, −128 dBm; "
            "these are not operating-band numbers."
        ),
    ),
    Clause(
        "6.3.3.6",
        "6.3 功率動態",
        "SRS time mask",
        723,
        "發 SRS 時的 ON／OFF 暫態，概念同 PRACH time mask。",
        ("6.3.3.6 SRS time mask",),
        ("NR Power",),
        extra="規範參考 38.101-1 6.3.3.6。",
        original=(
            "6.3.3.6.1 Test purpose\n"
            "To verify that the SRS time mask meets the requirements given in 6.3.3.6.5.\n"
            "The time mask for SRS time mask defines the transient period(s) allowed between transmit OFF "
            "power and transmit ON power when transmitting the SRS.\n"
            "Transmission of the wrong power increases interference to other channels, or increases transmission "
            "errors in the uplink channel."
        ),
    ),
    Clause(
        "6.3.4.2",
        "6.3 功率動態",
        "Absolute power tolerance",
        731,
        "單一 TPC 指令後，量到的功率與預期絕對值的誤差要在容差內。",
        ("6.3.4.2 Absolute power tolerance",),
        ("NR Power",),
        extra="規範參考 38.101-1 6.3.4.2。",
        original=(
            "6.3.4.2.1 Test purpose\n"
            "To verify the ability of the UE transmitter to set its initial output power to a specific value "
            "at the start of a contiguous transmission or non-contiguous transmission with a long transmission "
            "gap, i.e. transmission gap is larger than 20ms.\n"
            "The absolute power tolerance is the ability of the UE transmitter to set its initial output power "
            "to a specific value for the first sub-frame (1ms). The tolerance includes the channel estimation error. "
            "Normal-condition tolerance is ±9.0 dB."
        ),
    ),
    Clause(
        "6.3.4.4",
        "6.3 功率動態",
        "Aggregate power tolerance",
        749,
        "一段連續傳輸裡，功率控制的累積誤差。RFA 這項點數通常很少。",
        ("6.3.4.4 Aggregate power tolerance",),
        ("NR Power",),
        extra="規範參考 38.101-1 6.3.4.4。",
        original=(
            "6.3.4.4 Aggregate power tolerance\n"
            "To verify the ability of the UE to maintain its average output power during non-contiguous "
            "transmissions with a transmission gap larger than 20 ms. The aggregate power control tolerance "
            "applies over a longer observation than a single TPC step (contrast 6.3.4.2 / 6.3.4.3).\n"
            "The normative reference for this requirement is TS 38.101-1 clause 6.3.4.4."
        ),
    ),
    Clause(
        "6.4.1",
        "6.4 訊號品質",
        "Frequency error",
        994,
        "同時驗證收發頻率：接收機從 SS 取出正確頻率，發射機再據此產生載波。要求相對 gNB 載波 ±0.1 ppm（測試要求再加 15 Hz）。在 REFSENS 電平、UL 打到 PUMAX 下量。",
        ("6.4.1 Frequency error",),
        ("Freq Error in Hz",),
        extra="規範參考 38.101-1 6.4.1。",
        original=(
            "6.4.1.1 Test purpose\n"
            "This test verifies the ability of both, the receiver and the transmitter, to process frequency correctly.\n"
            "Receiver: to extract the correct frequency from the stimulus signal, offered by the System simulator, "
            "under ideal propagation conditions and low level.\n"
            "Transmitter: to derive the correct modulated carrier frequency from the results, gained by the receiver.\n"
            "The mean value of basic measurements of UE modulated carrier frequency shall be accurate to within "
            "±0.1 PPM observed over a period of 1 ms of cumulated measurement intervals compared to the carrier "
            "frequency received from the NR Node B. Test requirement: |Δf| ≤ (0.1 PPM + 15 Hz)."
        ),
    ),
    Clause(
        "6.4.2.1",
        "6.4 訊號品質",
        "Error Vector Magnitude",
        996,
        "量測波形與參考波形的誤差向量幅度。RFA 拆成 PRACH／PUCCH／PUSCH 三條。QPSK 限 17.5%；256QAM 3.5%。PUSCH 還會有 DMRS EVM。",
        (
            "6.4.2.1 PRACH Error Vector Magnitude",
            "6.4.2.1 PUCCH Error Vector Magnitude",
            "6.4.2.1 PUSCH Error Vector Magnitude",
        ),
        ("PUSCH EVM", "PUSCH DMRS EVM", "PUCCH EVM", "PRACH EVM"),
        extra="規範參考 38.101-1 6.4.2.1。",
        original=(
            "6.4.2.1.1 Test Purpose\n"
            "The Error Vector Magnitude is a measure of the difference between the reference waveform and the "
            "measured waveform. This difference is called the error vector. Before calculating the EVM the "
            "measured waveform is corrected by the sample timing offset and RF frequency offset. Then the "
            "carrier leakage shall be removed from the measured waveform before calculating the EVM.\n"
            "The RMS average of the basic EVM measurements shall not exceed: Pi/2-BPSK 30%, QPSK 17.5%, "
            "16QAM 12.5%, 64QAM 8%, 256QAM 3.5%. PUCCH EVM and PRACH EVM shall not exceed 17.5%."
        ),
    ),
    Clause(
        "6.4.2.2",
        "6.4 訊號品質",
        "Carrier leakage",
        1007,
        "載波洩漏是與載波同頻、幅度幾乎固定的正弦干擾，與想要訊號的大小無關。相對洩漏功率隨輸出功率分檔（例如 >10 dBm 要 ≤ −28 dBc）。",
        ("6.4.2.2 Carrier leakage",),
        ("CarrierLeakageWorstMargin",),
        extra="若 UE 回報 txDirectCurrentLocation=3300／3301，規格說本項可不測。",
        original=(
            "6.4.2.2.1 Test purpose\n"
            "Carrier leakage expresses itself as unmodulated sine wave with the carrier frequency or centre "
            "frequency of aggregated transmission bandwidth configuration. It is an interference of approximately "
            "constant amplitude and independent of the amplitude of the wanted signal.\n"
            "The purpose of this test is to exercise the UE transmitter to verify its modulation quality in terms "
            "of carrier leakage.\n"
            "In case the parameter 3300 or 3301 is reported from UE via txDirectCurrentLocation IE, carrier "
            "leakage measurement requirement shall be waived."
        ),
    ),
    Clause(
        "6.4.2.3",
        "6.4 訊號品質",
        "In-band emissions",
        1010,
        "未分配 RB 上的帶內雜散：未分配 RB 功率相對已分配 RB。RFA 分 PUCCH／PUSCH。含 General、IQ Image、Carrier leakage 合成限。",
        (
            "6.4.2.3 PUCCH In-band emissions",
            "6.4.2.3 PUSCH In-band emissions",
        ),
        ("IQImageWorstMargin", "GeneralWorstMargin", "CarrierLeakageWorstMargin"),
        extra="規範參考 38.101-1 6.4.2.3。",
        original=(
            "6.4.2.3.1 Test purpose\n"
            "The in-band emissions are a measure of the interference falling into the non-allocated resource blocks.\n"
            "The in-band emission is defined as the average emission across 12 sub-carriers and as a function of "
            "the RB offset from the edge of the allocated UL transmission bandwidth. The in-band emission is "
            "measured as the ratio of the UE output power in a non-allocated RB to the UE output power in an "
            "allocated RB.\n"
            "The purpose of this test is to exercise the UE transmitter to verify its modulation quality in terms "
            "of in-band emissions."
        ),
    ),
    Clause(
        "6.4.2.4",
        "6.4 訊號品質",
        "EVM equalizer spectrum flatness",
        1015,
        "EVM 計算用的等化器係數在頻帶內必須夠平，否則通道估計／均衡把失真吃掉、EVM 會看起來過好。",
        ("6.4.2.4 EVM equalizer spectrum flatness",),
        ("Spectrum Flatness",),
        extra="規範參考 38.101-1 6.4.2.4。",
        original=(
            "6.4.2.4.1 Test purpose\n"
            "The zero-forcing equalizer correction applied in the EVM measurement process (as described in Annex E) "
            "must meet a spectral flatness requirement for the EVM measurement to be valid. The EVM equalizer "
            "spectrum flatness is defined in terms of the maximum peak-to-peak ripple of the equalizer coefficients "
            "(dB) across the allocated uplink block.\n"
            "The EVM equalizer spectrum flatness requirement does not limit the correction applied to the signal "
            "in the EVM measurement process but for the EVM result to be valid, the equalizer correction that was "
            "applied must meet the EVM equalizer spectrum flatness minimum requirements."
        ),
    ),
    Clause(
        "6.4.2.5",
        "6.4 訊號品質",
        "EVM equalizer spectrum flatness for Pi/2 BPSK",
        1019,
        "Pi/2-BPSK（含特殊 DMRS）的等化器平坦度，與 6.4.2.4 分開。",
        ("6.4.2.5 EVM equalizer spectrum flatness for BPSK",),
        ("Spectrum Flatness",),
        extra="規範參考 38.101-1 6.4.2.5。",
        original=(
            "6.4.2.5.1 Test purpose\n"
            "The zero-forcing equalizer correction applied in the EVM measurement process (as described in Annex E) "
            "must meet a spectral flatness requirement for the EVM measurement to be valid.\n"
            "6.4.2.5.2 Test applicability\n"
            "This test case applies to all types of power class 3 capable NR UE release 15 and forward indicating "
            "support for UE capability powerBoosting-pi2BPSK and operating in TDD bands n40, n41, n77, n78 and n79. "
            "This test case also applies to NR UE release 16 and forward indicating support for "
            "lowPAPR-DMRS-PUSCHwithPrecoding-r16."
        ),
    ),
    Clause(
        "6.5.1",
        "6.5 頻譜",
        "Occupied bandwidth",
        1149,
        "佔用頻寬＝包含發射總功率 99% 的寬度，必須 ≤ 標稱通道頻寬。",
        ("6.5.1 Occupied bandwidth",),
        ("Occupied Bandwidth",),
        watch="Table 6.5.1.4.1-2：n77／n78／n79 要量 Low／Mid／High，不是只量 Mid。",
        extra="規範參考 38.101-1 6.5.1。",
        original=(
            "6.5.1.1 Test purpose\n"
            "To verify that the UE occupied bandwidth for all transmission bandwidth configurations supported "
            "by the UE are less than their specific limits.\n"
            "Occupied bandwidth is defined as the bandwidth containing 99 % of the total integrated mean power "
            "of the transmitted spectrum on the assigned channel.\n"
            "Table 6.5.1.4.1-2 Test frequency exceptions: n77 / n78 / n79 = Low, Mid and High range."
        ),
    ),
    Clause(
        "6.5.2.2",
        "6.5 頻譜",
        "Spectrum emission mask",
        1151,
        "通道邊緣以外、雜散區以內的不想要發射不得超過 SEM。RFA 細節列極多（GeneralWorstMargin 等），是全庫列數最多的條款之一。",
        ("6.5.2.2 Spectrum Emission Mask",),
        ("GeneralWorstMargin", "AllWorstMargin"),
        watch="Edge 1RB 與高階調變最容易貼限。n78／n79／n41 通道寬、offset 點多。",
        extra="規範參考 38.101-1 6.5.2.2。",
        original=(
            "6.5.2.1 General\n"
            "The Out of band emissions are unwanted emissions immediately outside the assigned channel bandwidth "
            "resulting from the modulation process and non-linearity in the transmitter but excluding spurious "
            "emissions. This out of band emission limit is specified in terms of a spectrum emission mask and "
            "an adjacent channel leakage power ratio.\n"
            "6.5.2.2.1 Test purpose\n"
            "To verify that the power of any UE emission shall not exceed specified level for the specified "
            "channel bandwidth."
        ),
    ),
    Clause(
        "6.5.2.3",
        "6.5 頻譜",
        "Additional spectrum emission mask",
        1158,
        "有額外 NS 頻譜要求時才適用的加嚴 SEM。沒有對應 NS 就 Skip。",
        ("6.5.2.3 Additional spectrum emission mask",),
        ("GeneralWorstMargin",),
        skip="沒有 NS_03／NS_04／NS_06／NS_35 這類 extra mask 時 Skip 是預期行為。",
        extra="與 6.2.3 A-MPR 成對。",
        original=(
            "6.5.2.3.1 Test purpose\n"
            "To verify that the power of any UE emission shall not exceed specified level for the specified "
            "channel bandwidth under the deployment scenarios where additional requirements are specified.\n"
            "Additional spectrum emission requirements are signalled by the network to indicate that the UE "
            "shall meet an additional requirement for a specific deployment scenario as part of the cell "
            "handover/broadcast message."
        ),
    ),
    Clause(
        "6.5.2.4.1",
        "6.5 頻譜",
        "NR ACLR",
        1165,
        "鄰近 NR 信道洩漏比。RFA 拆成 Offset L／Offset U，另有參考載波功率。",
        ("6.5.2.4.1 NR ACLR",),
        ("NR Offset L", "NR Offset U", "Reference carrier power"),
        watch="n78／n79 單 band 可達數百點。寬 BW、Edge RB、高階調變先看。V18 拿掉 Power class 1.5 欄（R17 為 31 dB）；現為 PC1 37／PC2 31／PC3 30 dB。",
        extra="規範參考 38.101-1 6.5.2.4.1。",
        original=(
            "6.5.2.4 Adjacent channel leakage ratio\n"
            "Adjacent Channel Leakage power Ratio (ACLR) is the ratio of the filtered mean power centred on "
            "the assigned channel frequency to the filtered mean power centred on an adjacent channel frequency.\n"
            "6.5.2.4.1.1 Test purpose\n"
            "To verify that UE transmitter does not cause unacceptable interference to adjacent channels in "
            "terms of Adjacent Channel Leakage power Ratio (ACLR).\n"
            "NR ACLR is the ratio of the filtered mean power centred on the assigned NR channel frequency to "
            "the filtered mean power centred on an adjacent NR channel frequency at nominal channel spacing. "
            "If the measured adjacent channel power is greater than −50 dBm then the NR ACLR shall be higher "
            "than the specified value (Power class 3: 30 dB)."
        ),
    ),
    Clause(
        "6.5.2.4.2",
        "6.5 頻譜",
        "UTRA ACLR",
        1168,
        "相鄰是 UTRA（3G）時才要求的 ACLR。NS_100 就是「此 NR band 仍有 UTRA 部署」。TDD 或沒有相鄰 UTRA 時常 Skip。",
        ("6.5.2.4.2 UTRA ACLR",),
        ("UTRA OffsetA L", "UTRA OffsetA U", "UTRA OffsetB L", "UTRA OffsetB U"),
        skip="TDD（n41／n78／n79）或 FDD 但測項標不適用時，Skip 多半正確。",
        watch="n1／n2／n3／n5／n8 表列可下 NS_100。",
        extra="規範參考 38.101-1 6.5.2.4.2。",
        original=(
            "6.5.2.4.2.1 Test purpose\n"
            "To verify that UE transmitter does not cause unacceptable interference to adjacent channels in "
            "terms of Adjacent Channel Leakage power Ratio (ACLR).\n"
            "6.5.2.4.2.2 Test applicability\n"
            "This test case applies for network signalling values NS_3U, NS_5U, NS_43U, and NS_100 to all types "
            "of NR Power Class 3 UE release 15 and forward.\n"
            "UTRA ACLR is specified for the first adjacent UTRA channel (UTRAACLR1, ±2.5 MHz from NR channel "
            "edge) and the 2nd adjacent UTRA channel (UTRAACLR2, ±7.5 MHz). NOTE: This NS can be signalled for "
            "NR bands that have UTRA services deployed."
        ),
    ),
    Clause(
        "7.3.2",
        "7 接收",
        "Reference sensitivity power level",
        1458,
        "低電平、理想傳播、不加噪時，指定參考信道的吞吐量仍須 ≥ 95%。RFA 的 N1X2／N1X4 是 1×2／1×4 接收天線組態，不是 n1 頻段。Search 列常有一串 NotSet（掃功率），最後一點才是結果。",
        (
            "7.3.2 Reference sensitivity power level(N1X2)",
            "7.3.2 Reference sensitivity power level(N1X4)",
            "Reference sensitivity Search(N1X2)",
            "Reference sensitivity Search(N1X4)",
        ),
        ("Throughput", "Reference Sensitivity"),
        watch="n7／n41／n77／n78／n79 預設要驗 4Rx（N1X4）；其餘至少 2Rx。量 REFSENS 時 UL 打到 PUMAX。n78 在 3300–3800 MHz 內限值可再嚴 0.5 dB。V18：n79 15 kHz 改為 −95.8+10log10(NRB/52)（R17 為 −89.6+10log10(NRB/216)）；n41／n77／n78 15 kHz 分母 50→52。RedCap 不適用本項。",
        extra="規範參考 38.101-1 7.3.2。",
        original=(
            "7.3.1 General\n"
            "The reference sensitivity power level REFSENS is the minimum mean power applied to each one of "
            "the UE antenna ports for all UE categories, at which the throughput shall meet or exceed the "
            "requirements for the specified reference measurement channel.\n"
            "7.3.2.1 Test purpose\n"
            "The test purpose is to verify the ability of the UE to receive data with a given average throughput "
            "for a specified reference measurement channel, under conditions of low signal level, ideal "
            "propagation and no added noise.\n"
            "The throughput shall be ≥ 95% of the maximum throughput of the reference measurement channels. "
            "The UE shall be verified with two Rx antenna ports in all supported frequency bands; additional "
            "requirements for four Rx ports shall be verified in operating bands where the UE is equipped with "
            "four Rx antenna ports.\n"
            "7.3.2.2 Test applicability\n"
            "This test case applies to all types of NR UE release 15 and forward that don't support RedCap."
        ),
    ),
    Clause(
        "7.4",
        "7 接收",
        "Maximum input level",
        1634,
        "接收機在很高的輸入電平時仍能維持吞吐量，確認前端不會過載。",
        ("7.4 Maximum input level",),
        ("Throughput",),
        extra="規範參考 38.101-1 7.4。",
        original=(
            "7.4 Maximum input level\n"
            "To verify the UE's ability to receive data with a given average throughput for a specified "
            "reference measurement channel, under conditions of high signal level, ideal propagation and no "
            "added noise.\n"
            "The normative reference for this requirement is TS 38.101-1 clause 7.4."
        ),
    ),
]

BY_ID = {c.id: c for c in CLAUSES}
CHAPTERS = []
for c in CLAUSES:
    if not CHAPTERS or CHAPTERS[-1] != c.chapter:
        CHAPTERS.append(c.chapter)


def clauses_in(chapter: str) -> list[Clause]:
    return [c for c in CLAUSES if c.chapter == chapter]


def match_clause(test_name: str) -> Clause | None:
    cid = clause_of(test_name)
    return BY_ID.get(cid)
