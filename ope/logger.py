"""Collect logs from the dithered-HPA behaviour policy."""
import numpy as np

from .policies import DitheredHPA
from .sim import D_REPS, EPISODE_LEN, M_KEYS, make_env, outcome, snapshot, step_action


def collect(workload: str, eps: float, episode_seeds: list[int], dither_seed) -> dict:
    """Run the behaviour for one episode per seed. Step t holds the context the
    controller saw (m, s), the logged delta, the behaviour probability of all three
    deltas, and the outcome observed after acting."""
    env = make_env(workload)
    pol = DitheredHPA(eps, np.random.default_rng(dither_seed))
    n, T = len(episode_seeds), EPISODE_LEN
    log = dict(workload=workload, eps=eps, seeds=np.asarray(episode_seeds),
               d_rep=np.zeros((n, T), np.int8), mu=np.zeros((n, T, 3)),
               sla=np.zeros((n, T)), cost=np.zeros((n, T)), latency=np.zeros((n, T)),
               m=[], s=[])
    for i, seed in enumerate(episode_seeds):
        _, info = env.reset(seed=int(seed))
        pol.reset()
        m = info["metrics"]
        ms, ss = [], []
        for t in range(T):
            s = snapshot(env._backend.s)
            ms.append({k: m[k] for k in M_KEYS})
            ss.append(s)
            d, p = pol.act(m, s)
            _, _, term, trunc, info = env.step(step_action(d))
            m = info["metrics"]
            log["d_rep"][i, t] = d
            log["mu"][i, t] = p
            log["sla"][i, t], log["cost"][i, t], log["latency"][i, t] = outcome(m, env._backend.s)
            if term or trunc:
                assert t == T - 1
        log["m"].append(ms)
        log["s"].append(ss)
    return log


def logged_prob(log: dict) -> np.ndarray:
    """Behaviour probability of the logged delta, (N, T)."""
    idx = log["d_rep"].astype(int) + 1          # D_REPS = (-1, 0, 1)
    assert D_REPS == (-1, 0, 1)
    return np.take_along_axis(log["mu"], idx[..., None], axis=2)[..., 0]


def subset(log: dict, n: int) -> dict:
    """The first n episodes of a log (logs are nested across n_episodes)."""
    return {k: (v[:n] if k in ("seeds", "d_rep", "mu", "sla", "cost", "latency", "m", "s") else v)
            for k, v in log.items()}
