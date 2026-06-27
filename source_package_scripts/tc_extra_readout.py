#!/usr/bin/env python3
"""
TC-EXTRA-READOUT-001
Velocity / CMB-lensing extra readout alignment module for Tau-web pipeline.

Purpose
-------
The Tau-web strong-witness criterion needs a third independent readout beyond:

  W_gal || W_lens

This module can test:

  1. peculiar-velocity tensor alignment:
       V_ab || W_gal

  2. CMB-lensing / ISW / external kappa tensor alignment:
       W_cmb_ab || W_gal

Input
-----
- --obs-result JSON from tc_obs_pipeline.py, containing W_gal.
- optional --velocity-catalog with columns:
    x,y,z,vx,vy,vz[,weight]
  or:
    ra,dec,redshift,vx,vy,vz[,weight]

- optional --cmb-kappa-catalog with columns:
    x,y,z,kappa
  or:
    ra,dec,redshift,kappa

Output
------
JSON with:
  velocity_alignment_pass
  cmb_alignment_pass
  C_gal_velocity
  C_gal_cmb
  final extra_readout_pass

This is a scaffold. Real velocity/CMB analysis requires survey-specific
systematics, selection functions, covariances, and blind testing.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


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
            raise ImportError("FITS input requires astropy. Install: pip install astropy") from exc
        return lower_columns(Table.read(path).to_pandas())
    raise ValueError(f"Unsupported file type: {path}")


def flat_lcdm_comoving_distance_mpc(z, h0=67.66, omega_m=0.3111, n_grid=4096):
    z = np.asarray(z, dtype=float)
    zmax = float(np.nanmax(z)) if z.size else 0.0
    if zmax <= 0:
        return np.zeros_like(z)
    c_km_s = 299792.458
    grid = np.linspace(0, zmax, n_grid)
    ez = np.sqrt(omega_m * (1 + grid) ** 3 + (1 - omega_m))
    inv = 1 / ez
    dz = grid[1] - grid[0]
    integ = np.zeros_like(grid)
    integ[1:] = np.cumsum(0.5 * (inv[1:] + inv[:-1]) * dz)
    return np.interp(z, grid, (c_km_s / h0) * integ)


def radec_to_unit_xyz(ra_deg, dec_deg):
    ra = np.deg2rad(np.asarray(ra_deg, dtype=float))
    dec = np.deg2rad(np.asarray(dec_deg, dtype=float))
    cosd = np.cos(dec)
    return np.column_stack([cosd * np.cos(ra), cosd * np.sin(ra), np.sin(dec)])


def find_col(df, candidates):
    cols = set(df.columns)
    for c in candidates:
        if c.lower() in cols:
            return c.lower()
    return None


def table_to_xyz(df, h0=67.66, omega_m=0.3111):
    cols = set(df.columns)
    if {"x", "y", "z"}.issubset(cols):
        return df[["x", "y", "z"]].to_numpy(dtype=float)

    racol = find_col(df, ["ra", "alpha"])
    deccol = find_col(df, ["dec", "delta"])
    zcol = find_col(df, ["redshift", "zred", "z_cosmo", "zobs"])
    if zcol is None and "z" in cols and not {"x", "y", "z"}.issubset(cols):
        zcol = "z"

    if racol and deccol and zcol:
        unit = radec_to_unit_xyz(df[racol].values, df[deccol].values)
        chi = flat_lcdm_comoving_distance_mpc(df[zcol].values, h0=h0, omega_m=omega_m)
        return unit * chi[:, None]

    raise ValueError("Need x,y,z or ra,dec,redshift coordinates.")


def table_weights(df, default_col_names=("weight", "weights")):
    for c in default_col_names:
        if c in df.columns:
            w = df[c].to_numpy(dtype=float)
            return np.where(np.isfinite(w) & (w > 0), w, 1.0)
    return np.ones(len(df), dtype=float)


def tensor_amp(Q):
    Q = np.asarray(Q, dtype=float)
    if not np.all(np.isfinite(Q)):
        return float("nan")
    return float(np.sqrt(np.sum(Q * Q)))


def tensor_cosine(A, B):
    A = np.asarray(A, dtype=float)
    B = np.asarray(B, dtype=float)
    denom = tensor_amp(A) * tensor_amp(B)
    if denom <= 0:
        return float("nan")
    return float(np.sum(A * B) / denom)


def principal_axis(Q):
    vals, vecs = np.linalg.eigh(np.asarray(Q, dtype=float))
    idx = int(np.argmax(np.abs(vals)))
    v = vecs[:, idx]
    return v / np.linalg.norm(v)


def axis_alignment(A, B):
    return float(abs(np.dot(principal_axis(A), principal_axis(B))))


def velocity_tensor(df: pd.DataFrame) -> np.ndarray:
    cols = set(df.columns)
    required = {"vx", "vy", "vz"}
    if not required.issubset(cols):
        raise ValueError("velocity catalogue needs vx,vy,vz columns")

    V = df[["vx", "vy", "vz"]].to_numpy(dtype=float)
    w = table_weights(df)
    ok = np.all(np.isfinite(V), axis=1) & np.isfinite(w) & (w > 0)
    V = V[ok]
    w = w[ok]

    if len(V) < 3:
        raise ValueError("Too few velocity vectors")

    # Remove mean bulk flow if present; tensor measures anisotropic velocity structure.
    Vc = V - np.average(V, axis=0, weights=w)
    norm = np.linalg.norm(Vc, axis=1)
    ok = norm > 0
    Vc = Vc[ok]
    w = w[ok]
    e = Vc / norm[ok, None]
    w = w / np.sum(w)

    Q = np.einsum("i,ia,ib->ab", w, e, e) - np.eye(3) / 3.0
    return Q


def density_tensor_from_kappa(df: pd.DataFrame, h0=67.66, omega_m=0.3111) -> np.ndarray:
    kcol = find_col(df, ["kappa", "convergence", "kap", "weight", "value"])
    if kcol is None:
        raise ValueError("cmb/kappa catalogue needs kappa/convergence/value column")
    X = table_to_xyz(df, h0=h0, omega_m=omega_m)
    k = df[kcol].to_numpy(dtype=float)
    # Use absolute kappa as anisotropy weight by default; signed maps can cancel too aggressively.
    w = np.abs(k)
    ok = np.all(np.isfinite(X), axis=1) & np.isfinite(w) & (w > 0)
    X = X[ok]
    w = w[ok]
    if len(X) < 3:
        raise ValueError("Too few kappa pixels")

    Xc = X - np.average(X, axis=0, weights=w)
    r = np.linalg.norm(Xc, axis=1)
    ok = r > 0
    e = Xc[ok] / r[ok, None]
    w = w[ok]
    w = w / np.sum(w)
    return np.einsum("i,ia,ib->ab", w, e, e) - np.eye(3) / 3.0


@dataclass
class ExtraReadoutResult:
    velocity_alignment_pass: bool
    cmb_alignment_pass: bool
    extra_readout_pass: bool
    C_gal_velocity: Optional[float]
    axis_gal_velocity: Optional[float]
    A_velocity: Optional[float]
    C_gal_cmb: Optional[float]
    axis_gal_cmb: Optional[float]
    A_cmb: Optional[float]
    threshold_C: float
    threshold_axis: float
    notes: list[str]


def analyze_extra(
    obs_result_path: str,
    velocity_catalog: Optional[str] = None,
    cmb_kappa_catalog: Optional[str] = None,
    threshold_C: float = 0.80,
    threshold_axis: float = 0.80,
    h0: float = 67.66,
    omega_m: float = 0.3111,
) -> ExtraReadoutResult:
    with open(obs_result_path, "r", encoding="utf-8") as f:
        obs = json.load(f)

    W_gal = np.array(obs["W_gal"], dtype=float)

    notes = []
    velocity_pass = False
    cmb_pass = False

    Cgv = axisgv = Av = None
    Cgc = axisgc = Ac = None

    if velocity_catalog:
        vdf = load_table(velocity_catalog)
        Vt = velocity_tensor(vdf)
        Cgv = tensor_cosine(W_gal, Vt)
        axisgv = axis_alignment(W_gal, Vt)
        Av = tensor_amp(Vt)
        velocity_pass = bool(Cgv >= threshold_C and axisgv >= threshold_axis)
        notes.append(f"velocity: C={Cgv:.4g}, axis={axisgv:.4g}, A={Av:.4g}")
    else:
        notes.append("velocity: missing")

    if cmb_kappa_catalog:
        cdf = load_table(cmb_kappa_catalog)
        Ct = density_tensor_from_kappa(cdf, h0=h0, omega_m=omega_m)
        Cgc = tensor_cosine(W_gal, Ct)
        axisgc = axis_alignment(W_gal, Ct)
        Ac = tensor_amp(Ct)
        cmb_pass = bool(Cgc >= threshold_C and axisgc >= threshold_axis)
        notes.append(f"cmb/kappa: C={Cgc:.4g}, axis={axisgc:.4g}, A={Ac:.4g}")
    else:
        notes.append("cmb/kappa: missing")

    return ExtraReadoutResult(
        velocity_alignment_pass=velocity_pass,
        cmb_alignment_pass=cmb_pass,
        extra_readout_pass=bool(velocity_pass or cmb_pass),
        C_gal_velocity=Cgv,
        axis_gal_velocity=axisgv,
        A_velocity=Av,
        C_gal_cmb=Cgc,
        axis_gal_cmb=axisgc,
        A_cmb=Ac,
        threshold_C=threshold_C,
        threshold_axis=threshold_axis,
        notes=notes,
    )


def main():
    parser = argparse.ArgumentParser(description="TC-EXTRA-READOUT-001 velocity/CMB extra readout alignment")
    parser.add_argument("--obs-result", required=True)
    parser.add_argument("--velocity-catalog", default=None)
    parser.add_argument("--cmb-kappa-catalog", default=None)
    parser.add_argument("--out", default="extra_readout_result.json")
    parser.add_argument("--threshold-C", type=float, default=0.80)
    parser.add_argument("--threshold-axis", type=float, default=0.80)
    parser.add_argument("--h0", type=float, default=67.66)
    parser.add_argument("--omega-m", type=float, default=0.3111)
    args = parser.parse_args()

    result = analyze_extra(
        obs_result_path=args.obs_result,
        velocity_catalog=args.velocity_catalog,
        cmb_kappa_catalog=args.cmb_kappa_catalog,
        threshold_C=args.threshold_C,
        threshold_axis=args.threshold_axis,
        h0=args.h0,
        omega_m=args.omega_m,
    )

    out = asdict(result)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
