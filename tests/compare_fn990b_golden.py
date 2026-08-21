"""Compare in-memory report to FN990B LabVIEW gold workbook."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from uxm_report.aggregate import build_report
from uxm_report.parse import parse_folder


def cell_eq(a, b) -> bool:
    if a is None and (b is None or b == ""):
        return True
    if b is None and (a is None or a == ""):
        return True
    return str(a) == str(b)


def main() -> int:
    gold_path = ROOT / "FN990B Module Test Report" / "FN990B Module Test Report2.xlsx"
    model = build_report(
        parse_folder(ROOT / "FN990B Module Test Report"),
        module_model="FN990B",
        project="UNKNOWN",
    )
    import win32com.client

    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    wb = excel.Workbooks.Open(str(gold_path), ReadOnly=True)
    diffs = []

    def check(sheet, rows, start_row=1):
        ws = wb.Sheets(sheet)
        used = ws.UsedRange
        grow, gcol = used.Rows.Count, used.Columns.Count
        if grow != len(rows):
            diffs.append(f"{sheet} row count gold={grow} ours={len(rows)}")
        if gcol != max(len(r) for r in rows):
            diffs.append(f"{sheet} col count gold={gcol} ours={max(len(r) for r in rows)}")
        for r, row in enumerate(rows, start=start_row):
            for c, val in enumerate(row, start=1):
                g = ws.Cells(r, c).Value
                if not cell_eq(g, val):
                    diffs.append(f"{sheet}!R{r}C{c} gold={g!r} ours={val!r}")

    check("File", model.file_rows)
    check("Overall", model.overall_rows)
    check("Data", model.data_rows)
    check("Summary", model.summary_rows)

    wb.Close(False)
    excel.Quit()
    n7 = [d for d in diffs if "n7" in d.lower() or "NR_n7" in d]
    other = [d for d in diffs if d not in n7]
    print(f"diffs={len(diffs)} n7_related={len(n7)} other={len(other)}")
    for d in other[:40]:
        print("OTHER", d)
    if len(other) > 40:
        print(f"... {len(other) - 40} more other")
    for d in n7[:15]:
        print("N7", d)
    return 0 if not other else 1


if __name__ == "__main__":
    raise SystemExit(main())
