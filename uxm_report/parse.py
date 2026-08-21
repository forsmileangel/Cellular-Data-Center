"""Parse Keysight UXM / RFA CSV and PDF session files."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

from .spec import normalize_band

MODE_RE = re.compile(
    r"(?P<prefix>SAFR1|NSAFR1|LTE|EUTRA)?\s*"
    r"(?P<band>NR_n\d+|n\d+|B\d+)\s+"
    r"SCS(?P<scs>\d+K).*?B(?P<bw>\d+M)",
    re.I,
)


@dataclass
class TestRow:
    test_name: str
    operating_band: str
    channel: int
    bw_token: str
    verdict: str
    time_s: float


@dataclass
class TestMode:
    raw: str
    rat: str
    band_id: str
    display_band: str
    scs: str
    bw: str
    rows: list[TestRow] = field(default_factory=list)


@dataclass
class DetailRow:
    time: str
    system: str
    test_case: str
    description: str
    band: str
    bandwidth: str
    scs: str
    arfcn: str
    freq_mhz: str
    expected_power: str
    ofdm: str
    modulation: str
    rb: str
    condition: str
    item: str
    lower: str
    value: str
    upper: str
    unit: str
    pf: str


@dataclass
class Session:
    path: Path
    filename: str
    header: dict[str, str]
    modes: list[TestMode]
    details: list[DetailRow] = field(default_factory=list)
    source_kind: str = "csv"
    parse_notes: str = ""
    raw_text: str = ""


def _test_name(tcn: str, name: str) -> str:
    tcn = tcn.strip()
    name = name.strip()
    if tcn == "Reference":
        return f"Reference {name}"
    if tcn:
        return f"{tcn} {name}".strip()
    return name


def _parse_mode(raw: str) -> tuple[str, str, str, str, str]:
    m = MODE_RE.search(raw.replace("  ", " "))
    if not m:
        raise ValueError(f"cannot parse Test Mode: {raw!r}")
    band_token = m.group("band")
    rat, band_id = normalize_band(band_token)
    prefix = (m.group("prefix") or "").upper()
    if prefix.startswith("LTE") or prefix.startswith("EUTRA"):
        rat = "LTE"
    display = f"NR_{band_id}" if rat == "NR" else f"B{band_id}"
    scs = (m.group("scs") or "").upper()
    bw = f"B{m.group('bw')}" if m.group("bw") else ""
    if bw and not bw.endswith("M"):
        bw = f"{bw}M"
    return rat, band_id, display, scs, bw or ""


def _detail_from_parts(hdr: list[str], parts: list[str]) -> DetailRow:
    row = {hdr[i]: (parts[i] if i < len(parts) else "") for i in range(len(hdr))}
    return DetailRow(
        time=row.get("Time", "").strip(),
        system=row.get("System", "").strip(),
        test_case=row.get("Test Case", "").strip(),
        description=row.get("Description", "").strip(),
        band=row.get("Band", "").strip(),
        bandwidth=row.get("Bandwidth", "").strip(),
        scs=row.get("SCS", "").strip(),
        arfcn=row.get("ARFCN", "").strip(),
        freq_mhz=row.get("Freq [MHz]", "").strip(),
        expected_power=row.get("Expected Power [dBm]", "").strip(),
        ofdm=row.get("OFDM", "").strip(),
        modulation=row.get("Modulation", "").strip(),
        rb=row.get("RB Allocation", "").strip(),
        condition=row.get("Condition", "").strip(),
        item=row.get("Item", "").strip(),
        lower=row.get("Lower Limit", "").strip(),
        value=row.get("Value", "").strip(),
        upper=row.get("Upper Limit", "").strip(),
        unit=row.get("Unit", "").strip(),
        pf=row.get("P/F", "").strip(),
    )


def parse_text(text: str, filename: str, path: Path | None = None) -> Session:
    return parse_lines(text.splitlines(), path or Path(filename), filename)


def parse_csv(path: str | Path) -> Session:
    path = Path(path)
    return parse_text(path.read_text(encoding="utf-8", errors="replace"), path.name, path)


def parse_lines(lines: list[str], path: Path, filename: str) -> Session:
    header: dict[str, str] = {}
    modes: list[TestMode] = []
    details: list[DetailRow] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.startswith("Time,System,"):
            hdr = next(csv.reader([line]))
            i += 1
            while i < n:
                if lines[i].strip():
                    parts = next(csv.reader([lines[i]]))
                    if len(parts) >= 8:
                        details.append(_detail_from_parts(hdr, parts))
                i += 1
            break
        if line.startswith("Test Mode,"):
            raw_mode = line.split(",", 1)[1].strip()
            rat, band_id, display, scs, bw = _parse_mode(raw_mode)
            i += 1
            if i < n and lines[i].startswith("ID,Test Case Number"):
                i += 1
            rows: list[TestRow] = []
            while i < n and not lines[i].startswith("Test Mode,") and not lines[i].startswith(
                "Time,System,"
            ):
                if lines[i].strip():
                    parts = next(csv.reader([lines[i]]))
                    if len(parts) >= 10 and parts[0].strip().isdigit():
                        bw_token = parts[6].strip() or bw
                        rows.append(
                            TestRow(
                                test_name=_test_name(parts[1], parts[2]),
                                operating_band=parts[3].strip(),
                                channel=int(float(parts[5].strip())),
                                bw_token=bw_token,
                                verdict=parts[8].strip(),
                                time_s=float(parts[9].strip() or 0),
                            )
                        )
                i += 1
            if not bw and rows:
                bw = rows[0].bw_token
            modes.append(
                TestMode(
                    raw=raw_mode,
                    rat=rat,
                    band_id=band_id,
                    display_band=display,
                    scs=scs,
                    bw=bw,
                    rows=rows,
                )
            )
            continue
        if (
            i < 40
            and not line.startswith("Cable Loss")
            and not line.startswith(",")
            and not line.startswith("Test Station")
            and not line.startswith("License Info")
        ):
            if "," in line:
                key, val = line.split(",", 1)
            elif ":" in line:
                key, val = line.split(":", 1)
            else:
                i += 1
                continue
            header[key.strip()] = val.strip()
        i += 1
    return Session(
        path=path,
        filename=filename,
        header=header,
        modes=modes,
        details=details,
    )


def ta_major(version: str) -> str:
    m = re.match(r"\s*(\d+)", version or "")
    return m.group(1) if m else ""


CONN_TEST_RE = re.compile(r"connection[_\s-]?test", re.I)


def is_connection_test(filename: str, test_plan: str = "") -> bool:
    return bool(CONN_TEST_RE.search(f"{test_plan} {filename}"))


def plan_label(filename: str, test_plan: str = "") -> str:
    blob = f"{test_plan} {filename}"
    if CONN_TEST_RE.search(blob):
        return "connection test"
    m = re.search(r"Full Test\s+N?\d+", blob, re.I)
    if m:
        return m.group(0)
    if re.search(r"full[_\s-]?test", blob, re.I):
        return "Full Test"
    return (test_plan or "").strip()


def _is_session_file(path: Path) -> bool:
    if path.name.lower().startswith("bandcombinations"):
        return False
    return path.suffix.lower() in {".csv", ".pdf"}


def list_report_files(folder: str | Path) -> list[Path]:
    folder = Path(folder)
    if not folder.is_dir():
        return []
    return sorted(
        (p for p in folder.iterdir() if p.is_file() and _is_session_file(p)),
        key=lambda p: p.name,
    )


def parse_file(path: str | Path) -> Session:
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        from .pdf_rfa import parse_pdf

        return parse_pdf(path)
    return parse_csv(path)


def parse_folder(folder: str | Path) -> list[Session]:
    folder = Path(folder).resolve()
    files = sorted(p for p in folder.glob("*.csv") if _is_session_file(p))
    return [parse_csv(p) for p in files]


def parse_selected(folder: str | Path, names: list[str] | None) -> list[Session]:
    folder = Path(folder).resolve()
    if names is None:
        return [parse_file(p) for p in list_report_files(folder)]
    if not names:
        return []
    files = []
    for name in names:
        path = (folder / Path(name).name).resolve()
        if path.parent != folder or path.suffix.lower() not in {".csv", ".pdf"}:
            raise ValueError(f"不允許的檔名: {name}")
        if not path.is_file():
            raise FileNotFoundError(f"找不到檔案: {path.name}")
        if not _is_session_file(path):
            continue
        files.append(path)
    files = sorted(files, key=lambda p: p.name)
    return [parse_file(p) for p in files]


def session_rat(session: Session) -> str:
    rats = {m.rat for m in session.modes}
    if rats == {"NR"}:
        return "NR"
    if rats == {"LTE"}:
        return "LTE"
    if not rats:
        return ""
    return "mixed"


def keep_bands(session: Session, bands: set[str]) -> Session:
    if not bands:
        return session
    session.modes = [m for m in session.modes if m.display_band in bands]
    return session


def bw_mhz(token: str) -> float:
    m = re.search(r"(\d+(?:\.\d+)?)", token or "")
    if not m:
        raise ValueError(f"cannot parse bandwidth: {token!r}")
    return float(m.group(1))
