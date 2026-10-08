"""M5 report: the demand-space twin against replay and the M3 estimators on live
truth, with the criteria fixed in real/PLAN_M5.md before the M5 runs.

  OMP_NUM_THREADS=1 taskset -c 16,18,...,38 nice -n 19 python real/m5_report.py > real/runs/m5_report.md

W1 is the development window (the twin was built while looking at its truth runs);
W2 and W3 are held out. hpa70 is the behaviour's own controller and its truth is
the eps = 0 log runs, which are also twin donors, so it is a sanity row only.
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from ope.policies import REAL_TARGETS  # noqa: E402
from ope.twin import Twin  # noqa: E402
from overnight_report import estimate  # noqa: E402
from realog import load_run, readiness_delay_steps, to_log, truth  # noqa: E402

WINDOWS = {"w1": "bitbrains io-bound 4725 (development)", "w2": "azure cpu-bound 1200 (held out)",
           "w3": "bitbrains cpu-bound 950 (held out)"}
HELD_OUT = ("w2", "w3")
SLA_GATE, COST_GATE = 3.0, 15.0
BASELINES = ["replay", "sntpdis_k4", "mbcalq_trees", "drmb_k4"]


def frames(tags):
    out = []
    for t in tags:
        r = load_run(t)
        if r is not None and len(r[0]) >= 100:
            out.append((t, r[0]))
    return out


def truth_of(w, name):
    tags = ([f"on_{w}_log_eps0_r1", f"on_{w}_log_eps0_r2"] if name == "hpa70"
            else [f"on_{w}_truth_{name}", f"on_{w}_truth_{name}_r2"])
    fr = frames(tags)
    if not fr:
        return None
    v = [truth(d) for _, d in fr]
    return dict(sla=np.mean([x["sla"] for x in v]), cost=np.mean([x["cost"] for x in v]),
                runs=[t for t, _ in fr], sla_runs=[x["sla"] for x in v])


def main():
    print("# M5: demand-space twin vs live truth (saul)\n")
    print("Criteria are in real/PLAN_M5.md (fixed before the M5 runs). W1 = development, W2/W3 = held out.\n")
    cells = []
    for w, desc in WINDOWS.items():
        logs = {e: frames([f"on_{w}_log_eps{e}_r{r}" for r in (1, 2)]) for e in ("0.1", "0")}
        if not all(logs.values()):
            print(f"## {w.upper()}: {desc}\n\nlog runs missing, skipped.\n")
            continue
        all_logs = [d for e in logs for _, d in logs[e]]
        ref = all_logs[0]
        rps, lf = ref.rps_target.values, ref.load_frac.values
        twin = Twin(all_logs)
        base = {}
        for e, fr in logs.items():
            ds = [d for _, d in fr]
            base[e] = estimate(to_log(ds), readiness_delay_steps(ds)[0])
        print(f"## {w.upper()}: {desc}\n")
        print("| target | truth runs | truth SLA% | twin SLA% [90% PI] [sens.] | " + " | ".join(f"{b} SLA err (eps .1/0)" for b in BASELINES)
              + " | truth cost | twin cost [90% PI] | " + " | ".join(f"{b} cost err % (.1/0)" for b in BASELINES) + " |")
        print("|---" * (6 + 2 * len(BASELINES)) + "|")
        for name, f in REAL_TARGETS.items():
            tr = truth_of(w, name)
            est = twin.estimate(f, rps, lf)
            if tr is None:
                print(f"| {name} | not run | | {est['sla']:.1f} | " + " | " * len(BASELINES) + f" | {est['cost']:.3f} |" + " |" * len(BASELINES))
                continue
            be = {(b, e): (abs(base[e][name][("sla", b)] - tr["sla"]),
                           100 * abs(base[e][name][("cost", b)] - tr["cost"]) / tr["cost"]) for b in BASELINES for e in base}
            te = (abs(est["sla"] - tr["sla"]), 100 * abs(est["cost"] - tr["cost"]) / tr["cost"])
            in_si = est["sla_si"][0] - 0.5 <= tr["sla"] <= est["sla_si"][1] + 0.5 and \
                est["cost_si"][0] * 0.98 <= tr["cost"] <= est["cost_si"][1] * 1.02
            cells.append(dict(window=w, target=name, twin_sla=te[0], twin_cost=te[1], in_si=in_si,
                              **{f"{b}_{e}_sla": be[(b, e)][0] for b, e in be}, **{f"{b}_{e}_cost": be[(b, e)][1] for b, e in be}))
            print(f"| {name} | {len(tr['runs'])} | {tr['sla']:.1f}{' ' + str([round(x, 1) for x in tr['sla_runs']]) if len(tr['runs']) > 1 else ''} | "
                  f"{est['sla']:.1f} [{est['sla_pi'][0]:.0f}, {est['sla_pi'][1]:.0f}] [{est['sla_si'][0]:.0f}, {est['sla_si'][1]:.0f}] | "
                  + " | ".join(f"{be[(b, '0.1')][0]:.1f} / {be[(b, '0')][0]:.1f}" for b in BASELINES)
                  + f" | {tr['cost']:.3f} | {est['cost']:.3f} [{est['cost_pi'][0]:.2f}, {est['cost_pi'][1]:.2f}] | "
                  + " | ".join(f"{be[(b, '0.1')][1]:.0f} / {be[(b, '0')][1]:.0f}" for b in BASELINES) + " |")
        print()
    if not cells:
        return
    c = pd.DataFrame(cells)
    c.to_csv(os.path.join(HERE, "runs", "m5_cells.csv"), index=False)
    print("## Criteria (real/PLAN_M5.md)\n")
    for scope, sub in (("held out (W2, W3), hpa70 excluded", c[c.window.isin(HELD_OUT) & (c.target != "hpa70")]),
                       ("development (W1), hpa70 excluded", c[(c.window == "w1") & (c.target != "hpa70")])):
        if sub.empty:
            print(f"- {scope}: no cells yet\n")
            continue
        n = len(sub)
        within = lambda s, k: int(((s[f"{k}_sla"] <= SLA_GATE) & (s[f"{k}_cost"] <= COST_GATE)).sum())  # noqa: E731
        print(f"**{scope}: {n} cells**\n")
        print("| estimator | median SLA err | max SLA err | median cost err % | within 3 pts & 15% |")
        print("|---|---|---|---|---|")
        print(f"| twin | {sub.twin_sla.median():.1f} | {sub.twin_sla.max():.1f} | {sub.twin_cost.median():.1f} | {within(sub, 'twin')}/{n} |")
        for b in BASELINES:
            for e in ("0.1", "0"):
                k = f"{b}_{e}"
                print(f"| {b} eps {e} | {sub[k + '_sla'].median():.1f} | {sub[k + '_sla'].max():.1f} | "
                      f"{sub[k + '_cost'].median():.1f} | {within(sub, k)}/{n} |")
        best = min((sub[f"{b}_{e}_sla"].median(), f"{b} eps {e}") for b in BASELINES if b != "replay" for e in ("0.1", "0"))
        p1 = sub.twin_sla.median() <= 3 and sub.twin_cost.median() <= 10
        p2 = sub.twin_sla.median() < best[0] and within(sub, "twin") > max(within(sub, f"{b}_{e}") for b in BASELINES for e in ("0.1", "0"))
        p3 = sub.in_si.mean() >= 0.8
        print(f"\n- P1 median |SLA err| <= 3 and median cost err <= 10%: {'PASS' if p1 else 'FAIL'}")
        print(f"- P2 twin beats the best baseline ({best[1]}, median {best[0]:.1f}) on median SLA error and on the gate count: {'PASS' if p2 else 'FAIL'}")
        print(f"- P3 truth inside the twin's sensitivity interval in >= 80% of cells: {100 * sub.in_si.mean():.0f}% -> {'PASS' if p3 else 'FAIL'}\n")
    print("Per-cell table: real/runs/m5_cells.csv.")


if __name__ == "__main__":
    main()
