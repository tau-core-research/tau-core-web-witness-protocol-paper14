#!/usr/bin/env python3
"""
TC-ZSTAB-001
Redshift-slice stability extension for the Tau-web observational pipeline.

This script computes the galaxy web tensor W_ab in multiple redshift/radial
slices and measures whether the dominant tensor pattern is stable across slices.

Main statistic
--------------
S_z = mean_{i<j} cos_tensor(W_i, W_j), with optional amplitude thresholding.

Tau-compatible expectation
--------------------------
A genuine large-scale Tau-morphological web candidate should not merely appear
as one anomalous slice. It should show a stable orientation across adjacent
redshift bins, after null/systematics controls.

Input
-----
CSV/FITS catalogue with either:
  - x,y,z Cartesian coordinates, or
  - ra,dec,redshift

For Cartesian input without redshift, the script uses radial distance as a proxy
and creates radial bins.

Output
------
JSON summary plus optional per-bin CSV.
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
# Minimal reused utilities
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


def flat_lcdm_comoving_distance_mpc(
    z: np.ndarray,
    h0: float = 67.66,
    omega_m: float = 0.3111,
    n_grid: int = 4096,
) -> np.ndarray:
    z = np.asarray(z, dtype=float)
    zmax = float(np.nanmax(z)) if z.size else 0.0
    if zmax <= 0:
        return np.zeros_like(z)

    c_km_s = 299792.458
    grid = np.linspace(0.0, zmax, n_grid)
    ez = np.sqrt(omega_m * (1.0 + grid) ** 3 + (1.0 - omega_m))
    inv_e = 1.0 / ez
    dz = grid[1] - grid[0]
    integ = np.zeros_like(grid)
    integ[1:] = np.cumsum(0.5 * (inv_e[1:] + inv_e[:-1]) * dz)
    return np.interp(z, grid, (c_km_s / h0) * integ)


def radec_to_unit_xyz(ra_deg: np.ndarray, dec_deg: np.ndarray) -> np.ndarray:
    ra = np.deg2rad(np.asarray(ra_deg, dtype=float))
    dec = np.deg2rad(np.asarray(dec_deg, dtype=float))
    cosd = np.cos(dec)
    return np.column_stack([cosd * np.cos(ra), cosd * np.sin(ra), np.sin(dec)])


def find_redshift_column(df: pd.DataFrame) -> Optional[str]:
    for candidate in ["redshift", "zred", "z_cosmo", "zobs"]:
        if candidate in df.columns:
            return candidate
    # Avoid treating Cartesian z as redshift if x/y also exist.
    if "z" in df.columns and not {"x", "y", "z"}.issubset(df.columns):
        return "z"
    return None


def table_to_xyz_and_slicevar(
    df: pd.DataFrame,
    h0: float = 67.66,
    omega_m: float = 0.3111,
) -> tuple[np.ndarray, np.ndarray, str]:
    cols = set(df.columns)

    if {"x", "y", "z"}.issubset(cols):
        X = df[["x", "y", "z"]].to_numpy(dtype=float)
        radius = np.linalg.norm(X, axis=1)
        return X, radius, "radius"

    zcol = find_redshift_column(df)
    if {"ra", "dec"}.issubset(cols) and zcol is not None:
        unit = radec_to_unit_xyz(df["ra"].values, df["dec"].values)
        z = df[zcol].to_numpy(dtype=float)
        chi = flat_lcdm_comoving_distance_mpc(z, h0=h0, omega_m=omega_m)
        return unit * chi[:, None], z, zcol

    raise ValueError("Input must contain either x,y,z or ra,dec,redshift/zred/z_cosmo/zobs.")


def table_weights(df: pd.DataFrame) -> np.ndarray:
    for col in ["weight", "weights", "fkp_weight", "comp_weight"]:
        if col in df.columns:
            w = df[col].to_numpy(dtype=float)
            return np.where(np.isfinite(w) & (w > 0), w, 1.0)
    return np.ones(len(df), dtype=float)


def pairwise_sample_indices(n: int, max_pairs: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    total = n * (n - 1) // 2
    if total <= max_pairs:
        return np.triu_indices(n, 1)

    i = rng.integers(0, n, size=max_pairs)
    j = rng.integers(0, n, size=max_pairs)
    mask = i != j
    return i[mask], j[mask]


def pairwise_sqdist(X: np.ndarray) -> np.ndarray:
    norms = np.sum(X * X, axis=1)
    return norms[:, None] + norms[None, :] - 2 * X @ X.T


def estimate_default_scale(X: np.ndarray, rng: np.random.Generator, sample_n: int = 384) -> float:
    idx = rng.choice(len(X), size=min(len(X), sample_n), replace=False)
    Y = X[idx]
    D = np.sqrt(np.maximum(pairwise_sqdist(Y), 0))
    tri = D[np.triu_indices_from(D, 1)]
    return float(np.nanmedian(tri))


def web_tensor(
    X: np.ndarray,
    weights: np.ndarray,
    R: Optional[float] = None,
    sigma_R: Optional[float] = None,
    max_pairs: int = 200_000,
    seed: int = 1234,
) -> np.ndarray:
    X = np.asarray(X, dtype=float)
    weights = np.asarray(weights, dtype=float)

    ok = np.all(np.isfinite(X), axis=1) & np.isfinite(weights) & (weights > 0)
    X = X[ok]
    weights = weights[ok]

    if len(X) < 5:
        return np.full((3, 3), np.nan)

    rng = np.random.default_rng(seed)
    Xc = X - np.average(X, axis=0, weights=weights)

    if R is None:
        R = estimate_default_scale(Xc, rng)
    if sigma_R is None:
        sigma_R = 0.5 * R

    i, j = pairwise_sample_indices(len(Xc), max_pairs=max_pairs, rng=rng)
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


def tensor_amp(Q: np.ndarray) -> float:
    if not np.all(np.isfinite(Q)):
        return float("nan")
    return float(np.sqrt(np.sum(Q * Q)))


def tensor_cosine(A: np.ndarray, B: np.ndarray) -> float:
    if not (np.all(np.isfinite(A)) and np.all(np.isfinite(B))):
        return float("nan")
    denom = tensor_amp(A) * tensor_amp(B)
    if denom <= 0:
        return float("nan")
    return float(np.sum(A * B) / denom)


def principal_axis(Q: np.ndarray) -> np.ndarray:
    vals, vecs = np.linalg.eigh(Q)
    idx = int(np.argmax(np.abs(vals)))
    v = vecs[:, idx]
    return v / np.linalg.norm(v)


def axis_dot(A: np.ndarray, B: np.ndarray) -> float:
    if not (np.all(np.isfinite(A)) and np.all(np.isfinite(B))):
        return float("nan")
    return float(abs(np.dot(principal_axis(A), principal_axis(B))))


# ----------------------------
# Redshift/radius stability
# ----------------------------

@dataclass
class BinResult:
    bin_index: int
    lo: float
    hi: float
    n_objects: int
    amplitude: float
    W: list


@dataclass
class ZStabResult:
    slice_variable: str
    n_bins: int
    min_per_bin: int
    valid_bins: int
    S_z_tensor: float
    S_z_axis: float
    amplitudes: list
    bin_results: list
    verdict: str


def make_bins(values: np.ndarray, n_bins: int, quantile_bins: bool = True) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]

    if quantile_bins:
        qs = np.linspace(0, 1, n_bins + 1)
        edges = np.quantile(values, qs)
        # Avoid duplicate edges.
        edges = np.unique(edges)
        if len(edges) < 3:
            raise ValueError("Too few unique bin edges.")
        return edges

    return np.linspace(np.nanmin(values), np.nanmax(values), n_bins + 1)


def compute_z_stability(
    X: np.ndarray,
    slice_var: np.ndarray,
    weights: np.ndarray,
    n_bins: int = 5,
    min_per_bin: int = 50,
    quantile_bins: bool = True,
    R: Optional[float] = None,
    sigma_R: Optional[float] = None,
    max_pairs: int = 200_000,
    seed: int = 1234,
) -> ZStabResult:
    edges = make_bins(slice_var, n_bins=n_bins, quantile_bins=quantile_bins)
    tensors = []
    bin_results = []

    for b in range(len(edges) - 1):
        lo, hi = edges[b], edges[b + 1]
        if b == len(edges) - 2:
            mask = (slice_var >= lo) & (slice_var <= hi)
        else:
            mask = (slice_var >= lo) & (slice_var < hi)

        n = int(np.sum(mask))
        if n < min_per_bin:
            W = np.full((3, 3), np.nan)
            amp = float("nan")
        else:
            W = web_tensor(
                X[mask],
                weights[mask],
                R=R,
                sigma_R=sigma_R,
                max_pairs=max_pairs,
                seed=seed + b,
            )
            amp = tensor_amp(W)
            tensors.append(W)

        bin_results.append(BinResult(
            bin_index=b,
            lo=float(lo),
            hi=float(hi),
            n_objects=n,
            amplitude=amp,
            W=W.tolist() if np.all(np.isfinite(W)) else [[None]*3 for _ in range(3)],
        ))

    cosines = []
    axes = []
    for i in range(len(tensors)):
        for j in range(i + 1, len(tensors)):
            cosines.append(tensor_cosine(tensors[i], tensors[j]))
            axes.append(axis_dot(tensors[i], tensors[j]))

    S_z_tensor = float(np.nanmean(cosines)) if cosines else float("nan")
    S_z_axis = float(np.nanmean(axes)) if axes else float("nan")
    amps = [br.amplitude for br in bin_results]

    if len(tensors) < 3:
        verdict = "INSUFFICIENT-BINS"
    elif S_z_tensor > 0.8 and S_z_axis > 0.8:
        verdict = "Z-STABLE"
    elif S_z_axis > 0.8 and S_z_tensor > 0.4:
        verdict = "AXIS-STABLE-WEAK"
    else:
        verdict = "Z-UNSTABLE"

    return ZStabResult(
        slice_variable="",
        n_bins=len(edges) - 1,
        min_per_bin=min_per_bin,
        valid_bins=len(tensors),
        S_z_tensor=S_z_tensor,
        S_z_axis=S_z_axis,
        amplitudes=amps,
        bin_results=[asdict(br) for br in bin_results],
        verdict=verdict,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="TC-ZSTAB-001 redshift/radial web tensor stability")
    parser.add_argument("--catalog", required=True, help="Galaxy catalogue CSV/FITS")
    parser.add_argument("--out", default="tau_zstab_result.json")
    parser.add_argument("--bins-out", default=None)
    parser.add_argument("--n-bins", type=int, default=5)
    parser.add_argument("--min-per-bin", type=int, default=50)
    parser.add_argument("--equal-width", action="store_true", help="Use equal-width instead of quantile bins")
    parser.add_argument("--R", type=float, default=None)
    parser.add_argument("--sigma-R", type=float, default=None)
    parser.add_argument("--h0", type=float, default=67.66)
    parser.add_argument("--omega-m", type=float, default=0.3111)
    parser.add_argument("--max-pairs", type=int, default=200000)
    parser.add_argument("--seed", type=int, default=1234)

    args = parser.parse_args()

    df = load_table(args.catalog)
    X, slice_var, var_name = table_to_xyz_and_slicevar(df, h0=args.h0, omega_m=args.omega_m)
    w = table_weights(df)

    result = compute_z_stability(
        X,
        slice_var,
        w,
        n_bins=args.n_bins,
        min_per_bin=args.min_per_bin,
        quantile_bins=not args.equal_width,
        R=args.R,
        sigma_R=args.sigma_R,
        max_pairs=args.max_pairs,
        seed=args.seed,
    )
    result.slice_variable = var_name

    out = asdict(result)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    if args.bins_out:
        pd.DataFrame([
            {
                "bin_index": br["bin_index"],
                "lo": br["lo"],
                "hi": br["hi"],
                "n_objects": br["n_objects"],
                "amplitude": br["amplitude"],
            }
            for br in out["bin_results"]
        ]).to_csv(args.bins_out, index=False)

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
