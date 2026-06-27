# TC-ZSTAB-DIAG-001 — Redshift stability diagnostic

## Purpose

`TC-ZSTAB-001` can fail for multiple reasons:

1. the web direction is genuinely unstable,
2. some bins have too little amplitude,
3. adjacent bins are stable but the global axis drifts,
4. the axis is stable but the tensor shape changes,
5. there are too few populated bins.

This diagnostic module reads `zstab_result.json` and computes:

\[
C_{ij}^{\rm tensor}
=
\frac{
\mathcal W_{ab}(z_i)\mathcal W^{ab}(z_j)
}{
\|\mathcal W(z_i)\|\|\mathcal W(z_j)\|
}
\]

and:

\[
C_{ij}^{\rm axis}
=
|e_i\cdot e_j|.
\]

It then classifies the failure mode.

## Example

```bash
python tc_zstab_diag.py \
  --zstab-result results/zstab_result.json \
  --out results/zstab_diag.json \
  --tensor-matrix-out results/zstab_tensor_matrix.csv \
  --axis-matrix-out results/zstab_axis_matrix.csv
```

## Failure modes

### `STABLE`

Both tensor and axis stability pass.

### `AXIS-STABLE-SHAPE-UNSTABLE`

The dominant direction is stable, but tensor eigenvalue pattern changes. This may mean a filament-to-sheet transition, amplitude evolution, or binning effects.

### `LOCAL-STABLE-GLOBAL-DRIFT`

Adjacent bins align, but far-apart bins drift. This can be physical evolution or light-cone geometry.

### `LOW-AMPLITUDE-BIN-NOISE`

Several bins have low amplitude, so directions become noise-dominated.

### `DIRECTION-UNSTABLE`

The main axis changes between bins. Treat as a failed Tau-stability test unless mocks show the same instability.

### `INSUFFICIENT-BINS`

Too few valid slices.

## Interpretation

A Tau-compatible web signature should ideally satisfy:

\[
S_z^{\rm tensor}>0.8
\]

and:

\[
S_z^{\rm axis}>0.8.
\]

If `TC-ZSTAB-DIAG-001` returns `DIRECTION-UNSTABLE`, the final verdict should remain a candidate at most, even if galaxy-lensing cross-readout is strong.

If it returns `AXIS-STABLE-SHAPE-UNSTABLE`, a weaker Tau-compatible interpretation may still be possible, but requires mock comparison and amplitude-weighted stability.
