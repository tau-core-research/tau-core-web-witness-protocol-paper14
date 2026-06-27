#!/usr/bin/env python3
"""
TC-ZSTAB-DIAG-001
Diagnostics for redshift/radial stability failures.

Purpose
-------
Given a JSON output from tc_zstab_pipeline.py, compute:

- pairwise tensor-cosine matrix between all valid bins
- pairwise principal-axis alignment matrix
- adjacent-bin stability
- amplitude diagnostics
- likely failure mode

This helps decide whether a ZSTAB failure is due to:
  1. genuinely unstable web direction,
  2. weak/low-amplitude bins,
  3. noisy binning,
  4. tensor-shape instability despite axis stability,
  5. insufficient populated bins.

Input
-----
JSON from tc_zstab_pipeline.py

Output
------
JSON diagnostics and optional CSV matrices.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


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


def axis_alignment(A: np.ndarray, B: np.ndarray) -> float:
    if not (np.all(np.isfinite(A)) and np.all(np.isfinite(B))):
        return float("nan")
    return float(abs(np.dot(principal_axis(A), principal_axis(B))))


def read_tensor(br: dict[str, Any]) -> np.ndarray | None:
    W = br.get("W")
    if W is None:
        return None
    try:
        Q = np.array(W, dtype=float)
        if Q.shape != (3, 3):
            return None
        if not np.all(np.isfinite(Q)):
            return None
        return Q
    except Exception:
        return None


@dataclass
class ZStabDiagnostic:
    input_file: str
    n_bins_total: int
    n_valid_bins: int
    amplitude_mean: float
    amplitude_min: float
    amplitude_max: float
    amplitude_cv: float
    global_tensor_mean: float
    global_axis_mean: float
    adjacent_tensor_mean: float
    adjacent_axis_mean: float
    low_amplitude_bins: list[int]
    unstable_pairs: list[list[int]]
    failure_mode: str
    recommendation: str


def diagnose(
    zstab: dict[str, Any],
    input_file: str,
    amp_relative_floor: float = 0.35,
    tensor_threshold: float = 0.8,
    axis_threshold: float = 0.8,
) -> tuple[ZStabDiagnostic, pd.DataFrame, pd.DataFrame]:
    bins = zstab.get("bin_results", [])
    tensors = []
    bin_ids = []
    amps = []

    for br in bins:
        Q = read_tensor(br)
        amp = br.get("amplitude")
        try:
            amp = float(amp)
        except Exception:
            amp = float("nan")

        if Q is not None and np.isfinite(amp):
            tensors.append(Q)
            bin_ids.append(int(br.get("bin_index", len(bin_ids))))
            amps.append(amp)

    n = len(tensors)
    if n == 0:
        diag = ZStabDiagnostic(
            input_file=input_file,
            n_bins_total=len(bins),
            n_valid_bins=0,
            amplitude_mean=float("nan"),
            amplitude_min=float("nan"),
            amplitude_max=float("nan"),
            amplitude_cv=float("nan"),
            global_tensor_mean=float("nan"),
            global_axis_mean=float("nan"),
            adjacent_tensor_mean=float("nan"),
            adjacent_axis_mean=float("nan"),
            low_amplitude_bins=[],
            unstable_pairs=[],
            failure_mode="INSUFFICIENT-BINS",
            recommendation="Re-run z-stability with more objects per bin or fewer bins.",
        )
        return diag, pd.DataFrame(), pd.DataFrame()

    tensor_mat = np.full((n, n), np.nan)
    axis_mat = np.full((n, n), np.nan)
    unstable_pairs = []

    for i in range(n):
        for j in range(n):
            tensor_mat[i, j] = tensor_cosine(tensors[i], tensors[j])
            axis_mat[i, j] = axis_alignment(tensors[i], tensors[j])
            if i < j and (tensor_mat[i, j] < tensor_threshold or axis_mat[i, j] < axis_threshold):
                unstable_pairs.append([bin_ids[i], bin_ids[j]])

    off = np.triu_indices(n, 1)
    global_tensor = float(np.nanmean(tensor_mat[off])) if len(off[0]) else float("nan")
    global_axis = float(np.nanmean(axis_mat[off])) if len(off[0]) else float("nan")

    adj_tensor_vals = []
    adj_axis_vals = []
    for i in range(n - 1):
        adj_tensor_vals.append(tensor_mat[i, i + 1])
        adj_axis_vals.append(axis_mat[i, i + 1])
    adjacent_tensor = float(np.nanmean(adj_tensor_vals)) if adj_tensor_vals else float("nan")
    adjacent_axis = float(np.nanmean(adj_axis_vals)) if adj_axis_vals else float("nan")

    amps_arr = np.array(amps, dtype=float)
    amp_mean = float(np.nanmean(amps_arr))
    amp_min = float(np.nanmin(amps_arr))
    amp_max = float(np.nanmax(amps_arr))
    amp_cv = float(np.nanstd(amps_arr) / (amp_mean + 1e-12))

    low_bins = [
        bin_ids[i]
        for i, a in enumerate(amps_arr)
        if a < amp_relative_floor * amp_max
    ]

    # Failure classification.
    if n < 3:
        mode = "INSUFFICIENT-BINS"
        rec = "Use fewer bins or require more objects per bin."
    elif global_axis >= axis_threshold and global_tensor < tensor_threshold:
        mode = "AXIS-STABLE-SHAPE-UNSTABLE"
        rec = (
            "Dominant axis is stable but tensor shape/amplitude changes. "
            "Try adjacent-bin-only verdict, amplitude-weighted S_z, and inspect sheet/filament eigenvalue ratios."
        )
    elif adjacent_axis >= axis_threshold and global_axis < axis_threshold:
        mode = "LOCAL-STABLE-GLOBAL-DRIFT"
        rec = (
            "Adjacent slices align but distant slices drift. "
            "This may indicate evolution, wide-bin geometry, or light-cone effects. Try narrower z windows or trend model."
        )
    elif len(low_bins) >= max(1, n // 3):
        mode = "LOW-AMPLITUDE-BIN-NOISE"
        rec = (
            "Several bins have weak web amplitude. "
            "Increase objects per bin, reduce number of bins, or use amplitude-weighted stability."
        )
    elif global_axis < axis_threshold and adjacent_axis < axis_threshold:
        mode = "DIRECTION-UNSTABLE"
        rec = (
            "Dominant web direction changes between bins. "
            "Treat as non-Tau-stable unless mocks show this is expected from sampling/systematics."
        )
    elif global_tensor >= tensor_threshold and global_axis >= axis_threshold:
        mode = "STABLE"
        rec = "Z-stability passes. Compare S_z against mocks for significance."
    else:
        mode = "MIXED"
        rec = "Mixed stability evidence. Inspect matrices and run mock/null comparison."

    diag = ZStabDiagnostic(
        input_file=input_file,
        n_bins_total=len(bins),
        n_valid_bins=n,
        amplitude_mean=amp_mean,
        amplitude_min=amp_min,
        amplitude_max=amp_max,
        amplitude_cv=amp_cv,
        global_tensor_mean=global_tensor,
        global_axis_mean=global_axis,
        adjacent_tensor_mean=adjacent_tensor,
        adjacent_axis_mean=adjacent_axis,
        low_amplitude_bins=low_bins,
        unstable_pairs=unstable_pairs,
        failure_mode=mode,
        recommendation=rec,
    )

    tensor_df = pd.DataFrame(tensor_mat, index=bin_ids, columns=bin_ids)
    axis_df = pd.DataFrame(axis_mat, index=bin_ids, columns=bin_ids)
    return diag, tensor_df, axis_df


def main() -> None:
    parser = argparse.ArgumentParser(description="TC-ZSTAB-DIAG-001 z-stability diagnostic")
    parser.add_argument("--zstab-result", required=True)
    parser.add_argument("--out", default="zstab_diag.json")
    parser.add_argument("--tensor-matrix-out", default=None)
    parser.add_argument("--axis-matrix-out", default=None)
    parser.add_argument("--amp-relative-floor", type=float, default=0.35)
    parser.add_argument("--tensor-threshold", type=float, default=0.8)
    parser.add_argument("--axis-threshold", type=float, default=0.8)
    args = parser.parse_args()

    with open(args.zstab_result, "r", encoding="utf-8") as f:
        zstab = json.load(f)

    diag, tensor_df, axis_df = diagnose(
        zstab,
        input_file=args.zstab_result,
        amp_relative_floor=args.amp_relative_floor,
        tensor_threshold=args.tensor_threshold,
        axis_threshold=args.axis_threshold,
    )

    out = asdict(diag)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    if args.tensor_matrix_out:
        tensor_df.to_csv(args.tensor_matrix_out)
    if args.axis_matrix_out:
        axis_df.to_csv(args.axis_matrix_out)

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
