#!/usr/bin/env python3
"""
TC-SYS-PROJECTOR-001
Systematics projector for Tau-web tensor analysis.

Purpose
-------
Given an observed catalogue and one or more systematics/random catalogues,
compute the observed web tensor W_obs and a systematics subspace H_sys.
Then project W_obs orthogonally away from H_sys:

    W_clean = (I - Pi_sys) W_obs

The tensors are represented in a 5D basis of symmetric trace-free 3x3 tensors.

Use cases
---------
- survey footprint/random catalogue tensor
- angular mask tensor
- completeness map proxy
- stellar contamination proxy
- redshift failure proxy
- fibre assignment proxy
- any catalogue-like systematics map converted to points

Input
-----
Observed catalogue:
  x,y,z or ra,dec,redshift

Systematics catalogues:
  x,y,z or ra,dec,redshift

Output
------
JSON with:
- W_obs
- W_sys_basis
- W_projected_sys
- W_clean
- amplitudes and retained fraction
- verdict

This is a scaffold, not a production survey-analysis replacement.
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
# Loading and coordinates
# ----------------------------

def _lower_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def load_table(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix in [".csv", ".txt"]:
        return _lower_columns(pd.read_csv(path))

    if suffix in [".fits", ".fit", ".fits.gz"]:
        try:
            from astropy.table import Table
        except ImportError as exc:
            raise ImportError("FITS input requires astropy. Install with: pip install astropy") from exc
        return _lower_columns(Table.read(path).to_pandas())

    raise ValueError(f"Unsupported file type: {path}")


def flat_lcdm_comoving_distance_mpc(z, h0=67.66, omega_m=0.3111, n_grid=4096):
    z = np.asarray(z, dtype=float)
    zmax = float(np.nanmax(z)) if z.size else 0.0
    if zmax <= 0:
        return np.zeros_like(z)

    c_km_s = 299792.458
    grid = np.linspace(0.0, zmax, n_grid)
    ez = np.sqrt(omega_m * (1 + grid) ** 3 + (1 - omega_m))
    inv_e = 1 / ez
    dz = grid[1] - grid[0]
    integ = np.zeros_like(grid)
    integ[1:] = np.cumsum(0.5 * (inv_e[1:] + inv_e[:-1]) * dz)
    return np.interp(z, grid, (c_km_s / h0) * integ)


def radec_to_unit_xyz(ra_deg, dec_deg):
    ra = np.deg2rad(np.asarray(ra_deg, dtype=float))
    dec = np.deg2rad(np.asarray(dec_deg, dtype=float))
    cosd = np.cos(dec)
    return np.column_stack([cosd * np.cos(ra), cosd * np.sin(ra), np.sin(dec)])


def table_to_xyz(df: pd.DataFrame, h0=67.66, omega_m=0.3111) -> np.ndarray:
    cols = set(df.columns)

    if {"x", "y", "z"}.issubset(cols):
        return df[["x", "y", "z"]].to_numpy(dtype=float)

    zcol = None
    for candidate in ["redshift", "zred", "z_cosmo", "zobs"]:
        if candidate in cols:
            zcol = candidate
            break
    if zcol is None and "z" in cols and not {"x", "y", "z"}.issubset(cols):
        zcol = "z"

    if {"ra", "dec"}.issubset(cols) and zcol is not None:
        unit = radec_to_unit_xyz(df["ra"].values, df["dec"].values)
        chi = flat_lcdm_comoving_distance_mpc(df[zcol].values, h0=h0, omega_m=omega_m)
        return unit * chi[:, None]

    raise ValueError("Table must contain either x,y,z or ra,dec,redshift/zred/z_cosmo/zobs.")


def table_weights(df: pd.DataFrame) -> np.ndarray:
    for col in ["weight", "weights", "fkp_weight", "comp_weight", "sys_weight"]:
        if col in df.columns:
            w = df[col].to_numpy(dtype=float)
            return np.where(np.isfinite(w) & (w > 0), w, 1.0)
    return np.ones(len(df), dtype=float)


# ----------------------------
# Web tensor
# ----------------------------

def pairwise_sqdist(X):
    norms = np.sum(X * X, axis=1)
    return norms[:, None] + norms[None, :] - 2 * X @ X.T


def estimate_default_scale(X, rng, sample_n=384):
    idx = rng.choice(len(X), size=min(len(X), sample_n), replace=False)
    Y = X[idx]
    D = np.sqrt(np.maximum(pairwise_sqdist(Y), 0))
    tri = D[np.triu_indices_from(D, 1)]
    return float(np.nanmedian(tri))


def pairwise_sample_indices(n, max_pairs, rng):
    total = n * (n - 1) // 2
    if total <= max_pairs:
        return np.triu_indices(n, 1)
    i = rng.integers(0, n, size=max_pairs)
    j = rng.integers(0, n, size=max_pairs)
    mask = i != j
    return i[mask], j[mask]


def web_tensor(X, weights=None, R=None, sigma_R=None, max_pairs=300_000, seed=1234):
    X = np.asarray(X, dtype=float)
    ok = np.all(np.isfinite(X), axis=1)
    X = X[ok]

    if weights is None:
        weights = np.ones(len(X), dtype=float)
    else:
        weights = np.asarray(weights, dtype=float)[ok]
        weights = np.where(np.isfinite(weights) & (weights > 0), weights, 1.0)

    if len(X) < 5:
        return np.full((3, 3), np.nan)

    rng = np.random.default_rng(seed)
    Xc = X - np.average(X, axis=0, weights=weights)

    if R is None:
        R = estimate_default_scale(Xc, rng)
    if sigma_R is None:
        sigma_R = 0.5 * R

    i, j = pairwise_sample_indices(len(Xc), max_pairs, rng)
    diff = Xc[j] - Xc[i]
    r = np.linalg.norm(diff, axis=1)
    ok = np.isfinite(r) & (r > 0)
    diff, r, i, j = diff[ok], r[ok], i[ok], j[ok]

    e = diff / r[:, None]
    K = np.exp(-0.5 * ((r - R) / sigma_R) ** 2)
    wij = weights[i] * weights[j] * K
    denom = np.sum(wij)

    if denom <= 0:
        return np.full((3, 3), np.nan)

    Q = np.einsum("i,ia,ib->ab", wij, e, e) / denom
    Q -= np.eye(3) / 3.0
    return Q


# ----------------------------
# STF vector space projection
# ----------------------------

def stf_to_vec(Q: np.ndarray) -> np.ndarray:
    """
    Map symmetric trace-free 3x3 tensor to 5D vector.
    Basis convention:
      v0 = Q_xx
      v1 = Q_yy
      v2 = sqrt(2) Q_xy
      v3 = sqrt(2) Q_xz
      v4 = sqrt(2) Q_yz

    Q_zz is implied by trace-free condition.
    This preserves Frobenius inner product up to the trace-free basis convention.
    """
    Q = np.asarray(Q, dtype=float)
    return np.array([
        Q[0, 0],
        Q[1, 1],
        np.sqrt(2) * Q[0, 1],
        np.sqrt(2) * Q[0, 2],
        np.sqrt(2) * Q[1, 2],
    ], dtype=float)


def vec_to_stf(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    Q = np.zeros((3, 3), dtype=float)
    Q[0, 0] = v[0]
    Q[1, 1] = v[1]
    Q[2, 2] = -v[0] - v[1]
    Q[0, 1] = Q[1, 0] = v[2] / np.sqrt(2)
    Q[0, 2] = Q[2, 0] = v[3] / np.sqrt(2)
    Q[1, 2] = Q[2, 1] = v[4] / np.sqrt(2)
    return Q


def tensor_amp(Q) -> float:
    if not np.all(np.isfinite(Q)):
        return float("nan")
    return float(np.sqrt(np.sum(Q * Q)))


def tensor_cos(A, B) -> float:
    denom = tensor_amp(A) * tensor_amp(B)
    if denom <= 0:
        return float("nan")
    return float(np.sum(A * B) / denom)


def orthonormal_basis(vectors: list[np.ndarray], eps: float = 1e-12) -> np.ndarray:
    """
    Modified Gram-Schmidt in 5D.
    Returns matrix B with basis vectors as columns.
    """
    basis = []
    for v in vectors:
        v = np.asarray(v, dtype=float)
        if not np.all(np.isfinite(v)):
            continue
        u = v.copy()
        for b in basis:
            u -= np.dot(b, u) * b
        norm = np.linalg.norm(u)
        if norm > eps:
            basis.append(u / norm)
    if not basis:
        return np.zeros((5, 0), dtype=float)
    return np.column_stack(basis)


def project_away(v_obs: np.ndarray, basis: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Returns (v_clean, v_sys_projected).
    """
    if basis.shape[1] == 0:
        return v_obs.copy(), np.zeros_like(v_obs)
    v_sys = basis @ (basis.T @ v_obs)
    return v_obs - v_sys, v_sys


