"""CLI: import UXM CSVs, store raw data, export Excel, or open the local UI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .pipeline import run_build, run_ingest
from .store import Store


def cmd_set_project(args: argparse.Namespace) -> int:
    store = Store(args.db)
    try:
        module_id = store.upsert_module(args.module)
        old = args.source or "UNKNOWN"
        row = store.conn.execute(
            "SELECT id FROM projects WHERE module_id=? AND name=?",
            (module_id, old),
        ).fetchone()
        if not row:
            print(f"error: no project {old!r} under module {args.module}", file=sys.stderr)
            return 2
        store.set_project_name(int(row[0]), args.to)
        store.conn.commit()
        print(f"renamed project {old!r} -> {args.to!r} for module {args.module}")
    finally:
        store.close()
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    try:
        names = [x for x in (args.files or "").split(",") if x.strip()]
        result = run_build(
            args.input,
            args.module,
            args.project,
            db=args.db,
            output=args.output or None,
            files=names or None,
        )
    except (ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    model = result.model
    print(f"module={model.module_model} project={model.project}")
    print(f"sessions={result.csv_count} files={len(model.columns)} tests={len(model.test_names)}")
    print(f"xlsx={result.output.resolve()}")
    for note in model.notes:
        print(f"note: {note}")
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    module = (args.module or "").strip()
    if not module:
        print("error: --module is required", file=sys.stderr)
        return 2
    project = (args.project or "").strip() or "UNKNOWN"
    names = [x.strip() for x in (args.files or "").split(",") if x.strip()]
    try:
        n_sess, n_det = run_ingest(
            args.input, module, project, files=names or None, db=args.db
        )
    except (ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"ingested sessions={n_sess} detail_rows={n_det} db={args.db}")
    return 0


def cmd_ui(args: argparse.Namespace) -> int:
    from .web import serve

    serve(host=args.host, port=args.port, open_browser=not args.no_browser)
    return 0


def cmd_start(args: argparse.Namespace) -> int:
    from .serverctl import start

    print(start(port=args.port, open_browser=not args.no_browser))
    return 0


def cmd_stop(args: argparse.Namespace) -> int:
    from .serverctl import stop

    print(stop())
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    from .serverctl import status

    running, pid, port = status()
    if running:
        print(f"開著 PID {pid}  http://127.0.0.1:{port}/")
        return 0
    print("關著")
    return 1


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="UXM report builder")
    sub = parser.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="Parse CSVs, store raw data, write Excel")
    b.add_argument("--input", required=True, help="Folder of UXM CSV files")
    b.add_argument("--module", required=True, help="Module model (required)")
    b.add_argument("--project", default="", help="Project name; default UNKNOWN")
    b.add_argument("--output", default="", help="Output xlsx path")
    b.add_argument("--db", default=str(root / "uxm.db"), help="SQLite path")
    b.add_argument("--files", default="", help="Comma-separated CSV names; default all")
    b.set_defaults(func=cmd_build)

    s = sub.add_parser("set-project", help="Fill or rename a project later (e.g. UNKNOWN -> real name)")
    s.add_argument("--module", required=True)
    s.add_argument("--to", required=True, help="New project name")
    s.add_argument("--source", default="UNKNOWN", help="Current project name")
    s.add_argument("--db", default=str(root / "uxm.db"))
    s.set_defaults(func=cmd_set_project)

    ing = sub.add_parser("ingest", help="Parse CSVs into SQLite only (no Excel)")
    ing.add_argument("--input", required=True)
    ing.add_argument("--module", required=True)
    ing.add_argument("--project", default="")
    ing.add_argument("--db", default=str(root / "uxm.db"))
    ing.add_argument("--files", default="", help="Comma-separated CSV names; default all")
    ing.set_defaults(func=cmd_ingest)

    u = sub.add_parser("ui", help="Open the local import UI in a browser")
    u.add_argument("--host", default="127.0.0.1")
    u.add_argument("--port", type=int, default=8765)
    u.add_argument("--no-browser", action="store_true")
    u.set_defaults(func=cmd_ui)

    st = sub.add_parser("start", help="Start the UI in the background")
    st.add_argument("--port", type=int, default=8765)
    st.add_argument("--no-browser", action="store_true")
    st.set_defaults(func=cmd_start)

    sp = sub.add_parser("stop", help="Stop the UI")
    sp.set_defaults(func=cmd_stop)

    ss = sub.add_parser("status", help="Show whether the UI is running")
    ss.set_defaults(func=cmd_status)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
