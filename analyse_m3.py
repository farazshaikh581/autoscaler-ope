"""M3 analysis: hybrids, the agreement switch, and the gate.

  python analyse_m3.py -> results/m3_summary.csv, m3_gate.csv, m3_hard_cells.csv, m3_switch.csv

Switch (decided per log, from the log alone): if the target's action agreement with
the logged actions is >= tau, use the high-agreement estimator (dr_k4; variant:
sntpdis_k4), else mb_trees. tau is chosen on the Azure main cells only (eps = 0.1,
all steps): fewest cells outside the gate, ties broken by the smaller max SLA error.
It is then applied unchanged to Bitbrains, which is the out-of-sample evaluation.
"""
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
SLA_GATE, COST_GATE, EPS_GATE = 3.0, 15.0, 0.1
ESTIMATORS = ["replay", "sntpdis_k4", "mb_trees", "mbcal_trees", "mbcalq_trees", "dr_k4", "dr_k8",
              "drmb_k2", "drmb_k4", "drmb_k8", "switch_dr", "switch_sn", "mb_knee", "mbcalq_knee"]
HARD = [("bitbrains", "io-bound", t) for t in ("hpa90", "hpa95", "slo_cost")]
SWITCHES = {"switch_dr": "dr_k4", "switch_sn": "sntpdis_k4"}
TAUS = np.round(np.arange(0.50, 1.0001, 0.01), 2)


def add_switch(est, name, high, tau):
    hi = est[est.estimator == high].set_index(["family", "workload", "target", "eps", "rep", "scope"])
    lo = est[est.estimator == "mb_trees"].set_index(["family", "workload", "target", "eps", "rep", "scope"])
    use_hi = hi.agreement >= tau
    sw = lo.copy()
    sw.loc[use_hi[use_hi].index] = hi.loc[use_hi[use_hi].index]
    sw = sw.reset_index().assign(estimator=name, switch_tau=tau, switch_used=np.where(
        use_hi.reindex(lo.index).values, high, "mb_trees"))
    return sw


def cell_errors(est):
    d = est[(est.target != "hpa70") & ~est.workload.str.contains("L100")]
    return (d.groupby(["family", "workload", "target", "scope", "eps", "estimator"])
            [["sla_abs_err", "cost_rel_err_pct", "agreement"]].mean().reset_index())


def outside(g):
    return g[(g.sla_abs_err > SLA_GATE) | (g.cost_rel_err_pct > COST_GATE)]


def choose_tau(est, high):
    az = est[(est.family == "azure") & (est.eps == EPS_GATE) & (est.scope == "all")]
    scores = []
    for tau in TAUS:
        ce = cell_errors(add_switch(az, "sw", high, tau))
        scores.append((len(outside(ce)), ce.sla_abs_err.max(), tau))
    best = min(scores)
    return best[2], pd.DataFrame(scores, columns=["azure_cells_outside", "azure_sla_max", "tau"])


def switch_sensitivity(est):
    """Azure does not pin tau down; for every tau, count gate failures on Azure and on
    Bitbrains (eps = 0.1, all steps). -> results/m3_switch_sensitivity.csv"""
    rows = []
    for name, high in SWITCHES.items():
        for tau in TAUS:
            for fam in ("azure", "bitbrains"):
                part = est[(est.family == fam) & (est.eps == EPS_GATE) & (est.scope == "all")]
                ce = cell_errors(add_switch(part, name, high, tau))
                rows.append(dict(switch=name, tau=tau, family=fam, cells_outside=len(outside(ce)),
                                 sla_max=ce.sla_abs_err.max()))
    sens = pd.DataFrame(rows)
    sens.to_csv(os.path.join(RES, "m3_switch_sensitivity.csv"), index=False)
    for name in SWITCHES:
        w = sens[sens.switch == name].pivot_table(index="tau", columns="family", values="cells_outside")
        ok_az = w[w.azure == 0]
        print(f"{name}: tau with 0 Azure failures: {ok_az.index.min():.2f}-{ok_az.index.max():.2f} "
              f"({len(ok_az)} values); of these, Bitbrains passes for "
              f"{int((ok_az.bitbrains == 0).sum())} (tau {ok_az[ok_az.bitbrains == 0].index.min():.2f}-"
              f"{ok_az[ok_az.bitbrains == 0].index.max():.2f})")


