"""Model-based replay and windowed doubly robust estimation.

Known platform mechanics (from the orchestrator's documentation, not learned):
a replica delta of -1/0/+1 per decision, replicas bounded to [1, 12], and a new
target taking SCALE_DELAY steps to become ready. The load sequence is exogenous and
taken from the log. Everything else (latency, success, utilisation as functions of
load and capacity) comes from a model fitted to logs (ope/model.py).
"""
import copy
from types import SimpleNamespace

import numpy as np

from .estimators import ratios
from .model import features
from .sim import SLA_MEAN_LATENCY_MS

REPLICA_LO, REPLICA_HI, SCALE_DELAY = 1, 12, 2


def shadow_with_snapshots(log: dict, factory):
    """Shadow replay that also keeps a copy of the controller just before each
    decision, so a rollout can resume the target from any logged step."""
    n, T = log["d_rep"].shape
    acts = np.zeros((n, T), dtype=np.int8)
    snaps = []
    for i in range(n):
        c = factory()
        c.reset()
        row = []
        for t in range(T):
            row.append(copy.copy(c))     # controllers hold only scalars
            acts[i, t] = c.act(log["m"][i][t], log["s"][i][t])[0]
        snaps.append(row)
    return acts, snaps


def rollout(model, ctrls, m0, s0, loads, valid, first_actions=None):
    """Advance len(ctrls) rollouts in lockstep for loads.shape[1] steps.

    ctrls: controllers (shallow copies are enough: they hold only scalars) already in the right internal state (consumed); m0: list of
    metric dicts they see first; s0: dict of int arrays (replicas, target_replicas,
    cpu_req, steps_to_ready); loads, valid: (B, H). first_actions, if given,
    overrides the controllers' first decision (they still observe it).
    Returns predicted sla_ok and cost, (B, H); entries with valid False are 0."""
    B, H = loads.shape
    rep, tgt = s0["replicas"].copy(), s0["target_replicas"].copy()
    cpu, rdy = s0["cpu_req"].copy(), s0["steps_to_ready"].copy()
    ms = list(m0)
    sla, cost = np.zeros((B, H)), np.zeros((B, H))
    for h in range(H):
        d = np.empty(B, dtype=int)
        for b in range(B):
            s = SimpleNamespace(replicas=int(rep[b]), target_replicas=int(tgt[b]), cpu_req=int(cpu[b]),
                                steps_to_ready=int(rdy[b]), mem_req=128, mem_need_now=0.0)
            d[b] = ctrls[b].act(ms[b], s)[0]
        if h == 0 and first_actions is not None:
            d = first_actions.astype(int)
        # apply, then advance readiness (same order as an orchestrator tick)
        tgt = np.clip(tgt + d, REPLICA_LO, REPLICA_HI)
        start = (tgt != rep) & (rdy == 0)
        rdy = np.where(start, SCALE_DELAY, rdy)
        ticking = rdy > 0
        rdy = np.where(ticking, rdy - 1, rdy)
        rep = np.where(ticking & (rdy == 0), tgt, rep)
        p = model.predict(features(loads[:, h], rep, cpu, rdy, tgt - rep))
        ok = (p["latency"] < SLA_MEAN_LATENCY_MS) & (p["success"] >= 0.99)
        sla[:, h] = np.where(valid[:, h], ok, 0.0)
        cost[:, h] = np.where(valid[:, h], rep * cpu / 1000.0, 0.0)
        ms = [dict(load_frac=float(loads[b, h]), rho=float(p["rho"][b]), latency=float(p["latency"][b]),
                   success=float(p["success"][b]), cpu_util=float(p["cpu_util"][b]), mem_pressure=0.0)
              for b in range(B)]
    return sla, cost


def _state(log, idx):
    """Logged pre-decision state at the (episode, step) pairs in idx, as arrays."""
    ss = [log["s"][i][t] for i, t in idx]
    return {k: np.array([getattr(s, k) for s in ss], dtype=int)
            for k in ("replicas", "target_replicas", "cpu_req", "steps_to_ready")}


def mb_estimate(log, model, factory):
    """Roll the target from each episode's start over the logged load. Returns
    per-step predicted (sla_ok, cost), (N, T)."""
    n, T = log["d_rep"].shape
    ctrls = [factory() for _ in range(n)]
    for c in ctrls:
        c.reset()
    idx = [(i, 0) for i in range(n)]
    return rollout(model, ctrls, [log["m"][i][0] for i in range(n)], _state(log, idx),
                   log["load"], np.ones((n, T), bool))


