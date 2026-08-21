"""Turn spec notes into short paragraphs instead of one blob."""

from __future__ import annotations

from html import escape

_ENDS = "。！？"


def prose_html(text: str, css: str = "spec-prose") -> str:
    """Render RF notes as separate <p> (and <ul> for '- ' lines)."""
    if not text or not text.strip():
        return ""
    blocks = [b.strip() for b in text.replace("\r\n", "\n").split("\n\n") if b.strip()]
    parts: list[str] = []
    for block in blocks:
        lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
        if lines and all(ln.startswith("- ") for ln in lines):
            items = "".join(f"<li>{escape(ln[2:].strip())}</li>" for ln in lines)
            parts.append(f"<ul>{items}</ul>")
            continue
        for line in lines:
            for sent in split_sentences(line):
                parts.append(f"<p>{escape(sent)}</p>")
    if not parts:
        return ""
    return f'<div class="{css}">{"".join(parts)}</div>'


def split_sentences(text: str) -> list[str]:
    text = " ".join(text.split()).strip()
    if not text:
        return []
    out: list[str] = []
    buf: list[str] = []
    for ch in text:
        buf.append(ch)
        if ch in _ENDS:
            sent = "".join(buf).strip()
            if sent:
                out.append(sent)
            buf = []
    tail = "".join(buf).strip()
    if tail:
        out.append(tail)
    return out or [text]
