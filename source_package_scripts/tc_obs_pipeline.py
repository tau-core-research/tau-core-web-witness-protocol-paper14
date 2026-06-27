#!/usr/bin/env python3
"""
TC-OBS-PIPELINE-001
Tau-web observational tensor pipeline.

Purpose
-------
Estimate a large-scale anisotropic web tensor W_ab from galaxy and lensing
catalogues, compare cross-readout alignment, and run basic null tests.

This is a research pipeline scaffold. It does not download survey data.
You provide catalogues as CSV files or FITS files.

Required galaxy columns, one of:
  A) x, y, z  : Cartesian comoving coordinates
  B) ra, dec, redshift : sky position and redshift

Optional galaxy columns:
  weight      : survey/completeness/FKP/etc. weight

Required lensing columns, one of:
  A) x, y, z
  B) ra, dec, redshift

Optional lensing columns:
  kappa       : convergence / mass proxy / lensing weight
  weight      : lensing source weight

Outputs
-------
- summary JSON
- optional per-null-test CSV

Main statistics
---------------
W_ab = STF[ sum_{i<j} w_i w_j K_R(r_ij)
             (e_ij,a e_ij,b - delta_ab/3) ]

C_gal_lens = <W_gal, W_lens> / (||W_gal|| ||W_lens||)

Verdict logic is intentionally conservative:
  - galaxy anisotropy alone is not Tau-compatible
  - Tau-compatible requires galaxy+lensing tensor alignment after nulls/systematics
"""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Iterable

import numpy as np
import pandas as pd


# ----------------------------
# Data loading
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
            raise ImportError(
                "FITS input requires astropy. Install with: pip install astropy"
            ) from exc

        tab = Table.read(path)
        return _lower_columns(tab.to_pandas())

    raise ValueError(f"Unsupported file type: {path}")


# ----------------------------
# Coordinates
# ----------------------------

def flat_lcdm_comoving_distance_mpc(
    z: np.ndarray,
    h0: float = 67.66,
    omega_m: float = 0.3111,
    n_grid: int = 4096,
) -> np.ndarray:
    """
    Approximate line-of-sight comoving distance in a flat LCDM cosmology.

    Uses a precomputed trapezoidal integral over z:
        chi(z) = c/H0 * integral_0^z dz'/E(z')
        E(z) = sqrt(omega_m (1+z)^3 + 1-omega_m)

    This is adequate for pipeline prototyping. For precision cosmology,
    replace with your survey team's fiducial cosmology utilities.
    """
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
    chi_grid = (c_km_s / h0) * integ
    return np.interp(z, grid, chi_grid)


def radec_to_unit_xyz(ra_deg: np.ndarray, dec_deg: np.ndarray) -> np.ndarray:
    ra = np.deg2rad(np.asarray(ra_deg, dtype=float))
    dec = np.deg2rad(np.asarray(dec_deg, dtype=float))
    cosd = np.cos(dec)
    return np.column_stack([cosd * np.cos(ra), cosd * np.sin(ra), np.sin(dec)])


def table_to_xyz(
    df: pd.DataFrame,
    h0: float = 67.66,
    omega_m: float = 0.3111,
) -> np.ndarray:
    cols = set(df.columns)

    if {"x", "y", "z"}.issubset(cols):
        return df[["x", "y", "z"]].to_numpy(dtype=float)

    # Accept common redshift aliases.
    zcol = None
    for candidate in ["redshift", "zred", "z_cosmo", "zobs", "z"]:
        if candidate in cols and candidate not in ["x", "y"]:
            zcol = candidate
            break

    if {"ra", "dec"}.issubset(cols) and zcol is not None:
        unit = radec_to_unit_xyz(df["ra"].values, df["dec"].values)
        chi = flat_lcdm_comoving_distance_mpc(df[zcol].values, h0=h0, omega_m=omega_m)
        return unit * chi[:, None]

    raise ValueError(
        "Input table must contain either x,y,z or ra,dec,redshift/zred/z_cosmo/zobs."
    )


