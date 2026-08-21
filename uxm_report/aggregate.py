"""Build Summary / Overall / Data / File tables from parsed UXM sessions."""

from __future__ import annotations

import re
from collections import OrderedDict
from dataclasses import dataclass, field

from .parse import Session, TestMode, bw_mhz, is_connection_test
from .spec import RANGES, classify_channels

RANGE_ORDER = {name: i for i, name in enumerate(RANGES)}


def labeled_name(name: str) -> str:
    return f" {name}" if not name.startswith(" ") else name


def duration_text(seconds: float) -> str:
    total = int(round(seconds))
    return f"{total // 60}m{total % 60}s"


def star_result(verdicts: list[str]) -> str:
    has_fail = any(v.lower() == "fail" for v in verdicts)
    has_skip = any(v.lower() == "skip" for v in verdicts)
    if has_fail and has_skip:
        return "Fail*"
    if has_fail:
        return "Fail"
    if has_skip:
        return "Pass*"
    if verdicts and all(v.lower() == "pass" for v in verdicts):
        return "Pass"
    if not verdicts:
        return ""
    return "Fail" if has_fail else "Pass"


def test_sort_key(name: str) -> tuple:
    m = re.match(r"^(\d+(?:\.\d+)*)\s+(.*)$", name.strip())
    if m:
        nums = tuple(int(x) for x in m.group(1).split("."))
        return (0, nums, m.group(2))
    return (1, (), name.strip())


@dataclass
class FileColumn:
    file_label: str
    filename: str
    session: Session
    mode: TestMode
    range_by_ch: dict[int, str]
    by_test: dict[str, dict[str, str]]  # test -> range -> verdict
    duration: str
    summary: str
    fail_items: str
    ta_version: str
    rfa_version: str
    note: str = ""


@dataclass
class WorkbookModel:
    module_model: str
    project: str
    imeis: list[str]
    test_names: list[str]
    columns: list[FileColumn]
    summary_rows: list[list[str | None]]
    overall_rows: list[list[str | None]]
    data_rows: list[list[str | None]]
    file_rows: list[list[str | None]]
    notes: list[str] = field(default_factory=list)


def _mode_ranges(mode: TestMode) -> dict[int, str]:
    channels = []
    for row in mode.rows:
        if row.channel not in channels:
            channels.append(row.channel)
    return classify_channels(channels, mode.rat, mode.band_id, bw_mhz(mode.bw))


def _build_column(index: int, session: Session, mode: TestMode) -> FileColumn:
    range_by_ch = _mode_ranges(mode)
    by_test: dict[str, dict[str, str]] = OrderedDict()
    verdicts: list[str] = []
    fail_bits: list[tuple[str, str]] = []
    for row in mode.rows:
        rng = range_by_ch.get(row.channel, "Mid")
        by_test.setdefault(row.test_name, {})
        prev = by_test[row.test_name].get(rng)
        if prev is None or (prev.lower() != "fail" and row.verdict.lower() == "fail"):
            by_test[row.test_name][rng] = row.verdict
        verdicts.append(row.verdict)
        if row.verdict.lower() == "fail":
            fail_bits.append((row.test_name, rng))
    fail_bits.sort(key=lambda x: (test_sort_key(x[0]), RANGE_ORDER.get(x[1], 9)))
    # unique (test, range)
    seen = set()
    fail_lines = []
    for name, rng in fail_bits:
        key = (name, rng)
        if key in seen:
            continue
        seen.add(key)
        fail_lines.append(f" {name}_{rng}")
    total = sum(r.time_s for r in mode.rows)
    note = ""
    if is_connection_test(session.filename, session.header.get("TestPlan", "")):
        note = "connection test"
    label = f"File {index} ({note})" if note else f"File {index}"
    return FileColumn(
        file_label=label,
        filename=session.filename,
        session=session,
        mode=mode,
        range_by_ch=range_by_ch,
        by_test=by_test,
        duration=duration_text(total),
        summary=star_result(verdicts),
        fail_items="\n".join(fail_lines),
        ta_version=session.header.get("TA Version", ""),
        rfa_version=session.header.get("RFA Version", ""),
        note=note,
    )


def _cell_ranges(range_verdicts: dict[str, str]) -> str | None:
    if not range_verdicts:
        return None
    parts = []
    for rng in RANGES:
        if rng in range_verdicts:
            parts.append(f"{rng}_{range_verdicts[rng]}")
    return "\n".join(parts) if parts else None


