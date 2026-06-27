#!/usr/bin/env python3
"""
TC-DESI-CONNECT-001
Connector from public DESI DR1 LSS catalogues to the Tau-web pipeline.

What this does
--------------
1. Builds official DESI DR1 LSS URLs for clustering data and random catalogues.
2. Optionally downloads selected FITS files.
3. Optionally converts FITS to lightweight CSV with ra,dec,redshift,weight.
4. Optionally runs the existing Tau-web modules:
     - tc_zstab_pipeline.py
     - tc_sys_projector.py
     - tc_mock_cov.py
     - tc_obs_pipeline.py, if a lensing catalogue is provided
     - tc_verdict_engine.py, if enough JSON inputs exist

Why lensing is external
-----------------------
DESI DR1 LSS is spectroscopic clustering data. The Tau-compatible signature
needs a second mass/lensing readout, so provide that separately via:
    --lensing-catalog /path/to/lensing_or_kappa_proxy.csv_or_fits

Large file warning
------------------
DESI random catalogues are often hundreds of MB to several GB. Use --plan first.
For first-pass development, choose a smaller tracer/region or a small --max-rows
after downloading.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


DR1_LSS_BASE = "https://data.desi.lbl.gov/public/dr1/survey/catalogs/dr1/LSS/iron/LSScats"
DEFAULT_VERSION = "v1.5"

# Common clustering tracer names visible in DESI DR1 LSS v1.5 directory.
SUPPORTED_TRACERS = [
    "LRG",
    "ELG_LOPnotqso",
    "QSO",
    "BGS_BRIGHT-21.5",
    "BGS_BRIGHT",
    "BGS_ANY",
    "LRG+ELG_LOPnotqso",
]
SUPPORTED_REGIONS = ["NGC", "SGC"]


@dataclass
class DESIPlan:
    tracer: str
    region: str
    version: str
    base_url: str
    data_url: str
    random_urls: list[str]
    data_local: str
    random_locals: list[str]
    reduced_data_csv: str
    reduced_random_csv: str
    warning: str


def build_lss_url(version: str, filename: str) -> str:
    return f"{DR1_LSS_BASE}/{version}/{filename}"


def build_desi_plan(
    tracer: str,
    region: str,
    version: str,
    random_indices: list[int],
    out_dir: Path,
) -> DESIPlan:
    if tracer not in SUPPORTED_TRACERS:
        raise ValueError(f"Unsupported tracer '{tracer}'. Known: {SUPPORTED_TRACERS}")
    if region not in SUPPORTED_REGIONS:
        raise ValueError(f"Unsupported region '{region}'. Use NGC or SGC.")

    out_dir.mkdir(parents=True, exist_ok=True)

    data_name = f"{tracer}_{region}_clustering.dat.fits"
    random_names = [f"{tracer}_{region}_{i}_clustering.ran.fits" for i in random_indices]

    return DESIPlan(
        tracer=tracer,
        region=region,
        version=version,
        base_url=f"{DR1_LSS_BASE}/{version}/",
        data_url=build_lss_url(version, data_name),
        random_urls=[build_lss_url(version, r) for r in random_names],
        data_local=str(out_dir / data_name),
        random_locals=[str(out_dir / r) for r in random_names],
        reduced_data_csv=str(out_dir / f"{tracer}_{region}_clustering.reduced.csv"),
        reduced_random_csv=str(out_dir / f"{tracer}_{region}_randoms.reduced.csv"),
        warning=(
            "DESI clustering/random FITS files can be large. Use --plan first; "
            "download only what you need; use --max-rows for a first lightweight pass."
        ),
    )


def download_file(url: str, dest: Path, overwrite: bool = False) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not overwrite:
        print(f"exists: {dest}")
        return

    print(f"download: {url}")
    print(f"      -> {dest}")

    def hook(block_num, block_size, total_size):
        if total_size > 0:
            done = block_num * block_size
            pct = min(100.0, 100.0 * done / total_size)
            if block_num % 200 == 0:
                print(f"  {pct:5.1f}% {done/1e9:.2f}/{total_size/1e9:.2f} GB", end="\r")

    urllib.request.urlretrieve(url, dest, hook)
    print(f"\nfinished: {dest}")


def normalize_columns(columns: list[str]) -> dict[str, str]:
    lower = {c.lower(): c for c in columns}
    mapping = {}

    for key in ["ra", "RA"]:
        if key.lower() in lower:
            mapping["ra"] = lower[key.lower()]
            break

    for key in ["dec", "DEC"]:
        if key.lower() in lower:
            mapping["dec"] = lower[key.lower()]
            break

    for key in ["z", "redshift", "Z", "Z_not4clus"]:
        if key.lower() in lower:
            mapping["redshift"] = lower[key.lower()]
            break

    # Common DESI LSS clustering weights. We multiply these if present.
    weight_candidates = [
        "weight",
        "WEIGHT",
        "WEIGHT_COMP",
        "WEIGHT_SYS",
        "WEIGHT_ZFAIL",
        "WEIGHT_FKP",
        "WEIGHT_RF",
    ]
    mapping["weights"] = [lower[w.lower()] for w in weight_candidates if w.lower() in lower]

    return mapping


def fits_to_reduced_csv(
    fits_paths: list[Path],
    out_csv: Path,
    max_rows: Optional[int] = None,
    seed: int = 1234,
) -> None:
    try:
        from astropy.table import Table
        import numpy as np
        import pandas as pd
    except ImportError as exc:
        raise ImportError(
            "FITS conversion needs astropy, numpy, pandas. Install: pip install astropy pandas numpy"
        ) from exc

    rng = np.random.default_rng(seed)
    frames = []

    for path in fits_paths:
        print(f"read FITS: {path}")
        tab = Table.read(path)
        cols = list(tab.colnames)
        m = normalize_columns(cols)

        missing = [k for k in ["ra", "dec", "redshift"] if k not in m]
        if missing:
            raise ValueError(f"{path} missing required columns {missing}. Available: {cols[:40]} ...")

        n = len(tab)
        if max_rows is not None and n > max_rows:
            idx = rng.choice(n, size=max_rows, replace=False)
            sub = tab[idx]
        else:
            sub = tab

        df = sub[[m["ra"], m["dec"], m["redshift"]]].to_pandas()
        df.columns = ["ra", "dec", "redshift"]

        if m["weights"]:
            weight = np.ones(len(sub), dtype=float)
            for wc in m["weights"]:
                try:
                    arr = np.asarray(sub[wc], dtype=float)
                    arr = np.where(np.isfinite(arr) & (arr > 0), arr, 1.0)
                    weight *= arr
                except Exception:
                    pass
            df["weight"] = weight
        else:
            df["weight"] = 1.0

        frames.append(df)

    out = pd.concat(frames, ignore_index=True)
    out.to_csv(out_csv, index=False)
    print(f"wrote reduced CSV: {out_csv} rows={len(out)}")


def run_cmd(cmd: list[str]) -> int:
    print("\n$", " ".join(cmd))
    return subprocess.call(cmd)


def run_pipeline(
    plan: DESIPlan,
    module_dir: Path,
    out_dir: Path,
    lensing_catalog: Optional[str],
    mock_glob: Optional[str],
    max_pairs: int,
) -> dict[str, str]:
    """
    Run available modules and return produced JSON paths.
    """
    outputs = {}

    data_csv = Path(plan.reduced_data_csv)
    random_csv = Path(plan.reduced_random_csv)

    zstab_json = out_dir / f"{plan.tracer}_{plan.region}_zstab.json"
    sys_json = out_dir / f"{plan.tracer}_{plan.region}_sys.json"
    mock_json = out_dir / f"{plan.tracer}_{plan.region}_mockcov.json"
    obs_json = out_dir / f"{plan.tracer}_{plan.region}_obs.json"
    verdict_json = out_dir / f"{plan.tracer}_{plan.region}_final_verdict.json"

    # Z stability.
    zstab_py = module_dir / "tc_zstab_pipeline.py"
    if zstab_py.exists():
        code = run_cmd([
            sys.executable, str(zstab_py),
            "--catalog", str(data_csv),
            "--n-bins", "5",
            "--min-per-bin", "50",
            "--out", str(zstab_json),
            "--max-pairs", str(max_pairs),
        ])
        if code == 0:
            outputs["zstab"] = str(zstab_json)

    # Systematics projection using randoms as footprint/template proxy.
    sys_py = module_dir / "tc_sys_projector.py"
    if sys_py.exists() and random_csv.exists():
        code = run_cmd([
            sys.executable, str(sys_py),
            "--observed", str(data_csv),
            "--systematics", str(random_csv),
            "--out", str(sys_json),
            "--max-pairs", str(max_pairs),
        ])
        if code == 0:
            outputs["systematics"] = str(sys_json)

    # Mock covariance if supplied.
    mock_py = module_dir / "tc_mock_cov.py"
    if mock_py.exists() and mock_glob:
        cmd = [
            sys.executable, str(mock_py),
            "--observed", str(data_csv),
            "--mock-glob", mock_glob,
            "--out", str(mock_json),
            "--max-pairs", str(max_pairs),
        ]
        if random_csv.exists():
            cmd.extend(["--systematics", str(random_csv)])
        code = run_cmd(cmd)
        if code == 0:
            outputs["mock"] = str(mock_json)

    # Cross-readout if lensing supplied.
    obs_py = module_dir / "tc_obs_pipeline.py"
    if obs_py.exists() and lensing_catalog:
        code = run_cmd([
            sys.executable, str(obs_py),
            "--galaxy", str(data_csv),
            "--lensing", lensing_catalog,
            "--n-nulls", "100",
            "--out", str(obs_json),
            "--max-pairs", str(max_pairs),
        ])
        if code == 0:
            outputs["obs"] = str(obs_json)

    # Final verdict if possible.
    verdict_py = module_dir / "tc_verdict_engine.py"
    if verdict_py.exists():
        cmd = [sys.executable, str(verdict_py), "--out", str(verdict_json)]
        if "obs" in outputs:
            cmd.extend(["--obs-result", outputs["obs"]])
        if "zstab" in outputs:
            cmd.extend(["--zstab-result", outputs["zstab"]])
        if "systematics" in outputs:
            cmd.extend(["--sys-result", outputs["systematics"]])
        if "mock" in outputs:
            cmd.extend(["--mock-result", outputs["mock"]])

        if len(cmd) > 4:
            code = run_cmd(cmd)
            if code == 0:
                outputs["verdict"] = str(verdict_json)

    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="TC-DESI-CONNECT-001 DESI DR1 connector for Tau-web pipeline")
    parser.add_argument("--tracer", default="LRG", choices=SUPPORTED_TRACERS)
    parser.add_argument("--region", default="NGC", choices=SUPPORTED_REGIONS)
    parser.add_argument("--version", default=DEFAULT_VERSION)
    parser.add_argument("--random-indices", nargs="*", type=int, default=[0])
    parser.add_argument("--out-dir", default="desi_tau_run")
    parser.add_argument("--module-dir", default=".")
    parser.add_argument("--plan", action="store_true", help="Only print URLs/paths; do not download/run")
    parser.add_argument("--download", action="store_true", help="Download DESI clustering/random files")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--prepare-csv", action="store_true", help="Convert FITS to reduced CSV")
    parser.add_argument("--max-rows", type=int, default=None, help="Max rows per FITS during CSV reduction")
    parser.add_argument("--run-pipeline", action="store_true", help="Run Tau modules after preparation")
    parser.add_argument("--lensing-catalog", default=None, help="Optional external lensing/kappa proxy CSV/FITS")
    parser.add_argument("--mock-glob", default=None, help="Optional mock CSV/FITS glob for tc_mock_cov")
    parser.add_argument("--max-pairs", type=int, default=300000)
    parser.add_argument("--seed", type=int, default=1234)

    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    module_dir = Path(args.module_dir)

    plan = build_desi_plan(
        tracer=args.tracer,
        region=args.region,
        version=args.version,
        random_indices=args.random_indices,
        out_dir=out_dir,
    )

    plan_json = out_dir / f"{args.tracer}_{args.region}_desi_plan.json"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(plan_json, "w", encoding="utf-8") as f:
        json.dump(asdict(plan), f, indent=2)

    print(json.dumps(asdict(plan), indent=2))
    print(f"\nplan written: {plan_json}")

    if args.plan:
        return

    if args.download:
        download_file(plan.data_url, Path(plan.data_local), overwrite=args.overwrite)
        for url, local in zip(plan.random_urls, plan.random_locals):
            download_file(url, Path(local), overwrite=args.overwrite)

    if args.prepare_csv:
        fits_to_reduced_csv([Path(plan.data_local)], Path(plan.reduced_data_csv), max_rows=args.max_rows, seed=args.seed)
        random_paths = [Path(p) for p in plan.random_locals if Path(p).exists()]
        if random_paths:
            fits_to_reduced_csv(random_paths, Path(plan.reduced_random_csv), max_rows=args.max_rows, seed=args.seed)
        else:
            print("no random FITS available for reduced random CSV")

    if args.run_pipeline:
        outputs = run_pipeline(
            plan=plan,
            module_dir=module_dir,
            out_dir=out_dir,
            lensing_catalog=args.lensing_catalog,
            mock_glob=args.mock_glob,
            max_pairs=args.max_pairs,
        )
        outputs_json = out_dir / f"{args.tracer}_{args.region}_pipeline_outputs.json"
        with open(outputs_json, "w", encoding="utf-8") as f:
            json.dump(outputs, f, indent=2)
        print("\nPipeline outputs:")
        print(json.dumps(outputs, indent=2))
        print(f"outputs written: {outputs_json}")


if __name__ == "__main__":
    main()
