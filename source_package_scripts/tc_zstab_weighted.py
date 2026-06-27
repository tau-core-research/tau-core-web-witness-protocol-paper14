#!/usr/bin/env python3
"""
TC-ZSTAB-WEIGHTED-001
Amplitude-weighted redshift/radial stability for Tau-web tensors.

Purpose
-------
The plain z-stability score can fail when some bins have very low web amplitude.
In those bins the principal direction is noise-dominated.

This module computes amplitude-weighted stability:

    S_tensor_w =
      sum_{i<j} (A_i A_j)^p C_ij / sum_{i<j} (A_i A_j)^p

    S_axis_w =
      sum_{i<j} (A_i A_j)^p |e_i·e_j| / sum_{i<j} (A_i A_j)^p

It also supports excluding bins whose amplitude is below a relative threshold.

Input
-----
JSON from tc_zstab_pipeline.py

Output
------
JSON with weighted stability, retained bins, and verdict.

Important
---------
This should not replace the plain stability test. It is a diagnostic rescue
only when TC-ZSTAB-DIAG indicates LOW-AMPLITUDE-BIN-NOISE.
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
class WeightedZStabResult:
    input_file: str
    n_bins_total: int
    n_valid_bins_raw: int
    n_bins_retained: int
    retained_bins: list[int]
    dropped_bins: list[int]
    amplitude_max: float
    amplitude_floor: float
    weight_power: float
    S_tensor_unweighted_retained: float
    S_axis_unweighted_retained: float
    S_tensor_weighted: float
    S_axis_weighted: float
    adjacent_tensor_weighted: float
    adjacent_axis_weighted: float
    verdict: str
    recommendation: str


def compute_weighted(
    zstab: dict[str, Any],
    input_file: str,
    amp_relative_floor: float = 0.35,
    weight_power: float = 1.0,
    tensor_threshold: float = 0.8,
    axis_threshold: float = 0.8,
    min_bins: int = 3,
) -> tuple[WeightedZStabResult, pd.DataFrame]:
    bins = zstab.get("bin_results", [])
    raw = []

    for br in bins:
        Q = read_tensor(br)
        if Q is None:
            continue
        try:
            amp = float(br.get("amplitude"))
        except Exception:
            amp = tensor_amp(Q)
        if not np.isfinite(amp):
            continue
        raw.append({
            "bin": int(br.get("bin_index", len(raw))),
            "amp": amp,
            "Q": Q,
        })

    if not raw:
        res = WeightedZStabResult(
            input_file=input_file,
            n_bins_total=len(bins),
            n_valid_bins_raw=0,
            n_bins_retained=0,
            retained_bins=[],
            dropped_bins=[],
            amplitude_max=float("nan"),
            amplitude_floor=float("nan"),
            weight_power=weight_power,
            S_tensor_unweighted_retained=float("nan"),
            S_axis_unweighted_retained=float("nan"),
            S_tensor_weighted=float("nan"),
            S_axis_weighted=float("nan"),
            adjacent_tensor_weighted=float("nan"),
            adjacent_axis_weighted=float("nan"),
            verdict="INSUFFICIENT-BINS",
            recommendation="No valid tensors available.",
        )
        return res, pd.DataFrame()

    amp_max = max(r["amp"] for r in raw)
    floor = amp_relative_floor * amp_max

    retained = [r for r in raw if r["amp"] >= floor]
    dropped = [r for r in raw if r["amp"] < floor]

    if len(retained) < min_bins:
        res = WeightedZStabResult(
            input_file=input_file,
            n_bins_total=len(bins),
            n_valid_bins_raw=len(raw),
            n_bins_retained=len(retained),
            retained_bins=[r["bin"] for r in retained],
            dropped_bins=[r["bin"] for r in dropped],
            amplitude_max=float(amp_max),
            amplitude_floor=float(floor),
            weight_power=weight_power,
            S_tensor_unweighted_retained=float("nan"),
            S_axis_unweighted_retained=float("nan"),
            S_tensor_weighted=float("nan"),
            S_axis_weighted=float("nan"),
            adjacent_tensor_weighted=float("nan"),
            adjacent_axis_weighted=float("nan"),
            verdict="INSUFFICIENT-RETAINED-BINS",
            recommendation=(
                "Too few bins remain after amplitude floor. Lower --amp-relative-floor, "
                "reduce number of z bins, or increase catalogue size."
            ),
        )
        return res, pd.DataFrame()

    pair_rows = []
    t_values = []
    a_values = []
    weights = []

    for i in range(len(retained)):
        for j in range(i + 1, len(retained)):
            ri, rj = retained[i], retained[j]
            t = tensor_cosine(ri["Q"], rj["Q"])
            a = axis_alignment(ri["Q"], rj["Q"])
            w = (ri["amp"] * rj["amp"]) ** weight_power
            pair_rows.append({
                "bin_i": ri["bin"],
                "bin_j": rj["bin"],
                "amp_i": ri["amp"],
                "amp_j": rj["amp"],
                "pair_weight": w,
                "tensor_cosine": t,
                "axis_alignment": a,
            })
            if np.isfinite(t) and np.isfinite(a) and np.isfinite(w):
                t_values.append(t)
                a_values.append(a)
                weights.append(w)

    t_values = np.array(t_values, dtype=float)
    a_values = np.array(a_values, dtype=float)
    weights = np.array(weights, dtype=float)

    if len(weights) == 0 or np.sum(weights) <= 0:
        S_tw = S_aw = float("nan")
    else:
        S_tw = float(np.sum(weights * t_values) / np.sum(weights))
        S_aw = float(np.sum(weights * a_values) / np.sum(weights))

    S_t_unw = float(np.nanmean(t_values)) if len(t_values) else float("nan")
    S_a_unw = float(np.nanmean(a_values)) if len(a_values) else float("nan")

    # Adjacent retained bins in original bin order.
    adj_t = []
    adj_a = []
    adj_w = []
    retained_sorted = sorted(retained, key=lambda r: r["bin"])
    by_bin = {r["bin"]: r for r in retained_sorted}
    for bi, bj in zip([r["bin"] for r in retained_sorted[:-1]], [r["bin"] for r in retained_sorted[1:]]):
        # Only count actually adjacent original bins as adjacent; if a bin was dropped between them,
        # treat this as non-adjacent.
        if bj != bi + 1:
            continue
        ri, rj = by_bin[bi], by_bin[bj]
        t = tensor_cosine(ri["Q"], rj["Q"])
        a = axis_alignment(ri["Q"], rj["Q"])
        w = (ri["amp"] * rj["amp"]) ** weight_power
        if np.isfinite(t) and np.isfinite(a):
            adj_t.append(t)
            adj_a.append(a)
            adj_w.append(w)

    if adj_w and np.sum(adj_w) > 0:
        adj_t = np.array(adj_t)
        adj_a = np.array(adj_a)
        adj_w = np.array(adj_w)
        S_adj_t = float(np.sum(adj_w * adj_t) / np.sum(adj_w))
        S_adj_a = float(np.sum(adj_w * adj_a) / np.sum(adj_w))
    else:
        S_adj_t = float("nan")
        S_adj_a = float("nan")

    if S_tw >= tensor_threshold and S_aw >= axis_threshold:
        verdict = "WEIGHTED-Z-STABLE"
        rec = "Weighted z-stability passes. Use with caution: compare weighted score against mocks."
    elif S_aw >= axis_threshold and S_tw >= 0.4:
        verdict = "WEIGHTED-AXIS-STABLE-WEAK"
        rec = "Axis survives after amplitude weighting, but tensor shape is not fully stable."
    elif S_adj_a >= axis_threshold and S_aw < axis_threshold:
        verdict = "ADJACENT-STABLE-GLOBAL-DRIFT"
        rec = "Adjacent retained bins align, but global retained-bin pattern drifts."
    else:
        verdict = "WEIGHTED-Z-UNSTABLE"
        rec = "Even amplitude-weighted stability fails. Treat Tau-web stability as not established."

    res = WeightedZStabResult(
        input_file=input_file,
        n_bins_total=len(bins),
        n_valid_bins_raw=len(raw),
        n_bins_retained=len(retained),
        retained_bins=[r["bin"] for r in retained],
        dropped_bins=[r["bin"] for r in dropped],
        amplitude_max=float(amp_max),
        amplitude_floor=float(floor),
        weight_power=float(weight_power),
        S_tensor_unweighted_retained=S_t_unw,
        S_axis_unweighted_retained=S_a_unw,
        S_tensor_weighted=S_tw,
        S_axis_weighted=S_aw,
        adjacent_tensor_weighted=S_adj_t,
        adjacent_axis_weighted=S_adj_a,
        verdict=verdict,
        recommendation=rec,
    )

    return res, pd.DataFrame(pair_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="TC-ZSTAB-WEIGHTED-001 weighted z-stability")
    parser.add_argument("--zstab-result", required=True)
    parser.add_argument("--out", default="zstab_weighted.json")
    parser.add_argument("--pairs-out", default=None)
    parser.add_argument("--amp-relative-floor", type=float, default=0.35)
    parser.add_argument("--weight-power", type=float, default=1.0)
    parser.add_argument("--tensor-threshold", type=float, default=0.8)
    parser.add_argument("--axis-threshold", type=float, default=0.8)
    parser.add_argument("--min-bins", type=int, default=3)
    args = parser.parse_args()

    with open(args.zstab_result, "r", encoding="utf-8") as f:
        zstab = json.load(f)

    res, pairs = compute_weighted(
        zstab,
        input_file=args.zstab_result,
        amp_relative_floor=args.amp_relative_floor,
        weight_power=args.weight_power,
        tensor_threshold=args.tensor_threshold,
        axis_threshold=args.axis_threshold,
        min_bins=args.min_bins,
    )

    out = asdict(res)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    if args.pairs_out:
        pairs.to_csv(args.pairs_out, index=False)

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
