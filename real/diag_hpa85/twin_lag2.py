"""Exploratory only (not in the repo): twin v2 with a second demand lag in the key."""
import sys, numpy as np, pandas as pd
from types import SimpleNamespace
sys.path.insert(0, "real"); sys.path.insert(0, ".")
from ope.twin import Twin, demand, log_scale, REPLICA_LO, REPLICA_HI, interval_v2
import ope.twin as T

class Twin2(Twin):
    def __init__(self, frames, cpu_req=200, w2=1.0, **kw):
        super().__init__(frames, cpu_req=cpu_req, **kw)
        self.w2 = w2
        D2 = []
        for d in frames:
            D = demand(d.rps_achieved.values, d.ready_replicas.values, cpu_req, self.m_per_rps)
            D2.append(np.r_[D[0], D[0], D[:-2]][1:])
        self.X = np.c_[self.X, w2 * np.log(np.maximum(np.concatenate(D2), 1e-3))]

    def rollout(self, factory, rps, load_frac, rng, rho_shift=0.0, start_replicas=2):
        pol = factory(); pol.reset()
        self._far, self._width, self._mix = [], [], []
        ready = req = prev_ready = start_replicas
        D_prev = D_prev2 = demand(rps[0], ready, self.cpu_req, self.m_per_rps)
        sla, cost = [], []; c = self.cols
        for t in range(len(rps)):
            D = demand(rps[t], ready, self.cpu_req, self.m_per_rps)
            q = np.r_[self._key(np.array([D]), np.array([D_prev]), np.array([int(ready != prev_ready)]))[0],
                      self.w2 * np.log(max(D_prev2, 1e-3))]
            dist = np.abs(self.X - q).sum(1)
            idx = np.argpartition(dist, self.k)[:self.k]
            self._far.append(dist[idx].min() > T.FAR); self._width.append(dist[idx].max()); self._mix.append(c["sla_ok"][idx].mean())
            j = rng.choice(idx); rho = c["rho"][j]
            if self.rescale and D < self.linear_below and c["D"][j] < self.linear_below:
                rho = rho * D / c["D"][j]
            rho = max(0.0, rho + rho_shift)
            if t >= 1:
                sla.append(c["sla_ok"][j]); cost.append(ready * self.cpu_req / 1000.0)
            m = dict(load_frac=float(load_frac[t]), rho=rho, latency=float(c["latency_mean_ms"][j]),
                     success=float(c["success"][j]), cpu_util=min(rho, 1.5), mem_pressure=0.0)
            s = SimpleNamespace(replicas=ready, target_replicas=req, cpu_req=self.cpu_req,
                                steps_to_ready=int(ready != req), mem_req=128, mem_need_now=0.0)
            a = pol.act(m, s)[0]
            req = int(np.clip(req + a, REPLICA_LO, REPLICA_HI))
            prev_ready, ready = ready, req
            D_prev2, D_prev = D_prev, D
        return np.array(sla, float), np.array(cost, float)

def twin_v2_lag2(frames, cpu_req=200):
    m, lb = log_scale(frames, cpu_req)
    return Twin2(frames, cpu_req=cpu_req, m_per_rps=m, linear_below=lb, use_chg=False)
