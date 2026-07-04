# Tau Core Web Witness Protocol Paper 14

Private Paper 14 scaffold:

**A source-frozen multi-readout Tau-web witness protocol**

This repository turns the `TAU_CORE_FULL_PACKAGE_001` material into a
paper-style reproducibility package.  It preserves the source package as
provenance, extracts the stable smoke-run outputs into derived summary
artifacts, and builds a compact manuscript plus arXiv source bundle.

## Main Claim

The paper defines a source-frozen protocol for promoting a cosmic-web anomaly
from a galaxy-only filamentarity signal to a Tau-compatible multi-readout
witness candidate.

Terminology note: the candidate source behind a Tau-compatible web witness is
a web-scale Tau **morphological body**. Galaxy, lensing, velocity, CMB, or
other web tensors are projected readout handles on that body, not the body
itself.

The core rule is:

```text
galaxy-only filamentarity != Tau-compatible signal
```

The minimum Tau-compatible candidate requires:

```text
W_clean,gal parallel W_clean,lens
+ redshift stability
+ systematics projection survival
+ mock rarity
```

A stronger witness candidate additionally requires an independent third readout:

```text
W_clean,gal parallel W_clean,lens parallel W_extra
```

The included stable smoke run reaches `STRONG-WITNESS-CANDIDATE` under the
package verdict engine, but only as a reproducible protocol smoke run.  It is
not a real-data discovery, not a cosmological validation, and not a proof of Tau Core.

Paper 17 adds a downstream readout-covariance guard for this ladder.  Any
future galaxy/lensing web alignment should be reported on two axes:
`Z_shared` for shared-parent covariance and `Z_orient` for
morphology/orientation support.  Orientation-only support is a warning/control
class, not Tau Core evidence by itself.

Paper 18 adds a more concrete photon-lensing morphology handle for this same
guarded ladder: the MAR template `T_tau = B_env A_f M_bf`.  In v2 it also
adds out-of-sample scale validation, physical shear mocks, and a toy
Null-Matter Link diagnostic.  These are useful source-side lensing/morphology
search statistics, but they do not by themselves promote Paper 14's web
witness.  MAR/shear/null-matter correlations remain orientation-like support
until they survive shared-parent covariance, source-overlap, survey-mask, and
systematics controls.

## Required v1.1 Audit Upgrade

A real-data-facing version should not rely only on the current smoke package.
The next reproducibility tier should add:

- raw-generator replay for mock/synthetic web and lensing blocks from seed,
  parent generator, feature matrix, mask and selection rule, noise model,
  covariance rule, and held-out split;
- sensitivity sweeps over thresholds, ridge `lambda` where applicable,
  SNR/map-noise assumptions, feature dimensions, redshift-bin choices, and
  held-out split definitions;
- mock-catalog injection with known web-aligned, misaligned, and
  systematics-dominated components;
- an independent implementation that rebuilds the frozen protocol without
  reusing the original scripts.

These are promotion requirements, not claims that the current smoke run is a
real-data validation.

## Does Not Claim

- It does not claim a detected cosmic-web Tau signal.
- It does not claim that Tau Core has been physically validated.
- It does not claim a replacement for dark matter, dark energy, GR, or LCDM.
- It does not claim that galaxy-only filamentarity is enough.
- It does not claim DESI, Planck, Euclid, Rubin, ACT, or real-survey endpoint
  validation.
- It does not claim a final theory of the cosmic web.

## Reproduce

```bash
python scripts/reproduce.py
```

This command regenerates derived summary tables, figures, the PDF manuscript,
the arXiv source archive, and runs the public package tests.

Expected terminal marker:

```text
PAPER14_REPRODUCTION_COMPLETE
```

## Included Source Package

The original materials from `TAU_CORE_FULL_PACKAGE_001.zip` are preserved under:

```text
source_package_manifest/
config/source_package/
data/source_package_docs/
source_package_scripts/
data/derived/tau_web_v2_full_smoke_stable/
```

The stable smoke-run verdict used by the paper is:

```text
data/derived/tau_web_v2_full_smoke_stable/final_verdict_v3.json
```

## Important Status Labels

```text
TAU_WEB_MULTI_READOUT_WITNESS_PROTOCOL_DECLARED
SOURCE_PACKAGE_IMPORTED_WITH_PROVENANCE
STABLE_SMOKE_RUN_REPRODUCED
STRONG_WITNESS_CANDIDATE_SMOKE_ONLY
REAL_DATA_ENDPOINT_NOT_CLAIMED
COSMOLOGICAL_VALIDATION_NOT_CLAIMED
PHYSICAL_TAU_CORE_VALIDATION_NOT_CLAIMED
```
