# TC-RUNBOOK-003 — Full Tau-Web Pipeline with Strong-Witness Third Readout

## Purpose

This is the full v3 runbook for the Tau-web observational pipeline.

It includes:

1. DESI / LSS galaxy readout,
2. lensing / mass-map readout,
3. redshift stability,
4. z-stability diagnostics,
5. weighted z-stability rescue,
6. systematics projection,
7. mock covariance,
8. optional third readout:
   - peculiar velocity tensor, or
   - CMB-lensing / ISW / kappa tensor,
9. final v3 verdict engine.

The full strong-witness signature is:

\[
\boxed{
\mathcal W^{\rm clean,gal}_{ab}
\parallel
\mathcal W^{\rm clean,lens}_{ab}
\parallel
\mathcal V_{ab}
}
\]

or:

\[
\boxed{
\mathcal W^{\rm clean,gal}_{ab}
\parallel
\mathcal W^{\rm clean,lens}_{ab}
\parallel
\mathcal W^{\rm CMB}_{ab}.
}
\]

---

# 1. Verdict ladder

## `NULL`

No significant cleaned galaxy web anomaly.

## `WEAK-ANOMALY-GALAXY-ONLY`

Galaxy filamentarity exists, but no independent lensing/mass readout alignment.

This is **not** Tau-compatible.

## `TAU-COMPATIBLE-CANDIDATE`

Galaxy–lensing cross-readout exists, but one or more controls are missing or failed.

## `TAU-COMPATIBLE-WEIGHTED-Z-CANDIDATE`

Weighted z-stability rescues a low-amplitude-bin failure. This is weaker than plain `TAU-COMPATIBLE`.

## `TAU-COMPATIBLE`

Galaxy–lensing cross-readout passes, plain z-stability passes, systematics cleaning passes, and mock rarity passes.

## `STRONG-WITNESS-CANDIDATE`

Everything in `TAU-COMPATIBLE` passes, plus at least one extra independent readout passes:

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

This is still a candidate, not a discovery claim.

---

# 2. Full v3 directory layout

```text
tau_web_run/
  scripts/
    tc_desi_connector.py
    tc_lensing_connector.py
    tc_obs_pipeline.py
    tc_zstab_pipeline.py
    tc_zstab_diag.py
    tc_zstab_weighted.py
    tc_sys_projector.py
    tc_mock_cov.py
    tc_extra_readout.py
    tc_verdict_engine_v3.py

  data/
    desi/
      LRG_NGC_clustering.reduced.csv
      LRG_NGC_randoms.reduced.csv

    lensing/
      lensing_input.csv
      lensing_reduced.csv

    velocity/
      velocities.csv

    cmb/
      cmb_kappa_pixels.csv

    mocks/
      mock_000.csv
      mock_001.csv

  results/
    obs_result.json
    zstab_result.json
    zstab_diag.json
    zstab_weighted.json
    sys_result.json
    mock_cov_result.json
    extra_result.json
    final_verdict_v3.json
```

---

# 3. Galaxy side: DESI

## 3.1 Plan

```bash
python scripts/tc_desi_connector.py \
  --tracer LRG \
  --region NGC \
  --random-indices 0 \
  --out-dir data/desi \
  --plan
```

## 3.2 Download and reduce

```bash
python scripts/tc_desi_connector.py \
  --tracer LRG \
  --region NGC \
  --random-indices 0 \
  --out-dir data/desi \
  --download \
  --prepare-csv \
  --max-rows 200000
```

Creates:

```text
data/desi/LRG_NGC_clustering.reduced.csv
data/desi/LRG_NGC_randoms.reduced.csv
```

---

# 4. Lensing / mass-map side

## 4.1 Kappa table

```bash
python scripts/tc_lensing_connector.py \
  --mode kappa-table \
  --input data/lensing/lensing_input.csv \
  --out data/lensing/lensing_reduced.csv \
  --redshift-proxy 1.0
```

## 4.2 Shear-flat development proxy

```bash
python scripts/tc_lensing_connector.py \
  --mode shear-flat \
  --input data/lensing/shear_catalog.csv \
  --out data/lensing/lensing_reduced.csv \
  --grid 128 \
  --redshift-proxy 1.0
```

## 4.3 HEALPix kappa map

```bash
python scripts/tc_lensing_connector.py \
  --mode healpix-kappa \
  --input data/lensing/kappa_map.fits \
  --out data/lensing/lensing_reduced.csv \
  --redshift-proxy 2.0 \
  --max-pixels 500000
```

---

# 5. Main two-readout Tau-web tests

## 5.1 Galaxy–lensing cross-readout

```bash
python scripts/tc_obs_pipeline.py \
  --galaxy data/desi/LRG_NGC_clustering.reduced.csv \
  --lensing data/lensing/lensing_reduced.csv \
  --n-nulls 100 \
  --out results/obs_result.json \
  --null-out results/obs_nulls.csv \
  --max-pairs 300000
```

Key condition:

\[
C_{\rm gal-lens}>0.8.
\]

## 5.2 Plain z-stability

```bash
python scripts/tc_zstab_pipeline.py \
  --catalog data/desi/LRG_NGC_clustering.reduced.csv \
  --n-bins 5 \
  --min-per-bin 500 \
  --out results/zstab_result.json \
  --bins-out results/zstab_bins.csv \
  --max-pairs 300000
```

