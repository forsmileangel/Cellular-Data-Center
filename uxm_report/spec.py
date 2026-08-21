"""NR / LTE band edges and Low/Mid/High from 3GPP TS 38.101-1 / 38.508-1 / 36.101 / 36.508."""

from __future__ import annotations

import re
from dataclasses import dataclass

# TS 38.101-1 Table 5.2-1: NR FR1 operating bands (DL MHz).
# TDD uses the same range for UL/DL.
NR_DL_MHZ: dict[str, tuple[float, float]] = {
    "n1": (2110.0, 2170.0),
    "n2": (1930.0, 1990.0),
    "n3": (1805.0, 1880.0),
    "n5": (869.0, 894.0),
    "n7": (2620.0, 2690.0),
    "n8": (925.0, 960.0),
    "n12": (729.0, 746.0),
    "n13": (746.0, 756.0),
    "n20": (791.0, 821.0),
    "n25": (1930.0, 1995.0),
    "n26": (859.0, 894.0),
    "n28": (758.0, 803.0),
    "n38": (2570.0, 2620.0),
    "n40": (2300.0, 2400.0),
    "n41": (2496.0, 2690.0),
    "n48": (3550.0, 3700.0),
    "n66": (2110.0, 2200.0),
    "n71": (617.0, 652.0),
    "n77": (3300.0, 4200.0),
    "n78": (3300.0, 3800.0),
    "n79": (4400.0, 5000.0),
}

# TS 36.101 Table 5.5-1: E-UTRA DL (MHz).
LTE_DL_MHZ: dict[str, tuple[float, float]] = {
    "1": (2110.0, 2170.0),
    "2": (1930.0, 1990.0),
    "3": (1805.0, 1880.0),
    "5": (869.0, 894.0),
    "7": (2620.0, 2690.0),
    "8": (925.0, 960.0),
    "12": (729.0, 746.0),
    "13": (746.0, 756.0),
    "20": (791.0, 821.0),
    "28": (758.0, 803.0),
    "38": (2570.0, 2620.0),
    "40": (2300.0, 2400.0),
    "41": (2496.0, 2690.0),
}

# TS 36.101 Table 5.7.3-1 (subset): F_DL_low, N_Offs-DL.
LTE_EARFCN: dict[str, tuple[float, int]] = {
    "1": (2110.0, 0),
    "2": (1930.0, 600),
    "3": (1805.0, 1200),
    "5": (869.0, 2400),
    "7": (2620.0, 2750),
    "8": (925.0, 3450),
    "12": (729.0, 5010),
    "13": (746.0, 5180),
    "20": (791.0, 6150),
    "28": (758.0, 9210),
    "38": (2570.0, 37750),
    "40": (2300.0, 38650),
    "41": (2496.0, 39650),
}

RANGES = ("Low", "Mid", "High")

# Split by DL F_low (TS 38.101-1 / 36.101). Same bins for NR and LTE.
# Low <1 GHz, Mid 1–2.2 GHz, High ≥2.2 GHz (includes n41/n7 and n77/n78/n79).
# Ultra-high = FR2 mmWave only (n257+).
NR_RANGE_ORDER = ("Low-band", "Mid-band", "High-band", "Ultra-high", "其他")
_FR2_MIN = 257


def nr_range_class(display: str) -> str:
    """Classify NR_n78 / B3 into Low/Mid/High/Ultra-high."""
    try:
        rat, band_id = normalize_band(display)
    except KeyError:
        return "其他"
    if rat == "NR":
        num = int(re.sub(r"\D", "", band_id) or "0")
        if num >= _FR2_MIN:
            return "Ultra-high"
        edges = NR_DL_MHZ.get(band_id)
    else:
        edges = LTE_DL_MHZ.get(band_id)
    if not edges:
        return "其他"
    f_low = edges[0]
    if f_low < 1000:
        return "Low-band"
    if f_low < 2200:
        return "Mid-band"
    return "High-band"


@dataclass(frozen=True)
class LmH:
    low: float
    mid: float
    high: float


