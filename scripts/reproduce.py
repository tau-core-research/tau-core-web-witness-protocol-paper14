#!/usr/bin/env python3
"""Reproduce Paper 14 derived artifacts, PDF, archive, and tests."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], cwd: Path = ROOT) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def build_pdf() -> None:
    source = ROOT / "paper14_submission_source"
    if shutil.which("tectonic"):
        run(["tectonic", "main.tex"], cwd=source)
    elif shutil.which("latexmk"):
        run(["latexmk", "-pdf", "-interaction=nonstopmode", "main.tex"], cwd=source)
    elif shutil.which("pdflatex"):
        run(["pdflatex", "-interaction=nonstopmode", "main.tex"], cwd=source)
        run(["pdflatex", "-interaction=nonstopmode", "main.tex"], cwd=source)
    else:
        raise RuntimeError("No LaTeX engine found: install tectonic, latexmk, or pdflatex.")


def main() -> None:
    run([sys.executable, "scripts/build_paper14_artifacts.py"])
    build_pdf()
    run([sys.executable, "scripts/build_arxiv_source.py"])
    run([sys.executable, "-m", "pytest", "tests"])
    print("PAPER14_REPRODUCTION_COMPLETE")


if __name__ == "__main__":
    main()

