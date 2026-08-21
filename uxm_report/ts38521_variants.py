"""A–L configuration families in TS 38.521-1 chapters 6 / 7.

These are not one-line aliases of the parent clause. Each letter changes
the reference point, how power is summed, which table applies, or whether
the parent test is even applicable.
"""

from __future__ import annotations

# letter -> (short name, one-line for the suffix table, longer RF note)
LETTERS: dict[str, tuple[str, str, str]] = {
    "A": (
        "CA",
        "載波聚合。量的不是單顆 CC 再抄一次本體，而是連續／非連續／帶間怎麼加總。",
        "CA 先分三種：帶內連續（兩顆 CC 貼在一起）、帶內非連續（中間有洞）、帶間（兩個 NR band）。"
        "雙 UL 且各 band 獨立天線接頭時，最大功率是兩個接頭相加，不是只看比較大的那顆。"
        "帶間常要加 ΔTIB,c（6.0）或 ΔRIB,c（7.3.3）。"
        "ACS／blocking 的干擾是對「聚合後的 DL」擺，不是對單一 PCC。",
    ),
    "B": (
        "NR-DC",
        "NR dual connectivity。MCG 與 SCG 兩組 NR 同時連，功率與雜散要一起看。",
        "NR-DC 是兩組 NR 細胞（主／副）同時連。射頻上很像帶間 CA：兩邊都在發、都在收。"
        "功率共用、雙 UL 雜散、以及哪一邊算 PCell 都會改測試組態。"
        "很多條會寫「同 6.2A／7.3A，但 DC 組合另表」，不要直接拿單載波數字套上去。",
    ),
    "C": (
        "SUL",
        "Supplementary uplink。DL 在一個 band，UL 改走較低頻的補 UL。",
        "SUL 的發射在補 UL band（常見 n80／n81／n82／n83／n84／n86），DL 仍在原 band。"
        "量 TX 時參考點是 SUL 接頭。6.3C 有 SUL↔一般 UL 的切換 time mask，不是一般 PUSCH ON/OFF。"
        "接收條款若標 7.xC，多半是「DL 在原 band、UL 在 SUL」時的靈敏度／阻擋例外。",
    ),
    "D": (
        "UL MIMO",
        "上行多天線。功率、EVM、ACLR 變成每 port 或兩 port 合成，本體常對「不支援 UL MIMO」才適用。",
        "UL MIMO 預設兩支 TX、閉環空間多工。最大功率表是「兩 port 一起」的，另有 ULFPTx（兩支都打滿）。"
        "V18 註：找不到 MPR=0 的 2-layer 測點時，改在 6.2D.2 用最小 MPR 覆蓋。"
        "PCMAX 測點常是 0／14／18 dBm 三檔，不是再對一次 23 dBm。"
        "本體 6.2／6.3／6.4 很多條寫「不支援 Tx diversity／UL MIMO 才適用」，支援的 UE 要走 D。",
    ),
    "E": (
        "V2X",
        "側鏈。測 PSSCH／PSCCH，不是 Uu 的 PUSCH。n47 有自己的 Power Class。",
        "V2X 走 PC5 側鏈，波形是 PSSCH／PSCCH，不是 Uu PUSCH。"
        "可「只發側鏈」或「側鏈與 NR UL 同時」。同時發時功率與雜散要兩條路一起看。"
        "n47 預設 PC3 23 dBm，也可 PC2 26 dBm。time mask 有 PSCCH/PSSCH 與 Uu↔SL 切換圖。"
        "接收條款 7.xE 是側鏈收，不是 Uu REFSENS 那張表。",
    ),
    "F": (
        "共享頻譜",
        "NR-U。n46／n96 預設 Power Class 5、20 dBm，要先聽再發。",
        "共享頻譜（NR-U／LAA）在 n46、n96。預設是 Power Class 5、20 dBm，不是 PC3 23 dBm。"
        "要 channel access／LBT，SEM、ACLR、雜散另有 NS。"
        "V18 的 6.2F.1 仍標不完整：沒有 MPR=0 的測點，改在 6.2F.2 用 1.5 dB MPR 覆蓋。"
        "REFSENS／4Rx 也有 n46／n96 專表，不要套 sub-3 GHz FDD 那張。",
    ),
    "G": (
        "Tx Diversity",
        "兩支 TX 分集。本體多數條款對「不支援 Tx Div」才適用，支援的走這一條。",
        "Tx diversity 是兩支 TX 輪流或同時發同一份資料，不是 UL MIMO 的兩層資料。"
        "本體 6.2／6.3／6.4 的適用條件常常寫「Power Class 2／3 且不支援 Tx diversity」。"
        "支援的 UE 不能拿本體那條當完成，要改走 6.xG／7.3G。"
        "限值多半仍對照 38.101-1 的 diversity 表，測組態改成兩 port。",
    ),
    "H": (
        "CA + UL MIMO",
        "一顆 CC 走 UL MIMO，另一顆走單 port。兩邊的表不能混用。",
        "CA 加上行 MIMO：支援 MIMO 的那顆 CC 走 6.2D／6.4D，另一顆走本體 6.2／6.4。"
        "6.2H 明文：部分測試「被 6.2.4 與 6.2D.4 覆蓋」，不是再出一張全新的 PCMAX 表。"
        "看結果時先分清哪一顆 CC 是 MIMO port。",
    ),
    "I": (
        "(e)RedCap",
        "能力縮減 UE。功率多半沿用 PC3，但頻寬、天線、REFSENS 表與本體不同。",
        "RedCap／eRedCap（Rel-17 起）頻寬與天線數較少。"
        "6.2I：最大功率沿用 6.2.1 的 Power Class 3，但通道頻寬改 38.508-1 的 RedCap 列。"
        "7.3.2 本體排除 RedCap，靈敏度要看 7.3I，不要拿 N1X2 那張主表硬套。"
        "一般模組引進若不是 RedCap SKU，這些條會 Skip。",
    ),
    "J": (
        "ATG",
        "空對地。參考點常是 TAB（陣列邊界），不是手機那種天線接頭。",
        "ATG 是機載 UE 對地面站。天線是陣列，限值常改到 TAB，不是手持裝置的 antenna connector。"
        "功率、雜散、REFSENS 都有 ATG 專表或註，數字不能直接抄 6.2.1／7.3.2。"
        "6.5J 連頻譜分區圖都重畫過（Figure 6.5J.0-1）。",
    ),
    "L": (
        "CA + Tx Div",
        "聚合再加發射分集。CA 怎麼加總、Tx Div 怎麼分 port，兩件事都要成立。",
        "CA + Tx diversity：聚合的加總規則同 A，port 數同 G。"
        "適用條件通常是「支援 CA 且支援 Tx Div」；只支援其中一個不要走 L。"
        "沒有另給的表就分別對回 6.xA 與 6.xG。",
    ),
}

