"""TS 38.521-1 chapter 6 / 7 index for the 3GPP reference pages.

Core single-carrier SA clauses are written out. A–L letter clauses are
the same measurement on another configuration (CA, MIMO, V2X, …).
Reuse tables and originals from ts38521 / ts38521_tables when present.
"""

from __future__ import annotations

from dataclasses import dataclass

from .ts38521 import BY_ID
from .ts38521_variants import fam_brief as _fam_brief
from .ts38521_variants import fam_orig as _fam_orig
from .ts38521_variants import suffix_rows


@dataclass(frozen=True)
class RefNode:
    id: str
    title: str
    page: int
    brief: str
    original: str = ""
    children: tuple[str, ...] = ()
    kind: str = "clause"
    chapter: str = "6"


SUFFIXES: tuple[tuple[str, str, str], ...] = suffix_rows()

# (id, title, page) for letter families — one card each, not every sub-bullet.
_FAM6 = (
    ("6.2A", "Transmitter power for CA", 331),
    ("6.2B", "Transmitter power for NR-DC", 396),
    ("6.2C", "Transmitter power for SUL", 407),
    ("6.2D", "Transmitter power for UL MIMO", 454),
    ("6.2E", "Transmitter power for V2X", 547),
    ("6.2F", "Transmitter power for shared spectrum", 602),
    ("6.2G", "Transmitter power for Tx Diversity", 620),
    ("6.2H", "Transmitter power for CA with UL MIMO", 676),
    ("6.2I", "Transmitter power for (e)RedCap", 693),
    ("6.2J", "Transmitter power for ATG", 696),
    ("6.2L", "Transmitter power for CA with Tx Diversity", 702),
    ("6.3A", "Output power dynamics for CA", 753),
    ("6.3B", "Output power dynamics for NR-DC", 814),
    ("6.3C", "Output power dynamics for SUL", 814),
    ("6.3D", "Output power dynamics for UL MIMO", 868),
    ("6.3E", "Output power dynamics for V2X", 906),
    ("6.3F", "Output power dynamics for shared spectrum", 923),
    ("6.3G", "Output power dynamics for Tx Diversity", 946),
    ("6.3H", "Output power dynamics for CA with UL MIMO", 962),
    ("6.3J", "Output power dynamics for ATG", 972),
    ("6.3L", "Output power dynamics for CA with Tx Diversity", 993),
    ("6.4A", "Transmit signal quality for CA", 1026),
    ("6.4B", "Transmit signal quality for NR-DC", 1046),
    ("6.4C", "Transmit signal quality for SUL", 1047),
    ("6.4D", "Transmit signal quality for UL MIMO", 1056),
    ("6.4E", "Transmit signal quality for V2X", 1086),
    ("6.4F", "Transmit signal quality for shared spectrum", 1107),
    ("6.4G", "Transmit signal quality for Tx Diversity", 1122),
    ("6.4H", "Transmit signal quality for CA with UL MIMO", 1131),
    ("6.4L", "Transmit signal quality for CA with Tx Diversity", 1146),
    ("6.5A", "Output RF spectrum emissions for CA", 1231),
    ("6.5B", "Output RF spectrum emissions for NR-DC", 1283),
    ("6.5C", "Output RF spectrum emissions for SUL", 1284),
    ("6.5D", "Output RF spectrum emissions for UL MIMO", 1306),
    ("6.5E", "Output RF spectrum emissions for V2X", 1355),
    ("6.5F", "Output RF spectrum emissions for shared spectrum", 1393),
    ("6.5G", "Output RF spectrum emissions for Tx Diversity", 1412),
    ("6.5H", "Output RF spectrum emissions for CA with UL MIMO", 1429),
    ("6.5J", "Output RF spectrum emissions for ATG", 1447),
    ("6.5L", "Output RF spectrum emissions for CA with Tx Diversity", 1452),
)

