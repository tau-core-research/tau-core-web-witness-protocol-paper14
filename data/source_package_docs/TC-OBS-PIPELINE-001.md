# TC-OBS-PIPELINE-001 — Tau-web observational pipeline

## Purpose

This pipeline tests the Tau Core cosmic-web signature:

\[
\mathcal W^{\rm gal}_{ab} \parallel \mathcal W^{\rm lens}_{ab}.
\]

A galaxy-only filament signal is **not** sufficient. The Tau-compatible signature requires the same large-scale anisotropic tensor to appear in at least two independent readout channels, ideally galaxy positions and weak-lensing/mass maps.

## Input data

### Galaxy catalogue

Minimum accepted columns:

- `x,y,z` Cartesian comoving coordinates, or
- `ra,dec,redshift`

Optional:

- `weight`, `fkp_weight`, `comp_weight`

DESI DR1 LSS catalogues are the natural first target because they are clustering-ready large-scale-structure catalogues.

### Lensing catalogue / map proxy

Minimum accepted columns:

- `x,y,z`, or
- `ra,dec,redshift`

Optional:

- `kappa` convergence/mass proxy
- `weight`

For real Euclid/Rubin-style shear catalogues, this scaffold should be extended with a proper shear-to-convergence or E/B-mode mass-map reconstruction stage before computing \(\mathcal W^{\rm lens}_{ab}\).

## Core statistic

For a set of objects with comoving positions \(X_i\), pair separation \(r_{ij}\), unit pair direction \(\hat\xi_{ij}\), and weights \(w_i\), define:

\[
\mathcal W_{ab}(R)
=
\mathcal N_R^{-1}
\sum_{i<j}
w_iw_jK_R(r_{ij})
\left(
\hat\xi_{ij,a}\hat\xi_{ij,b}
-
\frac{1}{3}\delta_{ab}
\right).
\]

This is a symmetric trace-free anisotropy tensor. It compresses the large-scale filament direction into a tensor object.

Amplitude:

\[
A_{\rm web}
=
\sqrt{\mathcal W_{ab}\mathcal W^{ab}}.
\]

Cross-readout tensor cosine:

\[
C_{\rm gal-lens}
=
\frac{
\mathcal W^{\rm gal}_{ab}\mathcal W_{\rm lens}^{ab}
}{
\|\mathcal W^{\rm gal}\|\|\mathcal W^{\rm lens}\|
}.
\]

Tau-compatible expectation:

\[
C_{\rm gal-lens}\approx 1.
\]

## Null tests

The initial scaffold implements:

1. **Angular scramble**  
   Preserve radial distribution, randomize sky directions.

2. **Radial scramble**  
   Preserve angular footprint, shuffle radial distances.

3. **Tensor rotation null**  
   Preserve the measured galaxy and lensing tensor amplitudes, but randomize their relative 3D orientation. This directly tests whether cross-readout alignment is stronger than accidental tensor alignment.

Required future additions:

3. Survey mask/random catalogue projection.

4. RSD/fibre-assignment/selection systematics tensors.

5. \(\Lambda\)CDM mock catalogue comparison.

6. Blind lensing test: fix \(\mathcal W^{\rm gal}_{ab}\) first, then evaluate lensing alignment without tuning.

## Verdict logic

- `NULL`: cleaned galaxy web tensor is not above nulls.
- `WEAK-ANOMALY-GALAXY-ONLY`: galaxy anisotropy exists, but lensing does not align.
- `TAU-COMPATIBLE`: galaxy and lensing tensors are both significant and aligned beyond null expectation.
- `STRONG-WITNESS`: future extension; requires galaxy + lensing + velocity + redshift stability.

## Example usage

```bash
python tc_obs_pipeline.py \
  --galaxy desi_lrg.csv \
  --lensing euclid_kappa_proxy.csv \
  --n-nulls 100 \
  --out tau_obs_result.json \
  --null-out tau_nulls.csv
```

## CSV example schema

Galaxy:

```csv
ra,dec,redshift,weight
150.01,2.31,0.71,1.02
150.04,2.34,0.72,0.98
```

Lensing proxy:

```csv
ra,dec,redshift,kappa
150.02,2.30,0.70,0.013
150.05,2.33,0.72,0.011
```

## Important limitation

This file is a pipeline scaffold, not a production cosmology analysis. For publication-quality work, add:

- official survey masks and random catalogues,
- covariance from mocks,
- jackknife/bootstrap errors,
- redshift-bin stability,
- lensing mass-map reconstruction,
- RSD corrections,
- blind-analysis locking.
