# Diagnosis of the hpa85 cost miss (real/diag_hpa85/README.md). Run from the repo root.
import sys, numpy as np, pandas as pd
sys.path.insert(0, "real"); sys.path.insert(0, ".")
from m5_report import frames
from ope.twin import twin_v2, demand, log_scale
from ope.policies import REAL_TARGETS
R = "real/runs/"
CASES = [("w5", "on_w5_truth_hpa85"), ("api_w1", "on_api_w1_truth_hpa85"), ("api_w4", "on_api_w4_truth_hpa85"),
         ("w4", "on_w4_truth_hpa85"), ("w4", "on_w4_truth_hpa85_r2")]
for w, tag in CASES:
    logs = [d for _, d in frames([f"on_{w}_log_eps{e}_r{r}" for e in ("0.1", "0") for r in (1, 2)])]
    m, lb = log_scale(logs)
    L = pd.concat([d.iloc[1:] for d in logs])
    LD = demand(L.rps_achieved.values, L.ready_replicas.values, 200, m)
    t = pd.read_csv(R + tag + ".csv")
    TD = demand(t.rps_achieved.values, t.ready_replicas.values, 200, m)
    sat_t, sat_l = TD > 1.0, LD > 1.0
    print(f"\n== {tag}  (m={m:.2f})")
    print(f"truth: mean ready {t.ready_replicas.mean():.2f}, scale-outs {(t.d_rep>0).sum()}, scale-ins {(t.d_rep<0).sum()}, saturated steps {sat_t.sum()}")
    print(f"truth saturated rho: mean {t.rho[sat_t].mean():.3f}, share > 0.935: {(t.cpu_util[sat_t] > 0.935).mean():.2f}")
    print(f"logs  saturated rho: mean {L.rho[sat_l].mean():.3f}, share > 0.935: {(L.cpu_util[sat_l] > 0.935).mean():.2f}, n={sat_l.sum()}")
    # rho by replica count when saturated
    for name, df, sat in (("truth", t, sat_t), ("logs", L, sat_l)):
        g = df[sat].groupby("ready_replicas").cpu_util.agg(["mean", "count", lambda x: (x > 0.935).mean()])
        print(f"  {name} saturated cpu_util by ready: " + "; ".join(f"{int(k)}:{r['mean']:.3f}/{r.iloc[2]:.2f} (n{int(r['count'])})" for k, r in g.iterrows()))
