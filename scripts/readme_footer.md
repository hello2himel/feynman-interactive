
<!-- MIRROR-README: appended by scripts/sync_from_hf.py. Upstream's text above
stays verbatim; everything below is this mirror's. Do not edit the marker. -->

## Community mirror — Netlify-hostable, book-styled

[![sync-from-hf](https://github.com/hello2himel/feynman-interactive/actions/workflows/sync-from-hf.yml/badge.svg)](https://github.com/hello2himel/feynman-interactive/actions/workflows/sync-from-hf.yml)
[![Deploy to Netlify](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/hello2himel/feynman-interactive)

This repo mirrors the Hugging Face Space
**[mishig/feynman-interactive](https://huggingface.co/spaces/mishig/feynman-interactive)**
(chapters 1–14 of the *Feynman Lectures*, Vol. I, with scroll-synced
wireframe demos) and repackages it as a plain static site. Details live in
**[MIRROR.md](MIRROR.md)**.

### Use it

- **Deploy your own copy:** press *Deploy to Netlify* above. Build settings
  come from `netlify.toml` (publish `site/`). Set a `PDF_URL` env var to use
  your own copy of the lecture PDF, or the default source is fetched.
- **Preview locally:** `python3 serve.py` → <http://localhost:7860>.
- **The book file:** `site/vol1.pdf` is *not* committed (copyright, same as
  upstream). Generate it from your own PDF:
  `pip install pymupdf && python3 extract_pdf.py /path/to/feynman-lectures.pdf site/vol1.pdf`.

### What's different from upstream

- **Book styling** — EB Garamond + Cormorant SC, warm paper palette with
  matching dark mode (`site/theme.css`, `site/fonts/`).
- **Theme control** — follows the OS by default; the header button pins
  Light/Dark (persisted). Dark mode inverts the scanned pages too.
- **Info dialog** — the header `i` keeps the keyboard shortcuts and adds
  about/reading/PDF info.
- **Real binaries** — pdf.js `.wasm` + fonts committed as regular files
  (upstream uses Git LFS/Xet), so static hosts need no extra setup.

### How the sync works

A scheduled workflow (`.github/workflows/sync-from-hf.yml`, every 12 h +
manual dispatch) overlays the current upstream snapshot via
`scripts/sync_from_hf.py`, preserving mirror files and re-applying the
`site/index.html` patches + this footer. It never pushes to Hugging Face.
