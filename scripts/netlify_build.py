"""Netlify build step: ensure site/vol1.pdf exists.

The lecture PDF is copyrighted and intentionally NOT committed to the repo
(same as the upstream Hugging Face Space, which fetches it at Docker build
time). This script downloads it and extracts Vol. I chapters 1-14 with
extract_pdf.py.

- PDF source: $PDF_URL env var, else the same default the Space Dockerfile uses.
- If site/vol1.pdf already exists, nothing is done.
- Any failure (no network, URL moved, etc.) is a WARNING, not a build
  failure: the app still deploys and shows its built-in "PDF not found" hint.

Usage (also see netlify.toml):
    pip install pymupdf
    python3 scripts/netlify_build.py
"""

import os
import subprocess
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, "site", "vol1.pdf")
DEFAULT_PDF_URL = "https://antilogicalism.com/wp-content/uploads/2018/04/feynman-lectures.pdf"


def main() -> int:
    if os.path.exists(TARGET) and os.path.getsize(TARGET) > 0:
        print(f"netlify_build: {TARGET} already present, skipping download.")
        return 0

    pdf_url = os.environ.get("PDF_URL", DEFAULT_PDF_URL)
    tmp_pdf = "/tmp/full.pdf"
    print(f"netlify_build: downloading {pdf_url} ...")
    try:
        req = urllib.request.Request(pdf_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as resp, open(tmp_pdf, "wb") as f:
            f.write(resp.read())
        print(f"netlify_build: downloaded {os.path.getsize(tmp_pdf)} bytes.")
    except Exception as e:  # noqa: BLE001 - build must not fail on PDF issues
        print(f"netlify_build: WARNING: could not download PDF: {e}")
        print("netlify_build: continuing without vol1.pdf (app will show its hint).")
        return 0

    try:
        subprocess.run(
            [sys.executable, os.path.join(ROOT, "extract_pdf.py"), tmp_pdf, TARGET],
            check=True,
        )
    except Exception as e:  # noqa: BLE001
        print(f"netlify_build: WARNING: PDF extraction failed: {e}")
        print("netlify_build: continuing without vol1.pdf (app will show its hint).")
        return 0
    finally:
        try:
            os.remove(tmp_pdf)
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
