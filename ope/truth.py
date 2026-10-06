"""Ground truth: run a policy on-policy in the simulator."""
import numpy as np

from .logger import high_load_mask
from .sim import EPISODE_LEN, make_env, outcome, step_action

TRUTH_SEED0 = 50_000_000      # disjoint from the logging seeds (drivers use < 20_000_000)


def run_episodes(workload: str, factory, seeds, episode_len: int = EPISODE_LEN) -> dict:
    """Per-episode on-policy values, one per seed: SLA% and cost over all steps and
    over the high-load steps (top quartile of load_frac in the episode)."""
    env = make_env(workload, episode_len)
    n = len(seeds)
    sla, cost, load = (np.zeros((n, episode_len)) for _ in range(3))
    for i, seed in enumerate(seeds):
        _, info = env.reset(seed=int(seed))
        c = factory()
        c.reset()
        m = info["metrics"]
        for t in range(episode_len):
            d = c.act(m, env._backend.s)[0]
            _, _, _, _, info = env.step(step_action(d))
            m = info["metrics"]
            sla[i, t], cost[i, t], _ = outcome(m, env._backend.s)
            load[i, t] = m["load_frac"]
    hi = high_load_mask(load)
    return dict(sla=100 * sla.mean(axis=1), cost=cost.mean(axis=1),
                sla_hi=100 * (sla * hi).sum(axis=1) / hi.sum(axis=1),
                cost_hi=(cost * hi).sum(axis=1) / hi.sum(axis=1))


def summarise(per_ep: dict) -> dict:
    out = {}
    for k, v in per_ep.items():
        out[k] = float(v.mean())
        out[f"{k}_se"] = float(v.std(ddof=1) / np.sqrt(len(v))) if len(v) > 1 else 0.0
    return out


def run_on_policy(workload: str, factory, episodes: int = 200) -> dict:
    """M1 truth: unpaired, seeds TRUTH_SEED0 + i."""
    s = summarise(run_episodes(workload, factory, [TRUTH_SEED0 + i for i in range(episodes)]))
    return {k: s[k] for k in ("sla", "sla_se", "cost", "cost_se")}
