"""Local SQLite store: module -> project -> folder -> IMEI -> session + raw CSV."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .interpret import meaning_of, skip_note
from .parse import Session, bw_mhz, session_rat, ta_major
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
CREATE TABLE IF NOT EXISTS folders (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    name TEXT NOT NULL,
    UNIQUE(project_id, name)
);
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    folder_id INTEGER NOT NULL REFERENCES folders(id),
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
    source_kind TEXT NOT NULL DEFAULT 'csv',
    ta_major TEXT,
    parse_notes TEXT,
    UNIQUE(folder_id, dut_id, filename)
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
            ("source_kind", "TEXT NOT NULL DEFAULT 'csv'"),
            ("ta_major", "TEXT"),
            ("parse_notes", "TEXT"),
        ):
            if name not in sess_cols:
                self.conn.execute(f"ALTER TABLE sessions ADD COLUMN {name} {decl}")
        for sid, ver in self.conn.execute(
            "SELECT id, ta_version FROM sessions WHERE ta_major IS NULL OR ta_major=''"
        ):
            self.conn.execute(
                "UPDATE sessions SET ta_major=? WHERE id=?",
                (ta_major(ver or ""), sid),
            )
        self.conn.execute(
            """
            UPDATE sessions SET rat='NR'
            WHERE (rat IS NULL OR rat='')
              AND id IN (SELECT session_id FROM test_rows WHERE band LIKE 'NR_%')
            """
        )
        self._migrate_folders()
        self.conn.commit()

    def _migrate_folders(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY,
                project_id INTEGER NOT NULL REFERENCES projects(id),
                name TEXT NOT NULL,
                UNIQUE(project_id, name)
            )
            """
        )
        sess_cols = {r[1] for r in self.conn.execute("PRAGMA table_info(sessions)")}
        if "folder_id" in sess_cols:
            for pid, in self.conn.execute("SELECT id FROM projects"):
                self.conn.execute(
                    "INSERT OR IGNORE INTO folders(project_id, name) VALUES (?, 'UNKNOWN')",
                    (pid,),
                )
            return
        self.conn.commit()
        self.conn.execute("PRAGMA foreign_keys=OFF")
        self.conn.commit()
        self.conn.execute("DROP TABLE IF EXISTS sessions_new")
        for pid, in self.conn.execute("SELECT id FROM projects"):
            self.conn.execute(
                "INSERT OR IGNORE INTO folders(project_id, name) VALUES (?, 'UNKNOWN')",
                (pid,),
            )
        self.conn.execute(
            """
            CREATE TABLE sessions_new (
                id INTEGER PRIMARY KEY,
                project_id INTEGER NOT NULL REFERENCES projects(id),
                folder_id INTEGER NOT NULL REFERENCES folders(id),
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
                source_kind TEXT NOT NULL DEFAULT 'csv',
                ta_major TEXT,
                parse_notes TEXT,
                UNIQUE(folder_id, dut_id, filename)
            )
            """
        )
        old = [r[1] for r in self.conn.execute("PRAGMA table_info(sessions)")]
        copy = [
            c
            for c in (
                "id",
                "project_id",
                "dut_id",
                "filename",
                "start_time",
                "stop_time",
                "test_plan",
                "ta_version",
                "rfa_version",
                "overall_result",
                "raw_csv",
                "instrument",
                "report_kind",
                "rat",
                "imported_at",
                "source_kind",
                "ta_major",
                "parse_notes",
            )
            if c in old
        ]
        col_sql = ", ".join(copy)
        self.conn.execute(
            f"""
            INSERT INTO sessions_new (
                {col_sql}, folder_id
            )
            SELECT {col_sql},
                   (SELECT f.id FROM folders f
                    WHERE f.project_id = sessions.project_id AND f.name='UNKNOWN')
            FROM sessions
            """
        )
        self.conn.execute("DROP TABLE sessions")
        self.conn.execute("ALTER TABLE sessions_new RENAME TO sessions")
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_folder ON sessions(folder_id)"
        )
        self.conn.execute("PRAGMA foreign_keys=ON")

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

    def upsert_folder(self, project_id: int, name: str) -> int:
        name = (name or "").strip() or "UNKNOWN"
        self.conn.execute(
            "INSERT OR IGNORE INTO folders(project_id, name) VALUES (?, ?)",
            (project_id, name),
        )
        row = self.conn.execute(
            "SELECT id FROM folders WHERE project_id=? AND name=?",
            (project_id, name),
        ).fetchone()
        return int(row[0])

    def list_folders(self, module: str, project: str) -> list[str]:
        rows = self.conn.execute(
            """
            SELECT f.name FROM folders f
            JOIN projects p ON p.id=f.project_id
            JOIN modules m ON m.id=p.module_id
            WHERE m.model=? AND p.name=?
            ORDER BY f.name
            """,
            (module, project),
        ).fetchall()
        return [r[0] for r in rows]

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

    def import_session(
        self,
        session: Session,
        module_model: str,
        project: str,
        data_folder: str = "",
    ) -> int:
        module_id = self.upsert_module(module_model)
        project_id = self.upsert_project(module_id, project)
        folder_id = self.upsert_folder(project_id, data_folder)
        imei = session.header.get("IMEI") or "UNKNOWN"
        dut_id = self.upsert_dut(module_id, imei)
        if session.raw_text:
            raw = session.raw_text
        elif session.path.is_file() and session.path.suffix.lower() != ".pdf":
            raw = session.path.read_text(encoding="utf-8", errors="replace")
        else:
            raw = ""
        rat = session_rat(session)
        kind = session.source_kind or "csv"
        major = ta_major(session.header.get("TA Version") or "")
        notes = session.parse_notes or ""
        self.conn.execute(
            """
            INSERT INTO sessions(
                project_id, folder_id, dut_id, filename, start_time, stop_time, test_plan,
                ta_version, rfa_version, overall_result, raw_csv,
                instrument, report_kind, rat, imported_at,
                source_kind, ta_major, parse_notes
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now','localtime'),?,?,?)
            ON CONFLICT(folder_id, dut_id, filename) DO UPDATE SET
                start_time=excluded.start_time,
                stop_time=excluded.stop_time,
                test_plan=excluded.test_plan,
                ta_version=excluded.ta_version,
                rfa_version=excluded.rfa_version,
                overall_result=excluded.overall_result,
                raw_csv=excluded.raw_csv,
                instrument=excluded.instrument,
                report_kind=excluded.report_kind,
                rat=excluded.rat,
                source_kind=excluded.source_kind,
                ta_major=excluded.ta_major,
                parse_notes=excluded.parse_notes
            """,
            (
                project_id,
                folder_id,
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
                kind,
                major,
                notes,
            ),
        )
        row = self.conn.execute(
            "SELECT id FROM sessions WHERE folder_id=? AND dut_id=? AND filename=?",
            (folder_id, dut_id, session.filename),
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

    def delete_sessions(self, session_ids: list[int]) -> int:
        n = 0
        for sid in session_ids:
            if self.delete_session(int(sid)):
                n += 1
        return n

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
            SELECT s.id, m.model, p.name, COALESCE(f.name,'UNKNOWN'), d.imei, s.filename, s.start_time,
                   s.imported_at, s.overall_result, s.test_plan,
                   s.ta_version, s.ta_major, s.source_kind, s.parse_notes,
                   (SELECT COUNT(*) FROM test_rows t WHERE t.session_id=s.id) AS n_sum,
                   (SELECT COUNT(*) FROM detail_rows x WHERE x.session_id=s.id) AS n_det,
                   (SELECT COUNT(*) FROM detail_rows x WHERE x.session_id=s.id AND x.pf='Fail') AS n_fail
            FROM sessions s
            JOIN projects p ON p.id=s.project_id
            JOIN modules m ON m.id=p.module_id
            JOIN duts d ON d.id=s.dut_id
            LEFT JOIN folders f ON f.id=s.folder_id
            ORDER BY m.model, p.name, f.name, s.imported_at, s.start_time, s.filename
            """
        ).fetchall()
        keys = (
            "id",
            "module",
            "project",
            "data_folder",
            "imei",
            "filename",
            "start_time",
            "imported_at",
            "overall_result",
            "test_plan",
            "ta_version",
            "ta_major",
            "source_kind",
            "parse_notes",
            "n_sum",
            "n_det",
            "n_fail",
        )
        return [dict(zip(keys, r)) for r in rows]

    def session_header(self, session_id: int) -> dict | None:
        row = self.conn.execute(
            """
            SELECT s.id, m.model, p.name, COALESCE(f.name,'UNKNOWN'), d.imei, s.filename,
                   s.start_time, s.stop_time,
                   s.imported_at, s.test_plan, s.ta_version, s.rfa_version, s.overall_result,
                   s.ta_major, s.source_kind, s.parse_notes
            FROM sessions s
            JOIN projects p ON p.id=s.project_id
            JOIN modules m ON m.id=p.module_id
            JOIN duts d ON d.id=s.dut_id
            LEFT JOIN folders f ON f.id=s.folder_id
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
            "data_folder",
            "imei",
            "filename",
            "start_time",
            "stop_time",
            "imported_at",
            "test_plan",
            "ta_version",
            "rfa_version",
            "overall_result",
            "ta_major",
            "source_kind",
            "parse_notes",
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
        session_ids: list[int] | None = None,
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
        if session_ids is not None:
            if not session_ids:
                return []
            placeholders = ",".join("?" * len(session_ids))
            sql += f" AND s.id IN ({placeholders})"
            args.extend(int(x) for x in session_ids)
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
                   s.instrument, s.report_kind, s.rat, COALESCE(f.name,'UNKNOWN'),
                   GROUP_CONCAT(DISTINCT t.band) AS bands
            FROM sessions s
            JOIN projects p ON p.id=s.project_id
            JOIN modules m ON m.id=p.module_id
            JOIN duts dut ON dut.id=s.dut_id
            LEFT JOIN folders f ON f.id=s.folder_id
            LEFT JOIN test_rows t ON t.session_id=s.id
            WHERE m.model=? AND p.name=?
            GROUP BY s.id
            ORDER BY f.name, s.filename
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
            "data_folder",
            "bands",
        )
        return [dict(zip(keys, r)) for r in rows]

    def filter_sessions(
        self,
        module: str = "",
        project: str = "",
        data_folder: str = "",
        imei: str = "",
    ) -> list[dict]:
        sql = """
            SELECT s.id, m.model, p.name, COALESCE(f.name,'UNKNOWN'), dut.imei,
                   s.filename, s.start_time, s.overall_result, s.report_kind, s.rat,
                   GROUP_CONCAT(DISTINCT t.band) AS bands
            FROM sessions s
            JOIN projects p ON p.id=s.project_id
            JOIN modules m ON m.id=p.module_id
            JOIN duts dut ON dut.id=s.dut_id
            LEFT JOIN folders f ON f.id=s.folder_id
            LEFT JOIN test_rows t ON t.session_id=s.id
            WHERE 1=1
        """
        args: list = []
        if module:
            sql += " AND m.model=?"
            args.append(module)
        if project:
            sql += " AND p.name=?"
            args.append(project)
        if data_folder:
            sql += " AND f.name=?"
            args.append(data_folder)
        if imei:
            sql += " AND dut.imei=?"
            args.append(imei)
        sql += " GROUP BY s.id ORDER BY m.model, p.name, f.name, s.filename"
        rows = self.conn.execute(sql, args).fetchall()
        keys = (
            "id",
            "module",
            "project",
            "data_folder",
            "imei",
            "filename",
            "start_time",
            "overall_result",
            "report_kind",
            "rat",
            "bands",
        )
        return [dict(zip(keys, r)) for r in rows]

    def session_report_kinds(self, session_ids: list[int]) -> dict[int, str]:
        out: dict[int, str] = {}
        for sid in session_ids:
            row = self.conn.execute(
                "SELECT report_kind FROM sessions WHERE id=?", (int(sid),)
            ).fetchone()
            if row:
                out[int(sid)] = (row[0] or "uxm").lower()
        return out

    def chart_points(
        self,
        module: str,
        project: str,
        band_token: str,
        test_like: str,
        item: str,
        limit: int = 800,
        data_folder: str = "",
        imei: str = "",
    ) -> list[dict]:
        """One test + one item. Optional project/folder/IMEI. Cap 800 points."""
        sql = """
            SELECT s.id, s.filename, s.start_time, x.test_case, x.item, x.band,
                   x.arfcn, x.value, x.lower_limit, x.upper_limit, x.unit, x.pf
            FROM detail_rows x
            JOIN sessions s ON s.id = x.session_id
            JOIN projects p ON p.id = s.project_id
            JOIN modules m ON m.id = p.module_id
            LEFT JOIN folders f ON f.id = s.folder_id
            JOIN duts dut ON dut.id = s.dut_id
            WHERE m.model=?
              AND x.pf IN ('Pass', 'Fail')
              AND x.item=?
              AND x.test_case LIKE ?
              AND UPPER(REPLACE(REPLACE(x.band,'NR_',''),'n','N'))
                  = UPPER(REPLACE(REPLACE(?, 'NR_', ''), 'n', 'N'))
        """
        args: list = [module, item, test_like, band_token]
        if project:
            sql += " AND p.name=?"
            args.append(project)
        if data_folder:
            sql += " AND f.name=?"
            args.append(data_folder)
        if imei:
            sql += " AND dut.imei=?"
            args.append(imei)
        sql += " ORDER BY s.start_time, s.id LIMIT ?"
        args.append(limit)
        rows = self.conn.execute(sql, args).fetchall()
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

    def move_session_project(
        self,
        session_id: int,
        module: str,
        new_project: str,
        new_folder: str = "",
    ) -> None:
        name = (new_project or "").strip() or "UNKNOWN"
        row = self.conn.execute(
            """
            SELECT m.id, COALESCE(f.name,'UNKNOWN') FROM sessions s
            JOIN projects p ON p.id=s.project_id
            JOIN modules m ON m.id=p.module_id
            LEFT JOIN folders f ON f.id=s.folder_id
            WHERE s.id=? AND m.model=?
            """,
            (session_id, module),
        ).fetchone()
        if not row:
            raise ValueError("找不到這個 session 或不屬於該模組")
        project_id = self.upsert_project(int(row[0]), name)
        folder_name = (new_folder or "").strip() or row[1] or "UNKNOWN"
        folder_id = self.upsert_folder(project_id, folder_name)
        self.conn.execute(
            "UPDATE sessions SET project_id=?, folder_id=? WHERE id=?",
            (project_id, folder_id, session_id),
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
            dest_id = int(dst[0])
            src_id = int(src[0])
            for sid, fname in self.conn.execute(
                """
                SELECT s.id, COALESCE(f.name,'UNKNOWN')
                FROM sessions s
                LEFT JOIN folders f ON f.id=s.folder_id
                WHERE s.project_id=?
                """,
                (src_id,),
            ):
                fid = self.upsert_folder(dest_id, fname)
                self.conn.execute(
                    "UPDATE sessions SET project_id=?, folder_id=? WHERE id=?",
                    (dest_id, fid, sid),
                )
            self.conn.execute("DELETE FROM folders WHERE project_id=?", (src_id,))
            self.conn.execute("DELETE FROM projects WHERE id=?", (src_id,))
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
        self.conn.execute("DELETE FROM folders WHERE project_id=?", (pid,))
        self.conn.execute("DELETE FROM projects WHERE id=?", (pid,))
        self.conn.commit()
        return len(ids)


