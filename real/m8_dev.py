"""M8 development: the queueing-model baseline (ope.queue_baseline) on W1-W4 against the
live truth, before it is frozen for the W5 test. No tuning: fitted latency parameters and
errors are reported as they come out.

  OMP_NUM_THREADS=1 taskset -c 16,18,20,22 nice -n 19 python real/m8_dev.py > real/runs/m8_dev.md
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from ope.policies import REAL_TARGETS  # noqa: E402
from ope.queue_baseline import QueueModel  # noqa: E402
from m5_report import frames, truth_of  # noqa: E402

print("# M8 development: queueing-model baseline on W1-W4\n")
print("| window | fit | a (ms) | b (ms) | median SLA err | max SLA err | median cost err % |")
print("|---|---|---|---|---|---|---|")
allerr = {True: [], False: []}
for w in ("w1", "w2", "w3", "w4"):
    logs = [d for _, d in frames([f"on_{w}_log_eps{e}_r{r}" for e in ("0.1", "0") for r in (1, 2)])]
    rps, lf = logs[0].rps_target.values, logs[0].load_frac.values
    for phys in (False, True):
        q = QueueModel(logs, physical=phys)
        se, ce = [], []
        for name, f in REAL_TARGETS.items():
            if name == "hpa70":
                continue
            tr = truth_of(w, name)
            if tr is None:
                continue
            e = q.estimate(f, rps, lf)
            se.append(abs(e["sla"] - tr["sla"]))
            ce.append(100 * abs(e["cost"] - tr["cost"]) / tr["cost"])
        allerr[phys] += se
        print(f"| {w} | {'non-negative' if phys else 'unconstrained (frozen)'} | {q.a:.2f} | {q.b:.2f} | {np.median(se):.1f} | {max(se):.1f} | {np.median(ce):.1f} |")
for phys in (False, True):
    v = allerr[phys]
    print(f"\nAll 32 cells, {'non-negative' if phys else 'unconstrained (frozen)'} fit: median {np.median(v):.1f}, max {max(v):.1f}")
