"""M6 development: twin ablations and variants on all cells with live truth (W1-W3).

W2/W3 were the M5 held-out windows; after M5 they are development data too, so
anything chosen here is tested on M6's new window (W4) only.

  OMP_NUM_THREADS=1 taskset -c 16,18,20,22 nice -n 19 python real/m6_dev.py > real/runs/m6_dev.md
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from ope.policies import REAL_TARGETS  # noqa: E402
from ope.twin import Twin, demand  # noqa: E402
from m5_report import frames, truth_of  # noqa: E402

WINDOWS = ("w1", "w2", "w3")
ONLY = sys.argv[1].split(",") if len(sys.argv) > 1 else []
SLA_NOISE_SD = 2.7            # run-to-run SD of one live run's SLA% (M5 repeat runs)
COST_NOISE_SD = 0.03          # relative run-to-run SD of cost (M5 repeat runs: 0-6%)


def log_only_scale(all_logs, cpu_req=200):
    """CPU per rps and the linear-regime bound from the logs alone (no knee check)."""
    d = pd.concat(all_logs)
    ok = d[(d.latency_mean_ms < 10) & d.cpu_used_m.notna()]
    m = ok.cpu_used_m.sum() / ok.rps_achieved.sum()
    D = demand(d.rps_achieved.values, d.ready_replicas.values, cpu_req, m)
    # linear regime: below the first demand decile-bin whose SLA rate drops under 95%
    edges = np.quantile(D, np.linspace(0, 1, 21))
    for lo, hi in zip(edges[:-1], edges[1:]):
        sel = (D >= lo) & (D < hi)
        if sel.any() and d.sla_ok.values[sel].mean() < 0.95:
            return m, float(lo)
    return m, float(edges[-1])


def variants(all_logs):
    m, lb = log_only_scale(all_logs)
    return {
        "M5 twin": dict(),
        "no lag": dict(use_lag=False),
        "no change flag": dict(use_chg=False),
        "no rescale": dict(rescale=False),
        "K=5": dict(k=5),
        "K=20": dict(k=20),
        "log-only scale": dict(m_per_rps=m, linear_below=lb, _info=f"m={m:.2f}, lin<{lb:.2f}"),
        "log-only no-chg": dict(m_per_rps=m, linear_below=lb, use_chg=False),
    }


def main():
    rows = []
    for w in WINDOWS:
        logs = {e: [d for _, d in frames([f"on_{w}_log_eps{e}_r{r}" for r in (1, 2)])] for e in ("0.1", "0")}
        all_logs = logs["0.1"] + logs["0"]
        rps, lf = all_logs[0].rps_target.values, all_logs[0].load_frac.values
        donor_sets = {"all 4 logs": all_logs, "eps 0 only": logs["0"], "eps 0.1 only": logs["0.1"],
                      "1 log (eps 0 r1)": logs["0"][:1]}
        for name, f in REAL_TARGETS.items():
            if name == "hpa70":
                continue
            tr = truth_of(w, name)
            if tr is None:
                continue
            cfgs = [(v, "all 4 logs", kw) for v, kw in variants(all_logs).items()] + \
                   [("M5 twin", ds, {}) for ds in donor_sets if ds != "all 4 logs"]
            if ONLY:
                cfgs = [c for c in cfgs if c[0] in ONLY and c[1] == "all 4 logs"]
            for v, ds, kw in cfgs:
                kw = dict(kw)
                info = kw.pop("_info", "")
                if info and name == "hpa30":
                    print(f"{w}: {v} {info}", file=sys.stderr, flush=True)
                est = Twin(donor_sets[ds], **kw).estimate(f, rps, lf, n=40)
                lo, hi = est["sla_si"]
                z = 1.645 * SLA_NOISE_SD
                clo, chi = est["cost_si"]
                cz = 1.645 * COST_NOISE_SD
                rows.append(dict(window=w, target=name, variant=v, donors=ds, n_truth=len(tr["runs"]),
                                 sla_err=abs(est["sla"] - tr["sla"]), cost_err=100 * abs(est["cost"] - tr["cost"]) / tr["cost"],
                                 in_si=(lo - 0.5 <= tr["sla"] <= hi + 0.5) and (clo * 0.98 <= tr["cost"] <= chi * 1.02),
                                 in_si_noise=(lo - z <= tr["sla"] <= hi + z) and (clo * (1 - cz) <= tr["cost"] <= chi * (1 + cz))))
            print(f"{w} {name} done", file=sys.stderr, flush=True)
    r = pd.DataFrame(rows)
    r.to_csv(os.path.join(HERE, "runs", "m6_dev_cells" + ("_" + "_".join(x.split()[0] for x in ONLY) if ONLY else "") + ".csv"), index=False)
    print("# M6 development: twin variants on W1-W3 (24 cells, hpa70 excluded)\n")
    print("| variant | donors | median SLA err | max SLA err | median cost err % | within 3 pts & 15% | in sens. interval | in interval + run noise |")
    print("|---|---|---|---|---|---|---|---|")
    for (v, ds), g in r.groupby(["variant", "donors"], sort=False):
        print(f"| {v} | {ds} | {g.sla_err.median():.1f} | {g.sla_err.max():.1f} | {g.cost_err.median():.1f} | "
              f"{int(((g.sla_err <= 3) & (g.cost_err <= 15)).sum())}/{len(g)} | {100 * g.in_si.mean():.0f}% | {100 * g.in_si_noise.mean():.0f}% |")


if __name__ == "__main__":
    main()
