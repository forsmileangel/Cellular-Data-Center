"""Local SQLite store: module -> project -> IMEI -> session + raw CSV."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .interpret import meaning_of, skip_note
from .parse import Session, bw_mhz, session_rat
from .spec import classify_channels

SCHEMA = """
CREATE TABLE IF NOT EXISTS modules (
    id INTEGER PRIMARY KEY,
    model TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    module_id INTEGER NOT NULL REFERENCES modules(id),
    name TEXT NOT NULL,
    UNIQUE(module_id, name)
);
CREATE TABLE IF NOT EXISTS duts (
    id INTEGER PRIMARY KEY,
    module_id INTEGER NOT NULL REFERENCES modules(id),
    imei TEXT NOT NULL,
    UNIQUE(module_id, imei)
);
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    dut_id INTEGER NOT NULL REFERENCES duts(id),
    filename TEXT NOT NULL,
    start_time TEXT,
    stop_time TEXT,
    test_plan TEXT,
    ta_version TEXT,
    rfa_version TEXT,
    overall_result TEXT,
    raw_csv TEXT NOT NULL,
    instrument TEXT NOT NULL DEFAULT 'uxm',
    report_kind TEXT NOT NULL DEFAULT 'uxm',
    rat TEXT,
    imported_at TEXT,
    UNIQUE(project_id, dut_id, filename)
);
CREATE TABLE IF NOT EXISTS test_rows (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    test_name TEXT NOT NULL,
    band TEXT NOT NULL,
    scs TEXT,
    bw TEXT,
    channel INTEGER,
    verdict TEXT,
    time_s REAL,
    lmh TEXT,
    spec_ref TEXT,
    interpret_note TEXT
);
CREATE TABLE IF NOT EXISTS detail_rows (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    time TEXT,
    system TEXT,
    test_case TEXT,
    description TEXT,
    band TEXT,
    bandwidth TEXT,
    scs TEXT,
    arfcn TEXT,
    freq_mhz TEXT,
    expected_power TEXT,
    ofdm TEXT,
    modulation TEXT,
    rb TEXT,
    condition TEXT,
    item TEXT,
    lower_limit TEXT,
    value TEXT,
    upper_limit TEXT,
    unit TEXT,
    pf TEXT
);
CREATE INDEX IF NOT EXISTS idx_detail_session ON detail_rows(session_id);
CREATE INDEX IF NOT EXISTS idx_detail_pf ON detail_rows(session_id, pf);
"""


class Store:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self._migrate()

    def _migrate(self) -> None:
        test_cols = {r[1] for r in self.conn.execute("PRAGMA table_info(test_rows)")}
        for name, decl in (
            ("lmh", "TEXT"),
            ("spec_ref", "TEXT"),
            ("interpret_note", "TEXT"),
        ):
            if name not in test_cols:
                self.conn.execute(f"ALTER TABLE test_rows ADD COLUMN {name} {decl}")
        sess_cols = {r[1] for r in self.conn.execute("PRAGMA table_info(sessions)")}
        for name, decl in (
            ("instrument", "TEXT NOT NULL DEFAULT 'uxm'"),
            ("report_kind", "TEXT NOT NULL DEFAULT 'uxm'"),
            ("rat", "TEXT"),
            ("imported_at", "TEXT"),
        ):
            if name not in sess_cols:
                self.conn.execute(f"ALTER TABLE sessions ADD COLUMN {name} {decl}")
        self.conn.execute(
            """
            UPDATE sessions SET rat='NR'
            WHERE (rat IS NULL OR rat='')
              AND id IN (SELECT session_id FROM test_rows WHERE band LIKE 'NR_%')
            """
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def upsert_module(self, model: str) -> int:
        self.conn.execute("INSERT OR IGNORE INTO modules(model) VALUES (?)", (model,))
        row = self.conn.execute("SELECT id FROM modules WHERE model=?", (model,)).fetchone()
        return int(row[0])

    def upsert_project(self, module_id: int, name: str) -> int:
        self.conn.execute(
            "INSERT OR IGNORE INTO projects(module_id, name) VALUES (?, ?)",
            (module_id, name),
        )
        row = self.conn.execute(
            "SELECT id FROM projects WHERE module_id=? AND name=?",
            (module_id, name),
        ).fetchone()
        return int(row[0])

    def set_project_name(self, project_id: int, name: str) -> None:
        self.conn.execute("UPDATE projects SET name=? WHERE id=?", (name, project_id))

    def upsert_dut(self, module_id: int, imei: str) -> int:
        self.conn.execute(
            "INSERT OR IGNORE INTO duts(module_id, imei) VALUES (?, ?)",
            (module_id, imei),
        )
        row = self.conn.execute(
            "SELECT id FROM duts WHERE module_id=? AND imei=?",
            (module_id, imei),
        ).fetchone()
        return int(row[0])

    def import_session(self, session: Session, module_model: str, project: str) -> int:
        module_id = self.upsert_module(module_model)
        project_id = self.upsert_project(module_id, project)
        imei = session.header.get("IMEI") or "UNKNOWN"
        dut_id = self.upsert_dut(module_id, imei)
        if session.path.is_file():
            raw = session.path.read_text(encoding="utf-8", errors="replace")
        else:
            raw = "\n".join([])
        rat = session_rat(session)
        self.conn.execute(
            """
            INSERT INTO sessions(
                project_id, dut_id, filename, start_time, stop_time, test_plan,
                ta_version, rfa_version, overall_result, raw_csv,
                instrument, report_kind, rat, imported_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now','localtime'))
            ON CONFLICT(project_id, dut_id, filename) DO UPDATE SET
                start_time=excluded.start_time,
                stop_time=excluded.stop_time,
                test_plan=excluded.test_plan,
                ta_version=excluded.ta_version,
                rfa_version=excluded.rfa_version,
                overall_result=excluded.overall_result,
                raw_csv=excluded.raw_csv,
                instrument=excluded.instrument,
                report_kind=excluded.report_kind,
                rat=excluded.rat
            """,
            (
                project_id,
                dut_id,
                session.filename,
                session.header.get("Start Time"),
                session.header.get("Stop Time"),
                session.header.get("TestPlan"),
                session.header.get("TA Version"),
                session.header.get("RFA Version"),
                session.header.get("Overall Result"),
                raw,
                "uxm",
                "uxm",
                rat,
            ),
        )
        row = self.conn.execute(
            "SELECT id FROM sessions WHERE project_id=? AND dut_id=? AND filename=?",
            (project_id, dut_id, session.filename),
        ).fetchone()
        session_id = int(row[0])
        self.conn.execute("DELETE FROM test_rows WHERE session_id=?", (session_id,))
        self.conn.execute("DELETE FROM detail_rows WHERE session_id=?", (session_id,))
        for mode in session.modes:
            try:
                chans = []
                for tr in mode.rows:
                    if tr.channel not in chans:
                        chans.append(tr.channel)
                lmh_map = classify_channels(chans, mode.rat, mode.band_id, bw_mhz(mode.bw))
            except Exception:
                lmh_map = {}
            for tr in mode.rows:
                meaning = meaning_of(tr.test_name)
                note = skip_note(tr.test_name, tr.verdict) or meaning.note
                self.conn.execute(
                    """
                    INSERT INTO test_rows(
                        session_id, test_name, band, scs, bw, channel, verdict, time_s,
                        lmh, spec_ref, interpret_note
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        session_id,
                        tr.test_name,
                        mode.display_band,
                        mode.scs,
                        mode.bw,
                        tr.channel,
                        tr.verdict,
                        tr.time_s,
                        lmh_map.get(tr.channel, ""),
                        meaning.spec,
                        note,
                    ),
                )
        for d in session.details:
            self.conn.execute(
                """
                INSERT INTO detail_rows(
                    session_id, time, system, test_case, description, band, bandwidth,
                    scs, arfcn, freq_mhz, expected_power, ofdm, modulation, rb,
                    condition, item, lower_limit, value, upper_limit, unit, pf
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    session_id,
                    d.time,
                    d.system,
                    d.test_case,
                    d.description,
                    d.band,
                    d.bandwidth,
                    d.scs,
                    d.arfcn,
                    d.freq_mhz,
                    d.expected_power,
                    d.ofdm,
                    d.modulation,
                    d.rb,
                    d.condition,
                    d.item,
                    d.lower,
                    d.value,
                    d.upper,
                    d.unit,
                    d.pf,
                ),
            )
        self.conn.commit()
        return session_id

    def delete_session(self, session_id: int) -> bool:
        self.conn.execute("DELETE FROM detail_rows WHERE session_id=?", (session_id,))
        self.conn.execute("DELETE FROM test_rows WHERE session_id=?", (session_id,))
        cur = self.conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def lineage_events(self, module: str | None = None) -> list[dict]:
        sql = """
            SELECT s.id AS session_id, s.filename, s.start_time, dut.imei,
                   t.test_name, t.band, t.lmh, t.channel, t.verdict
            FROM test_rows t
            JOIN sessions s ON s.id = t.session_id
            JOIN duts dut ON dut.id = s.dut_id
            JOIN projects p ON p.id = s.project_id
            JOIN modules m ON m.id = p.module_id
        """
        args: list = []
        if module:
            sql += " WHERE m.model=?"
            args.append(module)
        sql += " ORDER BY s.start_time, s.id"
        rows = self.conn.execute(sql, args).fetchall()
        keys = (
            "session_id",
            "filename",
            "start_time",
            "imei",
            "test_name",
            "band",
            "lmh",
            "channel",
            "verdict",
        )
        return [dict(zip(keys, r)) for r in rows]

    def list_sessions(self) -> list[dict]:
        rows = self.conn.execute(
            """
            SELECT s.id, m.model, p.name, d.imei, s.filename, s.start_time,
                   s.imported_at, s.overall_result, s.test_plan,
                   (SELECT COUNT(*) FROM test_rows t WHERE t.session_id=s.id) AS n_sum,
                   (SELECT COUNT(*) FROM detail_rows x WHERE x.session_id=s.id) AS n_det,
                   (SELECT COUNT(*) FROM detail_rows x WHERE x.session_id=s.id AND x.pf='Fail') AS n_fail
            FROM sessions s
            JOIN projects p ON p.id=s.project_id
            JOIN modules m ON m.id=p.module_id
            JOIN duts d ON d.id=s.dut_id
            ORDER BY m.model, p.name, s.imported_at, s.start_time, s.filename
            """
        ).fetchall()
        keys = (
            "id",
            "module",
            "project",
            "imei",
            "filename",
            "start_time",
            "imported_at",
            "overall_result",
            "test_plan",
            "n_sum",
            "n_det",
            "n_fail",
        )
        return [dict(zip(keys, r)) for r in rows]

    def session_header(self, session_id: int) -> dict | None:
        row = self.conn.execute(
            """
            SELECT s.id, m.model, p.name, d.imei, s.filename, s.start_time, s.stop_time,
                   s.imported_at, s.test_plan, s.ta_version, s.rfa_version, s.overall_result
            FROM sessions s
            JOIN projects p ON p.id=s.project_id
            JOIN modules m ON m.id=p.module_id
            JOIN duts d ON d.id=s.dut_id
            WHERE s.id=?
            """,
            (session_id,),
        ).fetchone()
        if not row:
            return None
        keys = (
            "id",
            "module",
            "project",
            "imei",
            "filename",
            "start_time",
            "stop_time",
            "imported_at",
            "test_plan",
            "ta_version",
            "rfa_version",
            "overall_result",
        )
        return dict(zip(keys, row))

    def session_tests(self, session_id: int) -> list[dict]:
        rows = self.conn.execute(
            """
            SELECT test_name, band, scs, bw, channel, lmh, verdict, time_s, spec_ref, interpret_note
            FROM test_rows WHERE session_id=? ORDER BY id
            """,
            (session_id,),
        ).fetchall()
        keys = (
            "test_name",
            "band",
            "scs",
            "bw",
            "channel",
            "lmh",
            "verdict",
            "time_s",
            "spec_ref",
            "interpret_note",
        )
        return [dict(zip(keys, r)) for r in rows]

    def session_details(
        self,
        session_id: int,
        pf: str | None = None,
        test_case: str | None = None,
        limit: int = 300,
    ) -> list[dict]:
        sql = """
            SELECT time, test_case, band, bandwidth, scs, arfcn, freq_mhz, item,
                   condition, lower_limit, value, upper_limit, unit, pf, modulation
            FROM detail_rows WHERE session_id=?
        """
        args: list = [session_id]
        if pf:
            sql += " AND pf=?"
            args.append(pf)
        if test_case:
            sql += " AND test_case LIKE ?"
            args.append(f"%{test_case}%")
        sql += " ORDER BY id LIMIT ?"
        args.append(limit)
        rows = self.conn.execute(sql, args).fetchall()
        keys = (
            "time",
            "test_case",
            "band",
            "bandwidth",
            "scs",
            "arfcn",
            "freq_mhz",
            "item",
            "condition",
            "lower_limit",
            "value",
            "upper_limit",
            "unit",
            "pf",
            "modulation",
        )
        return [dict(zip(keys, r)) for r in rows]

    def measure_rows(
        self,
        session_id: int | None = None,
        module: str | None = None,
    ) -> list[dict]:
        sql = """
            SELECT s.id AS session_id, s.filename, m.model, d.imei,
                   x.test_case, x.band, x.item, x.condition,
                   x.lower_limit, x.value, x.upper_limit, x.unit, x.pf, x.arfcn
            FROM detail_rows x
            JOIN sessions s ON s.id = x.session_id
            JOIN duts d ON d.id = s.dut_id
            JOIN projects p ON p.id = s.project_id
            JOIN modules m ON m.id = p.module_id
            WHERE x.pf IN ('Pass', 'Fail')
        """
        args: list = []
        if session_id:
            sql += " AND s.id=?"
            args.append(session_id)
        if module:
            sql += " AND m.model=?"
            args.append(module)
        rows = self.conn.execute(sql, args).fetchall()
        keys = (
            "session_id",
            "filename",
            "model",
            "imei",
            "test_case",
            "band",
            "item",
            "condition",
            "lower_limit",
            "value",
            "upper_limit",
            "unit",
            "pf",
            "arfcn",
        )
        return [dict(zip(keys, r)) for r in rows]

    def list_modules(self) -> list[dict]:
        rows = self.conn.execute(
            """
            SELECT m.model,
                   COUNT(DISTINCT p.id),
                   COUNT(DISTINCT d.imei),
                   COUNT(s.id)
            FROM modules m
            LEFT JOIN projects p ON p.module_id=m.id
            LEFT JOIN duts d ON d.module_id=m.id
            LEFT JOIN sessions s ON s.project_id=p.id
            GROUP BY m.id, m.model
            ORDER BY m.model
            """
        ).fetchall()
        return [
            {"model": r[0], "projects": r[1], "duts": r[2], "sessions": r[3]}
            for r in rows
        ]

    def clause_stats(self, module: str, project: str) -> list[dict]:
        """Summary-row counts by test_name + band + verdict. Not detail_rows."""
        rows = self.conn.execute(
            """
            SELECT t.test_name, t.band, t.verdict, COUNT(*)
            FROM test_rows t
            JOIN sessions s ON s.id=t.session_id
            JOIN projects p ON p.id=s.project_id
            JOIN modules m ON m.id=p.module_id
            WHERE m.model=? AND p.name=?
            GROUP BY t.test_name, t.band, t.verdict
            """,
            (module, project),
        ).fetchall()
        return [
            {"test_name": r[0], "band": r[1], "verdict": r[2], "n": r[3]}
            for r in rows
        ]

    def list_projects(self, module: str) -> list[dict]:
        rows = self.conn.execute(
            """
            SELECT p.name, COUNT(s.id)
            FROM projects p
            JOIN modules m ON m.id=p.module_id
            LEFT JOIN sessions s ON s.project_id=p.id
            WHERE m.model=?
            GROUP BY p.id, p.name
            ORDER BY p.name
            """,
            (module,),
        ).fetchall()
        return [{"name": r[0], "sessions": r[1]} for r in rows]

    def project_sessions(self, module: str, project: str) -> list[dict]:
        rows = self.conn.execute(
            """
            SELECT s.id, s.filename, dut.imei, s.start_time, s.overall_result,
                   s.instrument, s.report_kind, s.rat,
                   GROUP_CONCAT(DISTINCT t.band) AS bands
            FROM sessions s
            JOIN projects p ON p.id=s.project_id
            JOIN modules m ON m.id=p.module_id
            JOIN duts dut ON dut.id=s.dut_id
            LEFT JOIN test_rows t ON t.session_id=s.id
            WHERE m.model=? AND p.name=?
            GROUP BY s.id
            ORDER BY s.filename
            """,
            (module, project),
        ).fetchall()
        keys = (
            "id",
            "filename",
            "imei",
            "start_time",
            "overall_result",
            "instrument",
            "report_kind",
            "rat",
            "bands",
        )
        return [dict(zip(keys, r)) for r in rows]

    def chart_points(
        self,
        module: str,
        project: str,
        band_token: str,
        test_like: str,
        item: str,
        limit: int = 800,
    ) -> list[dict]:
        """One test + one item for one project band. Cap rows so HTML stays small."""
        rows = self.conn.execute(
            """
            SELECT s.id, s.filename, s.start_time, x.test_case, x.item, x.band,
                   x.arfcn, x.value, x.lower_limit, x.upper_limit, x.unit, x.pf
            FROM detail_rows x
            JOIN sessions s ON s.id = x.session_id
            JOIN projects p ON p.id = s.project_id
            JOIN modules m ON m.id = p.module_id
            WHERE m.model=? AND p.name=?
              AND x.pf IN ('Pass', 'Fail')
              AND x.item=?
              AND x.test_case LIKE ?
              AND UPPER(REPLACE(REPLACE(x.band,'NR_',''),'n','N'))
                  = UPPER(REPLACE(REPLACE(?, 'NR_', ''), 'n', 'N'))
            ORDER BY s.start_time, s.id
            LIMIT ?
            """,
            (module, project, item, test_like, band_token, limit),
        ).fetchall()
        keys = (
            "session_id",
            "filename",
            "start_time",
            "test_case",
            "item",
            "band",
            "arfcn",
            "value",
            "lower_limit",
            "upper_limit",
            "unit",
            "pf",
        )
        return [dict(zip(keys, r)) for r in rows]

    def load_raw_sessions(self, session_ids: list[int]) -> list[tuple[str, str]]:
        """Return (filename, raw_csv) in given id order."""
        out = []
        for sid in session_ids:
            row = self.conn.execute(
                "SELECT filename, raw_csv FROM sessions WHERE id=?",
                (sid,),
            ).fetchone()
            if row:
                out.append((row[0], row[1]))
        return out

    def move_session_project(self, session_id: int, module: str, new_project: str) -> None:
        name = (new_project or "").strip() or "UNKNOWN"
        row = self.conn.execute(
            """
            SELECT m.id FROM sessions s
            JOIN projects p ON p.id=s.project_id
            JOIN modules m ON m.id=p.module_id
            WHERE s.id=? AND m.model=?
            """,
            (session_id, module),
        ).fetchone()
        if not row:
            raise ValueError("找不到這個 session 或不屬於該模組")
        project_id = self.upsert_project(int(row[0]), name)
        self.conn.execute(
            "UPDATE sessions SET project_id=? WHERE id=?",
            (project_id, session_id),
        )
        self.conn.commit()

    def rename_project(self, module: str, old: str, new: str) -> None:
        new = (new or "").strip()
        if not new:
            raise ValueError("新專案名不可空白")
        module_id = self.conn.execute(
            "SELECT id FROM modules WHERE model=?", (module,)
        ).fetchone()
        if not module_id:
            raise ValueError("找不到模組")
        mid = int(module_id[0])
        src = self.conn.execute(
            "SELECT id FROM projects WHERE module_id=? AND name=?",
            (mid, old),
        ).fetchone()
        if not src:
            raise ValueError(f"找不到專案 {old}")
        dst = self.conn.execute(
            "SELECT id FROM projects WHERE module_id=? AND name=?",
            (mid, new),
        ).fetchone()
        if dst:
            self.conn.execute(
                "UPDATE sessions SET project_id=? WHERE project_id=?",
                (int(dst[0]), int(src[0])),
            )
            self.conn.execute("DELETE FROM projects WHERE id=?", (int(src[0]),))
        else:
            self.conn.execute(
                "UPDATE projects SET name=? WHERE id=?",
                (new, int(src[0])),
            )
        self.conn.commit()

    def delete_project(self, module: str, name: str) -> int:
        """Delete a project and every session under it. Returns deleted session count."""
        row = self.conn.execute(
            """
            SELECT p.id FROM projects p
            JOIN modules m ON m.id=p.module_id
            WHERE m.model=? AND p.name=?
            """,
            (module, name),
        ).fetchone()
        if not row:
            raise ValueError(f"找不到專案 {name}")
        pid = int(row[0])
        ids = [
            int(r[0])
            for r in self.conn.execute(
                "SELECT id FROM sessions WHERE project_id=?", (pid,)
            )
        ]
        for sid in ids:
            self.conn.execute("DELETE FROM detail_rows WHERE session_id=?", (sid,))
            self.conn.execute("DELETE FROM test_rows WHERE session_id=?", (sid,))
        self.conn.execute("DELETE FROM sessions WHERE project_id=?", (pid,))
        self.conn.execute("DELETE FROM projects WHERE id=?", (pid,))
        self.conn.commit()
        return len(ids)