_FAM7 = (
    ("7.3A", "Reference sensitivity for CA", 1491),
    ("7.3B", "Reference sensitivity for NR-DC", 1578),
    ("7.3C", "Reference sensitivity for SUL", 1579),
    ("7.3D", "Reference sensitivity for UL MIMO", 1597),
    ("7.3E", "Reference sensitivity for V2X", 1601),
    ("7.3F", "Reference sensitivity for shared spectrum", 1604),
    ("7.3G", "Reference sensitivity for Tx Diversity", 1608),
    ("7.3I", "Reference sensitivity for (e)RedCap", 1608),
    ("7.3J", "Reference sensitivity for ATG", 1631),
    ("7.4A", "Maximum input level for CA", 1636),
    ("7.4B", "Maximum input level for NR-DC", 1651),
    ("7.4D", "Maximum input level for UL MIMO", 1651),
    ("7.4F", "Maximum input level for shared spectrum", 1653),
    ("7.4J", "Maximum input level for ATG", 1658),
    ("7.5A", "Adjacent channel selectivity for CA", 1667),
    ("7.5B", "Adjacent channel selectivity for NR-DC", 1702),
    ("7.5D", "Adjacent channel selectivity for UL MIMO", 1702),
    ("7.5F", "Adjacent channel selectivity for shared spectrum", 1705),
    ("7.5J", "Adjacent channel selectivity for ATG", 1708),
    ("7.6A", "Blocking characteristics for CA", 1729),
    ("7.6B", "Blocking characteristics for NR-DC", 1794),
    ("7.6C", "Blocking characteristics for SUL", 1794),
    ("7.6D", "Blocking characteristics for UL MIMO", 1805),
    ("7.6E", "Blocking characteristics for V2X", 1812),
    ("7.6F", "Blocking characteristics for shared spectrum", 1818),
    ("7.6J", "Blocking characteristics for ATG", 1825),
    ("7.7A", "Spurious response for CA", 1838),
    ("7.7B", "Spurious response for NR-DC", 1843),
    ("7.7C", "Spurious response for SUL", 1843),
    ("7.7D", "Spurious response for UL MIMO", 1844),
    ("7.7E", "Spurious response for V2X", 1845),
    ("7.7F", "Spurious response for shared spectrum", 1847),
    ("7.7J", "Spurious response for ATG", 1849),
    ("7.8A", "Intermodulation characteristics for CA", 1855),
    ("7.8B", "Intermodulation characteristics for NR-DC", 1870),
    ("7.8D", "Intermodulation characteristics for UL MIMO", 1871),
    ("7.8E", "Intermodulation characteristics for V2X", 1874),
    ("7.8F", "Intermodulation characteristics for shared spectrum", 1876),
    ("7.8J", "Intermodulation characteristics for ATG", 1879),
    ("7.9A", "Spurious emissions for CA", 1884),
    ("7.9B", "Spurious emissions for NR-DC", 1886),
    ("7.9J", "Spurious emissions for ATG", 1886),
)