# What this chapter is measuring (the parent 6.2 / 7.3 …).
PARENTS: dict[str, str] = {
    "6.2": "發射功率：最大功率、MPR、A-MPR、PCMAX。",
    "6.3": "功率動態：最小功率、OFF、ON/OFF time mask、TPC。",
    "6.4": "發射品質：頻偏、EVM、載波洩漏、IBE、等化器平坦度。",
    "6.5": "發射頻譜：OBW、SEM、ACLR、雜散、發射互調。",
    "7.3": "參考靈敏度 REFSENS（吞吐 ≥95% 的最低 DL）。",
    "7.4": "最大輸入電平（前端不過載）。",
    "7.5": "鄰道選擇 ACS（鄰道有調變干擾時還能不能收）。",
    "7.6": "阻擋：in-band、OOB、窄帶 CW。",
    "7.7": "雜散響應（OOB 過不了的離散頻率）。",
    "7.8": "接收互調（兩個干擾差頻落到本信道）。",
    "7.9": "接收機從天線接頭洩出去的雜散。",
}

# (parent, letter) -> what actually changes versus the parent clause.
SPECIFICS: dict[tuple[str, str], str] = {
    ("6.2", "A"): (
        "帶間雙 UL：分接頭就各量再相加，量測至少 1 ms。有 CA 組合專用 Power Class 表（例如 CA_n1A-n3A），"
        "不是把 6.2.1 的 n1 與 n3 各看一次。"
        "帶內連續／非連續另有子條。ΔTIB,c（6.0）常在這裡出現。"
    ),
    ("6.2", "B"): (
        "NR-DC 兩組 UL 的功率要一起看，精神接近帶間 CA。"
        "組合列在 38.101-1 6.2B，不要用單一 band 的 23 dBm 當總功率上限。"
    ),
    ("6.2", "C"): (
        "量的是 SUL band 上的 TX。Power Class 跟 SUL 作業頻段走，不是 DL band 的 6.2.1。"
        "P-Max／PCMAX 也是對 SUL 那顆載波設。"
    ),
    ("6.2", "D"): (
        "兩 TX 接頭、閉環空間多工。表 6.2D.1.3-1 是合成功率。"
        "適用 ULFPTx 的 PC1.5 FWA／PC2／PC3（Rel-16 起）。"
        "找不到 MPR=0 的 2-layer 測點時，改測 6.2D.2。"
        "PCMAX 常見 0／14／18 dBm 三個測試點，容差另加 TT。"
    ),
    ("6.2", "E"): (
        "側鏈最大功率：n47 為 PC3 23±2 dBm，也可 PC2 26 +2/−3 dBm。"
        "與 NR UL 同時發時，兩條發射的功率與共存要一起看，不是只對 Uu 那張 6.2.1。"
    ),
    ("6.2", "F"): (
        "n46／n96 預設 Power Class 5、20 dBm（+2/−3）。"
        "6.2F.1 在 V18 仍標不完整，實測多半走 6.2F.2 的 1.5 dB MPR。"
    ),
    ("6.2", "G"): (
        "支援 Tx Div 的 UE 走這裡。本體 6.2.1 對 PC2／PC3「不支援 Tx Div」才適用，"
        "不要兩邊都報 Pass。"
    ),
    ("6.2", "H"): (
        "MIMO 那顆 CC 對 6.2D，另一顆對 6.2.4／6.2.1。"
        "規格寫部分測試已被那兩條覆蓋，不必期待 6.2H 再給一張完整 PCMAX 表。"
    ),
    ("6.2", "I"): (
        "RedCap 最大功率＝6.2.1 的 Power Class 3。"
        "測的通道頻寬改 38.508-1 的 RedCap 列，不是一般模組那組 Lowest／Mid／Highest。"
    ),
    ("6.2", "J"): (
        "ATG 功率在 TAB 上看。數字與手持 6.2.1 不同，帶緣 NOTE 也不一定能直接套。"
    ),
    ("6.2", "L"): (
        "CA 的加總規則＋Tx Div 的雙 port。沒有另表就分別對 6.2A 與 6.2G。"
    ),
    ("6.3", "A"): (
        "CA 切換載波時有專用 time mask（6.3A.3.0：CC1↔CC2、一帶一雙、band X↔Y）。"
        "那些圖是切換暫態，不是 6.3.3.2 那張一般 PUSCH ON/OFF。"
        "最小功率、OFF、TPC 在帶內連續時多半 per CC，帶間則各 band 分開看。"
    ),
    ("6.3", "B"): (
        "NR-DC 的動態條款大多指向 6.3A 或本體，重點是兩組 NR 同時在時 TPC／OFF 仍要成立。"
    ),
    ("6.3", "C"): (
        "SUL↔一般 UL 的切換 mask 在 6.3C.3.0，圖號 6.3C.3.0.2～6。"
        "不要用 6.3.3.2 的 10 µs PUSCH mask 去判 SUL 切換。"
    ),
    ("6.3", "D"): (
        "UL MIMO 的最小功率／time mask／TPC 要聲明是 per port 還是合成。"
        "本體 6.3 對「不支援 Tx Div」才適用時，支援 UL MIMO 的 UE 走這裡。"
    ),
    ("6.3", "E"): (
        "側鏈 time mask：PSCCH/PSSCH、S-SSB，以及 Uu↔SL 同載波／異載波切換。"
        "這幾張圖在印刷頁 914–915，跟 Uu 的 PRACH／SRS mask 不是同一張。"
    ),
    ("6.3", "F"): (
        "共享頻譜的 ON/OFF 與 TPC 爬升圖是 6.3F 自己的（先聽再發，OFF 定義不同）。"
    ),
    ("6.3", "G"): (
        "Tx Div 開啟時的動態。本體 6.3 多數對「不支援 Tx Div」才適用。"
    ),
    ("6.3", "H"): (
        "CA＋UL MIMO 的動態：MIMO CC 走 6.3D，另一顆走 6.3A／本體。"
    ),
    ("6.3", "J"): (
        "ATG 的動態在 TAB 上看。切換與 TPC 步階用 ATG 專表。"
    ),
    ("6.3", "L"): (
        "CA＋Tx Div 的動態。加總同 6.3A，port 數同 6.3G。"
    ),
    ("6.4", "A"): (
        "EVM／頻偏／平坦度在帶內連續 CA 時對聚合後的分配看；帶間則 per CC。"
        "Carrier leakage、IBE 的「未分配 RB」在兩顆 CC 中間那一段要另外定義。"
    ),
    ("6.4", "B"): (
        "NR-DC 的訊號品質多半 per CG。不要把兩組 NR 的 EVM 平均成一個數。"
    ),
    ("6.4", "C"): (
        "SUL 上的 EVM／頻偏。平坦度分區仍用 SUL 的 FUL，不是 DL band。"
    ),
    ("6.4", "D"): (
        "UL MIMO 的 EVM 與平坦度按 port 或合成規定，6.4D.2.4 有自己的測試圖。"
        "本體 6.4.2.x 常排除支援 UL MIMO 的 UE。"
    ),
    ("6.4", "E"): (
        "側鏈 PSSCH 的 EVM／平坦度。調變與參考波形跟 Uu PUSCH 不同。"
    ),
    ("6.4", "F"): (
        "共享頻譜的 EVM／平坦度。n46／n96 的 SCS 與佔用通道跟授權頻段不同。"
    ),
    ("6.4", "G"): (
        "Tx Div 開啟時的 EVM。本體 6.4 對不支援 Tx Div 才適用。"
    ),
    ("6.4", "H"): (
        "CA＋UL MIMO：MIMO CC 走 6.4D，另一顆走 6.4A。"
    ),
    ("6.4", "L"): (
        "CA＋Tx Div 的訊號品質。分別對回 6.4A 與 6.4G。"
    ),
    ("6.5", "A"): (
        "帶內連續 CA：OBW ≤ 聚合後通道頻寬。"
        "帶內非連續：所有 sub-block 功率和／總功率 >99%。"
        "帶間：OBW per CC。"
        "SEM／ACLR 的鄰道是對聚合後的邊緣算，不是對單一 CC 的邊緣。"
    ),
    ("6.5", "B"): (
        "NR-DC 的雜散／ACLR 要兩組 UL 都算進去，精神接近帶間 CA。"
    ),
    ("6.5", "C"): (
        "SUL 發射的 SEM／ACLR／雜散。保護的「鄰居」是 SUL 頻段旁邊那些系統。"
    ),
    ("6.5", "D"): (
        "UL MIMO 的 ACLR／SEM 多半看合成輸出。單 port 超標、合成沒超，仍要對規格用詞。"
    ),
    ("6.5", "E"): (
        "側鏈的 OBW／SEM／ACLR。n47 與 ITS 頻段共存是重點，不是 n1／n78 那組鄰居。"
    ),
    ("6.5", "F"): (
        "共享頻譜的 SEM／ACLR 另有 NS，OOB 寬度也不一定是 BW+5 MHz 那套。"
    ),
    ("6.5", "G"): (
        "Tx Div 開啟時的頻譜。本體 6.5 對不支援 Tx Div 才適用。"
    ),
    ("6.5", "H"): (
        "CA＋UL MIMO 的頻譜：兩邊的 ACLR／雜散都要過。"
    ),
    ("6.5", "J"): (
        "ATG 頻譜在 TAB 上看。Figure 6.5J.0-1 是 ATG 自己的分區圖，不是 6.5.0-1。"
    ),
    ("6.5", "L"): (
        "CA＋Tx Div 的頻譜。加總同 6.5A，port 同 6.5G。"
    ),
    ("7.3", "A"): (
        "每個 CC 吞吐都要 ≥95%，不是只看 PCC。"
        "帶內連續：SCC 用標稱通道間距。"
        "帶間：REFSENS 要加 ΔRIB,c；4Rx／8Rx 時 MSD>0 還要再加 |ΔRIB,4R／8R|。"
        "V18 仍標 4DL／5DL 的 REFSENS 為 FFS，2DL／2UL 測試表也不完整。"
    ),
    ("7.3", "B"): (
        "NR-DC 的 REFSENS 按各 CG 看，例外與 ΔRIB 用 DC 組合表，不是 7.3.2 單 band。"
    ),
    ("7.3", "C"): (
        "UL 在 SUL 時量原 band 的 DL REFSENS。SUL 諧波或互調落到 DL 時會有 MSD 例外。"
    ),
    ("7.3", "D"): (
        "UL MIMO 開啟時的 REFSENS。UL 打滿兩 port，自干擾通常比單 port 兇，表會另給或加 MSD。"
    ),
    ("7.3", "E"): (
        "側鏈收的靈敏度，參考信道是 PSSCH，不是 Uu PDSCH。不要拿 7.3.2 的 −100 dBm 去比。"
    ),
    ("7.3", "F"): (
        "n46／n96 有自己的 PREFSENS 表（含 4Rx）。帶間再加 7.3F.3 的 ΔRIB,c（例如 CA_n46-n48）。"
    ),
    ("7.3", "G"): (
        "Tx Div 開啟時的 REFSENS。7.3.2 另有 1d 給支援 Tx Div 的劣化表。"
    ),
    ("7.3", "I"): (
        "RedCap 的 REFSENS。7.3.2 本體排除 RedCap，一定要看 7.3I，通道與天線數都比較窄。"
    ),
    ("7.3", "J"): (
        "ATG 的 REFSENS 在 TAB／ATG 專用測點，不是手持 2Rx 那張主表。"
    ),
    ("7.4", "A"): (
        "最大輸入對每個 CC 都要過。帶內連續時前端看到的是聚合後的總功率，比單 CC −25 dBm 更嚴。"
    ),
    ("7.4", "B"): (
        "NR-DC 的最大輸入 per CG。兩組 DL 同時打滿時前端更容易過載。"
    ),
    ("7.4", "D"): (
        "UL MIMO 開啟、UL 打滿時的最大輸入。自干擾預算與本體 7.4 不同。"
    ),
    ("7.4", "F"): (
        "共享頻譜的最大輸入。n46／n96 的通道與干擾環境跟授權頻段不同。"
    ),
    ("7.4", "J"): (
        "ATG 的最大輸入在 TAB 上看。"
    ),
    ("7.5", "A"): (
        "干擾放在「聚合後 DL」的旁邊，不是只放在 PCC 旁邊。"
        "ACS 按 CA bandwidth class：sub-3 GHz class B／C 為 20／17 dB；≥3.3 GHz class B／C／D 為 26／33／25.2 dB。"
        "每個 CC 吞吐都要 ≥95%。Wanted 仍是每 CC REFSENS+14 dB，干擾上限 −25 dBm。"
    ),
    ("7.5", "B"): (
        "NR-DC 的 ACS 對各 CG 的 DL 分別擺鄰道干擾，不要只測 MCG。"
    ),
    ("7.5", "D"): (
        "UL MIMO 開啟時的 ACS。UL 兩 port 打滿，wanted 電平與本體相同，自干擾預算不同。"
    ),
    ("7.5", "F"): (
        "共享頻譜的 ACS。鄰道可能是別家 NR-U 或 Wi-Fi，表與 7.5 本體不同。"
    ),
    ("7.5", "J"): (
        "ATG 的 ACS，干擾與 wanted 都在 ATG 的參考點上看。"
    ),
    ("7.6", "A"): (
        "CA 的 in-band／OOB 範圍是對聚合後的接收帶算。"
        "帶內連續：兩邊 15 MHz（或 3×聚合 BW）從聚合邊緣起算，不是從 PCC 邊緣。"
        "帶間：每個 DL band 自己的 blocking 都要過。"
    ),
    ("7.6", "B"): (
        "NR-DC 的阻擋 per CG。兩組接收帶都要掃。"
    ),
    ("7.6", "C"): (
        "SUL 開啟時的阻擋。UL 在低頻、DL 在原 band，諧波／互調落到 DL 的例外在這裡。"
    ),
    ("7.6", "D"): (
        "UL MIMO 開啟時的阻擋。雙 UL 自干擾較大，MSD／例外表與本體不同。"
    ),
    ("7.6", "E"): (
        "側鏈收的阻擋。干擾相對的是 SL 接收帶，不是 Uu DL 帶。"
    ),
    ("7.6", "F"): (
        "共享頻譜的阻擋。n46／n96 的 OOB Range 與授權頻段不同。"
    ),
    ("7.6", "J"): (
        "ATG 的阻擋，參考點是 TAB。"
    ),
    ("7.7", "A"): (
        "CA 時 7.6A 過不了的離散頻率走這裡。每個 DL CC 都要處理自己的雜散響應點。"
    ),
    ("7.7", "B"): (
        "NR-DC 的雜散響應 per CG。"
    ),
    ("7.7", "C"): (
        "SUL 組態下，OOB 過不了的點改測 7.7C。"
    ),
    ("7.7", "D"): (
        "UL MIMO 開啟時的雜散響應。雙 TX 多一組混頻產物。"
    ),
    ("7.7", "E"): (
        "側鏈收的雜散響應。"
    ),
    ("7.7", "F"): (
        "共享頻譜的雜散響應。n46／n96 的離散點與授權頻段不同。"
    ),
    ("7.7", "J"): (
        "ATG 的雜散響應。"
    ),
    ("7.8", "A"): (
        "兩個干擾的差頻要落到聚合後的 DL（或指定 CC）上。"
        "帶內連續時偏移以聚合 BW 計算，不是單一 CC 的 BW。"
    ),
    ("7.8", "B"): (
        "NR-DC 的互調 per CG。差頻落到哪一組就測哪一組。"
    ),
    ("7.8", "D"): (
        "UL MIMO 開啟時的接收互調。雙 UL 改變前端的工作點。"
    ),
    ("7.8", "E"): (
        "側鏈收的互調。wanted 是 PSSCH。"
    ),
    ("7.8", "F"): (
        "共享頻譜的互調。干擾可能是別家 NR-U。"
    ),
    ("7.8", "J"): (
        "ATG 的接收互調。"
    ),
    ("7.9", "A"): (
        "CA 時每個接頭的 RX 雜散都要過。雙接頭不是只量其中一個。"
    ),
    ("7.9", "B"): (
        "NR-DC 的 RX 雜散，兩組接收鏈都要量。"
    ),
    ("7.9", "J"): (
        "ATG 的 RX 雜散在 TAB 上看。"
    ),
}

