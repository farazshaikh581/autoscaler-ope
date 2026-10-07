"""Knee check: where does web-service's latency knee sit on saul with CPU
limit = request = 200m, in the simulator's units (demand rho)?

2 replicas, offered rps stepped through demand rho ~0.6 and 0.80-1.05. Each level:
20 s warm-up, 50 s measured (latency from the load driver, CPU from the metrics
API polled during the measured part). Demand rho = rps * m_per_rps / (2 * 200m),
with m_per_rps fitted on the unsaturated levels, as in the joint repo's
phase1/calibration (sim knee: RHO_KNEE = 0.91, the sigmoid midpoint).

  taskset -c 0,2,4,6,8,10,12,14 python real/kneecheck.py
"""
import json
import os
import sys
import threading
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from harness import RUNLOG, LiveCluster, preflight_live, runlog  # noqa: E402,F401

RHO_LEVELS = [0.60, 0.80, 0.85, 0.88, 0.91, 0.94, 0.97, 1.00, 1.05]
M_PER_RPS_GUESS = 1.85          # mcores per rps on saul (pilot runs, undiluted)
WARM_S, MEASURE_S, REPLICAS = 20, 50, 2
SIM_KNEE = 0.91


def measure(cluster, rps):
    cluster._run_load(cluster.url, rps, WARM_S, quiet=True)
    t0 = time.time()
    cpu, stop = [], threading.Event()

    def poll():
        while not stop.wait(4):
            used, age, window, n = cluster.cpu_used()
            end = time.time() - age
            if n == REPLICAS and end - window >= t0:      # sample fully inside the measured load
                cpu.append(used)
    th = threading.Thread(target=poll, daemon=True)
    th.start()
    samples = cluster._run_load(cluster.url, rps, MEASURE_S, quiet=True)
    stop.set()
    th.join()
    s = cluster._summarize(samples)
    return dict(rps=rps, achieved=round(s["n"] / MEASURE_S, 1), mean_ms=s["mean_ms"], p99_ms=s["p99_ms"],
                success=s["success"], cpu_m=float(np.mean(cpu)) if cpu else float("nan"), cpu_samples=len(cpu))


def main():
    state = preflight_live()
    cluster = LiveCluster(load_seconds=MEASURE_S)
    runlog(f"OPE knee check: 2 replicas, CPU limit {state['cpu_limit']}, {len(RHO_LEVELS)} rps levels",
           len(RHO_LEVELS) * (WARM_S + MEASURE_S + 10) + 120)
    cluster.reset(replicas=REPLICAS, settle_s=30)
    rows = []
    try:
        for r in RHO_LEVELS:
            rps = int(round(r * REPLICAS * cluster.cpu_req / M_PER_RPS_GUESS))
            row = measure(cluster, rps)
            row["rho_meas"] = row["cpu_m"] / (REPLICAS * cluster.cpu_req)
            rows.append(row)
            print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()}), flush=True)
    finally:
        cluster.scale(2)
    base = [x for x in rows if x["mean_ms"] < 10 and x["rho_meas"] < 0.85 and x["cpu_samples"]]
    m_per_rps = sum(x["cpu_m"] for x in base) / sum(x["achieved"] for x in base)
    for x in rows:
        x["rho_demand"] = x["rps"] * m_per_rps / (REPLICAS * cluster.cpu_req)
    lat = np.array([x["mean_ms"] for x in rows])
    rho = np.array([x["rho_demand"] for x in rows])
    l0 = float(np.median([x["mean_ms"] for x in base]))

    def crossing(level):
        i = int(np.argmax(lat >= level)) if (lat >= level).any() else None
        if not i:
            return float("nan")
        return float(rho[i - 1] + (level - lat[i - 1]) * (rho[i] - rho[i - 1]) / (lat[i] - lat[i - 1]))
    mid = (l0 + lat.max()) / 2
    out = dict(m_per_rps=m_per_rps, l0_ms=l0, plateau_ms=float(lat.max()), knee_mid_rho=crossing(mid),
               sla20_rho=crossing(20.0), sim_knee=SIM_KNEE, cpu_limit=state["cpu_limit"], levels=rows,
               started=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    os.makedirs(os.path.join(HERE, "runs"), exist_ok=True)
    with open(os.path.join(HERE, "runs", "kneecheck.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(f"m_per_rps {m_per_rps:.3f}, L0 {l0:.1f} ms, top level {lat.max():.0f} ms; knee (latency midpoint) at "
          f"demand rho {out['knee_mid_rho']:.3f}, 20 ms SLA crossed at {out['sla20_rho']:.3f}; sim {SIM_KNEE}")


if __name__ == "__main__":
    main()
