"""Idempotent patches applied to upstream-owned site/index.html.

Upstream rebuilds regenerate site/index.html (and hashed asset names), and
the scheduled sync overwrites it, so these edits are re-applied after every
sync (scripts/sync_from_hf.py) and on every Netlify build
(scripts/netlify_build.py) instead of being one-time edits:

  1. Load the mirror's theme stylesheet (/theme.css) after the bundle CSS.
  2. Load the mirror's theme control script (/theme.js) in <head>.
  3. Add the light/dark/system theme toggle button to the header bar.
  4. Turn the "?" help button into an italic serif "i" info button.
  5. Append a mirror-owned info section to the help dialog (upstream
     shortcuts stay untouched).
  6. Remove the superseded spectral.css link, if present.

Usage:
    python3 scripts/theme_patch.py
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "site", "index.html")

THEME_CSS_LINE = '    <link rel="stylesheet" href="/theme.css" />\n'
THEME_JS_LINE = '    <script src="/theme.js"></script>\n'
THEME_BTN_LINE = (
    '      <button id="theme" title="Colour theme: follows your system. '
    'Activate to pin Light or Dark.">\u25d0 System</button>\n'
)
LEGACY_RE = re.compile(r"^.*spectral\.css.*\n?", re.M)
HELP_BTN_RE = re.compile(r'(<button[^>]*id="help-btn"[^>]*>)\?</button>')

MIRROR_INFO = """      <div id="mirror-info">
        <h4>About this book</h4>
        <p>Chapters 1&ndash;14 of the <em>Feynman Lectures on Physics</em>, Vol. I, with
        scroll-synced wireframe demos. The left pane runs the demo for whatever you are
        reading; the right pane is the book itself.</p>
        <h4>Reading with the demos</h4>
        <p>Scroll the book and the demo follows each marked point &mdash; <em>J</em> /
        <em>K</em> jump between them. <em>Hold</em> pins the current demo while you scroll.
        Drag the demo to orbit or zoom; its sliders rewrite the scene, and
        <em>Back to text values</em> restores what the text describes.</p>
        <h4>Light &amp; dark</h4>
        <p>The pages follow your system theme. Use the header control to pin
        <em>Light</em> or <em>Dark</em>; dark mode reprints the scanned pages and the demo in the dark paper tones.</p>
        <h4>The book file</h4>
        <p>The page scans come from your own PDF and are not included here for copyright
        reasons. On a self-hosted copy, extract them with
        <code>python3 extract_pdf.py</code> &mdash; see the README.</p>
        <h4>Elsewhere</h4>
        <p>Upstream Space:
        <a href="https://huggingface.co/spaces/mishig/feynman-interactive">mishig/feynman-interactive</a><br />
        This mirror:
        <a href="https://github.com/hello2himel/feynman-interactive">hello2himel/feynman-interactive</a></p>
      </div>
"""


def apply_patch() -> bool:
    """Apply all mirror patches. Returns True if the file changed."""
    with open(INDEX) as f:
        html = f.read()
    changed = False

    # 6. drop legacy spectral link
    html, n_removed = LEGACY_RE.subn("", html)
    changed |= n_removed > 0

    # 1. theme stylesheet after the bundle CSS (i.e. just before </head>)
    if "theme.css" not in html:
        anchor = "\n  </head>"
        if anchor not in html:
            raise SystemExit("theme_patch: no </head> found in site/index.html")
        html = html.replace(anchor, "\n" + THEME_CSS_LINE + "  </head>", 1)
        changed = True

    # 2. theme script in <head>, before the stylesheet links
    if "/theme.js" not in html:
        anchor = "\n    <link"
        if anchor not in html:
            raise SystemExit("theme_patch: no <link> found in site/index.html")
        html = html.replace(anchor, "\n" + THEME_JS_LINE.rstrip("\n") + anchor, 1)
        changed = True

    # 3. theme toggle button before the help button (same 6-space indent)
    if 'id="theme"' not in html:
        anchor = '\n      <button id="help-btn"'
        if anchor not in html:
            raise SystemExit("theme_patch: no help button found in site/index.html")
        html = html.replace(
            anchor, "\n" + THEME_BTN_LINE + '      <button id="help-btn"', 1
        )
        changed = True

    # 4. "?" -> italic serif "i" (styled via #help-btn in theme.css)
    html, n_help = HELP_BTN_RE.subn(r"\1i</button>", html)
    if n_help:
        html = html.replace(
            '<button id="help-btn" title="Keyboard shortcuts">',
            '<button id="help-btn" title="About this book &amp; keyboard shortcuts">',
            1,
        )
        changed = True

    # 5. mirror info section at the end of the help dialog. Refresh it when
    # the copy in MIRROR_INFO changed; insert it when missing.
    info_re = re.compile(r"      <div id=\"mirror-info\">.*?</div>\n", re.S)
    m_info = info_re.search(html)
    if m_info:
        if m_info.group(0) != MIRROR_INFO:
            html = html[: m_info.start()] + MIRROR_INFO + html[m_info.end():]
            changed = True
    else:
        m = re.search(r'(<dialog[^>]*id="help"[^>]*>)(.*?)(</dialog>)', html, re.S)
        if not m:
            raise SystemExit("theme_patch: no help dialog found in site/index.html")
        body = m.group(2)
        form_anchor = "\n      <form"
        if form_anchor not in body:
            raise SystemExit("theme_patch: no close form found in help dialog")
        body = body.replace(form_anchor, "\n" + MIRROR_INFO + "      <form", 1)
        html = html[: m.start(2)] + body + html[m.end(2):]
        changed = True

    if changed:
        with open(INDEX, "w") as f:
            f.write(html)
        print("theme_patch: site/index.html updated")
    return changed


if __name__ == "__main__":
    apply_patch()
