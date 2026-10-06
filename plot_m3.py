"""M3 summary figure: estimator x eps, median error over the main cells, hard cells marked.

  python plot_m3.py -> results/m3_summary.png
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analyse_m3 import SWITCHES, add_switch, cell_errors, choose_tau  # noqa: E402
from plot_m1 import GRID, INK, INK2, SURFACE, style  # noqa: E402
from plot_m2 import EPS, EPS_COLORS, HARD_MARKERS  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
SHOW = [("replay", "Replay"), ("sntpdis_k4", "SN trunc. PDIS k=4"), ("mb_trees", "MB trees"),
        ("mbcalq_trees", "MB trees, calibrated"), ("dr_k4", "DR k=4"), ("drmb_k4", "DR-MB k=4"),
        ("switch_dr", "Switch (DR k=4 / MB)"), ("mbcalq_knee", "MB knee, calibrated (bound)")]


def main():
    est = pd.read_csv(os.path.join(RES, "raw", "m3_estimates.csv.gz"))
    tau, _ = choose_tau(est, SWITCHES["switch_dr"])
    ce = cell_errors(pd.concat([est, add_switch(est, "switch_dr", SWITCHES["switch_dr"], tau)], ignore_index=True))
    d = ce[ce.scope == "all"]
    names = [e for e, _ in SHOW]
    fig, axes = plt.subplots(1, 2, figsize=(15, 4.8), facecolor=SURFACE)
    x, w = np.arange(len(names)), 0.26
    for ax, col, ylabel, gate in ((axes[0], "sla_abs_err", "|error|, SLA points", 3.0),
                                  (axes[1], "cost_rel_err_pct", "|error|, % of true cost", 15.0)):
        style(ax)
        for j, (eps, color) in enumerate(zip(EPS, EPS_COLORS)):
            g = d[d.eps == eps]
            med = g.groupby("estimator")[col].median().reindex(names)
            ax.bar(x + (j - 1) * w, med.clip(lower=0.01), width=w - 0.02, color=color, edgecolor=SURFACE,
                   linewidth=1, label=f"median over main cells, eps={eps:g}")
            for tgt, (mk, lab) in HARD_MARKERS.items():
                h = g[(g.family == "bitbrains") & (g.workload == "io-bound") & (g.target == tgt)]
                v = h.set_index("estimator")[col].reindex(names)
                ax.scatter(x + (j - 1) * w, v.clip(lower=0.01), marker=mk, s=26, facecolor=SURFACE,
                           edgecolor=INK, linewidth=1.2, zorder=3, label=lab if j == 0 else None)
            mx = g.groupby("estimator")[col].max().reindex(names)
            ax.scatter(x + (j - 1) * w, mx, marker="_", s=90, color=INK2, zorder=3,
                       label="max over main cells" if j == 0 else None)
        ax.axhline(gate, color=INK2, linewidth=1, linestyle=(0, (4, 3)))
        ax.set_yscale("log")
        ax.set_xticks(x, [l for _, l in SHOW], rotation=22, ha="right", fontsize=8)
        ax.set_ylabel(ylabel, color=INK2, fontsize=9)
        ax.grid(False, axis="x")
    axes[0].set_title("SLA% (dashed: 3-point gate)", color=INK, fontsize=10)
    axes[1].set_title("Cost (dashed: 15% gate)", color=INK, fontsize=10)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=7, frameon=False, fontsize=8, labelcolor=INK)
    fig.suptitle(f"Hybrid estimators (M3), 200 logged episodes, 4 main workloads x 8 targets; switch tau={tau:.2f} "
                 "chosen on Azure; values below 0.01 drawn at 0.01", color=INK, fontsize=11)
    fig.tight_layout(rect=(0, 0.08, 1, 0.94))
    fig.savefig(os.path.join(RES, "m3_summary.png"), dpi=160, facecolor=SURFACE)
    print("wrote results/m3_summary.png")


if __name__ == "__main__":
    main()