def table_weights(df: pd.DataFrame, default: float = 1.0, preferred: Iterable[str] = ("weight",)) -> np.ndarray:
    for col in preferred:
        if col in df.columns:
            w = df[col].to_numpy(dtype=float)
            w = np.where(np.isfinite(w) & (w > 0), w, default)
            return w
    return np.full(len(df), default, dtype=float)


# ----------------------------
# Tensor statistics
# ----------------------------

def pairwise_sample_indices(n: int, max_pairs: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    total = n * (n - 1) // 2
    if total <= max_pairs:
        return np.triu_indices(n, 1)

    i = rng.integers(0, n, size=max_pairs)
    j = rng.integers(0, n, size=max_pairs)
    mask = i != j
    return i[mask], j[mask]


def estimate_default_scale(X: np.ndarray, rng: np.random.Generator, sample_n: int = 512) -> float:
    n = len(X)
    if n < 3:
        raise ValueError("Need at least 3 objects.")
    idx = rng.choice(n, size=min(n, sample_n), replace=False)
    Y = X[idx]
    diffs = Y[:, None, :] - Y[None, :, :]
    D = np.linalg.norm(diffs, axis=2)
    tri = D[np.triu_indices_from(D, 1)]
    return float(np.nanmedian(tri))


def web_tensor(
    X: np.ndarray,
    weights: Optional[np.ndarray] = None,
    R: Optional[float] = None,
    sigma_R: Optional[float] = None,
    max_pairs: int = 500_000,
    seed: int = 1234,
) -> np.ndarray:
    """
    Pair-orientation STF web tensor in 3D.

    X: shape (N,3), comoving Cartesian coordinates.
    weights: per-object weights.
    R: target pair separation scale in same units as X.
    sigma_R: width of scale kernel.
    """
    X = np.asarray(X, dtype=float)
    X = X[np.all(np.isfinite(X), axis=1)]

    n = len(X)
    if n < 3:
        raise ValueError("Need at least 3 finite objects.")

    if weights is None:
        weights = np.ones(n)
    else:
        weights = np.asarray(weights, dtype=float)
        weights = weights[:n]
        weights = np.where(np.isfinite(weights) & (weights > 0), weights, 1.0)

    rng = np.random.default_rng(seed)
    Xc = X - np.average(X, axis=0, weights=weights)

    if R is None:
        R = estimate_default_scale(Xc, rng)
    if sigma_R is None:
        sigma_R = 0.5 * R

    i, j = pairwise_sample_indices(n, max_pairs=max_pairs, rng=rng)
    diff = Xc[j] - Xc[i]
    r = np.linalg.norm(diff, axis=1)
    ok = np.isfinite(r) & (r > 0)
    diff = diff[ok]
    r = r[ok]
    i = i[ok]
    j = j[ok]

    e = diff / r[:, None]
    K = np.exp(-0.5 * ((r - R) / sigma_R) ** 2)
    wij = weights[i] * weights[j] * K

    denom = np.sum(wij)
    if denom <= 0:
        raise ValueError("All pair weights vanished. Adjust R/sigma_R.")

    Q = np.einsum("i,ia,ib->ab", wij, e, e) / denom
    Q -= np.eye(3) / 3.0
    return Q


def density_tensor(
    X: np.ndarray,
    weights: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    STF density/inertia tensor. Useful for a gridded/convergence-like lensing proxy
    when pair orientation is not the right representation.
    """
    X = np.asarray(X, dtype=float)
    ok = np.all(np.isfinite(X), axis=1)
    X = X[ok]

    n = len(X)
    if n < 3:
        raise ValueError("Need at least 3 finite objects.")

    if weights is None:
        weights = np.ones(n)
    else:
        weights = np.asarray(weights, dtype=float)[ok]
        weights = np.where(np.isfinite(weights) & (weights > 0), weights, 1.0)

    Xc = X - np.average(X, axis=0, weights=weights)
    r = np.linalg.norm(Xc, axis=1)
    ok = r > 0
    e = Xc[ok] / r[ok, None]
    w = weights[ok]
    w = w / np.sum(w)
    Q = np.einsum("i,ia,ib->ab", w, e, e) - np.eye(3) / 3.0
    return Q


def tensor_amplitude(Q: np.ndarray) -> float:
    return float(np.sqrt(np.sum(Q * Q)))


def tensor_cosine(A: np.ndarray, B: np.ndarray) -> float:
    denom = tensor_amplitude(A) * tensor_amplitude(B)
    if denom == 0:
        return float("nan")
    return float(np.sum(A * B) / denom)


def principal_axis(Q: np.ndarray) -> np.ndarray:
    vals, vecs = np.linalg.eigh(Q)
    idx = int(np.argmax(np.abs(vals)))
    v = vecs[:, idx]
    return v / np.linalg.norm(v)


def axis_alignment(A: np.ndarray, B: np.ndarray) -> float:
    a = principal_axis(A)
    b = principal_axis(B)
    return float(abs(np.dot(a, b)))


# ----------------------------
# Null tests
# ----------------------------

def angular_scramble_xyz(X: np.ndarray, seed: int = 1234) -> np.ndarray:
    """
    Keep radial distances, randomize sky directions.
    """
    rng = np.random.default_rng(seed)
    r = np.linalg.norm(X, axis=1)
    u = rng.uniform(-1.0, 1.0, size=len(X))
    phi = rng.uniform(0.0, 2.0 * np.pi, size=len(X))
    s = np.sqrt(1.0 - u * u)
    dirs = np.column_stack([s * np.cos(phi), s * np.sin(phi), u])
    return dirs * r[:, None]


def radial_scramble_xyz(X: np.ndarray, seed: int = 1234) -> np.ndarray:
    """
    Keep sky directions, shuffle radial distances.
    """
    rng = np.random.default_rng(seed)
    r = np.linalg.norm(X, axis=1)
    dirs = X / np.maximum(r[:, None], 1e-12)
    r2 = rng.permutation(r)
    return dirs * r2[:, None]


def random_rotation_matrix(seed: int = 1234) -> np.ndarray:
    """
    Haar-random 3D rotation matrix.

    Used as a cross-readout alignment null: preserve the tensor amplitudes,
    but destroy physical galaxy/lensing co-orientation.
    """
    rng = np.random.default_rng(seed)
    q = rng.normal(size=4)
    q = q / np.linalg.norm(q)
    w, x, y, z = q
    return np.array([
        [1 - 2*y*y - 2*z*z, 2*x*y - 2*z*w,     2*x*z + 2*y*w],
        [2*x*y + 2*z*w,     1 - 2*x*x - 2*z*z, 2*y*z - 2*x*w],
        [2*x*z - 2*y*w,     2*y*z + 2*x*w,     1 - 2*x*x - 2*y*y],
    ])


@dataclass
class TensorResult:
    A_gal: float
    A_lens: float
    C_gal_lens: float
    axis_alignment: float
    W_gal: list
    W_lens: list


def analyze_catalogs(
    galaxy_path: str | Path,
    lensing_path: str | Path,
    R: Optional[float] = None,
    sigma_R: Optional[float] = None,
    h0: float = 67.66,
    omega_m: float = 0.3111,
    max_pairs: int = 500_000,
    seed: int = 1234,
) -> TensorResult:
    gal = load_table(galaxy_path)
    lens = load_table(lensing_path)

    Xg = table_to_xyz(gal, h0=h0, omega_m=omega_m)
    Xl = table_to_xyz(lens, h0=h0, omega_m=omega_m)

    wg = table_weights(gal, preferred=("weight", "weights", "fkp_weight", "comp_weight"))
    wl = table_weights(lens, preferred=("kappa", "weight", "weights", "lens_weight"))

    Wg = web_tensor(Xg, wg, R=R, sigma_R=sigma_R, max_pairs=max_pairs, seed=seed)
    # For lensing catalogues, use pair tensor if source positions represent a mass/convergence catalogue.
    # If using kappa pixels/peaks, density_tensor may be more appropriate. Here we default to density tensor.
    Wl = density_tensor(Xl, wl)

    return TensorResult(
        A_gal=tensor_amplitude(Wg),
        A_lens=tensor_amplitude(Wl),
        C_gal_lens=tensor_cosine(Wg, Wl),
        axis_alignment=axis_alignment(Wg, Wl),
        W_gal=Wg.tolist(),
        W_lens=Wl.tolist(),
    )


def run_nulls(
    galaxy_path: str | Path,
    lensing_path: str | Path,
    n_null: int = 100,
    R: Optional[float] = None,
    sigma_R: Optional[float] = None,
    h0: float = 67.66,
    omega_m: float = 0.3111,
    max_pairs: int = 300_000,
    seed: int = 1234,
) -> pd.DataFrame:
    gal = load_table(galaxy_path)
    lens = load_table(lensing_path)

    Xg = table_to_xyz(gal, h0=h0, omega_m=omega_m)
    Xl = table_to_xyz(lens, h0=h0, omega_m=omega_m)

    wg = table_weights(gal, preferred=("weight", "weights", "fkp_weight", "comp_weight"))
    wl = table_weights(lens, preferred=("kappa", "weight", "weights", "lens_weight"))

    rows = []

    # Real tensors, used for an orientation-only alignment null.
    Wg_real = web_tensor(Xg, wg, R=R, sigma_R=sigma_R, max_pairs=max_pairs, seed=seed)
    Wl_real = density_tensor(Xl, wl)

    for k in range(n_null):
        s = seed + 10_000 + k

        # Catalogue-level nulls for galaxy anisotropy.
        for name, Xg_null in [
            ("angular_scramble", angular_scramble_xyz(Xg, seed=s)),
            ("radial_scramble", radial_scramble_xyz(Xg, seed=s)),
        ]:
            Wg = web_tensor(Xg_null, wg, R=R, sigma_R=sigma_R, max_pairs=max_pairs, seed=s)
            Wl = Wl_real
            rows.append({
                "null_type": name,
                "run": k,
                "A_gal": tensor_amplitude(Wg),
                "A_lens": tensor_amplitude(Wl),
                "C_gal_lens": tensor_cosine(Wg, Wl),
                "axis_alignment": axis_alignment(Wg, Wl),
            })

        # Tensor-level cross-readout null: preserve both tensor amplitudes but randomize relative orientation.
        Rmat = random_rotation_matrix(seed=s + 500_000)
        Wl_rot = Rmat @ Wl_real @ Rmat.T
        rows.append({
            "null_type": "tensor_rotation",
            "run": k,
            "A_gal": tensor_amplitude(Wg_real),
            "A_lens": tensor_amplitude(Wl_rot),
            "C_gal_lens": tensor_cosine(Wg_real, Wl_rot),
            "axis_alignment": axis_alignment(Wg_real, Wl_rot),
        })

    return pd.DataFrame(rows)


def empirical_pvalue(value: float, null_values: np.ndarray, tail: str = "greater") -> float:
    null_values = np.asarray(null_values, dtype=float)
    null_values = null_values[np.isfinite(null_values)]
    if len(null_values) == 0:
        return float("nan")
    if tail == "greater":
        return float((1 + np.sum(null_values >= value)) / (len(null_values) + 1))
    if tail == "abs_greater":
        return float((1 + np.sum(np.abs(null_values) >= abs(value))) / (len(null_values) + 1))
    raise ValueError(tail)


def verdict_from_result(result: TensorResult, nulls: Optional[pd.DataFrame] = None) -> str:
    """
    Conservative rule:
    - High galaxy amplitude alone never yields Tau-compatible.
    - Need lensing amplitude and galaxy-lensing tensor cosine above null expectation.
    """
    if nulls is None or len(nulls) == 0:
        if result.A_gal > 0 and result.A_lens > 0 and result.C_gal_lens > 0.8:
            return "TAU-COMPATIBLE-CANDIDATE-NO-NULLS"
        return "INSUFFICIENT"

    align_nulls = nulls[nulls["null_type"] == "tensor_rotation"]
    amp_nulls = nulls[nulls["null_type"].isin(["angular_scramble", "radial_scramble"])]

    c_pool = align_nulls["C_gal_lens"].values if len(align_nulls) else nulls["C_gal_lens"].values
    a_pool = amp_nulls["A_gal"].values if len(amp_nulls) else nulls["A_gal"].values

    p_c = empirical_pvalue(result.C_gal_lens, c_pool, tail="greater")
    p_g = empirical_pvalue(result.A_gal, a_pool, tail="greater")

    # Lensing amplitude should be assessed against independent lensing mocks in production.
    # In this scaffold, require it to be non-trivial but do not use catalogue scrambles for A_lens.
    lens_nontrivial = result.A_lens > 0.05

    if p_c < 0.01 and p_g < 0.05 and lens_nontrivial and result.C_gal_lens > 0.8:
        return "TAU-COMPATIBLE"
    if p_g < 0.05 and not (p_c < 0.05 and lens_nontrivial):
        return "WEAK-ANOMALY-GALAXY-ONLY"
    if p_g >= 0.05:
        return "NULL"
    return "INCONCLUSIVE"


# ----------------------------
# CLI
# ----------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="TC-OBS-PIPELINE-001 Tau web tensor pipeline")
    parser.add_argument("--galaxy", required=True, help="Galaxy catalogue CSV/FITS")
    parser.add_argument("--lensing", required=True, help="Lensing/kappa catalogue CSV/FITS")
    parser.add_argument("--out", default="tau_obs_result.json", help="Output JSON path")
    parser.add_argument("--null-out", default=None, help="Optional null-test CSV path")
    parser.add_argument("--n-nulls", type=int, default=0, help="Number of angular/radial null runs")
    parser.add_argument("--R", type=float, default=None, help="Pair scale R in coordinate units")
    parser.add_argument("--sigma-R", type=float, default=None, help="Pair scale kernel width")
    parser.add_argument("--h0", type=float, default=67.66)
    parser.add_argument("--omega-m", type=float, default=0.3111)
    parser.add_argument("--max-pairs", type=int, default=500000)
    parser.add_argument("--seed", type=int, default=1234)

    args = parser.parse_args()

    result = analyze_catalogs(
        args.galaxy,
        args.lensing,
        R=args.R,
        sigma_R=args.sigma_R,
        h0=args.h0,
        omega_m=args.omega_m,
        max_pairs=args.max_pairs,
        seed=args.seed,
    )

    nulls = None
    if args.n_nulls > 0:
        nulls = run_nulls(
            args.galaxy,
            args.lensing,
            n_null=args.n_nulls,
            R=args.R,
            sigma_R=args.sigma_R,
            h0=args.h0,
            omega_m=args.omega_m,
            max_pairs=max(50_000, args.max_pairs // 2),
            seed=args.seed,
        )
        if args.null_out:
            nulls.to_csv(args.null_out, index=False)

    out = asdict(result)
    out["verdict"] = verdict_from_result(result, nulls)

    if nulls is not None:
        align_nulls = nulls[nulls["null_type"] == "tensor_rotation"]
        amp_nulls = nulls[nulls["null_type"].isin(["angular_scramble", "radial_scramble"])]
        c_pool = align_nulls["C_gal_lens"].values if len(align_nulls) else nulls["C_gal_lens"].values
        a_pool = amp_nulls["A_gal"].values if len(amp_nulls) else nulls["A_gal"].values
        out["null_summary"] = {
            "C_gal_lens_p_greater_tensor_rotation": empirical_pvalue(result.C_gal_lens, c_pool, "greater"),
            "A_gal_p_greater_catalog_scramble": empirical_pvalue(result.A_gal, a_pool, "greater"),
            "A_gal_95pct_catalog_scramble": float(np.nanpercentile(a_pool, 95)),
            "C_gal_lens_95pct_tensor_rotation": float(np.nanpercentile(c_pool, 95)),
        }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
