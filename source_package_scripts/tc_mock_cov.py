#!/usr/bin/env python3
"""
TC-MOCK-COV-001
Mock covariance and LCDM-reference significance for Tau-web tensors.

Purpose
-------
Given an observed catalogue and a set of mock catalogues, compute:

  W_obs
  W_mock[k]
  v_obs in 5D STF tensor space
  mean_mock, covariance_mock
  Mahalanobis chi2
  empirical p-values for amplitude and chi2

Optional:
  project observed and mock tensors away from a systematics tensor subspace
  before computing significance.

This module converts the Tau-web statistic from a geometric candidate into
a statistical anomaly candidate.

Input
-----
Observed catalogue:
  x,y,z or ra,dec,redshift

Mock catalogues:
  same schema as observed

Optional systematics catalogues:
  same schema, used to build H_sys and clean all tensors:
    v_clean = (I - Pi_sys) v

Output
------
JSON summary and optional per-mock CSV.

Important
---------
This is a scaffold. Publication-grade usage requires official mocks,
survey covariance prescriptions, jackknife/bootstrap, and survey-specific
weights/masks/RSD/fibre corrections.
"""

from __future__ import annotations

import argparse
import glob
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
# Tensor statistic
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


def stf_to_vec(Q: np.ndarray) -> np.ndarray:
    Q = np.asarray(Q, dtype=float)
    return np.array([
        Q[0, 0],
        Q[1, 1],
        np.sqrt(2) * Q[0, 1],
        np.sqrt(2) * Q[0, 2],
        np.sqrt(2) * Q[1, 2],
    ])


