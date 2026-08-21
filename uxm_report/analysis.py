"""Margin vs 3GPP limits. One DUT is not Cpk; Cpk needs many IMEIs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


UNSET_ABS = 1e20


def to_float(raw: str | None) -> float | None:
    if raw is None:
        return None
    text = str(raw).strip().replace(",", "")
    if not text or text.lower() in {"nan", "inf", "-inf", "n/a", "none"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def is_unset_value(raw: str | None, value: float | None = None) -> bool:
    """Keysight unused readings (e.g. -9.91e+37) or NaN are not real measurements."""
    text = str(raw or "").strip().lower()
    if text in {"nan", "inf", "-inf", "n/a", "none"}:
        return True
    if value is None:
        value = to_float(raw)
    if value is None:
        return False
    return abs(value) >= UNSET_ABS


def limit_float(raw: str | None) -> float | None:
    """Treat Keysight sentinels like -999 / 999 as 'no limit'."""
    value = to_float(raw)
    if value is None:
        return None
    if abs(value) >= 900:
        return None
    return value


@dataclass
class Point:
    value: float
    lsl: float | None
    usl: float | None
    unit: str
    pf: str
    test_case: str
    item: str
    band: str
    condition: str
    imei: str = ""
    session_id: int = 0
    filename: str = ""
    margin_lsl: float | None = None
    margin_usl: float | None = None
    nearest: float | None = None
    pos: float | None = None  # 0=LSL, 1=USL
    side: str = ""  # lower / upper / mid / unknown
    raw_value: str = ""
    unset: bool = False


def decorate(point: Point) -> Point:
    if point.lsl is not None:
        point.margin_lsl = point.value - point.lsl
    if point.usl is not None:
        point.margin_usl = point.usl - point.value
    if point.lsl is not None and point.usl is not None and point.usl != point.lsl:
        point.pos = (point.value - point.lsl) / (point.usl - point.lsl)
    margins = [m for m in (point.margin_lsl, point.margin_usl) if m is not None]
    if margins:
        point.nearest = min(margins)
        if point.margin_lsl is None:
            point.side = "upper"
        elif point.margin_usl is None:
            point.side = "lower"
        elif point.margin_lsl < point.margin_usl:
            point.side = "lower"
        elif point.margin_usl < point.margin_lsl:
            point.side = "upper"
        else:
            point.side = "mid"
    else:
        point.side = "unknown"
    return point


def from_row(row: dict) -> Point | None:
    if (row.get("pf") or "") not in {"Pass", "Fail"}:
        return None
    raw = row.get("value")
    value = to_float(raw)
    unset = is_unset_value(raw, value)
    if not unset and value is None:
        return None
    point = Point(
        value=0.0 if value is None else value,
        lsl=limit_float(row.get("lower_limit")),
        usl=limit_float(row.get("upper_limit")),
        unit=row.get("unit") or "",
        pf=row.get("pf") or "",
        test_case=row.get("test_case") or "",
        item=row.get("item") or "",
        band=row.get("band") or "",
        condition=row.get("condition") or "",
        imei=row.get("imei") or "",
        session_id=int(row.get("session_id") or 0),
        filename=row.get("filename") or "",
        raw_value=str(raw or "").strip(),
        unset=unset,
    )
    if point.unset:
        return point
    if point.lsl is None and point.usl is None:
        return None
    return decorate(point)


@dataclass
class Bias:
    usable: int = 0
    lower: int = 0
    mid: int = 0
    upper: int = 0
    fail: int = 0
    tight: int = 0  # nearest margin < 10% of window or < 1 unit


def summarize(points: Iterable[Point]) -> Bias:
    bias = Bias()
    for point in points:
        if point.unset:
            continue
        if point.pf == "Fail":
            bias.fail += 1
        if point.pos is None:
            continue
        bias.usable += 1
        if point.pos < 1 / 3:
            bias.lower += 1
        elif point.pos > 2 / 3:
            bias.upper += 1
        else:
            bias.mid += 1
        if point.nearest is not None and point.lsl is not None and point.usl is not None:
            window = point.usl - point.lsl
            if window > 0 and point.nearest < 0.1 * window:
                bias.tight += 1
    return bias
