"""Shared import + Excel build used by CLI and the local UI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .aggregate import WorkbookModel, build_report
from .excel_out import write_xlsx
from .parse import parse_selected
from .store import Store


@dataclass
class BuildResult:
    model: WorkbookModel
    output: Path
    csv_count: int


def run_ingest(
    folder: str | Path,
    module: str,
    project: str = "",
    files: list[str] | None = None,
    db: str | Path | None = None,
) -> tuple[int, int]:
    module = (module or "").strip()
    if not module:
        raise ValueError("模組型號必填")
    project = (project or "").strip() or "UNKNOWN"
    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError(f"找不到資料夾: {folder}")
    sessions = parse_selected(folder, files)
    if not sessions:
        raise ValueError("沒有選到任何 CSV")
    root = Path(__file__).resolve().parents[1]
    db_path = Path(db) if db else root / "uxm.db"
    store = Store(db_path)
    details = 0
    try:
        for session in sessions:
            store.import_session(session, module, project)
            details += len(session.details)
    finally:
        store.close()
    return len(sessions), details


def run_build(
    folder: str | Path,
    module: str,
    project: str = "",
    db: str | Path | None = None,
    output: str | Path | None = None,
    files: list[str] | None = None,
) -> BuildResult:
    module = (module or "").strip()
    if not module:
        raise ValueError("模組型號必填")
    project = (project or "").strip() or "UNKNOWN"
    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError(f"找不到資料夾: {folder}")
    sessions = parse_selected(folder, files)
    if not sessions:
        raise ValueError("沒有選到任何 CSV")

    root = Path(__file__).resolve().parents[1]
    db_path = Path(db) if db else root / "uxm.db"
    store = Store(db_path)
    try:
        for session in sessions:
            store.import_session(session, module, project)
    finally:
        store.close()

    model = build_report(sessions, module_model=module, project=project)
    if output:
        out = Path(output)
    else:
        out = root / "out" / f"{module} Module Test Report.xlsx"
    write_xlsx(model, out)
    return BuildResult(model=model, output=out, csv_count=len(sessions))


def run_report_from_db(
    module: str,
    project: str,
    session_ids: list[int],
    bands: list[str] | None = None,
    db: str | Path | None = None,
    output: str | Path | None = None,
) -> BuildResult:
    from .parse import keep_bands, parse_text

    module = (module or "").strip()
    if not module:
        raise ValueError("模組型號必填")
    if not session_ids:
        raise ValueError("請選擇要出報告的檔案或 band")
    root = Path(__file__).resolve().parents[1]
    db_path = Path(db) if db else root / "uxm.db"
    store = Store(db_path)
    try:
        pairs = store.load_raw_sessions(session_ids)
    finally:
        store.close()
    if not pairs:
        raise ValueError("資料庫裡找不到這些 session 的 raw CSV")
    want = set(bands or [])
    sessions = []
    for filename, raw in pairs:
        if not raw:
            raise ValueError(f"{filename} 沒有 raw CSV，請重新匯入")
        session = parse_text(raw, filename)
        if want:
            keep_bands(session, want)
        if session.modes:
            sessions.append(session)
    if not sessions:
        raise ValueError("選到的 band 在這些檔裡沒有資料")
    model = build_report(sessions, module_model=module, project=project or "UNKNOWN")
    if output:
        out = Path(output)
    else:
        out = root / "out" / f"{module} {project or 'UNKNOWN'} UXM Report.xlsx"
    write_xlsx(model, out)
    return BuildResult(model=model, output=out, csv_count=len(sessions))
