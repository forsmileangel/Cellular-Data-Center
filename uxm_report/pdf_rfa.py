"""Reconstruct Keysight RFA PDF reports into CSV-like text for parse_text."""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

from .parse import Session, parse_text

WEEKDAYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)
HEADER_KEYS = {
    "Test Station PC Name",
    "IMEI",
    "BarCode",
    "TestPlan",
    "Manufacturer",
    "Model",
    "UXM SN",
    "TA Version",
    "License Info",
    "UXM Version",
    "Run Test Mode",
    "3GPP Protocal Version",
    "3GPP Protocol Version",
    "RFA Version",
    "Configuration",
    "Start Time",
    "Stop Time",
    "Total Elapsed Time",
    "Total UE Control Times",
    "Overall Result",
    "Number of TestCases",
    "Testcases Pass",
    "Testcases Fail",
    "Testcases Skip",
    "Testcases NotSet",
}
SKIP_HEADER_PREFIX = (
    "Measurement Report",
    "Report Info",
    "Device Under Test",
    "Operator",
    "Station Info",
    "Comment",
    "Place",
    "Date:",
    "Person responsible",
)
SUMMARY_SKIP = {
    "ID",
    "Test Case",
    "Number",
    "Test Case Name",
    "Operating",
    "Band",
    "PCell",
    "Channel",
    "BW",
    "SCells",
    "Verdict",
    "time(s)",
    "SCells Verdict",
    "Overall Test Result",
}
VERDICTS = {"Pass", "Fail", "Skip", "NotSet", "Pass*", "Fail*"}
DETAIL_LABELS = (
    "Time",
    "System",
    "Band Combo Info",
    "Test Case",
    "Description",
    "Band",
    "Bandwidth",
    "SCS",
    "ARFCN",
    "Freq [MHz]",
    "LTESCC Info",
    "Expected Power [dBm]",
    "Others",
    "OFDM",
    "Modulation",
    "RB Allocation",
    "Condition",
)
ITEM_HDR = ("Item", "Lower Limit", "Value", "Upper Limit", "Unit", "Status")
DETAIL_HDR = [
    "Time",
    "System",
    "Band Combo Info",
    "Test Case",
    "Description",
    "Band",
    "Bandwidth",
    "SCS",
    "ARFCN",
    "Freq [MHz]",
    "LTESCC Info",
    "Expected Power [dBm]",
    "Others",
    "OFDM",
    "Modulation",
    "RB Allocation",
    "Condition",
    "Item",
    "Lower Limit",
    "Value",
    "Upper Limit",
    "Unit",
    "P/F",
]
CLAUSE_RE = re.compile(r"^\d+(?:\.\d+)+$")
BAND_RE = re.compile(r"^(?:n\d+[A-Z]?|B\d+[A-Z]?|NR_n\d+)$", re.I)
CHANNEL_RE = re.compile(r"^\d{5,7}$")
BW_RE = re.compile(r"^B\d+(?:\.\d+)?M$", re.I)
LIMIT_RE = re.compile(r"^(NaN|-?\d+(?:\.\d+)?)$", re.I)
LABEL_RE = re.compile(
    r"^(" + "|".join(re.escape(k) for k in DETAIL_LABELS) + r"):\s*(.*)$"
)
MODE_LINE_RE = re.compile(r"^Test Mode\s*,\s*(.+)$", re.I)
SECTION_RE = re.compile(
    r"^(?:"
    r"\d+\s+(?:NRFR|NSAFR|LTE|EUTRA)"
    r"|\d+\.\d+\s+(?:Reference|\d+(?:\.\d+)*)"
    r")",
    re.I,
)


def parse_pdf(path: str | Path) -> Session:
    path = Path(path)
    text, notes = reconstruct_pdf(path)
    session = parse_text(text, path.name, path)
    session.source_kind = "pdf"
    session.parse_notes = "\n".join(notes)
    session.raw_text = text
    return session


def reconstruct_pdf(path: str | Path) -> tuple[str, list[str]]:
    path = Path(path)
    try:
        import pymupdf
    except ImportError as exc:
        raise RuntimeError("需要 PyMuPDF 才能讀 RFA PDF（pip install pymupdf）") from exc
    doc = pymupdf.open(path)
    try:
        if doc.page_count == 0:
            raise ValueError(f"空的 PDF: {path.name}")
        lines = _pdf_lines(doc)
    finally:
        doc.close()
    if not any(
        ln.startswith("TA Version") or ln.startswith("TestPlan") or ln.startswith("IMEI")
        for ln in lines[:120]
    ):
        raise ValueError(f"不是 Keysight RFA 報告: {path.name}")
    notes: list[str] = []
    header, i = _parse_header(lines)
    modes, wrap_names, miss_sum, i = _parse_summary(lines, i)
    wrap_det, details, miss_det = _parse_details(lines)
    if not modes:
        raise ValueError(f"PDF 沒有 Test Mode 摘要表: {path.name}")
    n_rows = sum(len(m["rows"]) for m in modes)
    expect = header.get("Number of TestCases", "").strip()
    if expect.isdigit() and int(expect) != n_rows:
        notes.append(f"摘要列 {n_rows} 筆，封面 Number of TestCases={expect}")
    if wrap_names:
        notes.append(f"摘要測項名折行 {wrap_names} 筆（已空格接回）")
    if wrap_det:
        notes.append(f"細節欄位或 Item 名折行 {wrap_det} 筆（已接回）")
    notes.extend(miss_sum)
    notes.extend(miss_det)
    if not details:
        notes.append("沒有細節列（Skip／Retry 或 PDF 抽不到 Detail Test Result）")
    text = _emit_csv(header, modes, details)
    return text, notes


