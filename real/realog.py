"""Turn live harness runs into the simulator's log format, so the M1-M3 estimators
run on real data unchanged.

Alignment: harness row t holds the window measured just before decision t, so
decision t uses row t as its context (m, s) and logged action, and its outcome is
the window of row t+1. A 200-row run gives T = 199 decisions.
"""
import json
import os
from types import SimpleNamespace

import numpy as np
import pandas as pd

from ope.logger import OUT_DTYPE

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "runs")


def load_run(tag):
    p = os.path.join(RUNS, f"{tag}.csv")
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p)
    meta = json.load(open(os.path.join(RUNS, f"{tag}.json")))
    return d, meta


def _context(r):
    m = dict(load_frac=float(r.load_frac), rho=float(r.rho), latency=float(r.latency_mean_ms),
             success=float(r.success), cpu_util=float(r.cpu_util), mem_pressure=0.0)
    s = SimpleNamespace(replicas=int(r.ready_replicas), target_replicas=int(r.requested_replicas),
                        cpu_req=int(r.cpu_req), steps_to_ready=int(r.steps_to_ready), mem_req=128, mem_need_now=0.0)
    return m, s


def to_log(frames):
    """Stack one or more harness runs (DataFrames of equal length) into a log dict."""
    T = min(len(d) for d in frames) - 1
    n = len(frames)
    log = dict(seeds=np.arange(n), d_rep=np.zeros((n, T), np.int8), mu=np.zeros((n, T, 3)),
               sla=np.zeros((n, T)), cost=np.zeros((n, T)), latency=np.zeros((n, T)),
               load=np.zeros((n, T)), out=np.zeros((n, T), dtype=OUT_DTYPE), m=[], s=[])
    for i, d in enumerate(frames):
        d = d.iloc[:T + 1].reset_index(drop=True)
        ctx, nxt = d.iloc[:T], d.iloc[1:T + 1]
        log["d_rep"][i] = ctx.d_rep.values
        log["mu"][i] = ctx[["mu_minus", "mu_zero", "mu_plus"]].values
        log["sla"][i] = nxt.sla_ok.values
        log["cost"][i] = nxt.cost_vcpu.values
        log["latency"][i] = nxt.latency_mean_ms.values
        log["load"][i] = nxt.load_frac.values
        o = log["out"][i]
        o["replicas"], o["target_replicas"] = nxt.ready_replicas.values, nxt.requested_replicas.values
        o["cpu_req"], o["steps_to_ready"] = nxt.cpu_req.values, nxt.steps_to_ready.values
        o["latency"], o["success"] = nxt.latency_mean_ms.values, nxt.success.values
        o["cpu_util"], o["rho"] = nxt.cpu_util.fillna(0).values, nxt.rho.fillna(0).values
        ms, ss = zip(*(_context(r) for r in ctx.itertuples()))
        log["m"].append(list(ms))
        log["s"].append(list(ss))
    return log


def truth(d):
    """Live value of the policy that ran: mean outcome over rows 1..end (same alignment)."""
    return dict(sla=100 * d.sla_ok.iloc[1:].mean(), cost=d.cost_vcpu.iloc[1:].mean())


def readiness_delay_steps(frames):
    """Share of scale decisions whose new replica count is already ready at the next
    row, and the implied delay (1 if most are, else 2) for the MB rollout."""
    done = total = 0
    for d in frames:
        for t in range(len(d) - 1):
            if d.d_rep.iloc[t] != 0 and d.requested_replicas.iloc[t + 1] != d.requested_replicas.iloc[t]:
                total += 1
                done += d.ready_replicas.iloc[t + 1] == d.requested_replicas.iloc[t + 1]
    share = done / total if total else float("nan")
    return (1 if (total and share >= 0.5) else 2), share, total