Key condition:

\[
S_z^{\rm tensor}>0.8,
\quad
S_z^{\rm axis}>0.8.
\]

## 5.3 Z diagnostic

```bash
python scripts/tc_zstab_diag.py \
  --zstab-result results/zstab_result.json \
  --out results/zstab_diag.json \
  --tensor-matrix-out results/zstab_tensor_matrix.csv \
  --axis-matrix-out results/zstab_axis_matrix.csv
```

## 5.4 Weighted z-stability

```bash
python scripts/tc_zstab_weighted.py \
  --zstab-result results/zstab_result.json \
  --out results/zstab_weighted.json \
  --pairs-out results/zstab_weighted_pairs.csv \
  --amp-relative-floor 0.35 \
  --weight-power 1.0
```

Weighted rescue is allowed only if the diagnostic says the failure was not genuine direction instability.

---

# 6. Systematics

```bash
python scripts/tc_sys_projector.py \
  --observed data/desi/LRG_NGC_clustering.reduced.csv \
  --systematics data/desi/LRG_NGC_randoms.reduced.csv \
  --out results/sys_result.json \
  --max-pairs 300000
```

Reject if:

```text
SYSTEMATICS-DOMINATED
```

or if retained fraction is too low.

---

# 7. Mock covariance

```bash
python scripts/tc_mock_cov.py \
  --observed data/desi/LRG_NGC_clustering.reduced.csv \
  --mock-glob "data/mocks/mock_*.csv" \
  --systematics data/desi/LRG_NGC_randoms.reduced.csv \
  --out results/mock_cov_result.json \
  --mock-out results/mock_cov_rows.csv \
  --max-pairs 300000
```

Key conditions:

\[
p_A<0.05
\]

or:

\[
p_{\chi^2}<0.05.
\]

---

# 8. Third readout

## 8.1 Peculiar velocity tensor

Velocity input:

```csv
x,y,z,vx,vy,vz,weight
```

or:

```csv
ra,dec,redshift,vx,vy,vz,weight
```

Run:

```bash
python scripts/tc_extra_readout.py \
  --obs-result results/obs_result.json \
  --velocity-catalog data/velocity/velocities.csv \
  --out results/extra_result.json
```

This computes:

\[
\mathcal V_{ab}
=
\mathrm{STF}
\left[
\sum_i w_i\hat v_{i,a}\hat v_{i,b}
\right].
\]

Pass condition:

\[
\mathcal V_{ab}
\parallel
\mathcal W^{\rm gal}_{ab}.
\]

## 8.2 CMB/kappa tensor

CMB/kappa input:

```csv
x,y,z,kappa
```

or:

```csv
ra,dec,redshift,kappa
```

Run:

```bash
python scripts/tc_extra_readout.py \
  --obs-result results/obs_result.json \
  --cmb-kappa-catalog data/cmb/cmb_kappa_pixels.csv \
  --out results/extra_result.json
```

Pass condition:

\[
\mathcal W^{\rm CMB}_{ab}
\parallel
\mathcal W^{\rm gal}_{ab}.
\]

---

# 9. Final v3 verdict

```bash
python scripts/tc_verdict_engine_v3.py \
  --obs-result results/obs_result.json \
  --zstab-result results/zstab_result.json \
  --zdiag-result results/zstab_diag.json \
  --zweighted-result results/zstab_weighted.json \
  --sys-result results/sys_result.json \
  --mock-result results/mock_cov_result.json \
  --extra-result results/extra_result.json \
  --allow-weighted-z-rescue \
  --out results/final_verdict_v3.json
```

---

# 10. One-command orchestrator

Use:

```bash
./run_tau_web_desi_v3.sh
```

or:

```bash
TRACER=LRG \
REGION=NGC \
ROOT=tau_web_run \
MAX_ROWS=200000 \
MAX_PAIRS=300000 \
./run_tau_web_desi_v3.sh
```

Optional velocity:

```bash
VELOCITY_INPUT=tau_web_run/data/velocity/velocities.csv \
./run_tau_web_desi_v3.sh
```

Optional CMB/kappa:

```bash
CMB_KAPPA_INPUT=tau_web_run/data/cmb/cmb_kappa_pixels.csv \
./run_tau_web_desi_v3.sh
```

---

# 11. Interpretation

## Two-readout candidate

If:

\[
\mathcal W^{\rm gal}_{ab}
\parallel
\mathcal W^{\rm lens}_{ab}
\]

but no velocity/CMB readout exists, the maximum class is:

```text
TAU-COMPATIBLE
```

## Three-readout candidate

If:

\[
\mathcal W^{\rm gal}_{ab}
\parallel
\mathcal W^{\rm lens}_{ab}
\parallel
\mathcal V_{ab}
\]

or:

\[
\mathcal W^{\rm gal}_{ab}
\parallel
\mathcal W^{\rm lens}_{ab}
\parallel
\mathcal W^{\rm CMB}_{ab},
\]

then the maximum class is:

```text
STRONG-WITNESS-CANDIDATE
```

Still not a discovery claim.

---

# 12. Production warning

For real data:

- velocity catalogues need distance-error modelling,
- CMB/kappa maps need light-cone kernel treatment,
- third-readout mocks are mandatory,
- blind tests are mandatory,
- survey masks must be propagated through every readout.

The v3 pipeline is a formal research scaffold.
