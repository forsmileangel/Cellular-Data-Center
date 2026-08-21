"""Clickable term notes: overlay, close with X / Esc / outside click."""

from __future__ import annotations

from html import escape

from .prose import prose_html


def gloss_term(gid: str, label: str) -> str:
    return (
        f'<button type="button" class="gloss-open" data-gloss="{escape(gid)}">'
        f"{escape(label)}</button>"
    )


def gloss_panel(gid: str, title: str, body: str) -> str:
    return (
        f'<div id="gloss-{escape(gid)}" class="gloss-src" hidden '
        f'data-title="{escape(title)}">{body}</div>'
    )


def gloss_note(gid: str, title: str, text: str) -> str:
    return gloss_panel(gid, title, prose_html(text, "spec-prose"))


def gloss_shell() -> str:
    return """
<div id="gloss-box" class="gloss-box" hidden>
  <div class="gloss-panel" role="dialog" aria-modal="true" aria-labelledby="gloss-title">
    <div class="gloss-bar">
      <h3 id="gloss-title"></h3>
      <button type="button" class="gloss-x" aria-label="關閉">×</button>
    </div>
    <div id="gloss-body" class="gloss-body"></div>
  </div>
</div>
<script>
(function () {
  var box = document.getElementById("gloss-box");
  if (!box) return;
  var title = document.getElementById("gloss-title");
  var body = document.getElementById("gloss-body");
  function close() {
    box.hidden = true;
    document.documentElement.style.overflow = "";
  }
  function open(id) {
    var src = document.getElementById("gloss-" + id);
    if (!src) return;
    title.textContent = src.getAttribute("data-title") || "";
    body.innerHTML = src.innerHTML;
    box.hidden = false;
    document.documentElement.style.overflow = "hidden";
    var x = box.querySelector(".gloss-x");
    if (x) x.focus();
  }
  document.addEventListener("click", function (e) {
    var btn = e.target.closest(".gloss-open");
    if (btn) { e.preventDefault(); open(btn.getAttribute("data-gloss")); return; }
    if (e.target === box) close();
  });
  box.addEventListener("click", function (e) {
    if (e.target.closest(".gloss-x")) close();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !box.hidden) close();
  });
})();
</script>
"""


def gloss_css() -> str:
    return """
.gloss-open { display:inline; margin:0; padding:0 1px; border:none; border-bottom:1px dotted #008787;
  background:none; color:#008787; font:inherit; cursor:pointer; }
.gloss-open:hover { background:#e8f5f5; }
.gloss-src { display:none; }
.gloss-box { position:fixed; inset:0; z-index:40; background:rgba(0,0,0,.35);
  display:flex; align-items:flex-start; justify-content:center; padding:8vh 16px 16px; }
.gloss-box[hidden] { display:none; }
.gloss-panel { background:#fff; border:1px solid #ccc; max-width:40em; width:100%;
  max-height:80vh; overflow:auto; box-shadow:0 8px 24px rgba(0,0,0,.18); }
.gloss-bar { display:flex; align-items:center; justify-content:space-between;
  padding:10px 12px 8px; border-bottom:1px solid #e5e5e5; position:sticky; top:0; background:#fff; }
.gloss-bar h3 { margin:0; font-size:16px; color:#008787; padding-right:12px; }
.gloss-x { border:none; background:none; font-size:22px; line-height:1; color:#666;
  cursor:pointer; padding:0 4px; }
.gloss-x:hover { color:#000; }
.gloss-body { padding:12px 16px 16px; }
"""
