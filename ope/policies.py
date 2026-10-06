"""Behaviour and target policies, and shadow replay of a target along a log."""
import numpy as np

from .sim import D_REPS, ClassicalController, PredictiveController, in_bounds

BEHAVIOUR_UTIL = 0.70

# name -> factory. All targets are deterministic, replica-only (vpa=False).
TARGETS = {
    "hpa50": lambda: ClassicalController(vpa=False, target_util=0.5),
    "hpa60": lambda: ClassicalController(vpa=False, target_util=0.6),
    "hpa80": lambda: ClassicalController(vpa=False, target_util=0.8),
    "hpa90": lambda: ClassicalController(vpa=False, target_util=0.9),
    "pred70": lambda: PredictiveController(vpa=False, target_util=0.7),
}
# Sanity target: the behaviour's own base controller. Every IS estimator must be
# unbiased for it at any eps, including eps = 0.
SANITY_TARGETS = {"hpa70": lambda: ClassicalController(vpa=False, target_util=BEHAVIOUR_UTIL)}


class DitheredHPA:
    """HPA at u=0.70 whose replica delta is, with probability eps, replaced by a
    uniform draw from {-1, 0, +1}. A draw that would leave the replica bounds becomes
    0, so probs() is the exact probability of each delta given the state."""

    def __init__(self, eps: float, rng: np.random.Generator):
        self.eps, self.rng = eps, rng
        self.hpa = ClassicalController(vpa=False, target_util=BEHAVIOUR_UTIL)

    def reset(self) -> None:
        self.hpa.reset()

    def probs(self, d_hpa: int, s) -> np.ndarray:
        p = np.zeros(3)
        p[D_REPS.index(d_hpa)] += 1.0 - self.eps
        for d in D_REPS:
            p[D_REPS.index(d if in_bounds(d, s) else 0)] += self.eps / 3.0
        return p

    def act(self, m, s) -> tuple[int, np.ndarray]:
        d_hpa = self.hpa.act(m, s)[0]       # always called, so the HPA's counter keeps its history
        p = self.probs(d_hpa, s)
        d = d_hpa
        if self.eps > 0 and self.rng.random() < self.eps:
            d = int(self.rng.choice(D_REPS))
            if not in_bounds(d, s):
                d = 0
        return d, p


def shadow_actions(log: dict, factory) -> np.ndarray:
    """Replica delta the target would take at every logged step, (N, T).

    The target sees the logged metrics and state in order, so its internal state
    (scale-in counter, Holt level/trend) follows the logged history."""
    n, t_len = log["d_rep"].shape
    out = np.zeros((n, t_len), dtype=np.int8)
    for i in range(n):
        c = factory()
        c.reset()
        for t in range(t_len):
            out[i, t] = c.act(log["m"][i][t], log["s"][i][t])[0]
    return out
