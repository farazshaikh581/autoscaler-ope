"""M1 figures from results/raw/m1_estimates.csv.gz and results/m1_dither_cost.csv.

  python plot_m1.py   -> results/m1_err_vs_eps.png, results/m1_dither_cost.png
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")

# Reference categorical palette, fixed order (dataviz skill, light mode).
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
ESTIMATORS = [("replay", "Replay (naive)"), ("is", "Trajectory IS"), ("pdis", "PDIS"),
              ("wpdis", "Weighted PDIS"), ("tpdis_k1", "Truncated PDIS k=1"),
              ("tpdis_k2", "Truncated PDIS k=2"), ("tpdis_k4", "Truncated PDIS k=4"),
              ("tpdis_k8", "Truncated PDIS k=8")]
TARGETS = [("hpa50", "HPA u=0.5"), ("hpa60", "HPA u=0.6"), ("hpa80", "HPA u=0.8"),
           ("hpa90", "HPA u=0.9"), ("pred70", "Predictive u=0.7")]
WORKLOADS = ["cpu-bound", "io-bound", "mixed"]


def style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def err_vs_eps(est: pd.DataFrame):
    d = est[(est.n_episodes == 200)]
    eps = sorted(d.eps.unique())
    fig, axes = plt.subplots(1, len(TARGETS), figsize=(15, 3.6), sharey=True, facecolor=SURFACE)
    for ax, (tgt, tlabel) in zip(axes, TARGETS):
        style(ax)
        for color, (e, elabel) in zip(SERIES, ESTIMATORS):
            med = d[(d.target == tgt) & (d.estimator == e)].groupby("eps").sla_abs_err.median().reindex(eps)
            ax.plot(range(len(eps)), med.clip(lower=0.05), color=color, linewidth=2, marker="o",
                    markersize=5, markeredgecolor=SURFACE, markeredgewidth=1.5, label=elabel)
        ax.axhline(1.0, color=INK2, linewidth=1, linestyle=(0, (4, 3)))
        ax.set_yscale("log")
        ax.set_xticks(range(len(eps)), [f"{e:g}" for e in eps])
        ax.set_title(tlabel, color=INK, fontsize=10)
        ax.set_xlabel("dither probability eps", color=INK2, fontsize=9)
    axes[0].set_ylabel("median |error|, SLA points (log)", color=INK2, fontsize=9)
    axes[0].text(0.02, 1.0, "1 point", color=INK2, fontsize=7, va="bottom",
                 transform=axes[0].get_yaxis_transform())
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=8, frameon=False, fontsize=8, labelcolor=INK)
    fig.suptitle("Off-policy SLA% error vs dither, 200 logged episodes "
                 "(median over 3 workloads x 5 logging seeds)", color=INK, fontsize=11)
    fig.tight_layout(rect=(0, 0.08, 1, 0.95))
    fig.savefig(os.path.join(RES, "m1_err_vs_eps.png"), dpi=160, facecolor=SURFACE)


def dither_cost(dc: pd.DataFrame):
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4), facecolor=SURFACE)
    eps = sorted(dc.eps.unique())
    dc = dc.assign(sla_change_vs_eps0=-dc.sla_drop_vs_eps0)
    for ax, col, ylabel in ((axes[0], "sla_change_vs_eps0", "SLA change vs eps=0 (points)"),
                            (axes[1], "cost_change_vs_eps0", "cost change vs eps=0 (vCPU)")):
        ends = {wl: dc[(dc.workload == wl) & (dc.eps == max(eps))][col].iloc[0] for wl in WORKLOADS}
        order = sorted(WORKLOADS, key=ends.get)
        nudge = {wl: 6 * (i - 1) for i, wl in enumerate(order)}   # spread end labels by rank
        style(ax)
        for color, wl in zip(SERIES, WORKLOADS):
            s = dc[dc.workload == wl].set_index("eps")[col].reindex(eps)
            ax.plot(eps, s, color=color, linewidth=2, marker="o", markersize=5,
                    markeredgecolor=SURFACE, markeredgewidth=1.5, label=wl)
            ax.annotate(wl, (eps[-1], s.iloc[-1]), xytext=(6, nudge[wl]), textcoords="offset points",
                        color=INK2, fontsize=8, va="center")
        ax.axhline(0, color=INK2, linewidth=1)
        ax.set_xlabel("dither probability eps", color=INK2, fontsize=9)
        ax.set_ylabel(ylabel, color=INK2, fontsize=9)
        ax.set_xlim(-0.01, max(eps) * 1.25)
    axes[0].legend(frameon=False, fontsize=8, labelcolor=INK)
    fig.suptitle("What dithering costs the operator (behaviour policy, 1000 episodes per point)",
                 color=INK, fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(os.path.join(RES, "m1_dither_cost.png"), dpi=160, facecolor=SURFACE)


if __name__ == "__main__":
    err_vs_eps(pd.read_csv(os.path.join(RES, "raw", "m1_estimates.csv.gz")))
    dither_cost(pd.read_csv(os.path.join(RES, "m1_dither_cost.csv")))
    print("wrote results/m1_err_vs_eps.png, results/m1_dither_cost.png")
