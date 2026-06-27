# TC-EXTRA-READOUT-001 — Velocity / CMB-lensing extra readout

## Purpose

The Tau-web pipeline reaches `TAU-COMPATIBLE` when:

\[
\mathcal W^{\rm clean,gal}_{ab}
\parallel
\mathcal W^{\rm clean,lens}_{ab}
\]

passes together with z-stability, systematics cleaning, and mock rarity.

A stronger witness needs a third independent readout:

\[
\mathcal V_{ab}
\parallel
\mathcal W^{\rm gal}_{ab}
\]

or:

\[
\mathcal W^{\rm CMB}_{ab}
\parallel
\mathcal W^{\rm gal}_{ab}.
\]

This module computes those optional extra alignments.

## Velocity input

CSV/FITS with:

```csv
x,y,z,vx,vy,vz,weight
```

or:

```csv
ra,dec,redshift,vx,vy,vz,weight
```

The velocity tensor is:

\[
\mathcal V_{ab}
=
\mathrm{STF}
\left[
\sum_i w_i \hat v_{i,a}\hat v_{i,b}
\right].
\]

## CMB / kappa input

CSV/FITS with:

```csv
x,y,z,kappa
```

or:

```csv
ra,dec,redshift,kappa
```

The connector computes a density-style STF tensor from the kappa-weighted pixel positions.

## Example

```bash
python tc_extra_readout.py \
  --obs-result results/obs_result.json \
  --velocity-catalog data/velocity/velocities.csv \
  --out results/extra_result.json
```

or:

```bash
python tc_extra_readout.py \
  --obs-result results/obs_result.json \
  --cmb-kappa-catalog data/cmb/kappa_pixels.csv \
  --out results/extra_result.json
```

## Output fields

```json
{
  "velocity_alignment_pass": true,
  "cmb_alignment_pass": false,
  "extra_readout_pass": true,
  "C_gal_velocity": 0.91,
  "axis_gal_velocity": 0.95
}
```

## Important limitations

- Peculiar velocity catalogues have large distance and selection errors.
- Bulk flows must be treated carefully.
- CMB lensing is a broad light-cone kernel, not a thin redshift shell.
- Real use requires mocks and null tests for the third readout too.

This module is a scaffold for the final strong-witness criterion, not a publication-ready velocity or CMB-lensing analysis.