NODES: list[RefNode] = [
    RefNode("6", "Transmitter characteristics", 96, "UE 天線接頭上看發射：功率、動態、調變品質、頻譜。限值在 38.101-1 第 6 章，這裡是符合性測法。", kind="chapter", chapter="6", children=("6.0", "6.1", "6.2", "6.3", "6.4", "6.5")),
    RefNode("7", "Receiver characteristics", 1456, "天線接頭上看接收：靈敏度、最大輸入、鄰道選擇、阻擋、雜散響應、互調、接收雜散。限值在 38.101-1 第 7 章。", kind="chapter", chapter="7", children=("7.1", "7.2", "7.3", "7.4", "7.5", "7.6", "7.7", "7.8", "7.9")),
    RefNode(
        "6.0",
        "General test requirements for ΔTIB,c",
        96,
        "帶間 CA 或靠近帶緣時，最大功率容差再加一項 ΔTIB,c。看 6.2.1 數字前先確認這條有沒有加進去。",
        "6.0 General test requirements for ΔTIB,c\n"
        "An additional tolerance ΔTIB,c is applied to the maximum output power "
        "and configured transmitted power when the UE operates with inter-band "
        "CA or near the operating-band edge, as specified in TS 38.101-1 clause 6.2A.",
        kind="section",
        chapter="6",
    ),
    RefNode(
        "6.1",
        "General",
        96,
        "發射特性除非另寫，都在 UE 天線接頭量。後面 6.1A／E／I／J 只是把同一句話改寫到 CA、V2X、RedCap、ATG。",
        "6.1 General\n"
        "Unless otherwise stated, the transmitter characteristics are specified "
        "at the antenna connector of the UE. The test points, environmental "
        "conditions and reference measurement channels are given in TS 38.508-1 "
        "and in the clause-specific test configuration tables.",
        kind="section",
        chapter="6",
    ),
    RefNode(
        "6.2",
        "Transmitter power",
        112,
        "最大功率、允許降多少（MPR／A-MPR）、以及網路下的 PCMAX。RFA 的 NR Power 幾乎都落在這裡。",
        kind="section",
        chapter="6",
        children=("6.2.1", "6.2.2", "6.2.3", "6.2.4"),
    ),
    RefNode("6.2.1", "UE maximum output power", 112, "標稱功率＋容差。PC3 預設 23 dBm；V18 起不少 FDD 也有 PC2 26／部分 TDD 有 PC1 31。過大干擾別人，過小覆蓋不夠。"),
    RefNode("6.2.2", "UE maximum output power reduction", 119, "高階調變或 Edge RB 允許降功率（MPR），好讓 ACLR／SEM 過。規格寫若 6.5.2.4.1 已跑，這項可不另測。"),
    RefNode("6.2.3", "UE additional maximum output power reduction", 149, "網路用 additionalSpectrumEmission（NS_xx）加嚴頻譜時，才准再降（A-MPR）。總降幅通常 max(MPR, A-MPR)。沒有對應 NS 就 Skip。"),
    RefNode("6.2.4", "Configured transmitted power", 323, "量的是 PCMAX（P-Max、MPR、A-MPR、ΔTIB,c 算完的上限），不是再對一次 23 dBm。"),
    RefNode(
        "6.3",
        "Output power dynamics",
        709,
        "能壓多低、關得乾不乾淨、ON／OFF 暫態、以及 TPC 準不準。",
        kind="section",
        chapter="6",
        children=("6.3.1", "6.3.2", "6.3.3", "6.3.4"),
    ),
    RefNode("6.3.1", "Minimum output power", 709, "TPC 往下打到底，通道內寬帶功率要低於表列上限。V18 用公式：≤20 MHz 為 −40 dBm，更寬 −40+10log10(BW/20)。"),
    RefNode("6.3.2", "Transmit OFF power", 711, "不該發的時候通道平均功率 ≤ −50 dBm（再加 TT）。過高抬 RoT。本項由 6.3.3 time mask 覆蓋。"),
    RefNode(
        "6.3.3",
        "Transmit ON/OFF time mask",
        712,
        "OFF↔ON 只准短暫暫態（預設 10 µs；UE 可報 2／4／7 µs）。量錯功率會干擾別人，或讓本機 UL 誤碼上升。",
        "6.3.3 Transmit ON/OFF time mask\n"
        "The transmit power time mask defines the transient period(s) allowed "
        "between transmit OFF power and transmit ON power symbols. When a UE "
        "signals the transient period capability, tp can be 2, 4 or 7 µs. "
        "If no capability is signalled, the default transient period of 10 µs applies.",
        kind="section",
        chapter="6",
        children=("6.3.3.2", "6.3.3.3", "6.3.3.4", "6.3.3.6", "6.3.3.7"),
    ),
    RefNode("6.3.3.2", "General ON/OFF time mask", 713, "一般 PUSCH 的 OFF–暫態–ON–暫態–OFF。OFF 功率同 6.3.2，ON 功率同 6.2.1。"),
    RefNode(
        "6.3.3.3",
        "Transmit power time mask for slot and short or subslot boundaries",
        717,
        "slot／subslot 交界換功率或換 RB 時的暫態。規格自己註：目前測法解析度不夠，最低要求視為不可測。",
        "6.3.3.3\nNo test case details are specified. Current test procedures cannot "
        "provide enough resolution to identify non-conformant UEs. Therefore the "
        "minimum requirement is not testable.",
    ),
    RefNode("6.3.3.4", "PRACH time mask", 717, "發 PRACH 的 OFF→ON→OFF。RFA 名稱後的 −118／−124 是 preambleReceivedTargetPower，不是頻段。"),
    RefNode("6.3.3.6", "SRS time mask", 723, "發 SRS 的 ON／OFF 暫態，概念同 PRACH time mask。"),
    RefNode(
        "6.3.3.7",
        "PUSCH-PUCCH and PUSCH-SRS time masks",
        731,
        "連續兩段不同功率（PUSCH↔PUCCH／SRS）的交界。規格同樣標不可測。",
        "6.3.3.7 PUSCH-PUCCH and PUSCH-SRS time masks\n"
        "No test case details are specified. The minimum requirement is not testable.",
    ),
    RefNode(
        "6.3.4",
        "Power control",
        731,
        "TPC 準不準：第一次能不能打到絕對值、一步相對誤差、一段時間累積誤差。",
        kind="section",
        chapter="6",
        children=("6.3.4.2", "6.3.4.3", "6.3.4.4"),
    ),
    RefNode("6.3.4.2", "Absolute power tolerance", 731, "間隔 >20 ms 後第一個子幀，量到的功率對預期絕對值。常溫 ±9.0 dB（再加 TT）。"),
    RefNode(
        "6.3.4.3",
        "Relative power tolerance",
        734,
        "單一 TPC 步階（±1／±2／±3 dB）的相對誤差。連續傳或短間隔用這一條，不是 6.3.4.2。",
        "6.3.4.3 Relative power tolerance\n"
        "The relative power tolerance is the ability of the UE transmitter to "
        "set its output power relative to the power of the most recently "
        "transmitted sub-frame. The requirement applies for TPC step sizes "
        "of 1, 2 and 3 dB under normal conditions.",
    ),
    RefNode("6.3.4.4", "Aggregate power tolerance", 749, "一串 TPC 之後的累積誤差。RFA 這項點數通常很少。"),
    RefNode(
        "6.4",
        "Transmit signal quality",
        994,
        "載波準不準、星座乾不乾淨、沒分配到的 RB 有沒有漏、等化器夠不夠平。多半用 Annex E 一次算出來。",
        kind="section",
        chapter="6",
        children=("6.4.1", "6.4.2.1", "6.4.2.1a", "6.4.2.2", "6.4.2.3", "6.4.2.4", "6.4.2.5", "6.4.2.6"),
    ),
    RefNode("6.4.1", "Frequency error", 994, "收 SS 取出頻率，再據此發 UL。相對 gNB |Δf| ≤ 0.1 ppm + 15 Hz。在 REFSENS、UL 打到 PUMAX 下量。"),
    RefNode("6.4.2.1", "Error Vector Magnitude", 996, "量測波形對參考波形的誤差向量。QPSK 17.5%、256QAM 3.5%。RFA 拆 PRACH／PUCCH／PUSCH。"),
    RefNode(
        "6.4.2.1a",
        "Error Vector Magnitude including symbols with transient period",
        1003,
        "把暫態符號也算進 EVM。一般 6.4.2.1 是排除暫態的；這一條較嚴，看 PA 開關機乾不乾淨。",
        "6.4.2.1a EVM including symbols with transient period\n"
        "The EVM is evaluated including the symbols that contain an allowed "
        "power transient. The purpose is to verify modulation quality when "
        "the transient period is not excluded from the measurement interval.",
    ),
    RefNode("6.4.2.2", "Carrier leakage", 1007, "載波同頻的固定正弦洩漏。>10 dBm 要 ≤ −28 dBc。txDirectCurrentLocation=3300／3301 時免測。"),
    RefNode("6.4.2.3", "In-band emissions", 1010, "未分配 RB 相對已分配 RB 的功率。RFA 拆 General／IQ Image／Carrier leakage 三個 margin。"),
    RefNode("6.4.2.4", "EVM equalizer spectrum flatness", 1015, "EVM 用的 ZF 等化器係數在分配頻帶內要夠平，否則失真被吃掉、EVM 會看起來過好。"),
    RefNode("6.4.2.5", "EVM equalizer spectrum flatness for Pi/2 BPSK", 1019, "Pi/2-BPSK（含特殊 DMRS）的平坦度，適用 n40／n41／n77／n78／n79 且宣告 powerBoost 的 UE。"),
    RefNode(
        "6.4.2.6",
        "Phase continuity requirements for DMRS bundling",
        1022,
        "DMRS bundling 時，跨 slot 的相位要連得起來，否則 gNB 不能把多個 slot 當同一通道估。",
        "6.4.2.6 Phase continuity requirements for DMRS bundling\n"
        "When DMRS bundling is configured, the UE shall maintain phase "
        "continuity across the bundled slots so that the gNB can jointly "
        "estimate the channel. The requirement is verified from the phase "
        "offset measurement in Annex E.4.9.",
    ),
    RefNode(
        "6.5",
        "Output RF spectrum emissions",
        1149,
        "通道裡佔多寬、通道旁邊漏多少（SEM／ACLR）、更遠的諧波／雜散、以及被干擾時自己產不產互調。",
        kind="section",
        chapter="6",
        children=("6.5.1", "6.5.2.2", "6.5.2.3", "6.5.2.4.1", "6.5.2.4.2", "6.5.3", "6.5.4"),
    ),
    RefNode("6.5.1", "Occupied bandwidth", 1149, "含 99% 發射功率的寬度必須 ≤ 標稱通道頻寬。n77／n78／n79 要量 Low／Mid／High。"),
    RefNode("6.5.2.2", "Spectrum emission mask", 1151, "通道邊到雜散區之間的不想要發射。Edge 1RB、高階調變最容易貼限。"),
    RefNode("6.5.2.3", "Additional spectrum emission mask", 1158, "有 NS 加嚴 mask 才適用。沒有 NS_03／04／06／35 這類 extra mask 時 Skip 是預期行為。"),
    RefNode("6.5.2.4.1", "NR ACLR", 1165, "鄰近 NR 信道洩漏比。PC3 30 dB、PC2 31 dB、PC1（n14）37 dB。鄰信道功率 ≤ −50 dBm 時不比 ACLR。"),
    RefNode("6.5.2.4.2", "UTRA ACLR", 1168, "旁邊還有 3G 時才要。UTRAACLR1 33 dB、ACLR2 36 dB。NS_100 就是「此 NR band 仍有 UTRA」。TDD 常 Skip。"),
    RefNode(
        "6.5.3",
        "Spurious emissions",
        1170,
        "比 SEM 更遠：諧波、寄生、轉換產物。分一般雜散、與其他系統共存、以及 NS 加嚴。OOB／雜散分界 FOOB 隨 BW 變（3 MHz 為 6 MHz）。",
        "6.5.3 Spurious emissions\n"
        "Spurious emissions are caused by unwanted transmitter effects such as "
        "harmonics, parasitic emissions, intermodulation and frequency conversion "
        "products, but exclude out-of-band emissions unless otherwise stated.\n"
        "6.5.3.1.1 Test purpose\n"
        "To verify that UE transmitter does not cause unacceptable interference "
        "to other channels or other systems in terms of transmitter spurious emissions.",
        kind="section",
        chapter="6",
        children=("6.5.3.1", "6.5.3.2", "6.5.3.3"),
    ),
    RefNode(
        "6.5.3.1",
        "General spurious emissions",
        1170,
        "ITU SM.329 那組通用限。從通道邊往外超過 FOOB 之後用這張表，跟有沒有鄰居系統無關。",
        "6.5.3.1 General spurious emissions\n"
        "Unless otherwise stated, the spurious emission limits apply for the "
        "frequency ranges that are more than FOOB from the edge of the channel "
        "bandwidth. The limits apply for all transmit bandwidth configurations.",
    ),
    RefNode(
        "6.5.3.2",
        "Spurious emissions for UE co-existence",
        1173,
        "保護別的經營頻段（鄰 band、衛星、公共安全）。按「自己在哪個 NR band」查表，比 6.5.3.1 嚴。",
        "6.5.3.2 Spurious emissions for UE co-existence\n"
        "These requirements are specified in terms of an additional spectrum "
        "emission requirement to protect other operating bands and systems "
        "that may be deployed in the same geographical area.",
    ),
    RefNode(
        "6.5.3.3",
        "Additional spurious emissions",
        1200,
        "NS 加嚴的雜散（例如保護 GNSS 的 1559–1610 MHz）。沒宣告對應 NS 就不必測。",
        "6.5.3.3 Additional spurious emissions\n"
        "Additional spurious emission requirements are signalled by the network "
        "with an NS value. Example: NS_05 / NS_62 protect GNSS in 1559–1610 MHz.",
    ),
    RefNode(
        "6.5.4",
        "Transmit intermodulation",
        1228,
        "旁邊放一個 CW 干擾，看 UE 自己的非線性會不會生出落在鄰道的互調。這是發射機的 IMD，不是 7.8 接收互調。",
        "6.5.4.1 Test purpose\n"
        "To verify that the UE transmit intermodulation does not exceed the "
        "described value in the test requirement.",
    ),
    RefNode(
        "7.1",
        "General",
        1456,
        "接收特性在每個 UE 天線 port 上看。後面 7.1A／I／J 只是改寫到 CA、RedCap、ATG。",
        "7.1 General\n"
        "The receiver characteristics are specified at each UE antenna port "
        "for all UE categories unless otherwise stated.",
        kind="section",
        chapter="7",
    ),
    RefNode(
        "7.2",
        "Diversity characteristics",
        1457,
        "UE 至少 2Rx。n7／n41／n77／n78／n79 等預設還要驗 4Rx；V18 對 n77／n78 另有 8Rx。ΔRIB,4R／8R 加在 2Rx REFSENS 上（負值＝更嚴）。",
        "7.2 Diversity characteristics\n"
        "The UE shall be verified with two Rx antenna ports in all supported "
        "frequency bands. Additional requirements for four or eight Rx ports "
        "shall be verified in operating bands where the UE is so equipped. "
        "REFSENS for 4Rx / 8Rx = 2Rx value + ΔRIB,4R / ΔRIB,8R.",
        kind="section",
        chapter="7",
    ),
    RefNode(
        "7.3",
        "Reference sensitivity",
        1458,
        "理想傳播、不加噪，吞吐量仍須 ≥95% 的最低 DL 電平。量的時候 UL 打到 PUMAX，所以也在考 TX 雜散有沒有灌回自己的 RX。",
        kind="section",
        chapter="7",
        children=("7.3.2", "7.3.2_1", "7.3.3"),
    ),
    RefNode("7.3.2", "Reference sensitivity power level", 1458, "主表。RFA 的 N1X2／N1X4 是 1×2／1×4 天線組態，不是 n1。V18 排除 RedCap。"),
    RefNode(
        "7.3.2_1",
        "Reference sensitivity power level for XR",
        1489,
        "XR 業務的 REFSENS。通道與吞吐基準跟 7.3.2 不同，一般模組引進不會跑。",
        "7.3.2_1 Reference sensitivity power level for XR\n"
        "Reference sensitivity for XR traffic. The reference measurement "
        "channel and throughput requirement follow the XR configuration; "
        "the wanted-signal definition remains REFSENS as in clause 7.3.1.",
    ),
    RefNode(
        "7.3.3",
        "ΔRIB,c",
        1490,
        "帶間 CA 或自身諧波落進 DL 時，REFSENS 允許再鬆／再嚴的修正量。看 7.3A 之前先查這條。",
        "7.3.3 ΔRIB,c\n"
        "An additional relaxation or tightening of REFSENS applied when the "
        "UE is configured with inter-band CA, or when UL harmonics fall into "
        "the DL band, as specified in TS 38.101-1 clause 7.3A / 7.3.3.",
    ),
    RefNode("7.4", "Maximum input level", 1634, "DL 很強時前端不能過載。64QAM 約 −25 dBm（寬 BW 再放），256／1024QAM 再低 2 dB。吞吐仍要 ≥95%。"),
    RefNode(
        "7.5",
        "Adjacent channel selectivity",
        1661,
        "隔壁信道有強干擾時，自己這信道還能不能收。ACS 是「本信道濾波衰減／鄰信道濾波衰減」。測的是吞吐，不是直接量 ACS 比。",
        "7.5.1 Test purpose\n"
        "Adjacent channel selectivity (ACS) is a measure of a receiver's ability "
        "to receive an NR signal at its assigned channel frequency in the presence "
        "of an adjacent channel signal. ACS is the ratio of the receive filter "
        "attenuation on the assigned channel frequency to the receive filter "
        "attenuation on the adjacent channel(s).",
        kind="section",
        chapter="7",
    ),
    RefNode(
        "7.6",
        "Blocking characteristics",
        1714,
        "干擾不在鄰道、也不在雜散響應點時，RX 還能不能收。拆 in-band（帶內 ±15 MHz 或 3×BW）、OOB、窄帶 CW。",
        kind="section",
        chapter="7",
        children=("7.6.2", "7.6.3", "7.6.4"),
    ),
    RefNode(
        "7.6.2",
        "In-band blocking",
        1714,
        "干擾是另一個 NR 信號，落在接收帶內或帶外第一個 15 MHz（sub-3 GHz）。Wanted = REFSENS + 某 dB，吞吐 ≥95%。",
        "7.6.2.1 Test purpose\n"
        "In-band blocking is defined for an unwanted interfering signal falling "
        "into the range from 15 MHz below to 15 MHz above the UE receive band "
        "(FDL_high < 2700 MHz), or into an immediately adjacent frequency range "
        "up to 3×BWChannel (FDL_low ≥ 3300 MHz).",
    ),
    RefNode(
        "7.6.3",
        "Out-of-band blocking",
        1720,
        "干擾是帶外 CW，分 Range 1／2／3，越遠允許越強。過不了的離散頻率改去走 7.7 雜散響應。",
        "7.6.3 Out-of-band blocking\n"
        "Out-of-band blocking is a measure of the receiver's ability to receive "
        "a wanted signal in the presence of an unwanted CW interferer outside "
        "the operating band, except at frequencies where a spurious response occurs.",
    ),
    RefNode(
        "7.6.4",
        "Narrow band blocking",
        1726,
        "干擾是緊貼通道邊的 CW（不是整個鄰道）。考 SAW／通道濾波的過渡帶，不是 7.5 的調變鄰道。",
        "7.6.4 Narrow band blocking\n"
        "Narrow band blocking verifies the receiver in the presence of a CW "
        "interferer placed close to the wanted-channel edge, inside the first "
        "adjacent channel.",
    ),
    RefNode(
        "7.7",
        "Spurious response",
        1835,
        "7.6.3 過不了的那些離散頻率（混頻鏡頻、諧波）。在那些點把干擾放鬆，吞吐仍要 ≥95%。缺這能力時，遠處一個 CW 就能把覆蓋打掉。",
        "7.7.1 Test Purpose\n"
        "Spurious response is a measure of the ability of the receiver to receive "
        "a wanted signal on its assigned channel frequency without exceeding a "
        "given degradation due to the presence of an unwanted CW interfering "
        "signal at any other frequency for which a response is obtained, i.e. "
        "for which the out-of-band blocking limit as specified in subclause 7.6.3 "
        "is not met.",
        kind="section",
        chapter="7",
    ),
    RefNode(
        "7.8",
        "Intermodulation characteristics",
        1851,
        "兩個干擾（通常一個 CW、一個調變）差頻剛好落到本信道。考 LNA／混頻器線性。主測是 7.8.2 wideband IMD。",
        "7.8 Intermodulation characteristics\n"
        "7.8.1 General\n"
        "Intermodulation response rejection is a measure of the capability of "
        "the receiver to receive a wanted signal on its assigned channel "
        "frequency in the presence of two or more interfering signals which "
        "have a specific frequency relationship to the wanted signal.\n"
        "7.8.2 Wide band Intermodulation\n"
        "The wanted signal throughput shall be ≥ 95% of the maximum throughput "
        "of the reference measurement channel in the presence of the two "
        "interferers specified for wideband intermodulation.",
        kind="section",
        chapter="7",
        children=("7.8.2",),
    ),
    RefNode(
        "7.8.2",
        "Wide band Intermodulation",
        1851,
        "兩個干擾：CW 與調變信號，偏移按 38.101-1 7.8 表。Wanted 略高於 REFSENS，吞吐 ≥95%。",
        "7.8.2 Wide band Intermodulation\n"
        "Two interferers (CW and modulated) are applied at offsets specified "
        "in TS 38.101-1 clause 7.8. The wanted-signal throughput shall be "
        "≥ 95% of the maximum throughput of the reference measurement channel.",
    ),
    RefNode(
        "7.9",
        "Spurious emissions",
        1882,
        "接收機從天線接頭洩出去的雜散（本振洩漏、諧波）。跟 6.5.3 發射雜散分開量，通常 RX 開、TX 關或降功率。",
        "7.9 Spurious emissions\n"
        "The spurious emissions power is the power of emissions generated or "
        "amplified in a receiver that appear at the UE antenna connector. "
        "The power of any spurious emission shall not exceed the levels "
        "specified in TS 38.101-1 clause 7.9.",
        kind="section",
        chapter="7",
    ),
]

