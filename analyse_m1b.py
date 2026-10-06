"""M1b go/no-go and summary tables from results/m1b_*.csv.

  python analyse_m1b.py   -> results/m1b_go_nogo.csv, printed summary

A cell is family x workload x target (the hpa70 sanity target excluded), at n = 200
logged episodes, errors against the paired truth, averaged over the 5 logging seeds.
It qualifies if replay's error is >= 3 SLA points or >= 15% relative cost error at
some 0 < eps <= 0.1. It passes if, at such an eps, truncated PDIS with some k <= 4 has
at most half of replay's error on that metric; "significant" additionally requires
the bootstrap 95% interval of |err_est| - |err_replay| to lie below 0.

eps = 0 is excluded: without dither the target's deviating actions have no support,
and truncated PDIS then just zeroes the outcome on mismatched steps. That shrinks
the estimate towards 0 and can land near a low-SLA or low-cost target by accident.
"""
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
SLA_GATE, COST_GATE_PCT = 3.0, 15.0
FAMILIES = {"tpdis": ("tpdis_k1", "tpdis_k2", "tpdis_k4"),          # as specified
            "sntpdis": ("sntpdis_k1", "sntpdis_k2", "sntpdis_k4")}  # self-normalised check
MAX_EPS = 0.1


def go_nogo(est: pd.DataFrame, vs: pd.DataFrame, ks) -> pd.DataFrame:
    d = est[(est.n_episodes == 200) & (est.target != "hpa70") & (est.eps > 0) & (est.eps <= MAX_EPS)]
    err = (d.groupby(["family", "workload", "target", "scope", "eps", "estimator"])
           [["sla_abs_err", "cost_rel_err_pct"]].mean().reset_index())
    sign = d[d.estimator == "replay"].assign(
        sla_dir=lambda x: x.sla_truth_paired - x.sla_estimate,
        cost_dir=lambda x: x.cost_truth_paired - x.cost_estimate).groupby(
        ["family", "workload", "target", "scope"])[["sla_dir", "cost_dir"]].mean()
    rows = []
    for (fam, wl, tgt, scope), g in err.groupby(["family", "workload", "target", "scope"]):
        for met, col, gate in (("sla", "sla_abs_err", SLA_GATE), ("cost", "cost_rel_err_pct", COST_GATE_PCT)):
            rep = g[g.estimator == "replay"].set_index("eps")[col]
            qual_eps = rep[rep >= gate].index.tolist()
            best = None
            for e in qual_eps:
                for k in ks:
                    v = g[(g.eps == e) & (g.estimator == k)][col].iloc[0]
                    ratio = v / rep[e]
                    if best is None or ratio < best[2]:
                        best = (e, k, ratio, v, rep[e])
            row = dict(family=fam, workload=wl, target=tgt, scope=scope, metric=met,
                       replay_err_max=float(rep.max()), qualifies=bool(qual_eps),
                       truth_minus_replay=float(sign.loc[(fam, wl, tgt, scope), met + "_dir"]))
            if best:
                e, k, ratio, v, r = best
                ci = vs[(vs.family == fam) & (vs.workload == wl) & (vs.target == tgt) & (vs.scope == scope)
                        & (vs.metric == met) & (vs.eps == e) & (vs.estimator == k)].iloc[0]
                row.update(best_eps=e, best_estimator=k, replay_err=r, est_err=v, err_ratio=ratio,
                           halved=bool(ratio <= 0.5), significant=bool(ratio <= 0.5 and ci.ci_hi < 0),
                           diff_vs_replay=ci.diff_mean,
                           diff_ci_lo=ci.ci_lo, diff_ci_hi=ci.ci_hi, diff_units=ci.units)
            rows.append(row)
    return pd.DataFrame(rows)


