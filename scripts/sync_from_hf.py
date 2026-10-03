"""Sync this mirror with the upstream Hugging Face Space.

Used by .github/workflows/sync-from-hf.yml on a schedule. It downloads the
current upstream snapshot (full file contents, no git-lfs/xet needed) and
overlays it onto this repo, preserving mirror-specific files:

  kept as-is: .git/, .github/, netlify.toml, scripts/, MIRROR.md,
              .gitignore, .gitattributes (mirror stores wasm/fonts without LFS),
              site/spectral.css, site/fonts/ (mirror theming)

  After overlaying, the Spectral <link> patch is re-applied to
  site/index.html (scripts/spectral_patch.py), since that file is
  upstream-owned and the overlay restores the unpatched version.

Everything else is made to match upstream exactly, including deleting files
upstream removed. Exits 0 with no commit when already in sync.

Usage:
    pip install huggingface_hub hf_xet
    python3 scripts/sync_from_hf.py
"""

import os
import shutil
import subprocess
import sys

REPO_ID = os.environ.get("HF_SPACE_ID", "mishig/feynman-interactive")

# Paths (repo-relative) that belong to this mirror and must never be
# overwritten by upstream content. Entries are exact paths or directory
# prefixes: "scripts" keeps scripts/*, "site/fonts" keeps site/fonts/*.
KEEP = {
    ".git",
    ".github",
    "netlify.toml",
    "scripts",
    "MIRROR.md",
    ".gitignore",
    ".gitattributes",
    "site/spectral.css",
    "site/fonts",
}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(ROOT, "scripts"))
from spectral_patch import apply_patch  # noqa: E402


def kept(rel: str) -> bool:
    rel = rel.replace(os.sep, "/")
    return any(rel == k or rel.startswith(k + "/") for k in KEEP)


def run(*args: str) -> str:
    out = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if out.returncode != 0:
        print(out.stdout + out.stderr)
        raise SystemExit(f"command failed: {' '.join(args)}")
    return out.stdout.strip()


def snapshot_files(snapshot_dir: str) -> set[str]:
    files: set[str] = set()
    for dirpath, _dirnames, filenames in os.walk(snapshot_dir):
        for name in filenames:
            full = os.path.join(dirpath, name)
            files.add(os.path.relpath(full, snapshot_dir))
    return files


def main() -> int:
    from huggingface_hub import snapshot_download

    snapshot_dir = snapshot_download(repo_id=REPO_ID, repo_type="space")
    upstream = snapshot_files(snapshot_dir)
    print(f"sync: upstream snapshot has {len(upstream)} files.")

    for rel in sorted(upstream):
        if kept(rel):
            continue
        src = os.path.join(snapshot_dir, rel)
        dst = os.path.join(ROOT, rel)
        os.makedirs(os.path.dirname(dst) or ROOT, exist_ok=True)
        shutil.copyfile(src, dst)  # follows the HF cache symlinks -> real bytes

    # Remove tracked files that upstream deleted (but never touch KEEP paths).
    tracked = run("git", "ls-files").splitlines()
    upstream_norm = {p.replace(os.sep, "/") for p in upstream}
    removed = 0
    for rel in tracked:
        if kept(rel):
            continue
        if rel not in upstream_norm:
            path = os.path.join(ROOT, rel)
            if os.path.isfile(path):
                os.remove(path)
                removed += 1
    if removed:
        print(f"sync: removed {removed} file(s) deleted upstream.")

    # Re-apply mirror theming: the overlay restored upstream's index.html.
    apply_patch()

    run("git", "add", "-A")
    status = run("git", "status", "--porcelain")
    if not status:
        print("sync: already in sync, nothing to commit.")
        return 0

    run(
        "git",
        "commit",
        "-m",
        f"Sync from Hugging Face Space {REPO_ID}",
        "-m",
        "Automated mirror sync (upstream content only; mirror files preserved).",
    )
    print("sync: committed upstream changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
