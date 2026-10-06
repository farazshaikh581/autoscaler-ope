"""Pick M4 trace windows in the simulator: 200-step windows where the targets differ
strongly, and whose peak request rate fits saul's load generator and cluster.

  python real/pick_windows.py --family bitbrains --workload io-bound
  python real/pick_windows.py --family azure --workload cpu-bound

For every start (stride 25) runs HPA-70 (the behaviour's base), HPA-30, HPA-90, HPA-95
and SLO-cost on-policy for 200 steps, and reports SLA% / cost spread and peak rps at
max_rps = 2050 (node0's 1200 x 205/120). Writes real/windows_<family>_<workload>.csv.
"""
import argparse
import csv
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from ope.policies import TARGETS_M1B, SANITY_TARGETS  # noqa: E402
from ope.sim import make_env, outcome, step_action, use_family  # noqa: E402

POLICIES = {"hpa70": SANITY_TARGETS["hpa70"], **{k: TARGETS_M1B[k] for k in ("hpa30", "hpa90", "hpa95", "slo_cost")}}


def run(env, factory, start, steps):
    _, info = env.reset(seed=0, options={"start": start})
    c = factory()
    c.reset()
    m = info["metrics"]
    sla, cost, load = [], [], []
    for _ in range(steps):
        d = c.act(m, env._backend.s)[0]
        _, _, _, _, info = env.step(step_action(d))
        m = info["metrics"]
        ok, cst, _ = outcome(m, env._backend.s)
        sla.append(ok)
        cost.append(cst)
        load.append(m["load_frac"])
    return 100 * np.mean(sla), np.mean(cost), np.array(load)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True)
    ap.add_argument("--workload", required=True)
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--stride", type=int, default=25)
    ap.add_argument("--max-rps", type=float, default=2050.0)
    args = ap.parse_args()
    use_family(args.family)
    from envs.joint_hv_env import INTENSITY
    env = make_env(args.workload, args.steps)
    cpu_int = INTENSITY[args.workload]["cpu"]
    env.reset(seed=0)
    n = env._backend.n                       # trace length
    rows = []
    for start in range(0, n - args.steps - 1, args.stride):
        r = dict(start=start)
        for name, f in POLICIES.items():
            sla, cost, load = run(env, f, start, args.steps)
            r[f"sla_{name}"], r[f"cost_{name}"] = round(sla, 1), round(cost, 3)
        r["peak_rps"] = round(float(load.max()) * cpu_int * args.max_rps)
        r["mean_rps"] = round(float(load.mean()) * cpu_int * args.max_rps)
        r["sla_gap_70_vs_95"] = round(r["sla_hpa70"] - r["sla_hpa95"], 1)
        r["cost_gap_30_vs_95"] = round(r["cost_hpa30"] - r["cost_hpa95"], 3)
        rows.append(r)
    out = os.path.join(HERE, f"windows_{args.family}_{args.workload}.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out} ({len(rows)} windows)")


if __name__ == "__main__":
    main()
