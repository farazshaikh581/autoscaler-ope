"""Demand-space twin: off-policy evaluation by rollout in policy-invariant coordinates.

On the real cluster the trace fixes the offered load, and what a step looks like
(measured CPU, latency, success, SLA) depends on the per-pod demand
    D_t = rps_t * M_PER_RPS / (ready_t * cpu_req)
and on the previous step's demand (metrics lag), not on which policy chose the
replica count. The behaviour's logs cover a wide range of D even where they cover
few (replicas, load) cells, because the behaviour itself swings across the knee.

A rollout runs the target's own controller code over the window's load:
  1. compute D_t from the known load and the rolled-out ready replicas;
  2. draw one of the K logged steps nearest in (log D_t, log D_{t-1}, replica change
     at t) and take its rho, latency, success and SLA outcome jointly;
  3. below the knee region (both D < LINEAR_BELOW) rescale the donor's rho by
     D_t / D_donor, since unsaturated CPU is proportional to demand;
  4. requested += action; the new count is ready at the next step (readiness is
     one step on saul: 99-100% of scale decisions in the logs).
Each rollout is one simulated episode, so the spread of rollouts is a prediction
interval for a single live run. A sensitivity run shifts the measured rho by
+-RHO_SHIFT to expose policies whose decisions sit on a threshold.
"""
from types import SimpleNamespace

import numpy as np
import pandas as pd

M_PER_RPS = 1.727          # mcores per rps on saul (knee check, real/runs/kneecheck.json)
LINEAR_BELOW = 0.7         # per-pod demand below the knee region (knee check: flat to ~0.85)
K = 10
N_ROLLOUTS = 40
RHO_SHIFT = 0.03
REPLICA_LO, REPLICA_HI = 1, 12


def demand(rps, ready, cpu_req):
    return rps * M_PER_RPS / (np.maximum(ready, 1) * cpu_req)


class Twin:
    def __init__(self, frames, cpu_req=200, k=K):
        """frames: harness DataFrames of the behaviour's log runs (row 0 dropped, it
        precedes the first decision)."""
        rows = []
        for d in frames:
            d = d.copy()
            D = demand(d.rps_achieved.values, d.ready_replicas.values, cpu_req)
            rr = d.ready_replicas.values
            d["D"], d["Dp"] = D, np.r_[D[0], D[:-1]]
            d["chg"] = np.r_[0, (rr[1:] != rr[:-1]).astype(int)]
            rows.append(d.iloc[1:])
        self.d = pd.concat(rows, ignore_index=True)
        self.X = self._key(self.d.D.values, self.d.Dp.values, self.d.chg.values)
        self.cols = {c: self.d[c].values for c in ("rho", "latency_mean_ms", "success", "sla_ok", "D")}
        self.cpu_req, self.k = cpu_req, k

    @staticmethod
    def _key(D, Dp, chg):
        return np.c_[np.log(np.maximum(D, 1e-3)), np.log(np.maximum(Dp, 1e-3)), 10.0 * np.asarray(chg)]

    def rollout(self, factory, rps, load_frac, rng, rho_shift=0.0, start_replicas=2):
        """One episode of the target over the window; returns per-step (sla, cost)
        for steps 1..T-1, the same alignment as realog.truth()."""
        pol = factory()
        pol.reset()
        ready = req = prev_ready = start_replicas
        D_prev = demand(rps[0], ready, self.cpu_req)
        sla, cost = [], []
        c = self.cols
        for t in range(len(rps)):
            D = demand(rps[t], ready, self.cpu_req)
            q = self._key(np.array([D]), np.array([D_prev]), np.array([int(ready != prev_ready)]))[0]
            idx = np.argpartition(np.abs(self.X - q).sum(1), self.k)[:self.k]
            j = rng.choice(idx)
            rho = c["rho"][j]
            if D < LINEAR_BELOW and c["D"][j] < LINEAR_BELOW:
                rho = rho * D / c["D"][j]
            rho = max(0.0, rho + rho_shift)
            if t >= 1:
                sla.append(c["sla_ok"][j])
                cost.append(ready * self.cpu_req / 1000.0)
            m = dict(load_frac=float(load_frac[t]), rho=rho, latency=float(c["latency_mean_ms"][j]),
                     success=float(c["success"][j]), cpu_util=min(rho, 1.5), mem_pressure=0.0)
            s = SimpleNamespace(replicas=ready, target_replicas=req, cpu_req=self.cpu_req,
                                steps_to_ready=int(ready != req), mem_req=128, mem_need_now=0.0)
            a = pol.act(m, s)[0]
            req = int(np.clip(req + a, REPLICA_LO, REPLICA_HI))
            prev_ready, ready = ready, req
            D_prev = D
        return np.array(sla, float), np.array(cost, float)

    def estimate(self, factory, rps, load_frac, seed=0, n=N_ROLLOUTS):
        """Point estimates, single-run prediction intervals (5-95%) and the
        sensitivity interval (union over rho shifts of -RHO_SHIFT, 0, +RHO_SHIFT)."""
        out = {}
        for shift in (0.0, -RHO_SHIFT, RHO_SHIFT):
            rng = np.random.default_rng(seed)
            r = np.array([[100 * x.mean() for x in self.rollout(factory, rps, load_frac, rng, shift)]
                          for _ in range(n)])
            out[shift] = r
        base = out[0.0]
        allr = np.vstack(list(out.values()))
        return dict(sla=base[:, 0].mean(), cost=base[:, 1].mean() / 100,
                    sla_pi=tuple(np.percentile(base[:, 0], [5, 95])),
                    cost_pi=tuple(np.percentile(base[:, 1] / 100, [5, 95])),
                    sla_si=tuple(np.percentile(allr[:, 0], [5, 95])),
                    cost_si=tuple(np.percentile(allr[:, 1] / 100, [5, 95])),
                    sla_shift=[out[s][:, 0].mean() for s in (-RHO_SHIFT, RHO_SHIFT)],
                    cost_shift=[out[s][:, 1].mean() / 100 for s in (-RHO_SHIFT, RHO_SHIFT)])
