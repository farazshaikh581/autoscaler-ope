"""M7 report: does the knee-share flag (ope.twin, FLAG_KNEE) catch the twin's large
errors when the logs come from other behaviour policies, on windows W3 and W4?
Criteria are fixed in real/PLAN_M7.md before the M7 runs.

  OMP_NUM_THREADS=1 taskset -c 16,18,...,38 nice -n 19 python real/m7_report.py > real/runs/m7_report.md
"""
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from ope.twin import FLAG_KNEE  # noqa: E402
from m6_report import BASELINES, evaluate, md, summary  # noqa: E402

BIG = 6.0                      # |SLA error| above 2.5 x the run-to-run SD (2.39)


def main():
    print("# M7: knee-share flag on new loggers (W3, W4)\n")
    print(f"Criteria: real/PLAN_M7.md. Flag: knee_share > {FLAG_KNEE}; large error: |SLA err| > {BIG}.\n")
    parts = []
    for w in ("w3", "w4"):
        for lg, util in (("b85", 85), ("b50", 50)):
            df = evaluate(w, [f"on_{w}_log_{lg}_eps0.1_r{r}" for r in (1, 2)])
            print(f"## {w.upper()}, logs from dithered HPA-{util} (eps 0.1, 2 runs)\n")
            if df is None:
                print("log runs missing.\n")
                continue
            df["flagged"] = df.knee_share > FLAG_KNEE
            parts.append(df.assign(logger=lg))
            print(md(df[["target", "truth_runs", "truth_sla", "twin_sla", "twin_sla_err", "twin_cost_err",
                         "knee_share", "far_share", "flagged"]]))
            print()
            summary(df, ["twin", *BASELINES])
    if not parts:
        return
    a = pd.concat(parts)
    a.to_csv(os.path.join(HERE, "runs", "m7_cells.csv"), index=False)
    big, fl = a.twin_sla_err > BIG, a.flagged
    print(f"## Criteria ({len(a)} cells)\n")
    print(f"- large errors: {int(big.sum())}; flagged: {int(fl.sum())}; flagged with |SLA err| <= 3: {int((fl & (a.twin_sla_err <= 3)).sum())}")
    print(f"- D1 every cell with |SLA err| > {BIG} is flagged: {'PASS' if (fl | ~big).all() else 'FAIL'} "
          f"({int((big & fl).sum())}/{int(big.sum())} caught)")
    um = a.twin_sla_err[~fl].median()
    print(f"- D2 unflagged cells median |SLA err| <= 3: {um:.1f} -> {'PASS' if um <= 3 else 'FAIL'}")
    print(f"- unflagged cells: median {um:.1f}, max {a.twin_sla_err[~fl].max():.1f}, within 3 pts & 15% "
          f"{int(((a.twin_sla_err <= 3) & (a.twin_cost_err <= 15))[~fl].sum())}/{int((~fl).sum())}")
    if fl.any():
        print(f"- flagged cells: median {a.twin_sla_err[fl].median():.1f}, max {a.twin_sla_err[fl].max():.1f}")
    print("\nPer-cell table: real/runs/m7_cells.csv.")


if __name__ == "__main__":
    main()
