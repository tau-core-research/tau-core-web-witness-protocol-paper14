#!/usr/bin/env python3
"""Build a compact arXiv source archive for Paper 14."""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "paper14_submission_source"
ZIP = ROOT / "arxiv_submission_source.zip"


def main() -> None:
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in SRC.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(SRC))
    print(f"wrote {ZIP}")


if __name__ == "__main__":
    main()

