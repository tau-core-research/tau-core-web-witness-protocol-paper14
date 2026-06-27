# TC-ZSTAB-001 — Redshift stability module

## Purpose

A Tau-compatible web signal should not be a one-slice accident. It should preserve a coherent web tensor direction across adjacent redshift or radial bins.

This module computes:

\[
\mathcal W_{ab}(z_i)
\]

for each redshift/radial slice and then evaluates:

\[
S_z^{\rm tensor}
=
\left\langle
\frac{
\mathcal W_{ab}(z_i)\mathcal W^{ab}(z_j)
}{
\|\mathcal W(z_i)\|\|\mathcal W(z_j)\|
}
\right\rangle_{i<j}.
\]

It also computes an axis-only stability score:

\[
S_z^{\rm axis}
=
\langle |e_i\cdot e_j| \rangle_{i<j}.
\]

## Verdicts

- `Z-STABLE`: tensor and axis structure both stable.
- `AXIS-STABLE-WEAK`: same dominant direction survives, but tensor shape/amplitude less stable.
- `Z-UNSTABLE`: direction/tensor pattern does not persist.
- `INSUFFICIENT-BINS`: not enough populated bins.

## Example

```bash
python tc_zstab_pipeline.py \
  --catalog desi_lrg.csv \
  --n-bins 5 \
  --min-per-bin 500 \
  --out tau_zstab_result.json \
  --bins-out tau_zstab_bins.csv
```

## Interpretation

This module is not sufficient by itself. A strong Tau-web candidate needs:

\[
\mathcal W^{\rm gal}_{ab}
\parallel
\mathcal W^{\rm lens}_{ab}
\]

and redshift stability:

\[
S_z^{\rm tensor}, S_z^{\rm axis}
\]

above mock/null expectations.

## Required production additions

- compare \(S_z\) against DESI/Euclid/Rubin mocks,
- include survey random catalogues,
- include mask/systematics projection,
- test adjacent-bin and non-adjacent-bin stability separately,
- add jackknife covariance.
