"""M4 pilot step 1: can the pinned load generator reach the windows' peak rates?

  taskset -c 0,2,4,6,8,10,12,14 python real/loadcheck.py --rps 958 1253 --seconds 60

Scales web-service to 12 replicas so the app is not the bottleneck, drives each rate
for --seconds with phase1/loadgen.py (the harness's driver), and samples /proc/stat
for this process's CPUs once a second. Reports achieved rps (and its gap to the
target), success, latency, and per-core busy %. Scales back to 2 at the end. Uses
the same preflight as the harness (E1 finished, no HPA/VPA, all workers
schedulable, even CPUs only). Writes real/runs/loadcheck.json.
"""
import argparse
import json
import os
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import harness as H  # noqa: E402

from loadgen import run_load, summarize  # noqa: E402


def cpu_times():
    out = {}
    with open("/proc/stat") as f:
        for line in f:
            if line.startswith("cpu") and line[3].isdigit():
                parts = line.split()
                vals = list(map(int, parts[1:]))
                idle = vals[3] + vals[4]
                out[int(parts[0][3:])] = (sum(vals), idle)
    return out


def sample_busy(cpus, stop, result):
    prev = cpu_times()
    while not stop.is_set():
        time.sleep(1.0)
        cur = cpu_times()
        for c in cpus:
            tot, idle = cur[c][0] - prev[c][0], cur[c][1] - prev[c][1]
            result.setdefault(c, []).append(100.0 * (1 - idle / tot) if tot else 0.0)
        prev = cur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rps", type=int, nargs="+", required=True)
    ap.add_argument("--seconds", type=int, default=60)
    args = ap.parse_args()
    state = H.preflight_live()
    H.signal.signal(H.signal.SIGTERM, H._sigterm)
    H.runlog(f"OPE load check: {args.rps} rps x {args.seconds}s against 12 replicas",
             60 + len(args.rps) * (args.seconds + 15) + 120)
    cluster = H.LiveCluster(args.seconds)
    cpus = state["cpu_affinity"]
    report = dict(cluster=state, seconds=args.seconds, started=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                  checks=[])
    try:
        cluster.reset(replicas=12, settle_s=30)
        run_load(cluster.url, 50, 10)                       # warm-up
        for rps in args.rps:
            stop, busy = threading.Event(), {}
            th = threading.Thread(target=sample_busy, args=(cpus, stop, busy))
            th.start()
            t = time.time()
            samples = run_load(cluster.url, rps, args.seconds)
            elapsed = time.time() - t
            stop.set()
            th.join()
            s = summarize(samples)
            achieved = s["n"] / args.seconds
            per_core = {c: round(max(v), 1) for c, v in busy.items()}
            mean_core = {c: round(sum(v) / len(v), 1) for c, v in busy.items()}
            chk = dict(rps_target=rps, rps_achieved=round(achieved, 1), gap_pct=round(100 * (achieved - rps) / rps, 1),
                       wall_s=round(elapsed, 1), success=s["success"], mean_ms=s["mean_ms"], p99_ms=s["p99_ms"],
                       core_busy_max_pct=per_core, core_busy_mean_pct=mean_core,
                       pass_rate=abs(achieved - rps) <= 0.05 * rps, pass_cpu=max(mean_core.values()) < 70.0)
            report["checks"].append(chk)
            print(json.dumps(chk))
    finally:
        cluster.scale(2)
    os.makedirs(os.path.join(HERE, "runs"), exist_ok=True)
    with open(os.path.join(HERE, "runs", "loadcheck.json"), "w") as f:
        json.dump(report, f, indent=1)


if __name__ == "__main__":
    main()
