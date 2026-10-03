"""Idempotent patch: load the mirror's Spectral stylesheet in site/index.html.

Upstream rebuilds regenerate site/index.html (and hashed asset names), and
the scheduled sync overwrites it, so this patch is re-applied after every
sync (scripts/sync_from_hf.py) and on every Netlify build
(scripts/netlify_build.py) instead of being a one-time edit.

The <link> is inserted right after the bundle stylesheet so spectral.css
wins the cascade on equal specificity (e.g. the :root --ui/--serif vars).

Usage:
    python3 scripts/spectral_patch.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "site", "index.html")

MARKER = "spectral.css"
LINK_LINE = '    <link rel="stylesheet" href="/spectral.css" />\n'


def apply_patch() -> bool:
    """Insert the spectral.css link if missing. Returns True if changed."""
    with open(INDEX) as f:
        html = f.read()
    if MARKER in html:
        return False
    anchor = "\n  </head>"
    if anchor not in html:
        raise SystemExit("spectral_patch: no </head> found in site/index.html")
    # Put our stylesheet after the bundle CSS: the bundle <link> tags are the
    # last head children, so inserting just before </head> lands after them.
    html = html.replace(anchor, "\n" + LINK_LINE + "  </head>", 1)
    with open(INDEX, "w") as f:
        f.write(html)
    print("spectral_patch: injected /spectral.css into site/index.html")
    return True


if __name__ == "__main__":
    changed = apply_patch()
    sys.exit(0 if not changed else 0)
