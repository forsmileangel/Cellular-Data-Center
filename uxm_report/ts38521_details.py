"""Longer RF descriptions for /ref and /spec.

Used when 38.521-1 has no figure, and also under every core clause
so a page is never just a one-line brief + empty figure slot.
"""

from __future__ import annotations

from .ts38521_variants import fam_detail, _letter_of

# 38.521-1 chapter 7 has zero Figure captions (verified on V18.5.0).
CH7_NO_FIGURE = (
    "TS 38.521-1 第 7 章整章沒有 Figure。接收干擾怎麼擺、wanted 電平多少，"
    "全部寫在表裡，不是畫成方塊圖。限值本體在 38.101-1 第 7 章。"
)

CH6_POWER_NO_FIGURE = (
    "TS 38.521-1 這一條用表格規定標稱功率／容差／允許降幅，沒有 Figure。"
    "功率是一個數，不是頻域或時域波形。"
)


DETAILS: dict[str, str] = {
    "6.0": (
        "帶間 CA 或工作在帶緣附近時，6.2.1／6.2.4 的容差還要再加 ΔTIB,c。"
        "看最大功率數字前先確認這條有沒有加進去，否則會把本來允許的降幅當成 Fail。"
        "這一條沒有獨立限值表，數字在 38.101-1 6.2A。"
    ),
    "6.1": (
        "除非另寫，發射特性都在 UE 天線接頭量，不是 OTA。"
        "測點、環境、參考信道在 38.508-1 與各條的 Test configuration。"
        "6.1A／E／I／J 只是把同一句話改寫到 CA、V2X、RedCap、ATG，沒有另開一張功率表。"
    ),
    "6.2": (
        "發射功率三件事：能發多滿（6.2.1）、規格准你降多少（6.2.2 MPR、6.2.3 A-MPR）、"
        "網路把上限設完之後還在不在容差裡（6.2.4 PCMAX）。"
        "RFA 的 NR Power 幾乎都落在這裡。38.521-1 沒有功率波形圖，只有表。"
    ),
    "6.2.1": (
        "量天線接頭上的最大輸出功率，對照 Power Class 標稱值與容差。"
        "PC3 預設 23 dBm；V18 起不少 FDD 也有 PC2 26 dBm，部分 TDD／FDD 有 PC1 31 dBm。"
        "過大干擾鄰道與其他系統，過小覆蓋不夠。"
        "帶緣 4 MHz 內下限可再鬆 1.5 dB（NOTE 3）；n91–n94／n109 另有 NOTE 4 再鬆 0.3 dB。"
        "測的時候 UL 打到 PUMAX。沒有 Figure，限值就是下面的 Power Class 表。"
    ),
    "6.2.2": (
        "高階調變或 Edge RB 時，PA 要後退才能過 ACLR／SEM，所以規格允許 MPR。"
        "RFA 若已跑 6.5.2.4.1 NR ACLR，這項可不另測。"
        "看的是「准你降多少」，不是再對一次 23 dBm。"
        "沒有 Figure。PC2／PC1／n14 各有自己的 MPR 表。"
    ),
    "6.2.3": (
        "網路用 additionalSpectrumEmission（NS_xx）加嚴頻譜時，才准再降 A-MPR。"
        "總降幅通常是 max(MPR, A-MPR)，不是兩者相加。"
        "沒有對應 NS 就 Skip，這是預期行為。"
        "A-MPR 細表按 NS×band×RB 展開占上百頁，這裡只留你們會對到的 NS 一覽。"
        "沒有 Figure。"
    ),
    "6.2.4": (
        "量的是 PCMAX：P-Max、MPR、A-MPR、ΔTIB,c、ΔTC 算完之後的上下界，"
        "不是再對一次 23 dBm。"
        "要滿足 PCMAX_L ≤ 量到的 PUMAX ≤ PCMAX_H。"
        "PC2 被 P-Max=23 拉回 PC3 時 ΔP_PowerClass = 3 dB。"
        "沒有 Figure，公式在下面那張表。"
    ),
    "6.3": (
        "功率動態：能壓多低（6.3.1）、關得乾不乾淨（6.3.2）、"
        "OFF↔ON 只准短暫暫態（6.3.3）、TPC 準不準（6.3.4）。"
        "Time mask 與 TPC 圖是 38.521-1 少數有畫出來的地方。"
    ),
    "6.3.1": (
        "TPC 往下打到底，通道內寬帶功率要低於表列上限。"
        "V18：≤20 MHz 為 −40 dBm；更寬為 −40 + 10log10(BW/20) dBm。"
        "過高表示關不乾淨或偏置電流太大。沒有 Figure。"
    ),
    "6.3.2": (
        "不該發的時候（DTX、gap、OFF），通道平均功率 ≤ −50 dBm（再加 TT）。"
        "過高會抬鄰近細胞的 RoT。"
        "本項由 6.3.3 time mask 的 OFF 區間覆蓋，常不另跑。"
        "沒有獨立 Figure，看 6.3.3 的 ON/OFF 圖即可。"
    ),
    "6.3.3": (
        "OFF 與 ON 之間只准一段暫態 tp。"
        "沒宣告能力時預設 10 µs；UE 可報 2／4／7 µs，暫態起點 tp_start 見下表。"
        "OFF 功率同 6.3.2，ON 功率同 6.2.1。"
        "量錯功率會干擾別人，或讓本機 UL 誤碼上升。"
        "6.3.3.3 與 6.3.3.7 規格自己標不可測。"
    ),
    "6.3.3.2": (
        "一般 PUSCH：OFF → 暫態 → ON（至少一 slot，不含暫態）→ 暫態 → OFF。"
        "DTX 與 measurement gap 的 OFF 要求不適用。"
        "下圖是 V18 PDF Figure 6.3.3.2.3-1 原頁裁出。"
    ),
    "6.3.3.3": (
        "slot／subslot 交界換功率或換 RB 時的暫態。"
        "規格寫：目前測法解析度不夠，最低要求視為不可測，沒有 Test case details。"
        "因此沒有表、也沒有可執行的 RFA 項。"
    ),
    "6.3.3.4": (
        "PRACH preamble 的 OFF→ON→OFF。概念同一般 time mask，但 ON 區間是 preamble 長度，不是 PUSCH slot。"
        "RFA 名稱後的 −118／−124 是 preambleReceivedTargetPower，不是頻段。"
        "量測時間隨 preamble format 與 SCS 變，表在 PDF 印刷頁 718。"
        "下圖是 V18 PDF Figure 6.3.3.4.3-1（含其上方量測時間表）。"
    ),
    "6.3.3.6": (
        "SRS 的 ON／OFF 暫態。單次 SRS 與連續多個 SRS（功率不變／要變／中間 blank）各有一張 mask。"
        "天線切換的連續 SRS 另有 15／30 kHz 的特殊圖。"
        "下面五張都是 V18 PDF 原圖。"
    ),
    "6.3.3.7": (
        "PUSCH↔PUCCH 或 PUSCH↔SRS 交界、兩段功率不同。"
        "規格同樣標不可測，沒有 Test case details。"
    ),
    "6.3.4": (
        "TPC 三層：隔比較久後第一次打不打得到絕對值（6.3.4.2）、"
        "一步相對誤差（6.3.4.3）、一串 0 dB 之後還穩不穩（6.3.4.4）。"
        "相對誤差那條有 FDD／TDD 爬升、下降、交替的測試功率圖。"
    ),
    "6.3.4.2": (
        "間隔 >20 ms 後第一個子幀，量到的功率對預期絕對值。"
        "常溫 ±9.0 dB（再加 TT）。這是開環／第一次對準，不是一步 ±1 dB。"
        "沒有 Figure。"
    ),
    "6.3.4.3": (
        "相對最近一次傳的功率步階誤差。間隔 ≤20 ms 才用這一條。"
        "步階越大容差越鬆；含 SRS 轉接再鬆一檔；PA 模式切換可到 ±6.0 dB。"
        "頻率固定、沒有 gap 的 PUSCH↔PUCCH，ΔP≤1 dB 時收到 ±0.7 dB。"
        "下面是 V18 的 FDD／TDD 爬升、下降與交替測試圖。"
    ),
    "6.3.4.4": (
        "21 ms 內非連續傳、TPC 都是 0 dB，功率還能不能維持。"
        "相對第一次：PUCCH ±2.5 dB、PUSCH ±3.5 dB；測試要求再加 TT=0.7 dB。"
        "量五次，第 2 次以後都要落在第一次附近。"
        "下圖是測試用的 UL 傳送圖案，不是限值本身。"
    ),
    "6.4": (
        "發射訊號品質：載波準不準（6.4.1）、星座乾不乾淨（EVM）、"
        "沒分配到的 RB 有沒有漏（IBE）、等化器夠不夠平。"
        "多半用 Annex E 一次算出來。有 Figure 的是暫態 EVM 與平坦度。"
    ),
    "6.4.1": (
        "收 SS 取出頻率，再據此發 UL。相對 gNB |Δf| ≤ 0.1 ppm + 15 Hz。"
        "在 REFSENS、UL 打到 PUMAX 下量。"
        "偏了會讓 gNB 解不開，也會讓自己的 ACLR 看起來變差。"
        "沒有 Figure，限值是一個數字。"
    ),
    "6.4.2.1": (
        "量測波形對理想參考波形的誤差向量 RMS。"
        "QPSK 17.5%、16QAM 12.5%、64QAM 8%、256QAM 3.5%。"
        "RFA 拆 PRACH／PUCCH／PUSCH。一般 6.4.2.1 排除暫態符號。"
        "沒有 Figure，限值在表裡。"
    ),
    "6.4.2.1a": (
        "把允許暫態那段符號也算進 EVM，比 6.4.2.1 嚴。"
        "看 PA 開關機與 slot 交界乾不乾淨。"
        "下面兩張是 V18 原圖：暫態落在哪、以及測的時候 RB 怎麼擺。"
    ),
    "6.4.2.2": (
        "載波同頻的固定正弦洩漏（LO leakage）。"
        "P>10 dBm 要 ≤ −28 dBc，功率愈低容差愈鬆。"
        "txDirectCurrentLocation=3300／3301 時免測。"
        "沒有 Figure。"
    ),
    "6.4.2.3": (
        "未分配 RB 相對已分配 RB 的功率。拆 General、IQ Image、Carrier leakage 三個成分。"
        "每個空 RB 取「P̄RB−30 dB」與各成分功率和的較嚴者。"
        "測試要求再加 TT=0.8 dB。"
        "沒有 Figure，限值是公式＋三個成分。"
    ),
    "6.4.2.4": (
        "EVM 用的 ZF 等化器係數在分配頻帶內要夠平。"
        "若等化器把失真吃掉，EVM 會看起來過好、實際空中介面卻不好。"
        "Range 1（離帶緣 ≥3／5 MHz）4 dB p-p；Range 2 常溫 8、極端溫度 12。"
        "跨區還有 max(R2)−min(R1)、max(R1)−min(R2) 兩條。"
        "下圖是 V18 PDF 原圖。"
    ),
    "6.4.2.5": (
        "Pi/2-BPSK（含特殊 DMRS）的平坦度。"
        "適用 n40／n41／n77／n78／n79 且宣告 powerBoosting-pi2BPSK，"
        "或 Rel-16 lowPAPR DMRS。"
        "分區改以分配區塊中心 F_center 與 X=25% 分配頻寬來切，不是帶緣 3 MHz。"
        "測試要求 Range 1 為 6+TT、Range 2 為 14+TT（TT=1.4 dB）。"
        "下圖是 V18 原圖。"
    ),
    "6.4.2.6": (
        "DMRS bundling 時跨 slot 相位要連得起來，gNB 才能把多個 slot 當同一通道估。"
        "從 Annex E.4.9 的相位差驗證。V18 仍標 MU／TT 分析未完。"
        "沒有 Figure。"
    ),
    "6.5": (
        "發射頻譜四段：通道裡佔多寬（OBW）、通道旁邊（SEM／ACLR）、"
        "更遠的雜散、以及被 CW 灌進去時自己產不產互調。"
        "分界是 FOOB：3 MHz 通道為 6 MHz，其餘 BW+5 MHz。"
        "下圖 Figure 6.5.0-1 是 V18 原圖。"
    ),
    "6.5.1": (
        "含 99% 發射功率的寬度必須 ≤ 標稱通道頻寬。"
        "n77／n78／n79 要量 Low／Mid／High。"
        "過寬通常是 SEM／ACLR 也會一起貼限。沒有獨立 Figure，看 6.5.0-1 通道那一段。"
    ),
    "6.5.2.2": (
        "通道邊到雜散區之間的不想要發射（SEM）。"
        "Edge 1RB、高階調變最容易貼限。"
        "限值按離通道邊的偏移分區，單位多半是 dBm/測量頻寬。"
        "沒有獨立 SEM 原圖，區域關係看 6.5.0-1。"
    ),
    "6.5.2.3": (
        "有 NS 加嚴 mask 才適用（例如 NS_03／04／06／35）。"
        "沒有對應 extra mask 時 Skip 是預期行為。"
        "細表按 NS 展開，這裡只留對照。沒有獨立 Figure。"
    ),
    "6.5.2.4.1": (
        "鄰近 NR 信道洩漏比。PC3 30 dB、PC2 31 dB、PC1（n14）37 dB。"
        "鄰信道功率 ≤ −50 dBm 時不比 ACLR。"
        "沒有 Figure，限值是一個比。"
    ),
    "6.5.2.4.2": (
        "旁邊還有 3G 時才要。UTRAACLR1 33 dB、ACLR2 36 dB。"
        "NS_100 就是「此 NR band 仍有 UTRA」。TDD 常 Skip。"
        "沒有 Figure。"
    ),
    "6.5.3": (
        "比 SEM 更遠：諧波、寄生、轉換產物。排除 OOB，除非另寫。"
        "分一般雜散、與其他系統共存、以及 NS 加嚴。"
        "OOB／雜散分界就是 FOOB。6.5.3.2 共存表按「自己在哪個 NR band、保護誰」逐列，整本很長。"
    ),
    "6.5.3.1": (
        "ITU SM.329 那組通用限。離通道邊超過 FOOB 之後用這張表，跟有沒有鄰居系統無關。"
        "9 kHz–1 GHz 多半 −36 dBm，1 GHz 以上 −30 dBm／1 MHz。"
        "沒有獨立 Figure。"
    ),
    "6.5.3.2": (
        "保護別的經營頻段（鄰 band、衛星、公共安全）。"
        "按自己的 NR band 查表，通常比 6.5.3.1 嚴（例如 n1 保護其他 E-UTRA／NR 常見 −50 dBm/1 MHz）。"
        "整表太長，不整本搬；要哪一列再指定。"
        "沒有 Figure。"
    ),
    "6.5.3.3": (
        "NS 加嚴的雜散。典型：NS_05／NS_62 保護 GNSS 1559–1610 MHz。"
        "沒宣告對應 NS 就不必測。沒有 Figure。"
    ),
    "6.5.4": (
        "旁邊放一個 −40 dBc 的 CW，看 UE 自己的非線性會不會生出落在 ±BW／±2×BW 的互調。"
        "±BW 產物 < −29 dBc，±2×BW 產物 < −35 dBc。"
        "這是發射機 IMD，不是 7.8 接收互調。"
        "干擾跟 DL 重疊時這條不適用。沒有 Figure。"
    ),
    "7.1": (
        "接收特性在每個 UE 天線 port 上看。"
        "7.1A／I／J 只是改寫到 CA、RedCap、ATG。"
        + CH7_NO_FIGURE
    ),
    "7.2": (
        "UE 至少 2Rx。n7／n41／n77／n78／n79 等預設還要驗 4Rx；V18 對 n77／n78 另有 8Rx。"
        "4Rx／8Rx 的 REFSENS = 2Rx 表值 + ΔRIB,4R／8R（負值＝更嚴、靈敏度更好）。"
        + CH7_NO_FIGURE
    ),
    "7.3": (
        "理想傳播、不加干擾，吞吐量仍須 ≥95% 的最低 DL 電平。"
        "量的時候 UL 打到 PUMAX，所以也在考 TX 雜散有沒有灌回自己的 RX。"
        "主表是 7.3.2。N1X2／N1X4 是 1×2／1×4 天線，不是 n1。"
        + CH7_NO_FIGURE
    ),
    "7.3.2": (
        "REFSENS 主表，按 band × SCS × 通道頻寬。"
        "FDD 與 TDD 分開；PC2 另有劣化表；4Rx／8Rx 用 ΔRIB。"
        "V18 排除 RedCap（RedCap 走 7.3I）。"
        "RFA 的 Reference sensitivity Search 也對這一條。"
        + CH7_NO_FIGURE
    ),
    "7.3.2_1": (
        "XR 業務的 REFSENS。參考信道與吞吐基準跟 7.3.2 不同，一般模組引進不會跑。"
        + CH7_NO_FIGURE
    ),
    "7.3.3": (
        "帶間 CA 或自身 UL 諧波落進 DL 時，REFSENS 允許再鬆／再嚴的修正量 ΔRIB,c。"
        "看 7.3A 之前先查這條。數字在 38.101-1 7.3A／7.3.3。"
        + CH7_NO_FIGURE
    ),
    "7.4": (
        "DL 很強時前端不能過載。64QAM 約 −25 dBm（寬 BW 再放寬），256／1024QAM 再低 2 dB。"
        "吞吐仍要 ≥95%。UL 設為 PCMAX,L 再低 4 dB。"
        + CH7_NO_FIGURE
    ),
    "7.5": (
        "隔壁信道有強調變干擾時，自己這信道還能不能收。"
        "ACS 定義是「本信道濾波衰減／鄰信道濾波衰減」，但符合性測的是吞吐，不是直接量這個比。"
        "Wanted = REFSENS+14 dB；干擾最大看到 −25 dBm。"
        "sub-3 GHz：3／5／10 MHz 為 33 dB，15 MHz 30 dB，更寬用 27−10log10(BW/20)。"
        "n77／n78／n79：33 dB。"
        + CH7_NO_FIGURE
        + "下面那張方塊圖是依表畫的示意，不是 PDF 原圖。"
    ),
    "7.6": (
        "干擾不在鄰道、也不在雜散響應點時，RX 還能不能收。"
        "拆 in-band（帶內＋兩邊 15 MHz 或 3×BW，干擾是 NR 信號）、"
        "OOB（帶外 CW，Range 1／2／3 愈遠愈強）、窄帶 CW（貼通道邊）。"
        + CH7_NO_FIGURE
        + "示意依表畫，不是原圖。"
    ),
    "7.6.2": (
        "干擾是另一個 NR 信號。"
        "sub-3 GHz：Case 1 貼通道邊 −56 dBm，Case 2 接收帶 ±15 MHz −44 dBm。"
        "Wanted 約 REFSENS+6～+9 dB，隨 BW 變。"
        "n77／n78／n79 改用另一張表：干擾範圍到 3×BW 外，Pw=REFSENS+6。"
        "UL 設為 PCMAX 再低 4 dB。"
        + CH7_NO_FIGURE
    ),
    "7.6.3": (
        "干擾是帶外 CW。Range 1 −44 dBm（離帶 15–60 MHz）、"
        "Range 2 −30（60–85 MHz）、Range 3 −15（再往外；>6 GHz 改 −20）。"
        "n77／n78 Range 從 3×BW 起算。"
        "過不了的離散頻率改走 7.7 雜散響應，不要當成整條 OOB Fail。"
        + CH7_NO_FIGURE
    ),
    "7.6.4": (
        "干擾是緊貼通道邊、落在第一鄰道裡面的 CW，不是整條鄰道、也不是帶外很遠的 CW。"
        "考 SAW／通道濾波的過渡帶。"
        "Wanted = REFSENS 再加表列 dB，吞吐 ≥95%。"
        + CH7_NO_FIGURE
    ),
    "7.7": (
        "7.6.3 過不了的那些離散頻率（混頻鏡頻、諧波）。"
        "在那些點把干擾放在大約 −44 dBm，吞吐仍要 ≥95%。"
        "缺這能力時，遠處一個 CW 就能把覆蓋打掉。"
        + CH7_NO_FIGURE
    ),
    "7.8": (
        "兩個干擾（一個 CW、一個調變）差頻剛好落到本信道。"
        "考 LNA／混頻器三階互調。主測是 7.8.2。"
        "這是接收互調；發射被 CW 灌進去產 IMD 是 6.5.4。"
        + CH7_NO_FIGURE
        + "示意依表畫，不是原圖。"
    ),
    "7.8.2": (
        "兩個干擾都約 −46 dBm。偏移約 ±(BW/2+7.5) MHz 與 2 倍該值。"
        "Wanted 略高於 REFSENS（sub-3 GHz 約 +6～+9 dB）。"
        "n77／n78／n79：Pw=REFSENS+6。"
        + CH7_NO_FIGURE
    ),
    "7.9": (
        "接收機從天線接頭洩出去的雜散（本振洩漏、諧波）。"
        "30 MHz–1 GHz：−57 dBm／100 kHz；1 GHz 以上 −47 dBm／1 MHz。"
        "跟 6.5.3 發射雜散分開量，通常 RX 開、TX 關或降功率。"
        + CH7_NO_FIGURE
    ),
}


def detail_of(clause_id: str) -> str:
    if clause_id in DETAILS:
        return DETAILS[clause_id]
    if _letter_of(clause_id):
        return fam_detail(clause_id)
    if clause_id[:1] == "7":
        return CH7_NO_FIGURE
    return ""
