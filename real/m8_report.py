"""M8 report: a second pre-registered held-out window (W5) for twin v2, the queueing-model
baseline, a second truth run on W4, and bootstrap intervals. Criteria are fixed in
real/PLAN_M8.md before the M8 runs.

  OMP_NUM_THREADS=1 taskset -c 16,18,...,38 nice -n 19 python real/m8_report.py > real/runs/m8_report.md
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from ope.policies import REAL_TARGETS  # noqa: E402
from ope.queue_baseline import QueueModel  # noqa: E402
from ope.twin import interval_v2, twin_v2  # noqa: E402
from m5_report import frames, truth_of  # noqa: E402
from m6_report import md  # noqa: E402
from overnight_report import estimate  # noqa: E402
from realog import readiness_delay_steps, to_log  # noqa: E402

BASELINES = ["replay", "sntpdis_k4", "mbcalq_trees", "drmb_k4", "queue"]
TARGETS = [t for t in REAL_TARGETS if t != "hpa70"]
N_BOOT, SEED = 10000, 2027


def err(est_sla, est_cost, tr):
    return abs(est_sla - tr["sla"]), 100 * abs(est_cost - tr["cost"]) / tr["cost"]


def evaluate(w):
    lf_ = frames([f"on_{w}_log_eps{e}_r{r}" for e in ("0.1", "0") for r in (1, 2)])
    if len(lf_) < 4:
        return None
    logs = [d for _, d in lf_]
    rps, lf = logs[0].rps_target.values, logs[0].load_frac.values
    tw, q = twin_v2(logs), QueueModel(logs)
    base = estimate(to_log(logs), readiness_delay_steps(logs)[0])
    rows = []
    for name in TARGETS:
        tr = truth_of(w, name)
        if tr is None:
            continue
        f = REAL_TARGETS[name]
        e = tw.estimate(f, rps, lf)
        (slo, shi), (clo, chi) = interval_v2(e)
        r = dict(window=w, target=name, truth_runs=len(tr["runs"]), truth_sla=tr["sla"], truth_cost=tr["cost"],
                 twin_sla=e["sla"], twin_cost=e["cost"],
                 in_pi=bool(slo <= tr["sla"] <= shi and clo <= tr["cost"] <= chi))
        r["twin_sla_err"], r["twin_cost_err"] = err(e["sla"], e["cost"], tr)
        for b in BASELINES[:-1]:
            r[f"{b}_sla"] = base[name][("sla", b)]
            r[f"{b}_sla_err"], r[f"{b}_cost_err"] = err(base[name][("sla", b)], base[name][("cost", b)], tr)
        eq = q.estimate(f, rps, lf)
        r["queue_sla"] = eq["sla"]
        r["queue_sla_err"], r["queue_cost_err"] = err(eq["sla"], eq["cost"], tr)
        rows.append(r)
    return pd.DataFrame(rows)


def gate(df, k):
    return int(((df[f"{k}_sla_err"] <= 3) & (df[f"{k}_cost_err"] <= 15)).sum())


def summary(df):
    print("| estimator | median SLA err | max SLA err | median cost err % | within 3 pts & 15% |")
    print("|---|---|---|---|---|")
    for k in ["twin", *BASELINES]:
        print(f"| {k} | {df[f'{k}_sla_err'].median():.1f} | {df[f'{k}_sla_err'].max():.1f} | "
              f"{df[f'{k}_cost_err'].median():.1f} | {gate(df, k)}/{len(df)} |")
    print()


def boot(df):
    """Percentile bootstrap over cells: median |SLA error| per estimator, and the paired
    difference (baseline - twin) of medians."""
    rng = np.random.default_rng(SEED)
    n = len(df)
    idx = rng.integers(0, n, size=(N_BOOT, n))
    tw = df["twin_sla_err"].values
    out = {}
    for k in ["twin", *BASELINES]:
        v = df[f"{k}_sla_err"].values
        med = np.median(v[idx], axis=1)
        diff = np.median(v[idx], axis=1) - np.median(tw[idx], axis=1)
        out[k] = (np.median(v), *np.percentile(med, [2.5, 97.5]), *np.percentile(diff, [2.5, 97.5]))
    return out


def main():
    print("# M8: second pre-registered held-out window, queueing baseline, W4 repeat (saul)\n")
    print("Criteria: real/PLAN_M8.md (fixed before the M8 runs).\n")
    print("## A. W5 (Bitbrains io-bound 6150), held out\n")
    w5 = evaluate("w5")
    if w5 is None:
        print("W5 log runs missing.\n")
    else:
        print(md(w5[["target", "truth_runs", "truth_sla", "twin_sla", "twin_sla_err", "truth_cost", "twin_cost",
                     "twin_cost_err", "in_pi", "queue_sla", "queue_sla_err"]]))
        print()
        summary(w5)
        q1 = w5.twin_sla_err.median() <= 3 and w5.twin_cost_err.median() <= 10
        q2 = all(w5.twin_sla_err.median() < w5[f"{b}_sla_err"].median() for b in BASELINES) and \
            gate(w5, "twin") > max(gate(w5, b) for b in BASELINES)
        q3 = w5.in_pi.mean() >= 0.8
        print(f"- Q1 median |SLA err| <= 3 and median cost err <= 10%: {'PASS' if q1 else 'FAIL'}")
        print(f"- Q2 beats every baseline (incl. the queueing model) on median SLA error and gate count: {'PASS' if q2 else 'FAIL'}")
        print(f"- Q3 truth inside the v2 interval in >= 80% of cells: {100 * w5.in_pi.mean():.0f}% -> {'PASS' if q3 else 'FAIL'}\n")

    print("## B. W4 with two truth runs per target\n")
    w4 = evaluate("w4")
    summary(w4)
    print(f"- v2 interval coverage {100 * w4.in_pi.mean():.0f}%\n")

    if w5 is not None:
        pool = pd.concat([w4, w5])
        print(f"## C. Pooled pre-registered held-out cells (W4 + W5, {len(pool)} cells), bootstrap\n")
        b = boot(pool)
        print("| estimator | median SLA err | 95% CI | baseline - twin, 95% CI |")
        print("|---|---|---|---|")
        for k, (m, lo, hi, dlo, dhi) in b.items():
            print(f"| {k} | {m:.1f} | [{lo:.1f}, {hi:.1f}] | " + ("-" if k == "twin" else f"[{dlo:.1f}, {dhi:.1f}]") + " |")
        q4 = all(b[k][3] > 0 for k in BASELINES)
        print(f"\n- Q4 for every baseline, the 95% CI of (baseline - twin) median error is above 0: {'PASS' if q4 else 'FAIL'}\n")
        pool.to_csv(os.path.join(HERE, "runs", "m8_cells.csv"), index=False)
        print("Per-cell table: real/runs/m8_cells.csv.")


if __name__ == "__main__":
    main()
