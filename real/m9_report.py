"""M9 report: the second application (api-service), twin v2 and the baselines frozen.
Criteria are fixed in real/PLAN_M9.md before the M9 runs.

  OMP_NUM_THREADS=1 taskset -c 16,18,...,38 nice -n 19 python real/m9_report.py > real/runs/m9_report.md
"""
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from ope.twin import log_scale  # noqa: E402
from m5_report import frames  # noqa: E402
from m6_report import md  # noqa: E402
from m8_report import BASELINES, boot, evaluate, gate, summary  # noqa: E402

WINDOWS = {"api_w1": ("w1", "Bitbrains io-bound 4725"), "api_w4": ("w4", "Azure cpu-bound 4075")}


def criteria(df):
    q1 = df.twin_sla_err.median() <= 3 and df.twin_cost_err.median() <= 10
    q2 = all(df.twin_sla_err.median() < df[f"{b}_sla_err"].median() for b in BASELINES) and \
        gate(df, "twin") > max(gate(df, b) for b in BASELINES)
    q3 = df.in_pi.mean() >= 0.8
    print(f"- Q1 median |SLA err| <= 3 and median cost err <= 10%: {'PASS' if q1 else 'FAIL'}")
    print(f"- Q2 beats every baseline (incl. the queueing model) on median SLA error and gate count: {'PASS' if q2 else 'FAIL'}")
    print(f"- Q3 truth inside the v2 interval in >= 80% of cells: {100 * df.in_pi.mean():.0f}% -> {'PASS' if q3 else 'FAIL'}\n")


def main():
    print("# M9: a second application, api-service (saul)\n")
    print("Criteria: real/PLAN_M9.md (fixed before the M9 runs). Estimators frozen.\n")
    got, replay = [], []
    for i, (w, (web_w, desc)) in enumerate(WINDOWS.items()):
        print(f"## {'AB'[i]}. {w}: {desc}\n")
        df = evaluate(w)
        if df is None or df.empty:
            print("log or truth runs missing.\n")
            continue
        logs = [d for _, d in frames([f"on_{w}_log_eps{e}_r{r}" for e in ("0.1", "0") for r in (1, 2)])]
        m, lb = log_scale(logs)
        print(f"From the logs: CPU per rps {m:.3f} mcores, linear-regime bound D < {lb:.2f}.\n")
        print(md(df[["target", "truth_sla", "twin_sla", "twin_sla_err", "truth_cost", "twin_cost", "twin_cost_err",
                     "in_pi", "replay_sla", "replay_sla_err", "queue_sla", "queue_sla_err"]]))
        print()
        summary(df)
        criteria(df)
        got.append(df)
        web = evaluate(web_w)
        if web is not None:
            replay.append((w, df.replay_sla_err.median(), df.replay_sla_err.max(),
                           web.replay_sla_err.median(), web.replay_sla_err.max()))
    if replay:
        print("## Replay on both applications (not gated)\n")
        print("| window | api-service median | api-service max | web-service median | web-service max |")
        print("|---|---|---|---|---|")
        for w, a, b, c, d in replay:
            print(f"| {w} | {a:.1f} | {b:.1f} | {c:.1f} | {d:.1f} |")
        print()
    if len(got) == 2:
        pool = pd.concat(got)
        print(f"## C. Pooled ({len(pool)} cells), bootstrap\n")
        b = boot(pool)
        print("| estimator | median SLA err | 95% CI | baseline - twin, 95% CI |")
        print("|---|---|---|---|")
        for k, (med, lo, hi, dlo, dhi) in b.items():
            print(f"| {k} | {med:.1f} | [{lo:.1f}, {hi:.1f}] | " + ("-" if k == "twin" else f"[{dlo:.1f}, {dhi:.1f}]") + " |")
        q4 = all(b[k][3] > 0 for k in BASELINES)
        print(f"\n- Q4 for every baseline, the 95% CI of (baseline - twin) median error is above 0: {'PASS' if q4 else 'FAIL'}\n")
        pool.to_csv(os.path.join(HERE, "runs", "m9_cells.csv"), index=False)
        print("Per-cell table: real/runs/m9_cells.csv.")


if __name__ == "__main__":
    main()