def _pdf_lines(doc) -> list[str]:
    out: list[str] = []
    for page in doc:
        raw = [ln.strip() for ln in page.get_text("text").splitlines()]
        i = 0
        n = len(raw)
        while i < n:
            s = raw[i]
            if not s:
                i += 1
                continue
            if s.startswith(WEEKDAYS) and (s.endswith("AM") or s.endswith("PM")):
                i += 1
                if i < n and raw[i].isdigit():
                    i += 1
                continue
            out.append(s)
            i += 1
    return out


def _split_kv(line: str) -> tuple[str, str] | None:
    if "," in line:
        key, val = line.split(",", 1)
        return key.strip(), val.strip()
    if ":" in line:
        key, val = line.split(":", 1)
        if key.strip() in HEADER_KEYS or key.strip() in DETAIL_LABELS:
            return key.strip(), val.strip()
    return None


def _parse_header(lines: list[str]) -> tuple[dict[str, str], int]:
    header: dict[str, str] = {}
    last_key = ""
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if MODE_LINE_RE.match(line) or line == "Detail Test Result":
            break
        if line.startswith(SKIP_HEADER_PREFIX):
            i += 1
            continue
        kv = _split_kv(line)
        if kv and kv[0] in HEADER_KEYS:
            key, val = kv
            if key in header and val == "":
                i += 1
                continue
            if key in header and key == "License Info":
                header[key] = f"{header[key]}{val}"
            else:
                header[key] = val
            last_key = key
            i += 1
            continue
        if last_key == "License Info" and kv is None:
            header[last_key] = header.get(last_key, "") + line
            i += 1
            continue
        i += 1
    return header, i


def _is_row_start(tok: list[str], i: int) -> bool:
    if i + 1 >= len(tok):
        return False
    if not tok[i].isdigit():
        return False
    nxt = tok[i + 1]
    return bool(CLAUSE_RE.match(nxt) or nxt == "Reference")


def _parse_summary(
    lines: list[str], start: int
) -> tuple[list[dict], int, list[str], int]:
    modes: list[dict] = []
    wrap_names = 0
    missing: list[str] = []
    i = start
    n = len(lines)
    current: dict | None = None
    while i < n:
        line = lines[i]
        if line.startswith("HCCU Cable Loss") or line.startswith("Cable Loss"):
            break
        if line == "Detail Test Result":
            break
        m = MODE_LINE_RE.match(line)
        if m:
            current = {"raw": m.group(1).strip(), "rows": []}
            modes.append(current)
            i += 1
            while i < n and (lines[i] in SUMMARY_SKIP or lines[i] == "Overall Test Result"):
                i += 1
            continue
        if current is None:
            i += 1
            continue
        if not _is_row_start(lines, i):
            i += 1
            continue
        row_id = lines[i]
        tcn = lines[i + 1]
        j = i + 2
        name_parts: list[str] = []
        while j < n and not BAND_RE.match(lines[j]) and not _is_row_start(lines, j):
            if lines[j] in SUMMARY_SKIP:
                j += 1
                continue
            if lines[j].startswith("HCCU") or lines[j] == "Detail Test Result":
                break
            name_parts.append(lines[j])
            j += 1
            if len(name_parts) > 8:
                break
        if j >= n or not BAND_RE.match(lines[j]):
            missing.append(f"摘要 ID {row_id} 對不到 Operating Band，已略過後續欄")
            i = j
            continue
        if len(name_parts) > 1:
            wrap_names += 1
        name = " ".join(name_parts).strip()
        band = lines[j]
        j += 1
        channel = ""
        bw = ""
        verdict = ""
        time_s = ""
        if j < n and CHANNEL_RE.match(lines[j]):
            channel = lines[j]
            j += 1
        else:
            missing.append(f"摘要 ID {row_id} 缺 Channel")
        if j < n and BW_RE.match(lines[j]):
            bw = lines[j]
            j += 1
        else:
            missing.append(f"摘要 ID {row_id} 缺 BW")
        if j < n and lines[j] in VERDICTS:
            verdict = lines[j]
            j += 1
        elif j + 1 < n and (lines[j] + lines[j + 1]) in VERDICTS:
            verdict = lines[j] + lines[j + 1]
            wrap_names += 1
            j += 2
        else:
            missing.append(f"摘要 ID {row_id} 缺 Verdict")
        if j < n and re.match(r"^\.?\d+(?:\.\d+)?$", lines[j]):
            time_s = lines[j]
            j += 1
        else:
            missing.append(f"摘要 ID {row_id} 缺 time(s)")
        current["rows"].append(
            {
                "id": row_id,
                "tcn": tcn,
                "name": name,
                "band": band,
                "channel": channel,
                "bw": bw,
                "verdict": verdict,
                "time": time_s,
            }
        )
        i = j
    return modes, wrap_names, missing[:20], i