def build_report(
    sessions: list[Session],
    module_model: str,
    project: str = "UNKNOWN",
) -> WorkbookModel:
    if not module_model or not module_model.strip():
        raise ValueError("module_model is required")
    project = (project or "").strip() or "UNKNOWN"

    columns: list[FileColumn] = []
    file_no: dict[str, int] = {}
    for session in sessions:
        if not session.modes:
            continue
        key = session.filename
        if key not in file_no:
            file_no[key] = len(file_no) + 1
        idx = file_no[key]
        for mode in session.modes:
            columns.append(_build_column(idx, session, mode))

    test_names: list[str] = []
    seen = set()
    for col in columns:
        for name in col.by_test:
            if name not in seen:
                seen.add(name)
                test_names.append(name)
    test_names.sort(key=test_sort_key)

    imeis = []
    for session in sessions:
        imei = session.header.get("IMEI", "")
        if imei and imei not in imeis:
            imeis.append(imei)

    # File sheet: one row per source file, not per Test Mode / band.
    file_rows: list[list[str | None]] = [["Item", "Name", "TA Version", "RFA Version"]]
    seen_files: set[str] = set()
    for col in columns:
        if col.filename in seen_files:
            continue
        seen_files.add(col.filename)
        file_rows.append([col.file_label, col.filename, col.ta_version, col.rfa_version])

    # Overall
    overall_rows: list[list[str | None]] = [
        ["Band", "Bandwidth", "Result", "Fail Item", "File", "Note"]
    ]
    for col in columns:
        overall_rows.append(
            [
                col.mode.display_band,
                col.mode.bw,
                col.summary,
                col.fail_items or None,
                col.file_label,
                col.note or None,
            ]
        )

    # Data
    header = [None]
    for col in columns:
        header.append(f"{col.file_label}\n{col.mode.display_band}\n{col.mode.scs}\n{col.mode.bw}")
    data_rows: list[list[str | None]] = [header]
    data_rows.append(["Summary Result"] + [c.summary for c in columns])
    data_rows.append(["Total Duration(m:s)"] + [c.duration for c in columns])
    for name in test_names:
        row: list[str | None] = [labeled_name(name)]
        for col in columns:
            row.append(_cell_ranges(col.by_test.get(name, {})))
        data_rows.append(row)

    # Summary: identity rows then one row per test
    summary_rows: list[list[str | None]] = []
    proj_label = project if project and project not in {"UNKNOWN", "Report"} else project or "全部"
    imei_line = "/".join(imeis) if imeis else ""
    summary_rows.append([f"模組名稱：{module_model}", None, None, None, None])
    summary_rows.append([f"專案名稱：{proj_label}", None, None, None, None])
    summary_rows.append([f"IMEI：{imei_line}", None, None, None, None])
    summary_rows.append(["Test Case Name", "Band", "Result", "Fail iteams", "Notes"])
    notes: list[str] = []
    for name in test_names:
        bands: list[str] = []
        fail_bands: list[str] = []
        verdicts: list[str] = []
        for col in columns:
            rv = col.by_test.get(name)
            if not rv:
                continue
            if col.mode.display_band not in bands:
                bands.append(col.mode.display_band)
            verdicts.extend(rv.values())
            if any(v.lower() == "fail" for v in rv.values()):
                if col.mode.display_band not in fail_bands:
                    fail_bands.append(col.mode.display_band)
        result = star_result(verdicts)
        summary_rows.append(
            [
                labeled_name(name),
                "/".join(bands),
                result,
                "/".join(fail_bands) if fail_bands else None,
                None,
            ]
        )
        if "n7" in " ".join(bands).lower() or any(
            c.mode.band_id == "n7" and name in c.by_test for c in columns
        ):
            pass
    # Record known golden mismatch for n7 on FN990B Summary Band lists.
    if any(c.mode.band_id == "n7" for c in columns):
        notes.append(
            "Summary Band includes NR_n7 when that band ran the test; "
            "FN990B LabVIEW gold omits n7 from most Band cells."
        )

    return WorkbookModel(
        module_model=module_model.strip(),
        project=project,
        imeis=imeis,
        test_names=test_names,
        columns=columns,
        summary_rows=summary_rows,
        overall_rows=overall_rows,
        data_rows=data_rows,
        file_rows=file_rows,
        notes=notes,
    )