def main():
    est = pd.read_csv(os.path.join(RES, "raw", "m1b_estimates.csv.gz"))
    vs = pd.read_csv(os.path.join(RES, "raw", "m1b_vs_replay.csv.gz"))
    truth = pd.read_csv(os.path.join(RES, "m1b_truth.csv"))
    pd.set_option("display.width", 240)
    pd.set_option("display.max_columns", 30)

    u = truth[truth.truth == "unpaired"]
    print("== unpaired truth (2000 episodes): spread across the 8 targets ==")
    print(u[u.target != "hpa70"].groupby(["family", "workload"]).agg(
        sla_min=("sla", "min"), sla_max=("sla", "max"), sla_se=("sla_se", "max"),
        sla_hi_min=("sla_hi", "min"), sla_hi_max=("sla_hi", "max"),
        cost_min=("cost", "min"), cost_max=("cost", "max"), cost_se=("cost_se", "max")).round(3).to_string())

    cols = ["family", "workload", "target", "scope", "metric", "replay_err", "truth_minus_replay",
            "best_estimator", "best_eps", "est_err", "err_ratio", "halved", "significant",
            "diff_vs_replay", "diff_ci_lo", "diff_ci_hi"]
    out = []
    for fam_name, ks in FAMILIES.items():
        gn = go_nogo(est, vs, ks).assign(estimator_family=fam_name)
        out.append(gn)
        q = gn[gn.qualifies]
        print(f"\n== {fam_name}: qualifying cells (replay >= {SLA_GATE} SLA pts or >= {COST_GATE_PCT}% cost, "
              f"0 < eps <= {MAX_EPS}), halved ones ==")
        h = q[q.halved == True]  # noqa: E712
        print(h[cols].round(3).to_string(index=False) if len(h) else "none halved")
        for main_only in (True, False):
            sub = q if not main_only else q[~q.workload.str.contains("L100")]
            label = "main cells (200-step episodes)" if main_only else "including mixed_L100 extra cells"
            print(f"GO/NO-GO {fam_name}, {label}: {len(sub)} qualifying cell-metric-scopes, "
                  f"{int(sub.halved.sum())} halved (k<=4, 0<eps<={MAX_EPS}), "
                  f"{int(sub.significant.sum())} with the 95% CI below 0")
    pd.concat(out).to_csv(os.path.join(RES, "m1b_go_nogo.csv"), index=False)
    fixed_setting(est, vs, pd.concat(out))


def fixed_setting(est, vs, gn):
    """Pre-specified settings (no best-of-9): for each estimator at a fixed eps, over
    the main qualifying cells at that eps. -> results/m1b_fixed_setting.csv"""
    d = est[(est.n_episodes == 200) & (est.target != "hpa70") & ~est.workload.str.contains("L100")]
    err = d.groupby(["family", "workload", "target", "scope", "eps", "estimator"])[
        ["sla_abs_err", "cost_rel_err_pct"]].mean()
    rows = []
    cells = gn[gn.estimator_family == "tpdis"][["family", "workload", "target", "scope", "metric"]]
    for e in ("tpdis_k2", "tpdis_k4", "sntpdis_k2", "sntpdis_k4"):
        for eps in (0.05, 0.1):
            n = better = halved = sig = worse = 0
            for r in cells[~cells.workload.str.contains("L100")].itertuples():
                col, gate = ("sla_abs_err", SLA_GATE) if r.metric == "sla" else ("cost_rel_err_pct", COST_GATE_PCT)
                rep = err.loc[(r.family, r.workload, r.target, r.scope, eps, "replay"), col]
                if rep < gate:
                    continue
                v = err.loc[(r.family, r.workload, r.target, r.scope, eps, e), col]
                ci = vs[(vs.family == r.family) & (vs.workload == r.workload) & (vs.target == r.target)
                        & (vs.scope == r.scope) & (vs.metric == r.metric) & (vs.eps == eps) & (vs.estimator == e)].iloc[0]
                n += 1
                better += v < rep
                halved += v <= 0.5 * rep
                sig += (v <= 0.5 * rep) and ci.ci_hi < 0
                worse += ci.ci_lo > 0
            rows.append(dict(estimator=e, eps=eps, qualifying=n, better_than_replay=better, halved=halved,
                             halved_ci_below_0=sig, significantly_worse=worse))
    fs = pd.DataFrame(rows)
    fs.to_csv(os.path.join(RES, "m1b_fixed_setting.csv"), index=False)
    print("\n== pre-specified settings (main qualifying cells) ==")
    print(fs.to_string(index=False))


if __name__ == "__main__":
    main()
