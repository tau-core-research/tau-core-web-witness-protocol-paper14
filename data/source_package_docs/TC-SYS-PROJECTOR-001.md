# TC-SYS-PROJECTOR-001 — Systematics projector

## Purpose

The Tau-web statistic must not mistake survey geometry for physics.

This module projects an observed web tensor away from known systematics tensors:

\[
\mathcal W^{\rm clean}_{ab}
=
(I-\Pi_{\rm sys})\mathcal W^{\rm obs}_{ab}.
\]

The systematics subspace may be built from:

- survey random catalogues,
- angular footprint catalogues,
- completeness maps,
- stellar contamination templates,
- redshift-failure templates,
- fibre-assignment templates,
- extinction templates,
- any catalogue-like systematic converted into points.

## STF tensor vectorization

A symmetric trace-free \(3\times3\) tensor has 5 degrees of freedom. The script maps it to a 5D vector:

\[
v=
(Q_{xx},Q_{yy},\sqrt2 Q_{xy},\sqrt2 Q_{xz},\sqrt2 Q_{yz}).
\]

The systematics tensors form a basis:

\[
\mathcal H_{\rm sys}
=
\mathrm{span}\{
\mathcal S^{(1)},...,\mathcal S^{(N)}
\}.
\]

Then:

\[
v_{\rm clean}
=
v_{\rm obs}
-
B B^T v_{\rm obs}.
\]

## Verdicts

- `SYSTEMATICS-DOMINATED`: most observed anisotropy is removed.
- `PARTIALLY-SYSTEMATICS-CONTAMINATED`: significant retained signal, but systematics are large.
- `CLEAN-CANDIDATE`: most tensor amplitude survives projection.

## Example

```bash
python tc_sys_projector.py \
  --observed desi_lrg.csv \
  --systematics desi_randoms.csv footprint_template.csv \
  --out tau_sys_result.json
```

## Interpretation

This module is necessary before claiming:

\[
\mathcal W^{\rm gal}_{ab}
\parallel
\mathcal W^{\rm lens}_{ab}.
\]

The correct chain is:

\[
\mathcal W^{\rm obs}
\rightarrow
\mathcal W^{\rm clean}
\rightarrow
\text{cross-readout alignment}
\rightarrow
\text{redshift stability}
\rightarrow
\text{mock significance}.
\]

## Production additions

This scaffold should be extended with:

- official survey randoms,
- multiple systematics templates,
- weighted template amplitudes,
- covariance-aware projection,
- jackknife uncertainties,
- RSD/fibre-assignment dedicated templates,
- mask-only null catalogues.
