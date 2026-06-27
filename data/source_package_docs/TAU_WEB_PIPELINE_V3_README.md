# Tau Web Pipeline v3 Bundle

This is the full Tau-web pipeline with third-readout strong-witness support.

## Main additions over v2

- `tc_extra_readout.py`
- `tc_verdict_engine_v3.py`
- `TC-RUNBOOK-003.md`
- `run_tau_web_desi_v3.sh`

## Verdict ladder

```text
NULL
WEAK-ANOMALY-GALAXY-ONLY
TAU-COMPATIBLE-CANDIDATE
TAU-COMPATIBLE-WEIGHTED-Z-CANDIDATE
TAU-COMPATIBLE
STRONG-WITNESS-CANDIDATE
SYSTEMATICS-DOMINATED
```

## Strong witness condition

The strong-witness candidate requires at least three aligned readouts:

\[
W^{gal} \parallel W^{lens} \parallel V
\]

or:

\[
W^{gal} \parallel W^{lens} \parallel W^{CMB}.
\]

## First command

```bash
bash -n run_tau_web_desi_v3.sh
```

Then read `TC-RUNBOOK-003.md`.

## Scientific warning

This is a research scaffold. Real claims require official catalogues, masks, mocks, covariance, and blind tests.