for _fid, _title, _page in _FAM6:
    NODES.append(
        RefNode(_fid, _title, _page, _fam_brief(_fid), _fam_orig(_fid, _title), kind="family", chapter="6")
    )
for _fid, _title, _page in _FAM7:
    NODES.append(
        RefNode(_fid, _title, _page, _fam_brief(_fid), _fam_orig(_fid, _title), kind="family", chapter="7")
    )

BY_REF = {n.id: n for n in NODES}

SECTION_FAMILIES: dict[str, tuple[str, ...]] = {
    "6.2": tuple(i for i, _, _ in _FAM6 if i.startswith("6.2")),
    "6.3": tuple(i for i, _, _ in _FAM6 if i.startswith("6.3")),
    "6.4": tuple(i for i, _, _ in _FAM6 if i.startswith("6.4")),
    "6.5": tuple(i for i, _, _ in _FAM6 if i.startswith("6.5")),
    "7.3": tuple(i for i, _, _ in _FAM7 if i.startswith("7.3")),
    "7.4": tuple(i for i, _, _ in _FAM7 if i.startswith("7.4")),
    "7.5": tuple(i for i, _, _ in _FAM7 if i.startswith("7.5")),
    "7.6": tuple(i for i, _, _ in _FAM7 if i.startswith("7.6")),
    "7.7": tuple(i for i, _, _ in _FAM7 if i.startswith("7.7")),
    "7.8": tuple(i for i, _, _ in _FAM7 if i.startswith("7.8")),
    "7.9": tuple(i for i, _, _ in _FAM7 if i.startswith("7.9")),
}

CH6_SECTIONS = ("6.0", "6.1", "6.2", "6.3", "6.4", "6.5")
CH7_SECTIONS = ("7.1", "7.2", "7.3", "7.4", "7.5", "7.6", "7.7", "7.8", "7.9")


def original_of(node: RefNode) -> str:
    if node.original:
        return node.original
    clause = BY_ID.get(node.id)
    return clause.original if clause else ""


def has_rfa(node_id: str) -> bool:
    return node_id in BY_ID