def normalize_band(raw: str) -> tuple[str, str]:
    """Return (rat, band_id) e.g. ('NR', 'n1') or ('LTE', '1')."""
    s = raw.strip()
    s = re.sub(r"^[Nn][Rr]_", "", s)
    s = re.sub(r"[A-Za-z]+$", "", s) if re.match(r"^n\d+[A-Za-z]$", s) else s
    m = re.match(r"^n(\d+)$", s, re.I)
    if m:
        return "NR", f"n{m.group(1)}"
    m = re.match(r"^(?:B|EUTRA)?(\d+)$", s, re.I)
    if m:
        return "LTE", m.group(1)
    if s.lower().startswith("n"):
        return "NR", s.lower()
    raise KeyError(f"unknown band token: {raw!r}")


def display_band(rat: str, band_id: str) -> str:
    if rat == "NR":
        return f"NR_{band_id}"
    return f"B{band_id}"


def nr_arfcn_to_mhz(arfcn: int) -> float:
    """TS 38.101-1 Table 5.4.2.1-1."""
    if arfcn < 600000:
        return arfcn * 0.005
    if arfcn < 2016667:
        return 3000.0 + (arfcn - 600000) * 0.015
    return 24250.08 + (arfcn - 2016667) * 0.060


def lte_earfcn_to_mhz(earfcn: int, band_id: str) -> float:
    """TS 36.101: F_DL = F_DL_low + 0.1 * (N_DL - N_Offs-DL)."""
    if band_id not in LTE_EARFCN:
        raise KeyError(f"LTE EARFCN table missing band {band_id}")
    f_low, n_offs = LTE_EARFCN[band_id]
    return f_low + 0.1 * (earfcn - n_offs)


def channel_to_mhz(channel: int, rat: str, band_id: str) -> float:
    if rat == "NR":
        return nr_arfcn_to_mhz(channel)
    return lte_earfcn_to_mhz(channel, band_id)


def band_edges(rat: str, band_id: str) -> tuple[float, float]:
    table = NR_DL_MHZ if rat == "NR" else LTE_DL_MHZ
    if band_id not in table:
        raise KeyError(f"{rat} band {band_id} not in 3GPP table")
    return table[band_id]


def default_lmh(rat: str, band_id: str, bw_mhz: float) -> LmH:
    """TS 38.508-1 / 36.508 default RF test frequencies for a CBW."""
    f_low, f_high = band_edges(rat, band_id)
    low = f_low + bw_mhz / 2.0
    high = f_high - bw_mhz / 2.0
    mid = (f_low + f_high) / 2.0
    return LmH(low=low, mid=mid, high=high)


def classify_range(freq_mhz: float, lmh: LmH) -> str:
    targets = {"Low": lmh.low, "Mid": lmh.mid, "High": lmh.high}
    return min(targets, key=lambda k: abs(targets[k] - freq_mhz))


def classify_channels(
    channels: list[int],
    rat: str,
    band_id: str,
    bw_mhz: float,
) -> dict[int, str]:
    """Map each ARFCN/EARFCN to Low/Mid/High. Dedup collisions by frequency order."""
    if not channels:
        return {}
    lmh = default_lmh(rat, band_id, bw_mhz)
    freqs = {ch: channel_to_mhz(ch, rat, band_id) for ch in channels}
    assigned = {ch: classify_range(freqs[ch], lmh) for ch in channels}
    used: dict[str, list[int]] = {}
    for ch, rng in assigned.items():
        used.setdefault(rng, []).append(ch)
    collided = any(len(v) > 1 for v in used.values())
    if collided or len(set(assigned.values())) < len(channels) <= 3:
        ordered = sorted(set(channels), key=lambda c: freqs[c])
        labels = {1: ["Mid"], 2: ["Low", "High"], 3: ["Low", "Mid", "High"]}
        names = labels.get(len(ordered))
        if names:
            return {ch: names[i] for i, ch in enumerate(ordered)}
    return assigned
