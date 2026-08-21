"""Write the 4-sheet workbook via Excel COM, matching FN990B gold layout."""

from __future__ import annotations

from pathlib import Path

from .aggregate import WorkbookModel

# #B4C6E7 as Excel BGR
HEADER_FILL = 0xE7C6B4
HEADER_FONT = 0x333333
BORDER_COLOR = 0x404040  # 4210752

XL_CONTINUOUS = 1
XL_THIN = 2
XL_CENTER = -4108
XL_EDGE_LEFT = 7
XL_EDGE_TOP = 8
XL_EDGE_BOTTOM = 9
XL_EDGE_RIGHT = 10
XL_INSIDE_V = 11
XL_INSIDE_H = 12


def _apply_grid(rng) -> None:
    for edge in (
        XL_EDGE_LEFT,
        XL_EDGE_TOP,
        XL_EDGE_BOTTOM,
        XL_EDGE_RIGHT,
        XL_INSIDE_V,
        XL_INSIDE_H,
    ):
        border = rng.Borders(edge)
        border.LineStyle = XL_CONTINUOUS
        border.Weight = XL_THIN
        border.Color = BORDER_COLOR


def _put_values(ws, rows: list[list[object]]) -> tuple[int, int]:
    if not rows:
        return 0, 0
    ncols = max(len(r) for r in rows)
    padded = []
    for row in rows:
        padded.append(list(row) + [None] * (ncols - len(row)))
    ws.Range(ws.Cells(1, 1), ws.Cells(len(padded), ncols)).Value = padded
    return len(padded), ncols


def _style_font(rng) -> None:
    rng.Font.Name = "Calibri"
    rng.Font.Size = 12
    rng.Font.Color = HEADER_FONT


def write_xlsx(model: WorkbookModel, path: str | Path) -> Path:
    import win32com.client

    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    wb = excel.Workbooks.Add()
    while wb.Sheets.Count < 4:
        wb.Sheets.Add(After=wb.Sheets(wb.Sheets.Count))

    # --- Summary ---
    ws = wb.Sheets(1)
    ws.Name = "Summary"
    nrows, ncols = _put_values(ws, model.summary_rows)
    used = ws.Range(ws.Cells(1, 1), ws.Cells(nrows, ncols))
    _style_font(used)
    _apply_grid(used)
    ws.Columns(1).ColumnWidth = 48.36
    ws.Columns(2).ColumnWidth = 56.73
    ws.Columns(3).ColumnWidth = 6.0
    ws.Columns(4).ColumnWidth = 20.64
    ws.Columns(5).ColumnWidth = 5.64
    used.WrapText = False
    ws.Rows.RowHeight = 17

    # --- Overall ---
    ws = wb.Sheets(2)
    ws.Name = "Overall"
    # Widths first so wrap does not inflate row height against the default 8-wide column.
    ws.Columns(1).ColumnWidth = 7.27
    ws.Columns(2).ColumnWidth = 9.45
    ws.Columns(3).ColumnWidth = 6.0
    ws.Columns(4).ColumnWidth = 44.0
    ws.Columns(5).ColumnWidth = 6.27
    ws.Columns(6).ColumnWidth = 4.73
    nrows, ncols = _put_values(ws, model.overall_rows)
    used = ws.Range(ws.Cells(1, 1), ws.Cells(nrows, ncols))
    _style_font(used)
    _apply_grid(used)
    header = ws.Range(ws.Cells(1, 1), ws.Cells(1, ncols))
    header.Interior.Color = HEADER_FILL
    header.WrapText = False
    fail_col = ws.Range(ws.Cells(2, 4), ws.Cells(nrows, 4))
    fail_col.WrapText = True
    fail_col.VerticalAlignment = XL_CENTER
    ws.Rows(1).RowHeight = 17
    for r in range(2, nrows + 1):
        val = model.overall_rows[r - 1][3]
        lines = str(val).count("\n") + 1 if val else 1
        ws.Rows(r).RowHeight = 17 if lines == 1 else min(15.5 * lines, 93)

    # --- Data ---
    ws = wb.Sheets(3)
    ws.Name = "Data"
    ws.Columns(1).ColumnWidth = 48.36
    for c in range(2, max(len(r) for r in model.data_rows) + 1):
        ws.Columns(c).ColumnWidth = 9.36
    nrows, ncols = _put_values(ws, model.data_rows)
    used = ws.Range(ws.Cells(1, 1), ws.Cells(nrows, ncols))
    _style_font(used)
    _apply_grid(used)
    header = ws.Range(ws.Cells(1, 2), ws.Cells(1, ncols))
    header.WrapText = True
    header.VerticalAlignment = XL_CENTER
    ws.Rows(1).RowHeight = 62
    ws.Rows(2).RowHeight = 17
    ws.Rows(3).RowHeight = 17
    body = ws.Range(ws.Cells(4, 2), ws.Cells(nrows, ncols))
    body.WrapText = True
    body.VerticalAlignment = XL_CENTER
    for r in range(4, nrows + 1):
        ws.Rows(r).RowHeight = 46.5

    # --- File ---
    ws = wb.Sheets(4)
    ws.Name = "File"
    ws.Columns(1).ColumnWidth = 6.27
    ws.Columns(2).ColumnWidth = 79.09
    ws.Columns(3).ColumnWidth = 11.64
    ws.Columns(4).ColumnWidth = 14.82
    nrows, ncols = _put_values(ws, model.file_rows)
    used = ws.Range(ws.Cells(1, 1), ws.Cells(nrows, ncols))
    _style_font(used)
    _apply_grid(used)
    header = ws.Range(ws.Cells(1, 1), ws.Cells(1, ncols))
    header.Interior.Color = HEADER_FILL
    header.WrapText = False
    ws.Rows.RowHeight = 17
    ws.Rows(1).RowHeight = 17.5

    if path.exists():
        path.unlink()
    wb.SaveAs(str(path))
    wb.Close(False)
    excel.Quit()
    return path
