"""M1b figures: per-target error of replay vs truncated PDIS, by family x workload.

  python plot_m1b.py   -> results/m1b_err_by_target_sla.png, results/m1b_err_by_target_cost.png
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from plot_m1 import INK, INK2, SERIES, SURFACE, style  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
EPS, K = 0.05, 4
ESTIMATORS = [("replay", "Replay (naive)"), (f"tpdis_k{K}", f"Truncated PDIS k={K}"),
              (f"sntpdis_k{K}", f"Self-normalised truncated PDIS k={K}")]
TARGETS = ["hpa30", "hpa50", "hpa90", "hpa95", "hpa70_stab0", "hpa70_stab10", "slo_cost", "pred70"]
PANELS = [("azure", "cpu-bound"), ("azure", "io-bound"), ("azure", "mixed_L100"),
          ("bitbrains", "cpu-bound"), ("bitbrains", "io-bound"), ("bitbrains", "mixed_L100")]


def plot(est, col, ylabel, gate, out, title):
    d = est[(est.n_episodes == 200) & (est.eps == EPS) & (est.scope == "all")]
    fig, axes = plt.subplots(2, 3, figsize=(14, 6.4), facecolor=SURFACE)
    x = np.arange(len(TARGETS))
    for ax, (fam, wl) in zip(axes.flat, PANELS):
        style(ax)
        g = d[(d.family == fam) & (d.workload == wl)]
        for j, (color, (e, label)) in enumerate(zip(SERIES, ESTIMATORS)):
            v = g[g.estimator == e].groupby("target")[col].mean().reindex(TARGETS)
            ax.bar(x + (j - 1) * 0.27, v, width=0.25, color=color, label=label,
                   edgecolor=SURFACE, linewidth=1)
        ax.axhline(gate, color=INK2, linewidth=1, linestyle=(0, (4, 3)))
        ax.set_xticks(x, TARGETS, rotation=40, ha="right", fontsize=7)
        extra = " (100-step episodes)" if "L100" in wl else ""
        ax.set_title(f"{fam} {wl.replace('_L100', '')}{extra}", color=INK, fontsize=10)
    for ax in axes[:, 0]:
        ax.set_ylabel(ylabel, color=INK2, fontsize=9)
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, frameon=False, fontsize=9, labelcolor=INK)
    fig.suptitle(title, color=INK, fontsize=11)
    fig.tight_layout(rect=(0, 0.06, 1, 0.95))
    fig.savefig(os.path.join(RES, out), dpi=160, facecolor=SURFACE)


if __name__ == "__main__":
    est = pd.read_csv(os.path.join(RES, "raw", "m1b_estimates.csv.gz"))
    plot(est, "sla_abs_err", "|error|, SLA points", 3.0, "m1b_err_by_target_sla.png",
         f"SLA% error per target, eps={EPS}, 200 logged episodes, mean over 5 logging seeds "
         "(dashed: 3-point gate)")
    plot(est, "cost_rel_err_pct", "|error|, % of true cost", 15.0, "m1b_err_by_target_cost.png",
         f"Cost error per target, eps={EPS}, 200 logged episodes, mean over 5 logging seeds "
         "(dashed: 15% gate)")
    print("wrote results/m1b_err_by_target_sla.png, results/m1b_err_by_target_cost.png")