def main():
    est = pd.read_csv(os.path.join(RES, "raw", "m3_estimates.csv.gz"))
    pd.set_option("display.width", 240)
    pd.set_option("display.max_columns", 30)
    sw_rows, sw_log = [], []
    for name, high in SWITCHES.items():
        tau, scores = choose_tau(est, high)
        sw_log.append(scores.assign(switch=name))
        sw_rows.append(add_switch(est, name, high, tau))
        print(f"{name}: tau chosen on Azure = {tau:.2f} "
              f"(Azure cells outside gate {scores[scores.tau == tau].azure_cells_outside.iloc[0]})")
    pd.concat(sw_log).to_csv(os.path.join(RES, "m3_switch.csv"), index=False)
    switch_sensitivity(est)
    allest = pd.concat([est] + sw_rows, ignore_index=True)
    ce = cell_errors(allest)

    summ = (ce.groupby(["scope", "estimator", "eps"])
            .agg(sla_median=("sla_abs_err", "median"), sla_max=("sla_abs_err", "max"),
                 cost_rel_median=("cost_rel_err_pct", "median"), cost_rel_max=("cost_rel_err_pct", "max"),
                 cells=("sla_abs_err", "size")).reset_index())
    summ = summ[summ.estimator.isin(ESTIMATORS)]
    summ["estimator"] = pd.Categorical(summ.estimator, ESTIMATORS, ordered=True)
    summ = summ.sort_values(["scope", "estimator", "eps"])
    summ.to_csv(os.path.join(RES, "m3_summary.csv"), index=False)
    for scope in ("all", "high_load"):
        print(f"\n== main cells (32), eps={EPS_GATE}, scope {scope}: median / max ==")
        print(summ[(summ.scope == scope) & (summ.eps == EPS_GATE)].drop(columns=["scope", "eps"])
              .round(2).to_string(index=False))

    gate = []
    for (scope, e, eps), g in ce.groupby(["scope", "estimator", "eps"]):
        if e not in ESTIMATORS:
            continue
        for fam_scope, gg in (("all main cells", g), ("bitbrains only", g[g.family == "bitbrains"])):
            bad = outside(gg)
            gate.append(dict(scope=scope, estimator=e, eps=eps, cells_evaluated=fam_scope, cells=len(gg),
                             cells_outside_gate=len(bad), all_within=len(bad) == 0,
                             outside="; ".join(f"{r.family}/{r.workload}/{r.target} sla {r.sla_abs_err:.1f} "
                                               f"cost {r.cost_rel_err_pct:.1f}%" for r in bad.itertuples())))
    gate = pd.DataFrame(gate)
    gate.to_csv(os.path.join(RES, "m3_gate.csv"), index=False)
    print(f"\n== gate at eps={EPS_GATE}: cells outside (3 SLA pts / 15% cost) ==")
    gt = gate[gate.eps == EPS_GATE].pivot_table(index="estimator", columns=["scope", "cells_evaluated"],
                                                 values="cells_outside_gate")
    print(gt.reindex(ESTIMATORS).to_string())
    for r in gate[(gate.eps == EPS_GATE) & (gate.cells_evaluated == "all main cells")
                  & gate.estimator.isin(["drmb_k4", "mbcalq_trees", "switch_dr", "switch_sn"])].itertuples():
        print(f"  {r.scope:9s} {r.estimator:13s}: {r.outside or 'none outside'}")

    hard = ce[ce.apply(lambda r: (r.family, r.workload, r.target) in HARD, axis=1)]
    hard.to_csv(os.path.join(RES, "m3_hard_cells.csv"), index=False)
    print(f"\n== hard cells (Bitbrains io-bound), eps={EPS_GATE}: |SLA err| / cost rel err % ==")
    h = hard[(hard.eps == EPS_GATE)]
    print(h.pivot_table(index=["target", "scope"], columns="estimator", values="sla_abs_err")
          .reindex(columns=ESTIMATORS).round(1).to_string())
    print(h.pivot_table(index=["target", "scope"], columns="estimator", values="cost_rel_err_pct")
          .reindex(columns=ESTIMATORS).round(1).to_string())

    s = allest[(allest.target == "hpa70") & ~allest.workload.str.contains("L100") & (allest.eps == EPS_GATE)]
    print(f"\n== sanity hpa70, eps={EPS_GATE}: max over main cells of mean |SLA err| ==")
    san = (s.groupby(["scope", "estimator", "family", "workload"]).sla_abs_err.mean()
           .groupby(["scope", "estimator"]).max().reset_index(name="sla_err_max_over_main_cells"))
    san.to_csv(os.path.join(RES, "m3_sanity.csv"), index=False)
    print(s.groupby(["scope", "estimator", "family", "workload"]).sla_abs_err.mean()
          .groupby(["scope", "estimator"]).max().unstack("scope").reindex(ESTIMATORS).round(2).to_string())
    ag = ce[(ce.eps == EPS_GATE) & (ce.scope == "all") & (ce.estimator == "replay")]
    print("\n== action agreement with the logged actions, eps=0.1 (mean over reps) ==")
    print(ag.pivot_table(index="target", columns=["family", "workload"], values="agreement").round(2).to_string())


if __name__ == "__main__":
    main()
