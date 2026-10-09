"""M6 report: the log-only twin (ope.twin.twin_v2) on a new held-out window (W4), on
logs from two other behaviour policies (W1), and on the repeated W2/W3 truth.
Criteria are fixed in real/PLAN_M6.md before the M6 runs.

  OMP_NUM_THREADS=1 taskset -c 16,18,...,38 nice -n 19 python real/m6_report.py > real/runs/m6_report.md
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from ope.policies import REAL_TARGETS  # noqa: E402
from ope.twin import Twin, interval_v2, twin_v2  # noqa: E402
from m5_report import frames, truth_of  # noqa: E402
from overnight_report import estimate  # noqa: E402
from realog import readiness_delay_steps, to_log, truth  # noqa: E402

BASELINES = ["replay", "sntpdis_k4", "mbcalq_trees", "drmb_k4"]
FLAG_FAR = 0.10                # far_share above this: the estimate is flagged as outside support
TARGETS = [t for t in REAL_TARGETS if t != "hpa70"]


def md(df):
    """Markdown table without the optional tabulate dependency."""
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(f"{v:.3g}" if isinstance(v, float) else str(v) for v in r.values) + " |")
    return "\n".join(out)


def err(est_sla, est_cost, tr):
    return abs(est_sla - tr["sla"]), 100 * abs(est_cost - tr["cost"]) / tr["cost"]


def evaluate(w, log_tags, with_baselines=True, v1=False):
    """Rows per target: twin v2 (and v1) errors, interval hit, far share, baselines."""
    lf_ = frames(log_tags)
    if len(lf_) < len(log_tags):
        return None
    logs = [d for _, d in lf_]
    rps, lf = logs[0].rps_target.values, logs[0].load_frac.values
    tw = twin_v2(logs)
    t1 = Twin(logs) if v1 else None
    base = None
    if with_baselines:
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
                 twin_sla=e["sla"], twin_cost=e["cost"], far_share=e["far_share"],
                 in_pi=bool(slo <= tr["sla"] <= shi and clo <= tr["cost"] <= chi))
        r["twin_sla_err"], r["twin_cost_err"] = err(e["sla"], e["cost"], tr)
        if t1 is not None:
            e1 = t1.estimate(f, rps, lf)
            r["v1_sla_err"], r["v1_cost_err"] = err(e1["sla"], e1["cost"], tr)
        if base is not None:
            for b in BASELINES:
                r[f"{b}_sla_err"], r[f"{b}_cost_err"] = err(base[name][("sla", b)], base[name][("cost", b)], tr)
        rows.append(r)
    return pd.DataFrame(rows)


def summary(df, estimators):
    print("| estimator | median SLA err | max SLA err | median cost err % | within 3 pts & 15% |")
    print("|---|---|---|---|---|")
    for k in estimators:
        if f"{k}_sla_err" not in df:
            continue
        g = ((df[f"{k}_sla_err"] <= 3) & (df[f"{k}_cost_err"] <= 15)).sum()
        print(f"| {k} | {df[f'{k}_sla_err'].median():.1f} | {df[f'{k}_sla_err'].max():.1f} | "
              f"{df[f'{k}_cost_err'].median():.1f} | {g}/{len(df)} |")
    print()


def cells(df, extra=()):
    cols = ["target", "truth_runs", "truth_sla", "twin_sla", "twin_sla_err", "truth_cost", "twin_cost", "twin_cost_err",
            "in_pi", "far_share", *extra]
    print(md(df[[c for c in cols if c in df]]))
    print()


def main():
    print("# M6: log-only twin, new window, other loggers, repeated truth (saul)\n")
    print("Criteria: real/PLAN_M6.md (fixed before the M6 runs).\n")
    all_rows = []

    print("## A. W4 (Azure cpu-bound 4075), held out\n")
    w4 = evaluate("w4", [f"on_w4_log_eps{e}_r{r}" for e in ("0.1", "0") for r in (1, 2)], v1=True)
    if w4 is None:
        print("W4 log runs missing.\n")
    else:
        all_rows.append(w4.assign(test="W4"))
        cells(w4, ("v1_sla_err",))
        summary(w4, ["twin", "v1", *BASELINES])
        best = min(w4[f"{b}_sla_err"].median() for b in BASELINES if b != "replay")
        g = lambda k: int(((w4[f"{k}_sla_err"] <= 3) & (w4[f"{k}_cost_err"] <= 15)).sum())  # noqa: E731
        p1 = w4.twin_sla_err.median() <= 3 and w4.twin_cost_err.median() <= 10
        p2 = w4.twin_sla_err.median() < best and g("twin") > max(g(b) for b in BASELINES)
        p3 = w4.in_pi.mean() >= 0.8
        print(f"- P1 median |SLA err| <= 3 and median cost err <= 10%: {'PASS' if p1 else 'FAIL'}")
        print(f"- P2 beats the best non-replay baseline (median {best:.1f}) on median SLA error and gate count: {'PASS' if p2 else 'FAIL'}")
        print(f"- P3 truth inside the v2 prediction interval in >= 80% of cells: {100 * w4.in_pi.mean():.0f}% -> {'PASS' if p3 else 'FAIL'}\n")

    print("## B. Other behaviour policies on W1 (truth: the two W1 runs per target)\n")
    for lg, util in (("b85", 0.85), ("b50", 0.50)):
        df = evaluate("w1", [f"on_w1_log_{lg}_eps0.1_r{r}" for r in (1, 2)])
        print(f"### logs from dithered HPA-{int(util * 100)} (eps 0.1, 2 runs)\n")
        if df is None:
            print("log runs missing.\n")
            continue
        all_rows.append(df.assign(test=f"W1 logger {lg}"))
        cells(df)
        summary(df, ["twin", *BASELINES])
        flagged = df.far_share > FLAG_FAR
        print(f"- flagged (far share > {FLAG_FAR}): {int(flagged.sum())}/{len(df)} cells; median |SLA err| flagged "
              f"{df.twin_sla_err[flagged].median() if flagged.any() else float('nan'):.1f}, unflagged "
              f"{df.twin_sla_err[~flagged].median() if (~flagged).any() else float('nan'):.1f}")
        if lg == "b85":
            print(f"- L1 median |SLA err| <= 3 from HPA-85 logs: {'PASS' if df.twin_sla_err.median() <= 3 else 'FAIL'}")
        else:
            big = df.twin_sla_err > 5
            print(f"- L2 every cell with |SLA err| > 5 is flagged: {'PASS' if (flagged | ~big).all() else 'FAIL'} "
                  f"({int(big.sum())} such cells)")
        print()

    print("## C. W2 and W3 with two truth runs per target (development for v2)\n")
    for w in ("w2", "w3"):
        df = evaluate(w, [f"on_{w}_log_eps{e}_r{r}" for e in ("0.1", "0") for r in (1, 2)], with_baselines=False, v1=True)
        if df is None:
            continue
        all_rows.append(df.assign(test=f"{w.upper()} repeated truth"))
        print(f"### {w.upper()}\n")
        summary(df, ["twin", "v1"])
        print(f"- v2 interval coverage {100 * df.in_pi.mean():.0f}%\n")

    print("## D. Run-to-run noise of the live system\n")
    pairs = []
    for w in ("w1", "w2", "w3", "w4"):
        for name in TARGETS:
            fr = frames([f"on_{w}_truth_{name}", f"on_{w}_truth_{name}_r2"])
            if len(fr) == 2:
                a, b = (truth(d) for _, d in fr)
                pairs.append(dict(window=w, target=name, sla_r1=a["sla"], sla_r2=b["sla"], d_sla=abs(a["sla"] - b["sla"]),
                                  d_cost_pct=200 * abs(a["cost"] - b["cost"]) / (a["cost"] + b["cost"])))
    if pairs:
        p = pd.DataFrame(pairs)
        print(md(p))
        print(f"\nSD of one run's SLA% (from {len(p)} pairs): {np.sqrt((p.d_sla ** 2).mean() / 2):.2f}; "
              f"of cost: {np.sqrt((p.d_cost_pct ** 2).mean() / 2):.1f}%\n")
    if all_rows:
        pd.concat(all_rows).to_csv(os.path.join(HERE, "runs", "m6_cells.csv"), index=False)
        print("Per-cell table: real/runs/m6_cells.csv.")


if __name__ == "__main__":
    main()
