# TC-DESI-CONNECT-001 — DESI DR1 connector

## Purpose

This module connects the Tau-web pipeline to public DESI DR1 LSS catalogues.

It does four things:

1. Builds DESI DR1 LSS URLs for a tracer and sky region.
2. Optionally downloads clustering data and random catalogues.
3. Converts FITS to lightweight CSV with:

```csv
ra,dec,redshift,weight
```

4. Runs the existing Tau modules:

- `tc_zstab_pipeline.py`
- `tc_sys_projector.py`
- `tc_mock_cov.py`
- `tc_obs_pipeline.py` if a lensing catalogue is supplied
- `tc_verdict_engine.py`

## Why DESI only gives half the Tau-web witness

DESI DR1 LSS catalogues provide spectroscopic large-scale-structure tracer positions and random catalogues. The Tau-compatible signature also needs an independent mass/lensing readout:

\[
\mathcal W^{\rm clean,gal}_{ab}
\parallel
\mathcal W^{\rm clean,lens}_{ab}.
\]

So this connector handles the DESI galaxy/random/mock side, while lensing must be supplied separately as:

```bash
--lensing-catalog lensing_or_kappa_proxy.csv
```

## First safe command

Always start with:

```bash
python tc_desi_connector.py \
  --tracer LRG \
  --region NGC \
  --random-indices 0 \
  --out-dir desi_lrg_ngc_tau \
  --plan
```

This prints the exact URLs and local paths without downloading anything.

## Download + prepare small first-pass CSV

DESI random catalogues can be very large. For a first test:

```bash
python tc_desi_connector.py \
  --tracer LRG \
  --region NGC \
  --random-indices 0 \
  --out-dir desi_lrg_ngc_tau \
  --download \
  --prepare-csv \
  --max-rows 200000
```

`--max-rows` limits the reduced CSV size after download.

## Run galaxy-side pipeline

```bash
python tc_desi_connector.py \
  --tracer LRG \
  --region NGC \
  --random-indices 0 \
  --out-dir desi_lrg_ngc_tau \
  --prepare-csv \
  --max-rows 200000 \
  --run-pipeline \
  --module-dir /path/to/tau/scripts
```

This can run:

\[
\mathcal W^{\rm gal}_{ab},
\quad
S_z,
\quad
(I-\Pi_{\rm sys})\mathcal W.
\]

## Run with lensing input

```bash
python tc_desi_connector.py \
  --tracer LRG \
  --region NGC \
  --random-indices 0 \
  --out-dir desi_lrg_ngc_tau \
  --run-pipeline \
  --module-dir /path/to/tau/scripts \
  --lensing-catalog lensing_kappa_proxy.csv
```

Then the connector calls `tc_obs_pipeline.py` and `tc_verdict_engine.py`.

## Run with mock glob

```bash
python tc_desi_connector.py \
  --tracer LRG \
  --region NGC \
  --out-dir desi_lrg_ngc_tau \
  --run-pipeline \
  --mock-glob "mocks/LRG_NGC_mock_*.fits"
```

## Supported tracers

- `LRG`
- `ELG_LOPnotqso`
- `QSO`
- `BGS_BRIGHT-21.5`
- `BGS_BRIGHT`
- `BGS_ANY`
- `LRG+ELG_LOPnotqso`

Regions:

- `NGC`
- `SGC`

## Production warnings

This is a connector scaffold, not a DESI collaboration analysis. For serious use:

- use official DESI weights exactly as recommended,
- use many random catalogues, not just one,
- use official mocks for covariance,
- do not rely on row-subset CSVs for final claims,
- keep lensing analysis blind,
- document every catalogue version and cut.

## Minimal Tau-chain with DESI

Galaxy side:

\[
D_{\rm DESI}
\rightarrow
\mathcal W^{\rm gal}_{ab}
\rightarrow
\mathcal W^{\rm clean,gal}_{ab}
\rightarrow
S_z
\rightarrow
P_{\Lambda{\rm CDM}}(\mathcal W).
\]

Tau-compatible side:

\[
\mathcal W^{\rm clean,gal}_{ab}
\parallel
\mathcal W^{\rm clean,lens}_{ab}.
\]

DESI alone can produce at most a galaxy-side anomaly. It cannot by itself prove the cross-readout Tau signature.
