"""Start / stop the local UXM HTML server."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PID_FILE = ROOT / "uxm_ui.pid"
DEFAULT_PORT = 8765


def _alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, int(pid))  # QUERY_LIMITED
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return kernel32.GetLastError() == 5  # access denied = still running
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _listener_pid(port: int) -> int | None:
    """PID listening on TCP port, or None."""
    if sys.platform != "win32":
        return None
    r = subprocess.run(
        ["netstat", "-ano", "-p", "tcp"],
        capture_output=True,
    )
    out = (r.stdout or b"").decode("utf-8", errors="replace")
    suffix = f":{int(port)}"
    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 5 or parts[-2].upper() != "LISTENING":
            continue
        if parts[1] == f"127.0.0.1{suffix}" or parts[1].endswith(suffix):
            try:
                return int(parts[-1])
            except ValueError:
                return None
    return None


def status() -> tuple[bool, int | None, int | None]:
    if PID_FILE.is_file():
        parts = PID_FILE.read_text(encoding="utf-8").strip().split()
        try:
            pid = int(parts[0])
            port = int(parts[1]) if len(parts) > 1 else DEFAULT_PORT
        except ValueError:
            PID_FILE.unlink(missing_ok=True)
        else:
            if _alive(pid):
                return True, pid, port
            PID_FILE.unlink(missing_ok=True)
    pid = _listener_pid(DEFAULT_PORT)
    if pid and _alive(pid):
        PID_FILE.write_text(f"{pid} {DEFAULT_PORT}\n", encoding="utf-8")
        return True, pid, DEFAULT_PORT
    return False, None, None


def write_pid(port: int) -> None:
    PID_FILE.write_text(f"{os.getpid()} {port}\n", encoding="utf-8")


def clear_pid() -> None:
    PID_FILE.unlink(missing_ok=True)


def start(port: int = DEFAULT_PORT, open_browser: bool = True) -> str:
    running, pid, running_port = status()
    if running:
        return f"介面已在跑（PID {pid}）http://127.0.0.1:{running_port}/"
    args = [sys.executable, "-m", "uxm_report", "ui", "--port", str(port)]
    if not open_browser:
        args.append("--no-browser")
    subprocess.Popen(args, cwd=str(ROOT))
    return f"正在啟動 http://127.0.0.1:{port}/"


def stop() -> str:
    running, pid, port = status()
    if not running or pid is None:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/IM", "python.exe", "/FI", "WINDOWTITLE eq UXM Report UI"],
                capture_output=True,
            )
        leftover = _listener_pid(DEFAULT_PORT)
        if leftover:
            subprocess.run(["taskkill", "/PID", str(leftover), "/F"], capture_output=True)
            clear_pid()
            return f"已關閉介面（PID {leftover}，port {DEFAULT_PORT}）。"
        clear_pid()
        return "介面沒有在跑。"
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
    else:
        os.kill(pid, 15)
    clear_pid()
    return f"已關閉介面（PID {pid}，port {port}）。"
