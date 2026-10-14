"""Queueing-model baseline: an analytical simulator calibrated on the same logs.

The textbook what-if tool for an autoscaler is a queueing model of the service fitted to
monitoring data. Each ready pod is an M/M/1 server with utilisation equal to its per-pod
demand D (ope.twin.demand, CPU per request from the logs as in twin v2), and
    mean latency = a + b / (1 - D)   for D < 1, overload otherwise,
with a and b fitted by least squares on unsaturated logged steps (D < 0.95, success
>= 0.99). The frozen M8 baseline keeps the unconstrained fit: on the development windows
it is the more accurate of the two (median SLA error 6.7 against 8.9 points with a, b >= 0,
real/runs/m8_dev.md), although it gives a negative base latency on two windows. The
comparison is meant to be generous to the baseline. The controller sees CPU
utilisation = min(D, 1), as the model predicts. A step meets the SLA when the modelled
latency is under 20 ms and D < 1. The rollout runs the target's own controller code with
the same one-step readiness and replica bounds as the twin, and is deterministic.
"""
from types import SimpleNamespace

import numpy as np
import pandas as pd

from ope.twin import REPLICA_LO, REPLICA_HI, demand, log_scale

SLA_LATENCY_MS = 20.0
FIT_MAX_D = 0.95


class QueueModel:
    def __init__(self, frames, cpu_req=200, physical=False):
        self.cpu_req = cpu_req
        self.m_per_rps, _ = log_scale(frames, cpu_req)
        d = pd.concat([f.iloc[1:] for f in frames])
        D = demand(d.rps_achieved.values, d.ready_replicas.values, cpu_req, self.m_per_rps)
        ok = (D < FIT_MAX_D) & (d.success.values >= 0.99) & np.isfinite(d.latency_mean_ms.values)
        X = np.c_[np.ones(ok.sum()), 1.0 / (1.0 - D[ok])]
        y = d.latency_mean_ms.values[ok]
        (self.a, self.b), *_ = np.linalg.lstsq(X, y, rcond=None)
        self.a_free, self.b_free = self.a, self.b
        if physical and (self.a < 0 or self.b < 0):
            # latency cannot have a negative base or queueing term: refit the other alone
            if self.a < 0:
                self.a, self.b = 0.0, max(0.0, float(X[:, 1] @ y / (X[:, 1] @ X[:, 1])))
            else:
                self.a, self.b = max(0.0, float(y.mean())), 0.0

    def latency(self, D):
        return self.a + self.b / (1.0 - D) if D < 1.0 else np.inf

    def rollout(self, factory, rps, load_frac, start_replicas=2):
        pol = factory()
        pol.reset()
        ready = req = start_replicas
        sla, cost = [], []
        for t in range(len(rps)):
            D = demand(rps[t], ready, self.cpu_req, self.m_per_rps)
            lat = self.latency(D)
            ok = bool(lat < SLA_LATENCY_MS and D < 1.0)
            if t >= 1:
                sla.append(ok)
                cost.append(ready * self.cpu_req / 1000.0)
            rho = min(D, 1.0)
            m = dict(load_frac=float(load_frac[t]), rho=rho, latency=float(min(lat, 5000.0)),
                     success=1.0 if D < 1.0 else 1.0 / D, cpu_util=rho, mem_pressure=0.0)
            s = SimpleNamespace(replicas=ready, target_replicas=req, cpu_req=self.cpu_req,
                                steps_to_ready=int(ready != req), mem_req=128, mem_need_now=0.0)
            a = pol.act(m, s)[0]
            req = int(np.clip(req + a, REPLICA_LO, REPLICA_HI))
            ready = req
        return np.array(sla, float), np.array(cost, float)

    def estimate(self, factory, rps, load_frac):
        sla, cost = self.rollout(factory, rps, load_frac)
        return dict(sla=100 * sla.mean(), cost=cost.mean())
