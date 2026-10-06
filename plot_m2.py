"""M2 summary figure: estimator x eps, median error over the main cells, hard cells marked.

  python plot_m2.py -> results/m2_summary.png
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analyse_m2 import ESTIMATORS, HARD, cell_errors  # noqa: E402
from plot_m1 import GRID, INK, INK2, SURFACE, style  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
EPS = (0.0, 0.05, 0.1)
EPS_COLORS = ["#86b6ef", "#2a78d6", "#104281"]     # sequential blue ramp: eps is ordinal
HARD_MARKERS = {"hpa90": ("D", "Bitbrains io HPA-90"), "hpa95": ("^", "Bitbrains io HPA-95"),
                "slo_cost": ("s", "Bitbrains io SLO-cost-aware")}
LABELS = {"replay": "Replay", "sntpdis_k4": "SN trunc. PDIS k=4", "mb_trees": "MB trees",
          "mb_knee": "MB knee", "dr_k2": "DR k=2", "dr_k4": "DR k=4", "dr_k8": "DR k=8"}


def main():
    est = pd.read_csv(os.path.join(RES, "raw", "m2_estimates.csv.gz"))
    ce = cell_errors(est)
    d = ce[(ce.n_episodes == 200) & (ce.scope == "all")]
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.6), facecolor=SURFACE)
    x = np.arange(len(ESTIMATORS))
    w = 0.26
    for ax, col, ylabel, gate in ((axes[0], "sla_abs_err", "|error|, SLA points", 3.0),
                                  (axes[1], "cost_rel_err_pct", "|error|, % of true cost", 15.0)):
        style(ax)
        for j, (eps, color) in enumerate(zip(EPS, EPS_COLORS)):
            g = d[d.eps == eps]
            med = g.groupby("estimator")[col].median().reindex(ESTIMATORS)
            ax.bar(x + (j - 1) * w, med.clip(lower=0.05), width=w - 0.02, color=color,
                   edgecolor=SURFACE, linewidth=1, label=f"median over main cells, eps={eps:g}")
            for tgt, (mk, lab) in HARD_MARKERS.items():
                h = g[(g.family == "bitbrains") & (g.workload == "io-bound") & (g.target == tgt)]
                v = h.set_index("estimator")[col].reindex(ESTIMATORS)
                ax.scatter(x + (j - 1) * w, v.clip(lower=0.05), marker=mk, s=28, facecolor=SURFACE,
                           edgecolor=INK, linewidth=1.2, zorder=3, label=lab if j == 0 else None)
        ax.axhline(gate, color=INK2, linewidth=1, linestyle=(0, (4, 3)))
        ax.set_yscale("log")
        ax.set_xticks(x, [LABELS[e] for e in ESTIMATORS], rotation=20, ha="right", fontsize=8)
        ax.set_ylabel(ylabel, color=INK2, fontsize=9)
        ax.grid(True, axis="y", color=GRID, linewidth=0.8)
        ax.grid(False, axis="x")
    axes[0].set_title("SLA% (dashed: 3-point gate)", color=INK, fontsize=10)
    axes[1].set_title("Cost (dashed: 15% gate)", color=INK, fontsize=10)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=6, frameon=False, fontsize=8, labelcolor=INK)
    fig.suptitle("Off-policy error by estimator and dither, 200 logged episodes, 4 main workloads x 8 targets "
                 "(bars: median; markers: hard cells; values below 0.05 drawn at 0.05)", color=INK, fontsize=11)
    fig.tight_layout(rect=(0, 0.08, 1, 0.94))
    fig.savefig(os.path.join(RES, "m2_summary.png"), dpi=160, facecolor=SURFACE)
    print("wrote results/m2_summary.png")


if __name__ == "__main__":
    main()