# ----------------------------
# Analysis
# ----------------------------

@dataclass
class SysProjectorResult:
    A_obs: float
    A_sys_projected: float
    A_clean: float
    retained_fraction: float
    sys_fraction: float
    cos_obs_sys: float
    W_obs: list
    W_sys_projected: list
    W_clean: list
    n_systematics: int
    sys_rank: int
    verdict: str


def analyze_systematics(
    observed_path: str | Path,
    systematics_paths: list[str],
    R: Optional[float] = None,
    sigma_R: Optional[float] = None,
    h0: float = 67.66,
    omega_m: float = 0.3111,
    max_pairs: int = 300_000,
    seed: int = 1234,
) -> SysProjectorResult:
    obs_df = load_table(observed_path)
    X_obs = table_to_xyz(obs_df, h0=h0, omega_m=omega_m)
    w_obs = table_weights(obs_df)
    W_obs = web_tensor(X_obs, w_obs, R=R, sigma_R=sigma_R, max_pairs=max_pairs, seed=seed)

    sys_tensors = []
    for i, p in enumerate(systematics_paths):
        sys_df = load_table(p)
        X_sys = table_to_xyz(sys_df, h0=h0, omega_m=omega_m)
        w_sys = table_weights(sys_df)
        W_sys = web_tensor(X_sys, w_sys, R=R, sigma_R=sigma_R, max_pairs=max_pairs, seed=seed + 1000 + i)
        sys_tensors.append(W_sys)

    v_obs = stf_to_vec(W_obs)
    sys_vecs = [stf_to_vec(W) for W in sys_tensors]
    B = orthonormal_basis(sys_vecs)

    v_clean, v_sysproj = project_away(v_obs, B)

    W_clean = vec_to_stf(v_clean)
    W_sysproj = vec_to_stf(v_sysproj)

    A_obs = tensor_amp(W_obs)
    A_clean = tensor_amp(W_clean)
    A_sys = tensor_amp(W_sysproj)
    retained = A_clean / A_obs if A_obs > 0 else float("nan")
    sysfrac = A_sys / A_obs if A_obs > 0 else float("nan")
    cos = tensor_cos(W_obs, W_sysproj) if A_sys > 0 else 0.0

    if retained < 0.25:
        verdict = "SYSTEMATICS-DOMINATED"
    elif retained < 0.60:
        verdict = "PARTIALLY-SYSTEMATICS-CONTAMINATED"
    else:
        verdict = "CLEAN-CANDIDATE"

    return SysProjectorResult(
        A_obs=A_obs,
        A_sys_projected=A_sys,
        A_clean=A_clean,
        retained_fraction=float(retained),
        sys_fraction=float(sysfrac),
        cos_obs_sys=float(cos),
        W_obs=W_obs.tolist(),
        W_sys_projected=W_sysproj.tolist(),
        W_clean=W_clean.tolist(),
        n_systematics=len(systematics_paths),
        sys_rank=int(B.shape[1]),
        verdict=verdict,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="TC-SYS-PROJECTOR-001 systematics projector")
    parser.add_argument("--observed", required=True, help="Observed catalogue CSV/FITS")
    parser.add_argument("--systematics", nargs="+", required=True, help="One or more systematics/random catalogues")
    parser.add_argument("--out", default="tau_sys_projector_result.json")
    parser.add_argument("--R", type=float, default=None)
    parser.add_argument("--sigma-R", type=float, default=None)
    parser.add_argument("--h0", type=float, default=67.66)
    parser.add_argument("--omega-m", type=float, default=0.3111)
    parser.add_argument("--max-pairs", type=int, default=300000)
    parser.add_argument("--seed", type=int, default=1234)
    args = parser.parse_args()

    result = analyze_systematics(
        args.observed,
        args.systematics,
        R=args.R,
        sigma_R=args.sigma_R,
        h0=args.h0,
        omega_m=args.omega_m,
        max_pairs=args.max_pairs,
        seed=args.seed,
    )

    out = asdict(result)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
