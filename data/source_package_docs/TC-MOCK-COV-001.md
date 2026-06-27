# TC-MOCK-COV-001 — Mock covariance and ΛCDM-reference significance

## Purpose

The previous modules define and clean the Tau-web tensor:

\[
\mathcal W_{ab}^{\rm clean}.
\]

This module asks:

\[
\text{How rare is this tensor under ΛCDM-like mock catalogues?}
\]

It computes a 5D symmetric trace-free tensor vector:

\[
v=(Q_{xx},Q_{yy},\sqrt2Q_{xy},\sqrt2Q_{xz},\sqrt2Q_{yz})
\]

for the observed catalogue and for each mock.

## Statistics

Mock mean:

\[
\bar v_{\rm mock}
=
\frac1N\sum_i v_i.
\]

Mock covariance:

\[
C_{\rm mock}
=
\mathrm{Cov}(v_i).
\]

Observed Mahalanobis distance:

\[
\chi^2_{\rm obs}
=
(v_{\rm obs}-\bar v)^T
C_{\rm mock}^{-1}
(v_{\rm obs}-\bar v).
\]

Empirical p-value:

\[
p_{\chi^2}
=
\frac{1+\#\{\chi^2_{\rm mock}\geq\chi^2_{\rm obs}\}}{1+N_{\rm mock}}.
\]

Amplitude p-value:

\[
p_A
=
\frac{1+\#\{A_{\rm mock}\geq A_{\rm obs}\}}{1+N_{\rm mock}}.
\]

## Optional systematics cleaning

If systematics catalogues are supplied, the script first projects all observed and mock tensors away from the systematics subspace:

\[
v_{\rm clean}
=
(I-\Pi_{\rm sys})v.
\]

This makes the mock test consistent with `TC-SYS-PROJECTOR-001`.

## Verdicts

- `MOCK-COMPATIBLE`: observed clean tensor is common in mocks.
- `MOCK-RARE-WEAK`: either amplitude or χ² is rare.
- `MOCK-RARE-STRONG`: both amplitude and χ² are rare.

## Example

```bash
python tc_mock_cov.py \
  --observed desi_lrg_clean.csv \
  --mock-glob "mocks/desi_lrg_mock_*.csv" \
  --systematics desi_randoms.csv footprint_template.csv \
  --out tau_mock_cov_result.json \
  --mock-out tau_mock_rows.csv
```

## Interpretation in the Tau-web chain

A Tau-compatible cosmological witness requires:

1. nonzero cleaned galaxy tensor,
2. galaxy–lensing tensor alignment,
3. redshift stability,
4. rarity relative to ΛCDM mocks.

This module only handles item 4.

## Production requirements

For actual DESI/Euclid/Rubin analysis:

- use official mock catalogues,
- match survey masks and weights,
- use official randoms,
- include covariance from many mocks,
- apply Hartlap / Sellentin-Heavens corrections if appropriate,
- evaluate redshift-bin covariance,
- keep the lensing test blind.
