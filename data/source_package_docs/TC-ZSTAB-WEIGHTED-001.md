# TC-ZSTAB-WEIGHTED-001 — Amplitude-weighted redshift stability

## Purpose

Plain redshift stability can fail when one or more bins have weak web amplitude. In a weak bin, the principal axis is noise-dominated, so the unweighted score can falsely reject an otherwise coherent signal.

This module computes:

\[
S_{z,w}^{\rm tensor}
=
\frac{
\sum_{i<j}(A_iA_j)^p C_{ij}^{\rm tensor}
}{
\sum_{i<j}(A_iA_j)^p
}
\]

and:

\[
S_{z,w}^{\rm axis}
=
\frac{
\sum_{i<j}(A_iA_j)^p |e_i\cdot e_j|
}{
\sum_{i<j}(A_iA_j)^p
}.
\]

It can also drop very low-amplitude bins:

\[
A_i < f A_{\max}.
\]

Default:

\[
f=0.35,
\quad
p=1.
\]

## When to use

Use this only after `TC-ZSTAB-DIAG-001` reports:

```text
LOW-AMPLITUDE-BIN-NOISE
```

Do **not** use it to rescue a clearly direction-unstable signal.

## Example

```bash
python tc_zstab_weighted.py \
  --zstab-result results/zstab_result.json \
  --out results/zstab_weighted.json \
  --pairs-out results/zstab_weighted_pairs.csv \
  --amp-relative-floor 0.35 \
  --weight-power 1.0
```

## Verdicts

### `WEIGHTED-Z-STABLE`

Weighted tensor and axis stability both pass.

### `WEIGHTED-AXIS-STABLE-WEAK`

Dominant axis survives, but tensor shape is not fully stable.

### `ADJACENT-STABLE-GLOBAL-DRIFT`

Nearby slices align, but far-apart slices drift.

### `WEIGHTED-Z-UNSTABLE`

Even weighted stability fails.

### `INSUFFICIENT-RETAINED-BINS`

Too many bins were dropped by amplitude threshold.

## Interpretation

This module should produce a *secondary* stability flag, not replace the primary one.

Recommended logic:

- If plain `Z-STABLE`: pass.
- If plain fail but diagnostic says `LOW-AMPLITUDE-BIN-NOISE`, and weighted says `WEIGHTED-Z-STABLE`: allow `Z-STABLE-WEIGHTED-CANDIDATE`.
- If diagnostic says `DIRECTION-UNSTABLE`, do not rescue with weighting.