_ORIG = {
    "A": (
        "Carrier aggregation (intra-band contiguous, intra-band non-contiguous, "
        "or inter-band). For inter-band UL CA with separate antenna connectors, "
        "maximum output power is the sum of the power at each connector. "
        "REFSENS, ACS and blocking are verified per CC or against the aggregated "
        "downlink edge. ΔTIB,c / ΔRIB,c may apply."
    ),
    "B": (
        "NR dual connectivity (MCG + SCG). Both NR legs transmit and receive. "
        "Power sharing and spurious are treated similarly to inter-band CA. "
        "Do not reuse a single-carrier power-class number as the total limit."
    ),
    "C": (
        "Supplementary uplink. The UE transmits on the SUL band while receiving "
        "on the paired DL band. TX requirements apply at the SUL connector. "
        "Switching masks between SUL and the normal UL are specified in 6.3C."
    ),
    "D": (
        "UL MIMO (typically two TX connectors, closed-loop spatial multiplexing). "
        "Power, EVM and ACLR are specified per port or as a combined value. "
        "Many parent 6.x clauses apply only if the UE does not support UL MIMO "
        "or Tx diversity. ULFPTx and the 0/14/18 dBm PCMAX points belong here."
    ),
    "E": (
        "NR V2X sidelink (PSSCH/PSCCH on PC5), not Uu PUSCH. n47 has its own "
        "power class. Concurrent sidelink + NR UL has extra power and coexistence "
        "requirements. Time masks include PSCCH/PSSCH and Uu–SL switching."
    ),
    "F": (
        "Shared-spectrum channel access (NR-U) on n46/n96. Default power class "
        "is 5 (20 dBm). Channel access / LBT applies. SEM, ACLR and REFSENS "
        "use NS- or band-specific tables, not the licensed-band parent tables."
    ),
    "G": (
        "TX diversity. Parent 6.x clauses for PC2/PC3 often apply only when the "
        "UE does not support Tx diversity. UEs that do shall use the G clause."
    ),
    "H": (
        "CA with UL MIMO on one CC. The MIMO carrier follows the D clause; the "
        "other carrier follows the parent or A clause. Some tests are explicitly "
        "covered by 6.2.4 and 6.2D.4."
    ),
    "I": (
        "RedCap / eRedCap (Rel-17 onward). 6.2I reuses power class 3 from 6.2.1 "
        "but with RedCap channel bandwidths from TS 38.508-1. 7.3.2 excludes "
        "RedCap; use 7.3I for REFSENS."
    ),
    "J": (
        "Air-to-ground. Requirements are typically specified at the TAB, not at "
        "a handheld antenna connector. Power, emissions and REFSENS have ATG "
        "tables. 6.5J has its own spectrum figure."
    ),
    "L": (
        "CA with Tx diversity. Combine the aggregation rules of A with the "
        "dual-port rules of G. Use this clause only if the UE supports both."
    ),
}


