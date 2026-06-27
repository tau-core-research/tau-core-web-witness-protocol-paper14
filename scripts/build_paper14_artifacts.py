#!/usr/bin/env python3
"""Build Paper 14 derived tables and figures from the stable smoke run."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "data" / "derived" / "tau_web_v2_full_smoke_stable"
OUT = ROOT / "data" / "derived"
FIG = ROOT / "figures"
PAPER_FIG = ROOT / "paper14_submission_source" / "figures"


def read_json(name: str) -> dict:
    return json.loads((RUN / name).read_text())


def build_summary() -> None:
    obs = read_json("obs_result.json")
    zstab = read_json("zstab_result.json")
    zdiag = read_json("zstab_diag.json")
    zweighted = read_json("zstab_weighted.json")
    sys = read_json("sys_result.json")
    mock = read_json("mock_cov_result.json")
    extra = read_json("extra_result.json")
    final = read_json("final_verdict_v3.json")

    rows = [
        ("galaxy amplitude", "A_gal", obs["A_gal"], obs["verdict"]),
        ("lensing amplitude", "A_lens", obs["A_lens"], obs["verdict"]),
        ("galaxy-lensing tensor cosine", "C_gal_lens", obs["C_gal_lens"], obs["verdict"]),
        ("galaxy-lensing axis alignment", "axis_alignment", obs["axis_alignment"], obs["verdict"]),
        ("redshift tensor stability", "S_z_tensor", zstab["S_z_tensor"], zstab["verdict"]),
        ("redshift axis stability", "S_z_axis", zstab["S_z_axis"], zstab["verdict"]),
        ("weighted tensor stability", "S_tensor_weighted", zweighted["S_tensor_weighted"], zweighted["verdict"]),
        ("systematics retained fraction", "retained_fraction", sys["retained_fraction"], sys["verdict"]),
        ("mock amplitude p-greater", "p_amplitude_greater", mock["p_amplitude_greater"], mock["verdict"]),
        ("extra velocity cosine", "C_gal_velocity", extra["C_gal_velocity"], "extra_readout_pass=%s" % extra["extra_readout_pass"]),
        ("final score", "score", final["score"], final["final_verdict"]),
    ]

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "paper14_stable_smoke_summary.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["quantity", "field", "value", "module_verdict"])
        w.writerows(rows)

    status = {
        "final_verdict": final["final_verdict"],
        "score": final["score"],
        "evidence_level": final["evidence_level"],
        "claim_boundary": "stable smoke run only; no real-data physical validation",
        "recommended_next_actions": final["recommended_next_actions"],
        "z_stability_failure_mode": zdiag["failure_mode"],
    }
    (OUT / "paper14_stable_smoke_status.json").write_text(json.dumps(status, indent=2))


def save_both(fig, name: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    PAPER_FIG.mkdir(parents=True, exist_ok=True)
    for folder in (FIG, PAPER_FIG):
        fig.savefig(folder / name, bbox_inches="tight")


def build_protocol_ladder() -> None:
    levels = [
        ("Level 0", "null / no candidate"),
        ("Level 1", "galaxy-side anomaly only"),
        ("Level 2", "galaxy-lensing aligned\n+ z stable + clean + mock rare"),
        ("Level 3", "plus independent third readout\nstrong witness candidate"),
    ]
    colors = ["#f1f5f9", "#fde68a", "#bfdbfe", "#bbf7d0"]
    fig, ax = plt.subplots(figsize=(8.4, 3.2))
    ax.axis("off")
    for i, ((label, text), color) in enumerate(zip(levels, colors)):
        x = 0.05 + i * 0.235
        ax.add_patch(plt.Rectangle((x, 0.35), 0.2, 0.42, facecolor=color, edgecolor="#334155", linewidth=1.2))
        ax.text(x + 0.1, 0.66, label, ha="center", va="center", fontsize=10, weight="bold")
        ax.text(x + 0.1, 0.49, text, ha="center", va="center", fontsize=8)
        if i < len(levels) - 1:
            ax.annotate("", xy=(x + 0.225, 0.56), xytext=(x + 0.2, 0.56),
                        arrowprops=dict(arrowstyle="->", lw=1.2, color="#334155"))
    ax.text(0.5, 0.12, "Promotion requires independent readout survival, not curve/template rescue.",
            ha="center", va="center", fontsize=9)
    save_both(fig, "fig_tau_web_protocol_ladder.pdf")
    plt.close(fig)


def build_metric_bars() -> None:
    obs = read_json("obs_result.json")
    zstab = read_json("zstab_result.json")
    sys = read_json("sys_result.json")
    mock = read_json("mock_cov_result.json")
    extra = read_json("extra_result.json")
    labels = [
        "C gal-lens",
        "axis gal-lens",
        "S_z tensor",
        "S_z axis",
        "sys retained",
        "C gal-velocity",
    ]
    vals = [
        obs["C_gal_lens"],
        obs["axis_alignment"],
        zstab["S_z_tensor"],
        zstab["S_z_axis"],
        sys["retained_fraction"],
        extra["C_gal_velocity"],
    ]
    fig, ax = plt.subplots(figsize=(8.0, 3.4))
    bars = ax.bar(labels, vals, color=["#2563eb", "#2563eb", "#16a34a", "#16a34a", "#9333ea", "#f97316"])
    ax.axhline(0.8, color="#64748b", lw=1.2, ls="--", label="0.8 witness threshold")
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("unitless alignment / retained fraction")
    ax.set_title("Stable smoke-run readout-survival metrics")
    ax.tick_params(axis="x", rotation=25)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.3f}", ha="center", fontsize=8)
    ax.legend(loc="lower right", fontsize=8)
    save_both(fig, "fig_tau_web_smoke_metrics.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(5.8, 3.0))
    pvals = [obs["null_summary"]["A_gal_p_greater_catalog_scramble"],
             obs["null_summary"]["C_gal_lens_p_greater_tensor_rotation"],
             mock["p_amplitude_greater"],
             mock["p_chi2_greater"]]
    plabels = ["gal scramble", "tensor rotation", "mock amp", "mock chi2"]
    ax.bar(plabels, pvals, color="#0f766e")
    ax.axhline(0.05, color="#991b1b", lw=1.2, ls="--", label="0.05 reference")
    ax.set_ylabel("p-greater / null fraction")
    ax.set_title("Smoke-run null and mock rarity checks")
    ax.tick_params(axis="x", rotation=25)
    for i, v in enumerate(pvals):
        ax.text(i, v + 0.002, f"{v:.4f}", ha="center", fontsize=8)
    ax.legend(fontsize=8)
    save_both(fig, "fig_tau_web_null_checks.pdf")
    plt.close(fig)


def main() -> None:
    build_summary()
    build_protocol_ladder()
    build_metric_bars()
    print("paper14 artifacts built")


if __name__ == "__main__":
    main()

