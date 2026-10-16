# Diagnosis of the hpa85 cost miss (real/diag_hpa85/README.md). Run from the repo root.
import sys, numpy as np, pandas as pd
sys.path.insert(0, "real/diag_hpa85")
sys.path.insert(0, "real"); sys.path.insert(0, ".")
from twin_lag2 import twin_v2_lag2
from m5_report import frames, truth_of
from ope.policies import REAL_TARGETS
from ope.twin import interval_v2
w = sys.argv[1]
cells = pd.concat([pd.read_csv("real/runs/m8_cells.csv"), pd.read_csv("real/runs/m9_cells.csv")])
logs = [d for _, d in frames([f"on_{w}_log_eps{e}_r{r}" for e in ("0.1", "0") for r in (1, 2)])]
tw = twin_v2_lag2(logs); rps, lf = logs[0].rps_target.values, logs[0].load_frac.values
for name in [t for t in REAL_TARGETS if t != "hpa70"]:
    tr = truth_of(w, name); e = tw.estimate(REAL_TARGETS[name], rps, lf)
    (slo, shi), (clo, chi) = interval_v2(e)
    v2 = cells[(cells.window == w) & (cells.target == name)].iloc[0]
    print(f"{w},{name},{abs(e['sla']-tr['sla']):.2f},{100*abs(e['cost']-tr['cost'])/tr['cost']:.1f},{v2.twin_sla_err:.2f},{v2.twin_cost_err:.1f},{int(slo <= tr['sla'] <= shi and clo <= tr['cost'] <= chi)},{int(v2.in_pi)}", flush=True)