def _is_section(line: str) -> bool:
    if line in {"Detail Test Result", "HCCU Cable Loss"}:
        return True
    return bool(SECTION_RE.match(line))


def _parse_details(lines: list[str]) -> tuple[int, list[dict], list[str]]:
    try:
        start = lines.index("Detail Test Result") + 1
    except ValueError:
        return 0, [], ["PDF 沒有 Detail Test Result 區塊"]
    wrap = 0
    missing: list[str] = []
    details: list[dict] = []
    fields: dict[str, str] = {}
    items: list[tuple[str, str, str, str, str, str]] = []
    last_key = ""
    in_items = False
    i = start
    n = len(lines)

    def flush() -> None:
        nonlocal fields, items
        if not fields:
            items = []
            return
        if not items:
            missing.append(f"Time {fields.get('Time', '')} 沒有 Item 列")
        for item, lower, value, upper, unit, status in items:
            row = {k: fields.get(k, "") for k in DETAIL_LABELS}
            row["Item"] = item
            row["Lower Limit"] = lower
            row["Value"] = value
            row["Upper Limit"] = upper
            row["Unit"] = unit
            row["P/F"] = status
            details.append(row)
        fields = {}
        items = []

    while i < n:
        line = lines[i]
        if line.startswith("Time:"):
            flush()
            fields = {"Time": line.split(":", 1)[1].strip()}
            last_key = "Time"
            in_items = False
            i += 1
            continue
        if _is_section(line):
            in_items = False
            i += 1
            continue
        lab = LABEL_RE.match(line)
        if lab and not in_items:
            key, val = lab.group(1), lab.group(2).strip()
            if not fields:
                i += 1
                continue
            fields[key] = val
            last_key = key
            i += 1
            continue
        if line == "Item" and fields:
            in_items = True
            j = i + 1
            for expect in ITEM_HDR[1:]:
                if j < n and lines[j] == expect:
                    j += 1
            i = j
            continue
        if in_items and fields:
            name_parts = [line]
            j = i + 1
            while j < n and not LIMIT_RE.match(lines[j]) and not lines[j].startswith("Time:"):
                if lines[j] in ITEM_HDR or _is_section(lines[j]):
                    break
                name_parts.append(lines[j])
                j += 1
                if len(name_parts) > 6:
                    break
            if j + 4 >= n or not LIMIT_RE.match(lines[j]):
                missing.append(f"細節 Item 缺上下限: {' '.join(name_parts)[:60]}")
                i = j
                in_items = False
                continue
            if len(name_parts) > 1:
                wrap += 1
            item = " ".join(name_parts)
            lower, value, upper, unit, status = lines[j : j + 5]
            if status not in VERDICTS:
                missing.append(f"細節 Status 不像 Pass/Fail: {item[:40]} -> {status}")
            items.append((item, lower, value, upper, unit, status))
            i = j + 5
            continue
        if fields and last_key and not in_items and not _is_section(line):
            prev = fields.get(last_key, "")
            fields[last_key] = f"{prev} {line}".strip() if prev else line
            wrap += 1
            i += 1
            continue
        i += 1
    flush()
    return wrap, details, missing[:20]


def _emit_csv(header: dict[str, str], modes: list[dict], details: list[dict]) -> str:
    buf = io.StringIO()
    buf.write("SourceKind, pdf\n")
    order = [
        "IMEI",
        "TestPlan",
        "TA Version",
        "RFA Version",
        "Start Time",
        "Stop Time",
        "Overall Result",
        "Number of TestCases",
        "Testcases Pass",
        "Testcases Fail",
        "Testcases Skip",
        "Test Station PC Name",
        "Run Test Mode",
        "3GPP Protocal Version",
        "3GPP Protocol Version",
        "Total Elapsed Time",
    ]
    seen = set()
    for key in order:
        if key in header:
            if key == "TA Version":
                buf.write(f"{key}: {header[key]}\n")
            else:
                buf.write(f"{key}, {header[key]}\n")
            seen.add(key)
    for key, val in header.items():
        if key not in seen:
            buf.write(f"{key}, {val}\n")
    w = csv.writer(buf, lineterminator="\n")
    for mode in modes:
        buf.write(f"Test Mode,{mode['raw']}\n")
        buf.write(
            "ID,Test Case Number,Test Case Name,Operating Band,PCell,Channel,BW,SCells,Verdict,time(s)\n"
        )
        for row in mode["rows"]:
            w.writerow(
                [
                    row["id"],
                    row["tcn"],
                    row["name"],
                    row["band"],
                    "",
                    row["channel"],
                    row["bw"],
                    "",
                    row["verdict"],
                    row["time"],
                ]
            )
    if details:
        w.writerow(DETAIL_HDR + [""])
        for d in details:
            w.writerow([d.get(k, "") for k in DETAIL_HDR] + [""])
    return buf.getvalue()
