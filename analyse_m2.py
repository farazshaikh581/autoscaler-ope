"""M2 summary tables from results/raw/m2_estimates.csv.gz.

  python analyse_m2.py -> results/m2_summary.csv, m2_hard_cells.csv, m2_gate.csv,
                          m2_learning_curve.csv, printed summary

Main cells: Azure and Bitbrains cpu-bound and io-bound (200-step episodes) x the 8
targets (hpa70 sanity excluded). Errors are against the paired truth; each cell's
error is first averaged over the 5 logging seeds, then summarised across cells.
"""
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
ESTIMATORS = ["replay", "sntpdis_k4", "mb_trees", "mb_knee", "dr_k2", "dr_k4", "dr_k8"]
HARD = [("bitbrains", "io-bound", t) for t in ("hpa90", "hpa95", "slo_cost")]
SLA_GATE, COST_GATE = 3.0, 15.0


def cell_errors(est):
    d = est[(est.target != "hpa70") & ~est.workload.str.contains("L100")]
    return (d.groupby(["family", "workload", "target", "scope", "eps", "n_episodes", "estimator"])
            [["sla_abs_err", "cost_rel_err_pct"]].mean().reset_index())


def main():
    est = pd.read_csv(os.path.join(RES, "raw", "m2_estimates.csv.gz"))
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)
    ce = cell_errors(est)
    n200 = ce[ce.n_episodes == 200]

    summ = (n200.groupby(["scope", "estimator", "eps"])
            .agg(sla_median=("sla_abs_err", "median"), sla_max=("sla_abs_err", "max"),
                 cost_rel_median=("cost_rel_err_pct", "median"), cost_rel_max=("cost_rel_err_pct", "max"),
                 cells=("sla_abs_err", "size")).reset_index())
    summ["estimator"] = pd.Categorical(summ.estimator, ESTIMATORS, ordered=True)
    summ = summ.sort_values(["scope", "estimator", "eps"])
    summ.to_csv(os.path.join(RES, "m2_summary.csv"), index=False)
    print("== main cells, n=200: median and max error over 32 cells (4 workloads x 8 targets) ==")
    for scope in ("all", "high_load"):
        print(f"-- scope {scope}")
        print(summ[summ.scope == scope].drop(columns="scope").round(2).to_string(index=False))

    hard = n200[n200.apply(lambda r: (r.family, r.workload, r.target) in HARD, axis=1)]
    hard_t = hard.pivot_table(index=["target", "scope", "eps"], columns="estimator",
                              values=["sla_abs_err", "cost_rel_err_pct"])
    hard.to_csv(os.path.join(RES, "m2_hard_cells.csv"), index=False)
    print("\n== hard cells (Bitbrains io-bound), n=200, |SLA err| (points) ==")
    print(hard_t["sla_abs_err"][ESTIMATORS].round(1).to_string())
    print("\n== hard cells, cost relative error (%) ==")
    print(hard_t["cost_rel_err_pct"][ESTIMATORS].round(1).to_string())

    gate = []
    for (scope, e, eps), g in n200.groupby(["scope", "estimator", "eps"]):
        bad = g[(g.sla_abs_err > SLA_GATE) | (g.cost_rel_err_pct > COST_GATE)]
        gate.append(dict(scope=scope, estimator=e, eps=eps, cells=len(g), cells_outside_gate=len(bad),
                         all_within=len(bad) == 0,
                         outside=("; ".join(f"{r.family}/{r.workload}/{r.target} "
                                            f"sla {r.sla_abs_err:.1f} cost {r.cost_rel_err_pct:.1f}%"
                                            for r in bad.itertuples()))))
    gate = pd.DataFrame(gate)
    gate.to_csv(os.path.join(RES, "m2_gate.csv"), index=False)
    print(f"\n== every main cell within {SLA_GATE} SLA points and {COST_GATE}% cost? (n=200) ==")
    g = gate[gate.eps == 0.1]
    print(g[["scope", "estimator", "cells_outside_gate", "all_within"]].to_string(index=False))
    for r in g[g.estimator.isin(["mb_trees", "mb_knee"])].itertuples():
        print(f"  {r.scope} {r.estimator}: {r.outside or 'none outside'}")

    lc = (ce[ce.estimator.isin(["replay", "sntpdis_k4", "mb_trees", "mb_knee"])]
          .groupby(["scope", "estimator", "eps", "n_episodes"])
          .agg(sla_median=("sla_abs_err", "median"), sla_max=("sla_abs_err", "max"),
               cost_rel_median=("cost_rel_err_pct", "median")).reset_index())
    lc.to_csv(os.path.join(RES, "m2_learning_curve.csv"), index=False)
    print("\n== learning curve, scope all: median |SLA err| over main cells ==")
    print(lc[lc.scope == "all"].pivot_table(index=["estimator", "eps"], columns="n_episodes",
                                            values="sla_median").round(2).to_string())

    s = est[(est.target == "hpa70") & (est.n_episodes == 200) & ~est.workload.str.contains("L100")]
    print("\n== sanity target hpa70, n=200, max over main cells of mean |SLA err| ==")
    print(s.groupby(["scope", "estimator", "family", "workload"]).sla_abs_err.mean()
          .groupby(["scope", "estimator"]).max().unstack("scope").round(2).to_string())


if __name__ == "__main__":
    main()
