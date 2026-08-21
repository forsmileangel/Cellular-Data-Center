"""Analysis models and margin helpers.

Summary-row Verdict is the authoritative test status. Detail-row P/F is kept as
instrument evidence only; the helpers in this module never promote it to a
session/test verdict.
"""

from __future__ import annotations

import base64
import json
import math
import re
from dataclasses import dataclass
from typing import Iterable


UNSET_ABS = 1e20
PAGE_SIZE = 100
SCOPE_SEPARATOR = "\u241f"
DERIVED_ITEM_RE = re.compile(r"(?:worst\s*margin|margin)$", re.I)


@dataclass(frozen=True)
class AnalysisCohort:
    """One project/folder scope inside a module."""

    project: str
    data_folder: str

    @property
    def label(self) -> str:
        return f"{self.project} / {self.data_folder}"

    @property
    def token(self) -> str:
        return f"{self.project}{SCOPE_SEPARATOR}{self.data_folder}"

    @classmethod
    def from_token(cls, token: str) -> AnalysisCohort | None:
        if SCOPE_SEPARATOR not in token:
            return None
        project, data_folder = token.split(SCOPE_SEPARATOR, 1)
        if not project or not data_folder:
            return None
        return cls(project, data_folder)


@dataclass(frozen=True)
class AnalysisFilter:
    module: str = ""
    scopes: tuple[AnalysisCohort, ...] = ()
    imei: str = ""
    band: str = ""
    clause: str = ""
    status: str = ""
    mode: str = "latest"
    page: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(self, "mode", "history" if self.mode == "history" else "latest")
        object.__setattr__(self, "page", max(1, int(self.page or 1)))


@dataclass(frozen=True)
class MeasurementGroup:
    """Exact detail condition/limit group; safe to rank or plot together."""

    clause: str
    item: str
    band: str
    bandwidth: str
    scs: str
    modulation: str
    rb: str
    condition: str
    unit: str
    lower_limit: str
    upper_limit: str
    count: int = 0

    @property
    def signature(self) -> tuple[str, ...]:
        return (
            self.clause,
            self.item,
            self.band,
            self.bandwidth,
            self.scs,
            self.modulation,
            self.rb,
            self.condition,
            self.unit,
            self.lower_limit,
            self.upper_limit,
        )

    @property
    def token(self) -> str:
        raw = json.dumps(self.signature, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

    @classmethod
    def from_token(cls, token: str) -> MeasurementGroup | None:
        try:
            raw = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
            values = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeError, json.JSONDecodeError):
            return None
        if not isinstance(values, list) or len(values) != 11:
            return None
        return cls(*(str(value or "") for value in values))


@dataclass(frozen=True)
class SpecInsight:
    clause: str
    title: str = ""
    version: str = ""
    page: int | None = None
    purpose: str = ""
    watch: str = ""
    extra: str = ""
    detail: str = ""
    available: bool = False


def measurement_group_from_row(row: dict, count: int = 0) -> MeasurementGroup:
    return MeasurementGroup(
        clause=clause_of(row.get("test_case") or ""),
        item=row.get("item") or "",
        band=row.get("band") or "",
        bandwidth=row.get("bandwidth") or "",
        scs=row.get("scs") or "",
        modulation=row.get("modulation") or "",
        rb=row.get("rb") or "",
        condition=row.get("condition") or "",
        unit=row.get("unit") or "",
        lower_limit=row.get("lower_limit") or "",
        upper_limit=row.get("upper_limit") or "",
        count=count,
    )


def to_float(raw: str | None) -> float | None:
    if raw is None:
        return None
    text = str(raw).strip().replace(",", "")
    if not text or text.lower() in {"nan", "inf", "-inf", "n/a", "none"}:
        return None
    try:
        value = float(text)
        return value if math.isfinite(value) else None
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


def clause_of(text: str | None) -> str:
    match = re.match(r"^\s*(\d+(?:\.\d+)*)\b", text or "")
    return match.group(1) if match else ""


def measurement_state(raw: str | None, item: str = "") -> str:
    """Return measured / unset / derived / invalid for a detail value."""
    value = to_float(raw)
    if is_unset_value(raw, value):
        return "unset"
    if value is None:
        return "invalid"
    if DERIVED_ITEM_RE.search((item or "").strip()):
        return "derived"
    return "measured"


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
    state: str = "measured"
    clause: str = ""
    project: str = ""
    data_folder: str = ""
    bandwidth: str = ""
    scs: str = ""
    modulation: str = ""
    rb: str = ""
    arfcn: str = ""
    margin_ratio: float | None = None


def decorate(point: Point) -> Point:
    if point.lsl is not None:
        point.margin_lsl = point.value - point.lsl
    if point.usl is not None:
        point.margin_usl = point.usl - point.value
    if point.lsl is not None and point.usl is not None and point.usl != point.lsl:
        window = point.usl - point.lsl
        point.pos = (point.value - point.lsl) / window
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
        if point.lsl is not None and point.usl is not None:
            window = point.usl - point.lsl
            if window > 0:
                point.margin_ratio = point.nearest / window
    else:
        point.side = "unknown"
    return point


def from_row(row: dict) -> Point | None:
    if (row.get("pf") or "") not in {"Pass", "Fail"}:
        return None
    raw = row.get("value")
    value = to_float(raw)
    state = measurement_state(raw, row.get("item") or "")
    unset = state in {"unset", "invalid"}
    if state == "invalid" and value is None:
        value = 0.0
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
        state=state,
        clause=clause_of(row.get("test_case") or ""),
        project=row.get("project") or "",
        data_folder=row.get("data_folder") or "",
        bandwidth=row.get("bandwidth") or "",
        scs=row.get("scs") or "",
        modulation=row.get("modulation") or "",
        rb=row.get("rb") or "",
        arfcn=row.get("arfcn") or "",
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
