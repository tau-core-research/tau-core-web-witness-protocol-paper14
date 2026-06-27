#!/usr/bin/env python3
"""
TC-LENSING-CONNECT-001
Lensing / mass-map connector for the Tau-web observational pipeline.

Purpose
-------
Convert an external lensing readout into the lightweight catalogue format
accepted by tc_obs_pipeline.py:

  ra, dec, redshift, kappa

or

  x, y, z, kappa

Supported modes
---------------
1. kappa-table
   Input already contains ra,dec,redshift,kappa or x,y,z,kappa.
   The connector normalizes column names and writes a reduced CSV.

2. shear-flat
   Input contains ra,dec and shear columns e1/e2 or g1/g2.
   The connector makes a crude flat-sky Kaiser-Squires E-mode kappa proxy
   on a rectangular grid, then writes pixel centres with kappa values.
   This is for development/testing, not production cosmology.

3. healpix-kappa
   Input is a HEALPix kappa/convergence FITS map.
   Requires healpy. Writes pixel centres as ra,dec,redshift,kappa.
   Use --redshift-proxy to assign an effective shell redshift.

Important warning
-----------------
A production weak-lensing analysis requires shear calibration, PSF systematics,
photo-z handling, masks, E/B-mode validation, covariance, and survey-specific
mass-map reconstruction. This connector is only a bridge into the Tau-web
tensor pipeline.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


# ----------------------------
# Generic loading
# ----------------------------

def lower_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def load_table(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix in [".csv", ".txt"]:
        return lower_columns(pd.read_csv(path))

    if suffix in [".fits", ".fit", ".fits.gz"]:
        try:
            from astropy.table import Table
        except ImportError as exc:
            raise ImportError("FITS table input requires astropy. Install: pip install astropy") from exc
        return lower_columns(Table.read(path).to_pandas())

    raise ValueError(f"Unsupported table type: {path}")


def find_col(df: pd.DataFrame, names: list[str]) -> Optional[str]:
    cols = set(df.columns)
    for n in names:
        if n.lower() in cols:
            return n.lower()
    return None


def normalize_kappa_table(
    input_path: str | Path,
    output_csv: str | Path,
    redshift_proxy: Optional[float] = None,
    max_rows: Optional[int] = None,
    seed: int = 1234,
) -> dict:
    df = load_table(input_path)
    rng = np.random.default_rng(seed)

    if max_rows is not None and len(df) > max_rows:
        df = df.iloc[rng.choice(len(df), size=max_rows, replace=False)].reset_index(drop=True)

    kcol = find_col(df, ["kappa", "kap", "convergence", "map", "value", "weight"])
    if kcol is None:
        raise ValueError("kappa-table mode requires kappa/convergence/map/value/weight column")

    if {"x", "y", "z"}.issubset(set(df.columns)):
        out = df[["x", "y", "z"]].copy()
        out["kappa"] = df[kcol].astype(float)
    else:
        racol = find_col(df, ["ra", "alpha"])
        deccol = find_col(df, ["dec", "delta"])
        zcol = find_col(df, ["redshift", "zred", "z_cosmo", "zobs"])

        if racol is None or deccol is None:
            raise ValueError("kappa-table needs either x,y,z or ra,dec plus kappa")

        out = pd.DataFrame({
            "ra": df[racol].astype(float),
            "dec": df[deccol].astype(float),
            "kappa": df[kcol].astype(float),
        })

        if zcol is not None:
            out["redshift"] = df[zcol].astype(float)
        elif redshift_proxy is not None:
            out["redshift"] = float(redshift_proxy)
        else:
            raise ValueError("ra/dec kappa table needs redshift column or --redshift-proxy")

        out = out[["ra", "dec", "redshift", "kappa"]]

    out = out.replace([np.inf, -np.inf], np.nan).dropna()
    out.to_csv(output_csv, index=False)

    return {
        "mode": "kappa-table",
        "rows_in": int(len(df)),
        "rows_out": int(len(out)),
        "output_csv": str(output_csv),
    }


# ----------------------------
# Flat-sky shear -> kappa proxy
# ----------------------------

def tangent_plane(ra_deg: np.ndarray, dec_deg: np.ndarray) -> tuple[np.ndarray, np.ndarray, float, float]:
    ra = np.deg2rad(np.asarray(ra_deg, dtype=float))
    dec = np.deg2rad(np.asarray(dec_deg, dtype=float))
    ra0 = float(np.mean(ra))
    dec0 = float(np.mean(dec))
    x = (ra - ra0) * np.cos(dec0)
    y = dec - dec0
    return x, y, np.rad2deg(ra0), np.rad2deg(dec0)


def inv_tangent_plane(x: np.ndarray, y: np.ndarray, ra0_deg: float, dec0_deg: float) -> tuple[np.ndarray, np.ndarray]:
    dec0 = np.deg2rad(dec0_deg)
    ra = np.deg2rad(ra0_deg) + x / np.cos(dec0)
    dec = np.deg2rad(dec0_deg) + y
    return np.rad2deg(ra) % 360.0, np.rad2deg(dec)


def shear_to_kappa_flat(
    input_path: str | Path,
    output_csv: str | Path,
    grid: int = 128,
    smooth_sigma_pix: float = 1.5,
    redshift_proxy: Optional[float] = None,
    min_weight: float = 1e-9,
    max_rows: Optional[int] = None,
    seed: int = 1234,
) -> dict:
    """
    Crude Kaiser-Squires flat-sky E-mode reconstruction:
      kappa_E(k) = [(kx^2-ky^2) gamma1(k) + 2kxky gamma2(k)] / k^2

    For development only.
    """
    rng = np.random.default_rng(seed)
    df = load_table(input_path)

    if max_rows is not None and len(df) > max_rows:
        df = df.iloc[rng.choice(len(df), size=max_rows, replace=False)].reset_index(drop=True)

    racol = find_col(df, ["ra", "alpha"])
    deccol = find_col(df, ["dec", "delta"])
    if racol is None or deccol is None:
        raise ValueError("shear-flat requires ra and dec")

    g1col = find_col(df, ["g1", "e1", "gamma1", "shear1"])
    g2col = find_col(df, ["g2", "e2", "gamma2", "shear2"])
    if g1col is None or g2col is None:
        raise ValueError("shear-flat requires g1/g2 or e1/e2 columns")

    wcol = find_col(df, ["weight", "w", "lens_weight"])
    zcol = find_col(df, ["redshift", "zred", "zphot", "z", "z_mean"])

    x, y, ra0, dec0 = tangent_plane(df[racol].values, df[deccol].values)
    g1 = df[g1col].to_numpy(dtype=float)
    g2 = df[g2col].to_numpy(dtype=float)
    w = df[wcol].to_numpy(dtype=float) if wcol else np.ones(len(df))
    w = np.where(np.isfinite(w) & (w > min_weight), w, 0.0)

    ok = np.isfinite(x) & np.isfinite(y) & np.isfinite(g1) & np.isfinite(g2) & (w > 0)
    x, y, g1, g2, w = x[ok], y[ok], g1[ok], g2[ok], w[ok]

    if len(x) < 10:
        raise ValueError("Too few valid shear sources")

    pad = 1e-6
    xmin, xmax = float(x.min() - pad), float(x.max() + pad)
    ymin, ymax = float(y.min() - pad), float(y.max() + pad)

    xi = np.clip(((x - xmin) / (xmax - xmin) * grid).astype(int), 0, grid - 1)
    yi = np.clip(((y - ymin) / (ymax - ymin) * grid).astype(int), 0, grid - 1)

    G1 = np.zeros((grid, grid), dtype=float)
    G2 = np.zeros((grid, grid), dtype=float)
    W = np.zeros((grid, grid), dtype=float)

    np.add.at(G1, (yi, xi), w * g1)
    np.add.at(G2, (yi, xi), w * g2)
    np.add.at(W, (yi, xi), w)

    mask = W > 0
    G1[mask] /= W[mask]
    G2[mask] /= W[mask]

    # Optional Gaussian smoothing if scipy is present.
    if smooth_sigma_pix and smooth_sigma_pix > 0:
        try:
            from scipy.ndimage import gaussian_filter
            G1 = gaussian_filter(G1, smooth_sigma_pix)
            G2 = gaussian_filter(G2, smooth_sigma_pix)
            W_s = gaussian_filter(W, smooth_sigma_pix)
            mask = W_s > np.percentile(W_s[W_s > 0], 20) if np.any(W_s > 0) else mask
        except Exception:
            pass

    ft1 = np.fft.fft2(G1)
    ft2 = np.fft.fft2(G2)

    ky = np.fft.fftfreq(grid) * 2 * np.pi
    kx = np.fft.fftfreq(grid) * 2 * np.pi
    KX, KY = np.meshgrid(kx, ky)
    K2 = KX * KX + KY * KY
    K2[0, 0] = np.inf

    kernel1 = (KX * KX - KY * KY) / K2
    kernel2 = (2 * KX * KY) / K2
    kappa_ft = kernel1 * ft1 + kernel2 * ft2
    kappa_ft[0, 0] = 0.0

    kappa = np.real(np.fft.ifft2(kappa_ft))

    yy, xx = np.indices((grid, grid))
    xcen = xmin + (xx + 0.5) / grid * (xmax - xmin)
    ycen = ymin + (yy + 0.5) / grid * (ymax - ymin)
    ra, dec = inv_tangent_plane(xcen.ravel(), ycen.ravel(), ra0, dec0)

    kval = kappa.ravel()
    m = mask.ravel() if mask.shape == kappa.shape else np.ones(kappa.size, dtype=bool)

    if redshift_proxy is not None:
        zval = np.full(kappa.size, float(redshift_proxy))
    elif zcol is not None:
        zval = np.full(kappa.size, float(np.nanmedian(df[zcol].to_numpy(dtype=float))))
    else:
        raise ValueError("shear-flat needs --redshift-proxy or a redshift/z column")

    out = pd.DataFrame({
        "ra": ra[m],
        "dec": dec[m],
        "redshift": zval[m],
        "kappa": kval[m],
    })
    out = out.replace([np.inf, -np.inf], np.nan).dropna()
    out.to_csv(output_csv, index=False)

    return {
        "mode": "shear-flat",
        "sources_in": int(len(df)),
        "valid_sources": int(len(x)),
        "grid": int(grid),
        "pixels_out": int(len(out)),
        "output_csv": str(output_csv),
        "warning": "Flat-sky Kaiser-Squires proxy only; not production-quality mass mapping.",
    }


# ----------------------------
# HEALPix map -> kappa table
# ----------------------------

def healpix_kappa_to_table(
    input_path: str | Path,
    output_csv: str | Path,
    redshift_proxy: float,
    max_pixels: Optional[int] = None,
    seed: int = 1234,
    min_abs_kappa: Optional[float] = None,
) -> dict:
    try:
        import healpy as hp
    except ImportError as exc:
        raise ImportError("healpix-kappa mode requires healpy. Install: pip install healpy") from exc

    rng = np.random.default_rng(seed)
    m = hp.read_map(str(input_path), verbose=False)
    m = np.asarray(m, dtype=float)
    nside = hp.get_nside(m)

    ok = np.isfinite(m)
    if min_abs_kappa is not None:
        ok &= np.abs(m) >= float(min_abs_kappa)

    pix = np.where(ok)[0]
    if max_pixels is not None and len(pix) > max_pixels:
        pix = rng.choice(pix, size=max_pixels, replace=False)

    theta, phi = hp.pix2ang(nside, pix)
    ra = np.rad2deg(phi)
    dec = 90.0 - np.rad2deg(theta)

    out = pd.DataFrame({
        "ra": ra,
        "dec": dec,
        "redshift": float(redshift_proxy),
        "kappa": m[pix],
    })
    out.to_csv(output_csv, index=False)

    return {
        "mode": "healpix-kappa",
        "nside": int(nside),
        "pixels_out": int(len(out)),
        "output_csv": str(output_csv),
    }


# ----------------------------
# Optional downstream Tau run
# ----------------------------

def run_obs_pipeline(
    galaxy_catalog: str,
    lensing_csv: str,
    module_dir: str,
    out_json: str,
    max_pairs: int,
) -> int:
    script = Path(module_dir) / "tc_obs_pipeline.py"
    if not script.exists():
        raise FileNotFoundError(script)

    cmd = [
        "python", str(script),
        "--galaxy", galaxy_catalog,
        "--lensing", lensing_csv,
        "--n-nulls", "100",
        "--out", out_json,
        "--max-pairs", str(max_pairs),
    ]
    print("$", " ".join(cmd))
    return __import__("subprocess").call(cmd)


def main() -> None:
    parser = argparse.ArgumentParser(description="TC-LENSING-CONNECT-001 lensing connector")
    parser.add_argument("--mode", required=True, choices=["kappa-table", "shear-flat", "healpix-kappa"])
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True, help="Output reduced lensing CSV")
    parser.add_argument("--redshift-proxy", type=float, default=None)
    parser.add_argument("--max-rows", type=int, default=None)
    parser.add_argument("--max-pixels", type=int, default=None)
    parser.add_argument("--min-abs-kappa", type=float, default=None)
    parser.add_argument("--grid", type=int, default=128)
    parser.add_argument("--smooth-sigma-pix", type=float, default=1.5)
    parser.add_argument("--seed", type=int, default=1234)

    parser.add_argument("--run-obs", action="store_true")
    parser.add_argument("--galaxy-catalog", default=None)
    parser.add_argument("--module-dir", default=".")
    parser.add_argument("--obs-out", default="tau_obs_from_lensing_connector.json")
    parser.add_argument("--max-pairs", type=int, default=300000)

    args = parser.parse_args()

    if args.mode == "kappa-table":
        meta = normalize_kappa_table(
            args.input,
            args.out,
            redshift_proxy=args.redshift_proxy,
            max_rows=args.max_rows,
            seed=args.seed,
        )
    elif args.mode == "shear-flat":
        meta = shear_to_kappa_flat(
            args.input,
            args.out,
            grid=args.grid,
            smooth_sigma_pix=args.smooth_sigma_pix,
            redshift_proxy=args.redshift_proxy,
            max_rows=args.max_rows,
            seed=args.seed,
        )
    elif args.mode == "healpix-kappa":
        if args.redshift_proxy is None:
            raise ValueError("healpix-kappa requires --redshift-proxy")
        meta = healpix_kappa_to_table(
            args.input,
            args.out,
            redshift_proxy=args.redshift_proxy,
            max_pixels=args.max_pixels,
            seed=args.seed,
            min_abs_kappa=args.min_abs_kappa,
        )
    else:
        raise ValueError(args.mode)

    if args.run_obs:
        if args.galaxy_catalog is None:
            raise ValueError("--run-obs requires --galaxy-catalog")
        code = run_obs_pipeline(
            galaxy_catalog=args.galaxy_catalog,
            lensing_csv=args.out,
            module_dir=args.module_dir,
            out_json=args.obs_out,
            max_pairs=args.max_pairs,
        )
        meta["obs_pipeline_exit_code"] = int(code)
        meta["obs_result_json"] = args.obs_out

    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
