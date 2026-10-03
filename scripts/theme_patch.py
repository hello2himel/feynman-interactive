"""Idempotent patches applied to upstream-owned site/index.html.

Upstream rebuilds regenerate site/index.html (and hashed asset names), and
the scheduled sync overwrites it, so these edits are re-applied after every
sync (scripts/sync_from_hf.py) and on every Netlify build
(scripts/netlify_build.py) instead of being one-time edits.

Structural patches (fail loudly if anchors vanish):
  1. Mirror theme stylesheet (/theme.css) after the bundle CSS.
  2. Mirror theme script (/theme.js) right after it (moved below the CSS so
     render-blocking stylesheets are discovered first; still runs pre-paint).
  3. Font preload for EB Garamond.
  4. Light/dark/system theme toggle button in the header bar.
  5. Mirror-owned info section in the help dialog (upstream shortcuts stay).
  6. Mirror-owned missing-PDF guidance + retry button.
  7. Orphan-demo banner slot + cue counter + polite live region.
     Explicit × close button as the dialog's first child.
     Brand mark (mirror logo) + favicon links.

Cosmetic upstream-text patches (skipped silently when upstream rewords):
  8. "?" help button -> italic serif "i" (+ labels).
  9. Accessible names for icon buttons, dialog, divider, live pagelabel.
 10. Plain-English control labels (Hold Demo, Restore Book Values, …).
 11. "?" / "Esc" rows in the shortcuts list; "Close (Esc)" with autofocus.

Plus: removal of the superseded spectral.css link, if present.

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
PRELOAD_LINE = (
    '    <link rel="preload" href="/fonts/EBGaramond.woff2" as="font"'
    ' type="font/woff2" crossorigin />\n'
)
THEME_BTN_LINE = (
    '      <button id="theme" title="Colour theme: follows your system. '
    'Activate to pin Light or Dark.">\u25d0 System</button>\n'
)
LEGACY_RE = re.compile(r"^.*spectral\.css.*\n?", re.M)
HELP_BTN_RE = re.compile(r'(<button[^>]*id="help-btn"[^>]*>)\?</button>')

MIRROR_INFO = """      <div id="mirror-info">
        <p class="orientation">This page pairs each marked passage with a runnable demo.
        If the right pane has no pages loaded, the left pane still works &mdash; start
        with <em>J</em> / <em>K</em>.</p>
        <h4>About this book</h4>
        <p>Chapters 1&ndash;14 of the <em>Feynman Lectures on Physics</em>, Vol. I, with
        scroll-synced wireframe demos. The left pane runs the demo for whatever you are
        reading; the right pane is the book itself.</p>
        <h4>Reading with the demos</h4>
        <p>Scroll the book and the demo follows each demo point &mdash; <em>J</em> /
        <em>K</em> jump between them. <em>Hold</em> pins the current demo while you scroll.
        Drag the demo to orbit or zoom (touch: one finger orbits, pinch zooms, two fingers
        pan); its sliders rewrite the scene, and <em>Restore Book Values</em> undoes your
        changes and restores what the text describes. On phones the menu holds chapters,
        demo points and display; <em>Prev</em> / <em>Next</em> step through points.</p>
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

MISSING_HTML = """        <div id="missing" hidden>
          <p class="m-kicker">Demo mode &middot; no book pages needed</p>
          <h2>Play with the idea first</h2>
          <p>This demo is live anyway &mdash; try the sliders, then step points with
          <em>Prev</em> / <em>Next</em>.</p>
          <p class="m-cta"><button id="browse-demos" type="button">Browse chapters</button>
          <button id="retry-pdf" type="button">Check again</button></p>
          <p id="retry-status" role="status"></p>
          <details class="m-src"><summary>Where do the pages come from?</summary>
          <p>Page scans ship with <em>your own copy</em> for copyright reasons. Self-host:
          <code>python3 extract_pdf.py /path/to/feynman-lectures.pdf site/vol1.pdf</code>,
          then reload. Deployed copies can set a <code>PDF_URL</code> &mdash; see the
          <a href="https://github.com/hello2himel/feynman-interactive#the-book-file">README</a>.</p></details>
        </div>
"""

ORPHAN_HTML = (
    '<p id="demo-orphan" hidden>The book pages aren&rsquo;t loaded, so this demo '
    "runs on its own"
    '<span class="mob-only"> &mdash; find chapters in the menu, step points with '
    "<em>Prev</em> / <em>Next</em>.</span>"
    '<span class="desk-only"> &mdash; <em>J</em> / <em>K</em> still step through '
    "the demos.</span></p>\n"
)


def _swap(html, old, new):
    """Exact-string replace-once. Returns (html, changed). Never raises."""
    if old not in html:
        return html, False
    return html.replace(old, new, 1), True


