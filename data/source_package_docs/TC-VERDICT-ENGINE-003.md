# TC-VERDICT-ENGINE-003 — Strong witness with third readout

## Purpose

This extends verdict v2 with the third-readout criterion.

If the following pass:

1. galaxy anomaly,
2. galaxy–lensing cross-readout,
3. z-stability,
4. systematics cleaning,
5. mock rarity,
6. velocity or CMB/kappa extra readout,

then final verdict becomes:

```text
STRONG-WITNESS-CANDIDATE
```

## Third readout examples

Velocity:

\[
\mathcal V_{ab}
\parallel
\mathcal W^{\rm gal}_{ab}.
\]

CMB/kappa:

\[
\mathcal W^{\rm CMB}_{ab}
\parallel
\mathcal W^{\rm gal}_{ab}.
\]

## Example

```bash
python tc_extra_readout.py \
  --obs-result results/obs_result.json \
  --velocity-catalog data/velocity/velocities.csv \
  --out results/extra_result.json

python tc_verdict_engine_v3.py \
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

## Conservative warning

`STRONG-WITNESS-CANDIDATE` is not a discovery claim.

For real data it requires:

- velocity/CMB-specific mocks,
- independent systematics controls,
- blind axis test,
- covariance with galaxy/lensing maps.
