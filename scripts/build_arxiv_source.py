#!/usr/bin/env python3
"""Build a compact arXiv source archive for Paper 14."""

from __future__ import annotations

import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "paper14_submission_source"
ZIP = ROOT / "arxiv_submission_source.zip"
EXCLUDED_SUFFIXES = {".aux", ".log", ".out", ".toc", ".blg", ".synctex.gz"}


def should_include(path: Path) -> bool:
    if path.name == "main.pdf":
        return False
    if any(str(path).endswith(suffix) for suffix in EXCLUDED_SUFFIXES):
        return False
    return path.is_file()


def main() -> None:
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(SRC.rglob("*")):
            if should_include(path):
                zf.write(path, path.relative_to(SRC).as_posix())
    print(f"wrote {ZIP}")


if __name__ == "__main__":
    main()
