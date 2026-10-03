"""Idempotent patch: load the mirror's theme stylesheet in site/index.html.

Upstream rebuilds regenerate site/index.html (and hashed asset names), and
the scheduled sync overwrites it, so this patch is re-applied after every
sync (scripts/sync_from_hf.py) and on every Netlify build
(scripts/netlify_build.py) instead of being a one-time edit.

The <link> is inserted right before </head> (after the bundle stylesheet)
so theme.css wins the cascade on equal specificity (e.g. the :root vars).
Also removes the superseded spectral.css link, if present.

Usage:
    python3 scripts/theme_patch.py
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "site", "index.html")

MARKER = "theme.css"
LINK_LINE = '    <link rel="stylesheet" href="/theme.css" />\n'
LEGACY_RE = re.compile(r'^.*spectral\.css.*\n?', re.M)


def apply_patch() -> bool:
    """Ensure the theme.css link is present (and legacy links gone)."""
    with open(INDEX) as f:
        html = f.read()
    cleaned, n_removed = LEGACY_RE.subn("", html)
    if MARKER in cleaned:
        changed = n_removed > 0
        if changed:
            with open(INDEX, "w") as f:
                f.write(cleaned)
            print("theme_patch: removed legacy spectral.css link")
        return changed
    anchor = "\n  </head>"
    if anchor not in cleaned:
        raise SystemExit("theme_patch: no </head> found in site/index.html")
    # The bundle <link> tags are the last head children, so inserting just
    # before </head> lands after them.
    html = cleaned.replace(anchor, "\n" + LINK_LINE + "  </head>", 1)
    with open(INDEX, "w") as f:
        f.write(html)
    print("theme_patch: injected /theme.css into site/index.html")
    return True


if __name__ == "__main__":
    apply_patch()
