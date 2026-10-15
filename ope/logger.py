"""Collect logs from the dithered-HPA behaviour policy."""
import numpy as np

from .policies import DitheredHPA
from .controllers import D_REPS, EPISODE_LEN, M_KEYS, outcome, snapshot


# Observed after each step: serving replicas, requested replicas, CPU request,
# steps until a pending scale lands, and the observed metrics.
OUT_DTYPE = np.dtype([("replicas", "i4"), ("target_replicas", "i4"), ("cpu_req", "i4"),
                      ("steps_to_ready", "i4"), ("latency", "f8"), ("success", "f8"),
                      ("cpu_util", "f8"), ("rho", "f8")])


def collect(workload: str, eps: float, episode_seeds: list[int], dither_seed,
            episode_len: int = EPISODE_LEN) -> dict:
    """Run the behaviour for one episode per seed. Step t holds the context the
    controller saw (m, s), the logged delta, the behaviour probability of all three
    deltas, and the outcome observed after acting. Simulation only."""
    from .sim import make_env, step_action
    env = make_env(workload, episode_len)
    pol = DitheredHPA(eps, np.random.default_rng(dither_seed))
    n, T = len(episode_seeds), episode_len
    log = dict(workload=workload, eps=eps, seeds=np.asarray(episode_seeds),
               d_rep=np.zeros((n, T), np.int8), mu=np.zeros((n, T, 3)),
               sla=np.zeros((n, T)), cost=np.zeros((n, T)), latency=np.zeros((n, T)),
               load=np.zeros((n, T)), out=np.zeros((n, T), dtype=OUT_DTYPE),
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
            log["load"][i, t] = m["load_frac"]      # exogenous: same under any policy
            so = env._backend.s                      # what an operator sees after the step
            log["out"][i, t] = (so.replicas, so.target_replicas, so.cpu_req, so.steps_to_ready,
                                m["latency"], m["success"], m["cpu_util"], m["rho"])
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
    return {k: (v[:n] if k in ("seeds", "d_rep", "mu", "sla", "cost", "latency", "load", "out", "m", "s") else v)
            for k, v in log.items()}


def high_load_mask(load: np.ndarray, q: float = 0.75) -> np.ndarray:
    """Steps in the top quartile of load_frac within their own episode, (N, T)."""
    return load >= np.quantile(load, q, axis=1, keepdims=True)
