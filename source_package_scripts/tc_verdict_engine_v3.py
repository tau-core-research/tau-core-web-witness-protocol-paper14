#!/usr/bin/env python3
"""
TC-VERDICT-ENGINE-003
Final Tau-web verdict engine with extra readout strong-witness logic.

Differences from v2
-------------------
- If galaxy/lensing cross-readout, z-stability, systematics, mock rarity,
  and an extra readout pass, the verdict becomes:

      STRONG-WITNESS-CANDIDATE

  even if mock p-values are only "mock rare weak".

- If mock p-values are also very strong, evidence_level records this.

This keeps:
  TAU-COMPATIBLE = two-readout candidate
  STRONG-WITNESS-CANDIDATE = three-readout candidate
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


# We intentionally reuse v2 by importing if available? To keep this standalone,
# call v2 then upgrade verdict if extra readout passes and all other flags pass.

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="TC-VERDICT-ENGINE-003 strong witness wrapper")
    parser.add_argument("--v2-script", default=None, help="Path to tc_verdict_engine_v2.py; default same directory")
    parser.add_argument("--obs-result", default=None)
    parser.add_argument("--zstab-result", default=None)
    parser.add_argument("--zdiag-result", default=None)
    parser.add_argument("--zweighted-result", default=None)
    parser.add_argument("--sys-result", default=None)
    parser.add_argument("--mock-result", default=None)
    parser.add_argument("--extra-result", default=None)
    parser.add_argument("--allow-weighted-z-rescue", action="store_true")
    parser.add_argument("--out", default="tau_final_verdict_v3.json")
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    v2_script = Path(args.v2_script) if args.v2_script else here / "tc_verdict_engine_v2.py"
    if not v2_script.exists():
        raise FileNotFoundError(v2_script)

    tmp = Path(args.out).with_suffix(".v2tmp.json")

    cmd = [sys.executable, str(v2_script), "--out", str(tmp)]
    for flag, val in [
        ("--obs-result", args.obs_result),
        ("--zstab-result", args.zstab_result),
        ("--zdiag-result", args.zdiag_result),
        ("--zweighted-result", args.zweighted_result),
        ("--sys-result", args.sys_result),
        ("--mock-result", args.mock_result),
        ("--extra-result", args.extra_result),
    ]:
        if val:
            cmd.extend([flag, val])
    if args.allow_weighted_z_rescue:
        cmd.append("--allow-weighted-z-rescue")

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise SystemExit(proc.returncode)

    verdict = load_json(tmp)
    extra = load_json(args.extra_result) if args.extra_result else None

    flags = verdict.get("flags", {})
    all_core_pass = (
        flags.get("galaxy_anomaly", {}).get("pass")
        and flags.get("cross_readout", {}).get("pass")
        and flags.get("z_stability", {}).get("pass")
        and flags.get("systematics", {}).get("pass")
        and flags.get("mock_rarity", {}).get("pass")
    )
    extra_pass = bool(extra and extra.get("extra_readout_pass"))

    if all_core_pass and extra_pass:
        mock_strong = bool(flags.get("mock_rarity", {}).get("strong"))
        verdict["final_verdict"] = "STRONG-WITNESS-CANDIDATE"
        verdict["score"] = float(verdict.get("score", 0.0)) + 1.0
        verdict["evidence_level"] = (
            "three-readout-core-pass-mock-strong"
            if mock_strong else
            "three-readout-core-pass"
        )
        verdict["flags"]["extra_readout_v3"] = {
            "pass": True,
            "reason": "; ".join(extra.get("notes", [])),
            "velocity_alignment_pass": extra.get("velocity_alignment_pass"),
            "cmb_alignment_pass": extra.get("cmb_alignment_pass"),
            "C_gal_velocity": extra.get("C_gal_velocity"),
            "C_gal_cmb": extra.get("C_gal_cmb"),
        }
        verdict.setdefault("recommended_next_actions", [])
        verdict["recommended_next_actions"].append(
            "Strong-witness candidate still requires real-data third-readout mocks/nulls before any physical claim."
        )
    elif extra is not None:
        verdict["flags"]["extra_readout_v3"] = {
            "pass": bool(extra.get("extra_readout_pass")),
            "reason": "; ".join(extra.get("notes", [])),
            "velocity_alignment_pass": extra.get("velocity_alignment_pass"),
            "cmb_alignment_pass": extra.get("cmb_alignment_pass"),
        }

    verdict["engine"] = "TC-VERDICT-ENGINE-003"

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(verdict, f, indent=2)

    try:
        tmp.unlink()
    except Exception:
        pass

    print(json.dumps(verdict, indent=2))


if __name__ == "__main__":
    main()
