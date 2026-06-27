# TC-LENSING-CONNECT-001 — Lensing / mass-map connector

## Purpose

The Tau-web signature requires an independent mass/lensing readout:

\[
\mathcal W^{\rm clean,gal}_{ab}
\parallel
\mathcal W^{\rm clean,lens}_{ab}.
\]

DESI gives the galaxy/LSS side. This connector prepares the lensing side and writes a reduced file accepted by `tc_obs_pipeline.py`:

```csv
ra,dec,redshift,kappa
```

or:

```csv
x,y,z,kappa
```

## Supported modes

### 1. `kappa-table`

Use this when you already have a convergence / mass-map / kappa catalogue.

```bash
python tc_lensing_connector.py \
  --mode kappa-table \
  --input kappa_catalog.csv \
  --out lensing_reduced.csv \
  --redshift-proxy 1.0
```

If the input already has a redshift column, `--redshift-proxy` is not needed.

### 2. `shear-flat`

Use this for development with a small flat-sky shear catalogue containing:

```csv
ra,dec,e1,e2,weight,redshift
```

or:

```csv
ra,dec,g1,g2,weight,redshift
```

Example:

```bash
python tc_lensing_connector.py \
  --mode shear-flat \
  --input shear_catalog.csv \
  --out kappa_proxy.csv \
  --grid 128 \
  --redshift-proxy 1.0
```

This performs a crude flat-sky Kaiser–Squires E-mode proxy. It is **not production quality**.

### 3. `healpix-kappa`

Use this for HEALPix convergence maps, for example CMB-lensing-like maps.

```bash
python tc_lensing_connector.py \
  --mode healpix-kappa \
  --input kappa_map.fits \
  --out kappa_pixels.csv \
  --redshift-proxy 2.0 \
  --max-pixels 500000
```

Requires `healpy`.

## Run directly into the Tau OBS pipeline

```bash
python tc_lensing_connector.py \
  --mode kappa-table \
  --input kappa_catalog.csv \
  --out lensing_reduced.csv \
  --galaxy-catalog desi_lrg_reduced.csv \
  --module-dir /path/to/tau/scripts \
  --run-obs \
  --obs-out tau_obs_result.json
```

## Real-data notes

### Planck / CMB lensing

Planck all-sky maps are distributed in HEALPix format. CMB lensing is an integrated mass readout over a broad kernel, not a narrow redshift shell, so `--redshift-proxy` is only a practical embedding for the current 3D tensor scaffold. A more correct future version should use a light-cone integral instead of assigning one shell.

### Euclid / Rubin weak lensing

For Euclid/Rubin-style weak lensing, production analysis must use calibrated shear catalogues, masks, photo-z distributions, E/B-mode checks, and survey covariance. The `shear-flat` mode is only a development bridge.

## Current limitation

The current Tau tensor code expects a 3D point catalogue. Real lensing maps are projected 2D fields with broad kernels. This connector converts them into an approximate point/pixel catalogue so the existing tensor machinery can run. A future module should implement a true light-cone tensor:

\[
\mathcal W^{\rm lens}_{ab}
=
\int d\chi\,K_{\rm lens}(\chi)\,
\mathcal P_\perp^{cd}
\Delta^\tau_{cd}(\chi\hat n).
\]

## Production checklist

Before interpreting a lensing alignment as Tau-compatible:

- use calibrated shear/convergence products,
- include survey masks,
- remove additive/multiplicative shear bias,
- run E/B-mode null tests,
- use random-source / rotated-shape nulls,
- keep galaxy-to-lensing direction test blind,
- compare to joint galaxy+lensing mocks.
