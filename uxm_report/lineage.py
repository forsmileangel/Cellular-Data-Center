"""Link earlier Fail to a later retry Pass on the same DUT / band / test / LMH."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class RetryLink:
    superseded: bool
    later_filename: str = ""
    later_start: str = ""
    later_session_id: int = 0


def event_key(row: dict) -> tuple:
    lmh = row.get("lmh") or str(row.get("channel") or "")
    return (
        row.get("imei") or "",
        row.get("band") or "",
        row.get("test_name") or "",
        lmh,
    )


def build_links(events: list[dict]) -> dict[tuple, RetryLink]:
    """Map (session_id, test_name, lmh) -> retry outcome for Fail rows."""
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for ev in events:
        groups[event_key(ev)].append(ev)
    links: dict[tuple, RetryLink] = {}
    for items in groups.values():
        items.sort(key=lambda x: (x.get("start_time") or "", int(x.get("session_id") or 0)))
        for i, ev in enumerate(items):
            if (ev.get("verdict") or "").lower() != "fail":
                continue
            later = next(
                (x for x in items[i + 1 :] if (x.get("verdict") or "").lower() == "pass"),
                None,
            )
            lmh = ev.get("lmh") or str(ev.get("channel") or "")
            key = (int(ev["session_id"]), ev.get("test_name") or "", lmh)
            if later:
                links[key] = RetryLink(
                    True,
                    later.get("filename") or "",
                    later.get("start_time") or "",
                    int(later.get("session_id") or 0),
                )
            else:
                links[key] = RetryLink(False)
    return links


def latest_verdict(events: list[dict]) -> dict[tuple, dict]:
    """Latest row per (imei, band, test, lmh)."""
    best: dict[tuple, dict] = {}
    for ev in sorted(events, key=lambda x: (x.get("start_time") or "", int(x.get("session_id") or 0))):
        best[event_key(ev)] = ev
    return best