def window_q(log, model, snaps, kmax):
    """Model values for DR: from every logged step j, roll the target for kmax steps
    (V) and the same with the logged action first (Q). Returns dict of
    (N, T, kmax) arrays: v_sla, v_cost, q_sla, q_cost (value of step j+h)."""
    n, T = log["d_rep"].shape
    idx = [(i, j) for i in range(n) for j in range(T)]
    pos = np.arange(T)[None, :] + np.arange(kmax)[:, None]               # (kmax, T)
    loads = np.zeros((n * T, kmax))
    valid = np.zeros((n * T, kmax), bool)
    for i in range(n):
        ok = pos < T
        loads[i * T:(i + 1) * T] = np.where(ok, log["load"][i][np.minimum(pos, T - 1)], 0).T
        valid[i * T:(i + 1) * T] = ok.T
    m0 = [log["m"][i][j] for i, j in idx]
    s0 = _state(log, idx)
    out = {}
    for tag, first in (("v", None), ("q", log["d_rep"].reshape(-1))):
        ctrls = [copy.copy(snaps[i][j]) for i, j in idx]
        sla, cost = rollout(model, ctrls, m0, s0, loads, valid, first)
        out[f"{tag}_sla"] = sla.reshape(n, T, kmax)
        out[f"{tag}_cost"] = cost.reshape(n, T, kmax)
    return out


def dr_per_step(rho, r, v, q, k):
    """Windowed per-decision DR with self-normalised weights, per step (N, T).

    For outcome step t the window starts at j = max(0, t-k+1):
      DR_t = V_j(t) + sum_{i=j..t} Wbar_{j:i} * (next_i - Q_i(t)),
    next_i = V_{i+1}(t) for i < t and the observed r_t for i = t; V_i(t), Q_i(t) are
    model values of step t from logged step i (target throughout, or the logged
    action first). W_{j:i} is the product of ratios over decisions j..i, divided
    by its mean over episodes (a term with zero mean weight is dropped)."""
    n, T = r.shape
    out = np.zeros((n, T))
    for t in range(T):
        j = max(0, t - k + 1)
        est = v[:, j, t - j].copy()
        w = np.ones(n)
        for i in range(j, t + 1):
            w = w * rho[:, i]
            mw = w.mean()
            if mw <= 0:
                break                      # no support from here on: keep the model value
            nxt = v[:, i + 1, t - i - 1] if i < t else r[:, t]
            est += (w / mw) * (nxt - q[:, i, t - i])
        out[:, t] = est
    return out


def dr_ratios(log, target_actions, mu):
    return ratios(target_actions == log["d_rep"], mu)


class LoggedActions:
    """Replays one logged episode's replica deltas open-loop, for calibrating the
    model on the behaviour's own trajectory."""

    def __init__(self, deltas):
        self.deltas, self.t = deltas, 0

    def reset(self):
        self.t = 0

    def act(self, m, s):
        d = int(self.deltas[self.t])
        self.t += 1
        return (d, 0, 0)


def mb_logged(log, model):
    """Model rollout of the logged action sequence from each episode start.
    Returns predicted per-step (sla_ok, cost), (N, T), to compare with the log."""
    n, T = log["d_rep"].shape
    ctrls = [LoggedActions(log["d_rep"][i]) for i in range(n)]
    idx = [(i, 0) for i in range(n)]
    return rollout(model, ctrls, [log["m"][i][0] for i in range(n)], _state(log, idx),
                   log["load"], np.ones((n, T), bool))


def window_anchor(v, k):
    """V_j(t) with j = max(0, t-k+1): the value windowed DR starts from, (N, T)."""
    n, T, _ = v.shape
    return np.stack([v[:, max(0, t - k + 1), t - max(0, t - k + 1)] for t in range(T)], axis=1)


def dr_mb_per_step(dr, v, k, mb_full):
    """DR anchored on the full-horizon MB value: replace windowed DR's anchor (the
    model value from the behaviour's state k decisions back) with the model's
    prediction of the same step from the episode start under the target. Equals
    mb_full + (dr - anchor); at full horizon (j = 0) it is ordinary DR."""
    return mb_full + (dr - window_anchor(v, k))