def _letter_of(fid: str) -> str:
    for ch in fid:
        if ch.isalpha():
            return ch
    return ""


def _parent_of(fid: str) -> str:
    out = []
    for ch in fid:
        if ch.isalpha():
            break
        out.append(ch)
    return "".join(out).rstrip(".")


def fam_brief(fid: str) -> str:
    letter = _letter_of(fid)
    parent = _parent_of(fid)
    name, _line, _note = LETTERS.get(letter, (letter, "", ""))
    what = PARENTS.get(parent, "")
    return "\n\n".join(p for p in (
        f"{parent} 的「{name}」變體，不是把 {parent} 再抄一次。",
        what,
    ) if p)


def fam_detail(fid: str) -> str:
    letter = _letter_of(fid)
    parent = _parent_of(fid)
    name, _line, note = LETTERS.get(letter, (letter, "", ""))
    spec = SPECIFICS.get((parent, letter), "")
    parent_txt = PARENTS.get(parent, "")
    extra = ""
    if parent.startswith("7"):
        extra = "38.521-1 第 7 章沒有 Figure，限值在表裡。"
    elif parent == "6.2":
        extra = "功率變體一樣沒有波形圖，差在怎麼加總、用哪張 Power Class／MPR 表。"
    bits = [
        f"組態是「{name}」。量的是：{parent_txt}",
        note,
        spec,
        extra,
        "限值本體在 38.101-1 對應的字母條款。38.521-1 這裡是測法與適用條件。",
        "沒有另給的表就對回本體，但適用條件、參考點、要不要加總，以這一條為準。",
    ]
    return "\n\n".join(b.strip() for b in bits if b and b.strip())


def fam_orig(fid: str, title: str) -> str:
    letter = _letter_of(fid)
    body = _ORIG.get(
        letter,
        "This letter clause applies the parent requirement to another configuration.",
    )
    return f"{fid} {title}\n{body}"


def suffix_rows() -> tuple[tuple[str, str, str], ...]:
    rows = [("（無）", "單載波 SA", "沒有字母＝FR1 standalone 單載波，測項本體。")]
    for key in ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "L"):
        name, line, _note = LETTERS[key]
        rows.append((key, name, line))
    return tuple(rows)