def vec_to_stf(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    Q = np.zeros((3, 3))
    Q[0, 0] = v[0]
    Q[1, 1] = v[1]
    Q[2, 2] = -v[0] - v[1]
    Q[0, 1] = Q[1, 0] = v[2] / np.sqrt(2)
    Q[0, 2] = Q[2, 0] = v[3] / np.sqrt(2)
    Q[1, 2] = Q[2, 1] = v[4] / np.sqrt(2)
    return Q


def tensor_amp_from_vec(v: np.ndarray) -> float:
    Q = vec_to_stf(v)
    return float(np.sqrt(np.sum(Q * Q)))


def tensor_amp(Q: np.ndarray) -> float:
    return float(np.sqrt(np.sum(np.asarray(Q) * np.asarray(Q))))


# ----------------------------
# Systematics projection
# ----------------------------

def orthonormal_basis(vectors, eps=1e-12):
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
        return np.zeros((5, 0))
    return np.column_stack(basis)


def project_away(v, basis):
    if basis.shape[1] == 0:
        return v.copy(), np.zeros_like(v)
    sys = basis @ (basis.T @ v)
    return v - sys, sys


def build_sys_basis(paths, R=None, sigma_R=None, h0=67.66, omega_m=0.3111, max_pairs=300_000, seed=1234):
    vecs = []
    for i, p in enumerate(paths):
        df = load_table(p)
        X = table_to_xyz(df, h0=h0, omega_m=omega_m)
        w = table_weights(df)
        W = web_tensor(X, w, R=R, sigma_R=sigma_R, max_pairs=max_pairs, seed=seed + 1000 + i)
        vecs.append(stf_to_vec(W))
    return orthonormal_basis(vecs)


# ----------------------------
# Mock covariance
# ----------------------------

def empirical_p_greater(value, null_values):
    null_values = np.asarray(null_values, dtype=float)
    null_values = null_values[np.isfinite(null_values)]
    if len(null_values) == 0:
        return float("nan")
    return float((1 + np.sum(null_values >= value)) / (len(null_values) + 1))


def covariance_with_shrinkage(X: np.ndarray, shrink: float = 0.05) -> np.ndarray:
    """
    X shape: (n_mocks, 5)
    """
    cov = np.cov(X, rowvar=False, ddof=1)
    if cov.ndim == 0:
        cov = np.eye(X.shape[1]) * float(cov)
    diag = np.diag(np.diag(cov))
    return (1 - shrink) * cov + shrink * diag + 1e-10 * np.eye(cov.shape[0])


def mahalanobis(v, mean, invcov):
    d = v - mean
    return float(d.T @ invcov @ d)


@dataclass
class MockCovResult:
    n_mocks: int
    n_systematics: int
    sys_rank: int
    A_obs_clean: float
    A_mock_mean: float
    A_mock_sd: float
    p_amplitude_greater: float
    chi2_obs: float
    chi2_mock_mean: float
    chi2_mock_sd: float
    p_chi2_greater: float
    z_amp_rough: float
    W_obs_clean: list
    W_mock_mean: list
    verdict: str


def analyze_mock_cov(
    observed_path: str,
    mock_paths: list[str],
    systematics_paths: list[str] | None = None,
    R: Optional[float] = None,
    sigma_R: Optional[float] = None,
    h0: float = 67.66,
    omega_m: float = 0.3111,
    max_pairs: int = 300_000,
    seed: int = 1234,
    shrink: float = 0.05,
) -> tuple[MockCovResult, pd.DataFrame]:
    systematics_paths = systematics_paths or []

    basis = build_sys_basis(
        systematics_paths,
        R=R,
        sigma_R=sigma_R,
        h0=h0,
        omega_m=omega_m,
        max_pairs=max_pairs,
        seed=seed,
    ) if systematics_paths else np.zeros((5, 0))

    obs_df = load_table(observed_path)
    X_obs = table_to_xyz(obs_df, h0=h0, omega_m=omega_m)
    w_obs = table_weights(obs_df)
    W_obs = web_tensor(X_obs, w_obs, R=R, sigma_R=sigma_R, max_pairs=max_pairs, seed=seed)
    v_obs = stf_to_vec(W_obs)
    v_obs_clean, _ = project_away(v_obs, basis)

    mock_rows = []
    mock_vecs = []

    for i, p in enumerate(mock_paths):
        df = load_table(p)
        X = table_to_xyz(df, h0=h0, omega_m=omega_m)
        w = table_weights(df)
        W = web_tensor(X, w, R=R, sigma_R=sigma_R, max_pairs=max_pairs, seed=seed + 10_000 + i)
        v = stf_to_vec(W)
        v_clean, v_sys = project_away(v, basis)
        mock_vecs.append(v_clean)
        mock_rows.append({
            "mock": Path(p).name,
            "A_clean": tensor_amp_from_vec(v_clean),
            "A_raw": tensor_amp(W),
            "sys_removed_amp": tensor_amp_from_vec(v_sys),
        })

    M = np.vstack(mock_vecs)
    mean = np.mean(M, axis=0)
    cov = covariance_with_shrinkage(M, shrink=shrink)
    invcov = np.linalg.pinv(cov)

    chi2_obs = mahalanobis(v_obs_clean, mean, invcov)
    chi2_mocks = np.array([mahalanobis(M[i], mean, invcov) for i in range(len(M))])

    A_obs = tensor_amp_from_vec(v_obs_clean)
    A_mocks = np.array([tensor_amp_from_vec(v) for v in M])

    p_amp = empirical_p_greater(A_obs, A_mocks)
    p_chi2 = empirical_p_greater(chi2_obs, chi2_mocks)
    z_amp = float((A_obs - np.mean(A_mocks)) / (np.std(A_mocks, ddof=1) + 1e-12))

    if p_chi2 < 0.01 and p_amp < 0.05:
        verdict = "MOCK-RARE-STRONG"
    elif p_chi2 < 0.05 or p_amp < 0.05:
        verdict = "MOCK-RARE-WEAK"
    else:
        verdict = "MOCK-COMPATIBLE"

    result = MockCovResult(
        n_mocks=len(mock_paths),
        n_systematics=len(systematics_paths),
        sys_rank=int(basis.shape[1]),
        A_obs_clean=A_obs,
        A_mock_mean=float(np.mean(A_mocks)),
        A_mock_sd=float(np.std(A_mocks, ddof=1)),
        p_amplitude_greater=p_amp,
        chi2_obs=chi2_obs,
        chi2_mock_mean=float(np.mean(chi2_mocks)),
        chi2_mock_sd=float(np.std(chi2_mocks, ddof=1)),
        p_chi2_greater=p_chi2,
        z_amp_rough=z_amp,
        W_obs_clean=vec_to_stf(v_obs_clean).tolist(),
        W_mock_mean=vec_to_stf(mean).tolist(),
        verdict=verdict,
    )
    return result, pd.DataFrame(mock_rows)


def collect_mock_paths(mock_args, mock_glob):
    paths = []
    if mock_args:
        paths.extend(mock_args)
    if mock_glob:
        paths.extend(glob.glob(mock_glob))
    paths = sorted(set(str(Path(p)) for p in paths))
    if not paths:
        raise ValueError("No mock catalogues supplied. Use --mocks or --mock-glob.")
    return paths


def main():
    parser = argparse.ArgumentParser(description="TC-MOCK-COV-001 mock covariance for Tau-web tensor")
    parser.add_argument("--observed", required=True, help="Observed catalogue CSV/FITS")
    parser.add_argument("--mocks", nargs="*", default=None, help="Mock catalogue paths")
    parser.add_argument("--mock-glob", default=None, help="Glob pattern for mock catalogues")
    parser.add_argument("--systematics", nargs="*", default=None, help="Optional systematics template catalogues")
    parser.add_argument("--out", default="tau_mock_cov_result.json")
    parser.add_argument("--mock-out", default=None, help="Optional per-mock CSV")
    parser.add_argument("--R", type=float, default=None)
    parser.add_argument("--sigma-R", type=float, default=None)
    parser.add_argument("--h0", type=float, default=67.66)
    parser.add_argument("--omega-m", type=float, default=0.3111)
    parser.add_argument("--max-pairs", type=int, default=300000)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--shrink", type=float, default=0.05)
    args = parser.parse_args()

    mock_paths = collect_mock_paths(args.mocks, args.mock_glob)

    result, mock_df = analyze_mock_cov(
        args.observed,
        mock_paths,
        systematics_paths=args.systematics,
        R=args.R,
        sigma_R=args.sigma_R,
        h0=args.h0,
        omega_m=args.omega_m,
        max_pairs=args.max_pairs,
        seed=args.seed,
        shrink=args.shrink,
    )

    out = asdict(result)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    if args.mock_out:
        mock_df.to_csv(args.mock_out, index=False)

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
