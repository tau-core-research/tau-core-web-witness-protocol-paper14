# TC-VALIDATION-AUDIT-001 — Tau-Web Pipeline Scientific Validation Audit

## Purpose

The v3 Tau-web pipeline is now technically complete as a research scaffold:

\[
D_{\rm gal}
+
D_{\rm lens}
+
D_{\rm sys}
+
D_{\rm mock}
+
D_{\rm z}
+
D_{\rm extra}
\rightarrow
\text{verdict}.
\]

This audit defines the scientific guardrails needed before any real-data claim.

The central rule remains:

\[
\boxed{
\text{galaxy-only filamentarity is not a Tau-compatible signal.}
}
\]

A Tau-compatible candidate requires:

\[
\boxed{
\mathcal W^{\rm clean,gal}_{ab}
\parallel
\mathcal W^{\rm clean,lens}_{ab}
}
\]

plus z-stability, systematics cleaning, and mock rarity.

A strong witness candidate additionally requires:

\[
\boxed{
\mathcal W^{\rm clean,gal}_{ab}
\parallel
\mathcal W^{\rm clean,lens}_{ab}
\parallel
\mathcal W^{\rm extra}_{ab}.
}
\]

---

# 1. Claim hierarchy

## Level 0 — Null

No significant cleaned galaxy web tensor.

\[
\mathcal W^{\rm clean,gal}_{ab}\approx0.
\]

Interpretation:

```text
No anomaly.
```

---

## Level 1 — Galaxy-side anomaly

\[
\mathcal W^{\rm clean,gal}_{ab}\neq0
\]

and rare relative to galaxy mocks.

Interpretation:

```text
Interesting galaxy/LSS anomaly, not Tau-compatible yet.
```

Verdict:

```text
WEAK-ANOMALY-GALAXY-ONLY
```

---

## Level 2 — Tau-compatible candidate

\[
\mathcal W^{\rm clean,gal}_{ab}
\parallel
\mathcal W^{\rm clean,lens}_{ab}.
\]

with controls:

\[
S_z\text{ stable},
\]

\[
\text{not systematics dominated},
\]

\[
\text{mock rare}.
\]

Verdict:

```text
TAU-COMPATIBLE
```

Interpretation:

```text
Two independent readouts show the same large-scale anisotropic tensor.
```

---

## Level 3 — Strong witness candidate

\[
\mathcal W^{\rm clean,gal}_{ab}
\parallel
\mathcal W^{\rm clean,lens}_{ab}
\parallel
\mathcal W^{\rm extra}_{ab}.
\]

where extra is velocity or CMB/kappa/ISW.

Verdict:

```text
STRONG-WITNESS-CANDIDATE
```

Interpretation:

```text
Three-readout morphological witness candidate.
```

Still not a discovery claim.

---

# 2. Hard vetoes

The following conditions veto a Tau interpretation.

## V1 — Systematics-dominated tensor

If:

\[
\|\Pi_{\rm sys}\mathcal W^{\rm obs}\|
\approx
\|\mathcal W^{\rm obs}\|
\]

or retained fraction is too low:

```text
SYSTEMATICS-DOMINATED
```

Then no physical Tau claim is allowed.

---

## V2 — Galaxy-only signal

If:

\[
\mathcal W^{\rm gal}\neq0
\]

but:

\[
\mathcal W^{\rm lens}\approx0
\]

or:

\[
C_{\rm gal-lens}
\]

is not rare under tensor-rotation nulls, then verdict must remain:

```text
WEAK-ANOMALY-GALAXY-ONLY
```

---

## V3 — Direction-unstable redshift behavior

If z-diagnostic says:

```text
DIRECTION-UNSTABLE
```

then weighted rescue is not allowed.

---

## V4 — Mock-compatible tensor

If:

\[
p_A \geq 0.05
\]

and:

\[
p_{\chi^2}\geq0.05,
\]

then the tensor is not rare relative to mocks.

No anomaly claim.

---

## V5 — Post-hoc axis tuning

If the lensing or velocity axis is searched after seeing the galaxy axis without a preregistered test, the result is exploratory only.

No confirmatory claim.

---

# 3. Required null tests

## N1 — Angular scramble

Preserve radial distribution, randomize sky directions.

Expected:

\[
\mathcal W^{\rm gal}\rightarrow0.
\]

---

## N2 — Radial scramble

Preserve angular footprint, shuffle radii/redshifts.

If signal remains, footprint or angular systematics are suspected.

---

## N3 — Tensor rotation null

Preserve galaxy and lensing tensor amplitudes, randomize relative orientation.

Expected:

\[
C_{\rm gal-lens}
\]

should fall to random-orientation distribution.

---

## N4 — Survey randoms

Use official survey random catalogues to build:

\[
\mathcal H_{\rm sys}.
\]

Then project:

\[
\mathcal W^{\rm clean}
=
(I-\Pi_{\rm sys})\mathcal W^{\rm obs}.
\]

---

## N5 — Mock covariance

Use official \(\Lambda\)CDM mocks:

\[
P_{\Lambda{\rm CDM}}(\mathcal W).
\]

Compute both amplitude p-value and Mahalanobis p-value.

---

## N6 — Blind lensing test

Galaxy tensor must be frozen first:

\[
\mathcal W^{\rm gal}_{ab}\ \text{locked}.
\]

Then lensing alignment is evaluated once.

No repeated tuning.

---

## N7 — Extra readout nulls

Velocity/CMB readout needs its own nulls:

- velocity direction randomization,
- bulk-flow subtraction null,
- distance-error perturbation,
- CMB/kappa map rotation,
- mask-only CMB/kappa test.

---

# 4. Pre-registered thresholds

Default exploratory thresholds:

| Quantity | Threshold |
|---|---:|
| \(C_{\rm gal-lens}\) | \(>0.80\) |
| tensor-rotation \(p\) | \(<0.05\) |
| \(S_z^{\rm tensor}\) | \(>0.80\) |
| \(S_z^{\rm axis}\) | \(>0.80\) |
| systematics retained fraction | \(>0.60\) |
| mock \(p_A\) or \(p_{\chi^2}\) | \(<0.05\) |
| extra readout alignment | \(>0.80\) |

For confirmatory work, thresholds should be preregistered before opening the lensing/extra-readout result.

---

# 5. Failure mode table

| Failure | Meaning | Allowed action |
|---|---|---|
| `NULL` | no significant tensor | stop |
| `WEAK-ANOMALY-GALAXY-ONLY` | galaxy-only anisotropy | seek lensing readout; no Tau claim |
| `SYSTEMATICS-DOMINATED` | survey/template aligned | improve systematics model |
| `Z-UNSTABLE` | redshift direction unstable | do not upgrade |
| `LOW-AMPLITUDE-BIN-NOISE` | weak bins dominate failure | weighted rescue allowed |
| `WEIGHTED-Z-UNSTABLE` | even weighted stability fails | no z-stability |
| `MOCK-COMPATIBLE` | common in mocks | no anomaly |
| `TAU-COMPATIBLE` | two-readout candidate | seek third readout |
| `STRONG-WITNESS-CANDIDATE` | three-readout candidate | run external replication |

---

# 6. What would falsify the Tau-web module?

The Tau-web module is weakened or falsified if, after proper systematics and mocks:

## F1 — Galaxy signal vanishes

\[
\mathcal W^{\rm clean,gal}_{ab}\approx0.
\]

## F2 — Lensing fails to align

\[
C_{\rm gal-lens}
\approx0
\]

or is common under tensor-rotation null.

## F3 — Redshift instability persists

\[
S_z^{\rm tensor},S_z^{\rm axis}
\]

fail even after amplitude/noise diagnostics.

## F4 — Mocks reproduce the signal

\[
p_A,p_{\chi^2}\geq0.05.
\]

## F5 — Extra readout contradicts

Velocity or CMB/kappa tensor is significantly misaligned:

\[
C_{\rm gal-extra}<0
\]

or consistent with random orientation.

## F6 — Survey-systematics alignment dominates

\[
\mathcal W^{\rm obs}\in\mathcal H_{\rm sys}.
\]

---

# 7. What would strengthen the Tau-web module?

## S1 — Independent galaxy tracers

LRG, ELG, QSO, BGS all show compatible cleaned tensors.

## S2 — Independent lensing maps

Euclid/Rubin/Planck-like kappa maps independently align.

## S3 — Velocity field alignment

\[
\mathcal V_{ab}
\parallel
\mathcal W^{\rm gal}_{ab}.
\]

## S4 — CMB-lensing / ISW consistency

A weak but aligned projected CMB-lensing/ISW tensor.

## S5 — Stable redshift evolution

Not just stable direction, but a smooth amplitude evolution:

\[
\mathcal W_{ab}(z)
\approx
\lambda(z)\mathcal W_{ab}(z_0).
\]

## S6 — External replication

Same pipeline frozen and run on independent survey data.

---

# 8. Minimum publishable analysis package

A serious analysis should include:

1. frozen code commit,
2. frozen runbook,
3. input catalogue versions,
4. random catalogue versions,
5. mock catalogue versions,
6. thresholds,
7. blind-test declaration,
8. all null outputs,
9. covariance outputs,
10. final JSON verdict,
11. failure cases,
12. reproducibility script.

---

# 9. Recommended next module

\[
\boxed{\text{TC-REPLICATION-PACK-001}}
\]

Purpose:

Create a reproducibility package with:

- config file,
- exact command sequence,
- checksum manifest,
- expected output schema,
- frozen thresholds,
- preregistration template.

This turns the current research scaffold into a shareable audit packet.
