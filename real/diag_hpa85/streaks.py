# Diagnosis of the hpa85 cost miss (real/diag_hpa85/README.md). Run from the repo root.
import sys, numpy as np, pandas as pd
sys.path.insert(0, "real"); sys.path.insert(0, ".")
from m5_report import frames
from ope.twin import demand, log_scale
R = "real/runs/"
def streak(sat):
    out, n = [], 0
    for s in sat:
        n = n + 1 if s else 0; out.append(n)
    return np.array(out)
def table(dfs, m):
    rows = []
    for d in dfs:
        D = demand(d.rps_achieved.values, d.ready_replicas.values, 200, m)
        s = streak(D > 1.0)
        rows.append(pd.DataFrame(dict(streak=np.minimum(s, 5), cpu=d.cpu_util.values, sat=D > 1.0)))
    x = pd.concat(rows); x = x[x.sat]
    return x.groupby("streak").cpu.agg(["mean", "count"])
allT, allL = [], []
for w in ("w4", "w5", "api_w1", "api_w4"):
    logs = [d for _, d in frames([f"on_{w}_log_eps{e}_r{r}" for e in ("0.1", "0") for r in (1, 2)])]
    m, _ = log_scale(logs)
    tr = [pd.read_csv(R + f"on_{w}_truth_{p}.csv") for p in ("hpa85", "hpa95", "slo_cost", "hpa70_stab0")]
    allT.append(table(tr, m).assign(w=w)); allL.append(table(logs, m).assign(w=w))
T = pd.concat(allT).reset_index(); L = pd.concat(allL).reset_index()
f = lambda X: X.groupby("streak").apply(lambda g: pd.Series(dict(cpu=np.average(g["mean"], weights=g["count"]), n=g["count"].sum())))
print("saturated cpu_util by consecutive saturated steps (5 = 5 or more)")
print("TRUTH (hpa85, hpa95, slo_cost, stab0):"); print(f(T).round(3).to_string())
print("LOGS (dithered HPA-70):"); print(f(L).round(3).to_string())