def apply_patch() -> bool:
    """Apply all mirror patches. Returns True if the file changed."""
    with open(INDEX) as f:
        html = f.read()
    changed = False

    # Legacy spectral link.
    html, n_removed = LEGACY_RE.subn("", html)
    changed |= n_removed > 0

    # 1. theme stylesheet just before </head>.
    if "theme.css" not in html:
        anchor = "\n  </head>"
        if anchor not in html:
            raise SystemExit("theme_patch: no </head> found in site/index.html")
        html = html.replace(anchor, "\n" + THEME_CSS_LINE + "  </head>", 1)
        changed = True

    # 2. theme script right after the theme stylesheet (migrates older
    # position before the CSS links). No-op when already in place.
    anchor = "\n" + THEME_CSS_LINE
    if anchor not in html:
        raise SystemExit("theme_patch: theme.css link not found in site/index.html")
    if anchor + THEME_JS_LINE not in html:
        html = re.sub(r"^.*<script src=\"/theme\.js\"></script>\n?", "", html, flags=re.M)
        html = html.replace(anchor, anchor + THEME_JS_LINE, 1)
        changed = True

    # 3. font preload after the viewport meta.
    if 'rel="preload"' not in html:
        anchor = (
            '\n    <meta name="viewport" content="width=device-width,'
            ' initial-scale=1" />'
        )
        if anchor not in html:
            raise SystemExit("theme_patch: viewport meta not found")
        html = html.replace(anchor, anchor + "\n" + PRELOAD_LINE.rstrip("\n"), 1)
        changed = True

    # 4. theme toggle button before the help button.
    if 'id="theme"' not in html:
        anchor = '\n      <button id="help-btn"'
        if anchor not in html:
            raise SystemExit("theme_patch: no help button found in site/index.html")
        html = html.replace(
            anchor, "\n" + THEME_BTN_LINE + '      <button id="help-btn"', 1
        )
        changed = True

    # 5. mirror info section (refresh when the copy changed).
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

    # 6. missing-PDF guidance (refresh when the copy changed).
    missing_re = re.compile(r"        <div id=\"missing\" hidden>.*?</div>\n", re.S)
    m_missing = missing_re.search(html)
    if m_missing:
        if m_missing.group(0) != MISSING_HTML:
            html = (
                html[: m_missing.start()] + MISSING_HTML + html[m_missing.end():]
            )
            changed = True

    # 7a. orphan-demo banner slot after the demo note. Refresh the copy
    # when ORPHAN_HTML changed; insert it when missing.
    orphan_re = re.compile(r" *<p id=\"demo-orphan\" hidden>.*?</p>\n", re.S)
    m_orphan = orphan_re.search(html)
    if m_orphan:
        want = "      " + ORPHAN_HTML
        if m_orphan.group(0) != want:
            html = html[: m_orphan.start()] + want + html[m_orphan.end():]
            changed = True
    elif 'id="demo-orphan"' not in html:
        html, c = _swap(
            html, '      <div id="demo-note"></div>', '      <div id="demo-note"></div>\n      ' + ORPHAN_HTML.rstrip("\n")
        )
        changed |= c

    # 7d. brand mark (mirror logo) as the first child of .brand.
    if 'brand-mark' not in html:
        m = re.search(r'(<div class="brand">)', html)
        if m:
            mark = open(os.path.join(ROOT, "scripts", "brandmark.svg"), encoding="utf-8").read().strip()
            html = html[: m.end(1)] + mark + " " + html[m.end(1):]
            changed = True

    # 7e. favicon links before the theme stylesheet.
    if "favicon.svg" not in html:
        anchor = "\n" + THEME_CSS_LINE
        if anchor not in html:
            raise SystemExit("theme_patch: theme.css link not found in site/index.html")
        favicons = (
            '\n    <link rel="icon" href="/favicon.svg" type="image/svg+xml" />'
            '\n    <link rel="alternate icon" href="/favicon.png" />'
        )
        html = html.replace(anchor, favicons + anchor, 1)
        changed = True

    # 7c. explicit × close button as the dialog's first child.
    if 'id="help-close"' not in html:
        m = re.search(r'(<dialog[^>]*id="help"[^>]*>)', html)
        if m:
            x_btn = (
                m.group(1)
                + '\n      <button id="help-close" type="button"'
                ' aria-label="Close this panel">'
                '<svg class="ri" viewBox="0 0 24 24" aria-hidden="true"'
                ' fill="currentColor"><path d="M11.9997 10.5865L16.9495 '
                "5.63672L18.3637 7.05093L13.4139 12.0007L18.3637 16.9504L16.9495 "
                "18.3646L11.9997 13.4149L7.04996 18.3646L5.63574 16.9504L10.5855 "
                "12.0007L5.63574 7.05093L7.04996 5.63672L11.9997 10.5865Z\"/></button>"
            )
            html = html[: m.end(1)] + x_btn[len(m.group(1)):] + html[m.end(1):]
            changed = True

    # 7b. cue counter + polite live region after the next-cue button.
    if 'id="cue-count"' not in html:
        m = re.search(r'(<button[^>]*id="next-cue"[^>]*>.*?</button>)', html)
        if m:
            insert = (
                m.group(1)
                + '\n      <span id="cue-count" aria-hidden="true"></span>'
                + '\n      <div id="pos-live" class="sr-only" role="status"></div>'
            )
            html = html[: m.start(1)] + insert + html[m.end(1):]
            changed = True

    # 8. "?" -> "i".
    html, n_help = HELP_BTN_RE.subn(r"\1i</button>", html)
    changed |= n_help > 0
    html, c = _swap(
        html,
        '<button id="help-btn" title="Keyboard shortcuts">',
        '<button id="help-btn" title="About this book &amp; keyboard shortcuts">',
    )
    changed |= c
    # Convergent attribute top-up (works on fresh and already-patched files).
    m_btn = re.search(r'<button[^>]*id="help-btn"[^>]*>', html)
    if m_btn:
        tag = m_btn.group(0)
        if "aria-label=" not in tag:
            tag = tag.replace(
                "<button", '<button aria-label="About this book and keyboard shortcuts"', 1
            )
            changed = True
        if "aria-haspopup" not in tag:
            tag = tag.replace("<button", '<button aria-haspopup="dialog"', 1)
            changed = True
        html = html[: m_btn.start()] + tag + html[m_btn.end():]

    # 9a. icon-button accessible names.
    html, c = _swap(html, '<button id="prev-cue" title="Previous demo point (K)">', '<button id="prev-cue" title="Previous demo point (K)" aria-label="Previous demo point (K)">')
    changed |= c
    html, c = _swap(html, '<button id="next-cue" title="Next demo point (J)">', '<button id="next-cue" title="Next demo point (J)" aria-label="Next demo point (J)">')
    changed |= c
    # 9b. dialog name + heading anchor.
    html, c = _swap(html, '<dialog id="help">', '<dialog id="help" aria-labelledby="help-title">')
    changed |= c
    # 9c. divider keyboard operability.
    html, c = _swap(
        html,
        '<div id="divider" role="separator" aria-orientation="vertical" title="Drag to resize">',
        '<div id="divider" role="separator" aria-orientation="vertical" tabindex="0"'
        ' aria-label="Resize demo and text panes. Left and right arrows."'
        ' aria-valuemin="25" aria-valuemax="75" aria-valuenow="46" title="Drag to resize">',
    )
    changed |= c
    # 9d. polite live pagelabel.
    html, c = _swap(
        html,
        '<span id="pagelabel" class="muted">',
        '<span id="pagelabel" class="muted" role="status" aria-live="polite" aria-atomic="true">',
    )
    changed |= c

    # 10a. Hold Demo (title case + verb agreement).
    html, c = _swap(html, ">Hold demo</button>", ">Hold Demo</button>")
    changed |= c
    html, c = _swap(
        html,
        'title="Keep the current demo while you scroll (H)"',
        'title="Hold the current demo while you scroll (H)"',
    )
    changed |= c
    # 10b. Restore Book Values (plain English + matching title).
    html, c = _swap(
        html,
        '<button id="restore" hidden title="Undo your slider changes and return to the values for this part of the text">Back to text values</button>',
        '<button id="restore" hidden title="Undo your slider changes and restore the values described in the text">Restore Book Values</button>',
    )
    changed |= c
    # 10c. dialog heading covers the About content too.
    html, c = _swap(html, "<h3>Shortcuts</h3>", "<h3 id=\"help-title\">Shortcuts &amp; About</h3>")
    changed |= c
    # 10d. one vocabulary: demo points (not marks / marked points).
    html, c = _swap(
        html,
        "The marks in the left margin of the pages show where a demo changes. Click one to jump there.",
        "The marks in the left margin show each demo point. Click one to jump there.",
    )
    changed |= c
    # 10e. document the ? / Esc keys inside the shortcuts list.
    if "<dt>?</dt>" not in html:
        html, c = _swap(
            html,
            "        <dt>Drag / scroll on demo</dt><dd>Pan \u00b7 zoom (2D) or orbit \u00b7 zoom (3D)</dd>",
            "        <dt>Drag / scroll on demo</dt><dd>Pan \u00b7 zoom (2D) or orbit \u00b7 zoom (3D)</dd>\n"
            "        <dt>?</dt><dd>Open this panel</dd>\n"
            "        <dt>Esc</dt><dd>Close this panel</dd>",
        )
        changed |= c
    # 10f. Close states its shortcut and takes initial focus.
    html, c = _swap(
        html,
        "<form method=\"dialog\"><button>Close</button></form>",
        "<form method=\"dialog\"><button autofocus>Close (Esc)</button></form>",
    )
    changed |= c

    # Visible select labels + orientation titles.
    html, c = _swap(
        html,
        '<select id="chapter" aria-label="Chapter"></select>',
        '<label class="sel-label" for="chapter">Ch.</label>'
        '<select id="chapter" aria-label="Chapter" title="Chapter (all 14)"></select>',
    )
    changed |= c
    html, c = _swap(
        html,
        '<select id="section" aria-label="Section"></select>',
        '<label class="sel-label" for="section">\u00a7</label>'
        '<select id="section" aria-label="Section" title="Section within this chapter"></select>',
    )
    changed |= c

    if changed:
        with open(INDEX, "w") as f:
            f.write(html)
        print("theme_patch: site/index.html updated")
    return changed


if __name__ == "__main__":
    apply_patch()
