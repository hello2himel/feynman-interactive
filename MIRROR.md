# feynman-interactive (GitHub mirror, Netlify-hostable)

[![sync-from-hf](https://github.com/hello2himel/feynman-interactive/actions/workflows/sync-from-hf.yml/badge.svg)](https://github.com/hello2himel/feynman-interactive/actions/workflows/sync-from-hf.yml)

Community mirror of the Hugging Face Space
**[`mishig/feynman-interactive`](https://huggingface.co/spaces/mishig/feynman-interactive)**
(upstream commit `a7566b3`, 2026-10-01), repackaged so it can be hosted on
[Netlify](https://www.netlify.com/) as a plain static site.

> Personal study tool: chapters 1–14 of the Feynman Lectures Vol. I with
> scroll-synced wireframe demos.

## How it works

Upstream is a Docker Space whose only runtime job is serving the prebuilt
static app in `site/` on port 7860 (see `serve.py`). There is no backend
logic, so Netlify just needs `site/` as its publish directory:

| Concern | Hugging Face Space | This mirror (Netlify) |
|---|---|---|
| Static files | `site/` served by `serve.py` | `site/` published directly (`netlify.toml`) |
| `.mjs` / `.wasm` MIME types | `mimetypes` overrides in `serve.py` | `[[headers]]` in `netlify.toml` |
| Asset caching | `Cache-Control` in `serve.py` | `[[headers]]` in `netlify.toml` |
| Lecture PDF (`site/vol1.pdf`) | fetched + extracted at Docker build time | fetched + extracted at Netlify build time (`scripts/netlify_build.py`) |

## Deploy to Netlify

1. Fork or use this repo, then **Add new site → Import an existing project**
   in Netlify and pick the repo. Build settings are read from `netlify.toml`:
   - Build command: `pip install -q pymupdf && python3 scripts/netlify_build.py`
   - Publish directory: `site`
2. (Optional) Set a `PDF_URL` environment variable in Netlify to use your own
   copy of the 1376-page Feynman Lectures PDF. Without it, the default URL
   from the upstream Dockerfile is used.
3. Deploy. If the PDF can't be fetched, the build still succeeds and the app
   shows its built-in "PDF not found" hint.

Or one click (replace `<user>` after forking):

[![Deploy to Netlify](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/hello2himel/feynman-interactive)

## Theming: Spectral typeface

The whole site is set in the **Spectral** serif family (self-hosted woff2 in
`site/fonts/`, latin subsets only, ~160 KB total), except math: KaTeX keeps
its own fonts, and PDF.js internals / the signature handwriting input / form
monospace are untouched.

How it works: the bundle themes everything through the `--ui` and `--serif`
CSS variables, so the mirror-owned `site/spectral.css` (loaded after the
bundle CSS) just redefines those two variables plus `@font-face` rules.
`site/index.html` is upstream-owned and gets clobbered on every sync, so the
`<link>` injection is an idempotent patch (`scripts/spectral_patch.py`)
re-applied by the sync workflow and by the Netlify build — never a one-time
edit.

## Local preview

```bash
python3 serve.py        # serves site/ at http://localhost:7860
# or: npx netlify dev  # same headers as production
```

To generate `site/vol1.pdf` from your own PDF (not included, see below):

```bash
pip install pymupdf
python3 extract_pdf.py /path/to/feynman-lectures.pdf site/vol1.pdf
```

## Sync with upstream

This is a third-party mirror. A scheduled workflow
(`.github/workflows/sync-from-hf.yml`, every 12 h + manual dispatch)
downloads the current upstream Space snapshot and overlays it here, preserving
mirror-only files (`netlify.toml`, `scripts/`, `.github/`, `MIRROR.md`,
`.gitignore`, `.gitattributes`, `site/spectral.css`, `site/fonts/`).
It never pushes anything to Hugging Face. After overlaying, the Spectral
`<link>` patch is re-applied to the upstream-owned `site/index.html`
(`scripts/spectral_patch.py`), so theming survives syncs.

Run a sync manually any time:

```bash
pip install huggingface_hub hf_xet
python3 scripts/sync_from_hf.py
git push
```

## Notes

- **Copyright:** the Feynman Lectures PDF is not stored in this repo (same as
  upstream). Bring your own copy and extract `vol1.pdf` as shown above.
- **Binaries:** `site/pdfjs/wasm/*.wasm` and the LiberationSans fonts are
  committed as regular files (upstream keeps them in Git LFS/Xet) so Netlify
  serves them with no extra setup. See `.gitattributes`.
- Upstream files (`README.md`, `Dockerfile`, `serve.py`, `extract_pdf.py`,
  `site/`) are verbatim copies and get overwritten on each sync — except
  `site/index.html`, which additionally carries the one-line Spectral
  stylesheet `<link>` (re-applied automatically after every sync, see above).
  Mirror docs live in this file so they survive syncs.
