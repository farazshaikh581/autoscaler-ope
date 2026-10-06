"""Ground truth: run a policy on-policy in the simulator."""
import numpy as np

from .sim import EPISODE_LEN, make_env, outcome, step_action

TRUTH_SEED0 = 50_000_000      # disjoint from the logging seeds (driver uses < 20_000_000)


def run_on_policy(workload: str, factory, episodes: int = 200) -> dict:
    env = make_env(workload)
    sla = np.zeros((episodes, EPISODE_LEN))
    cost = np.zeros((episodes, EPISODE_LEN))
    for i in range(episodes):
        _, info = env.reset(seed=TRUTH_SEED0 + i)
        c = factory()
        c.reset()
        m = info["metrics"]
        for t in range(EPISODE_LEN):
            d = c.act(m, env._backend.s)[0]
            _, _, _, _, info = env.step(step_action(d))
            m = info["metrics"]
            sla[i, t], cost[i, t], _ = outcome(m, env._backend.s)
    ep_sla, ep_cost = 100 * sla.mean(axis=1), cost.mean(axis=1)
    return dict(sla=float(ep_sla.mean()), sla_se=float(ep_sla.std(ddof=1) / np.sqrt(episodes)),
                cost=float(ep_cost.mean()), cost_se=float(ep_cost.std(ddof=1) / np.sqrt(episodes)))
