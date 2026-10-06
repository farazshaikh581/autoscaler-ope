"""Off-policy estimators of a per-step mean outcome (SLA% or cost).

Inputs are (N, T) arrays: match = target delta equals logged delta, mu = behaviour
probability of the logged delta, r = outcome after the logged action. The targets
are deterministic, so the per-step ratio is rho = match / mu.

Convention for the self-normalised estimator: a step where every episode has
zero weight contributes 0 (no logged support for the target there).
"""
import numpy as np

TRUNC_K = (1, 2, 4, 8)


def ratios(match: np.ndarray, mu: np.ndarray) -> np.ndarray:
    return np.where(match, 1.0 / mu, 0.0)


def replay(rho, r):
    """Naive: the logged average, ignoring the policy change."""
    return float(r.mean())


def trajectory_is(rho, r):
    w = np.prod(rho, axis=1)
    return float(np.mean(w * r.mean(axis=1)))


def pdis(rho, r):
    w = np.cumprod(rho, axis=1)
    return float(np.mean(w * r))


def wpdis(rho, r):
    w = np.cumprod(rho, axis=1)
    den = w.sum(axis=0)
    num = (w * r).sum(axis=0)
    per_step = np.divide(num, den, out=np.zeros_like(num), where=den > 0)
    return float(per_step.mean())


def truncated_weights(rho, k):
    """w[t] = product of the ratios of decisions t-k+1 .. t."""
    w = rho.copy()
    for d in range(1, k):
        shifted = np.ones_like(rho)
        shifted[:, d:] = rho[:, :-d]
        w *= shifted
    return w


def tpdis(rho, r, k):
    return float(np.mean(truncated_weights(rho, k) * r))


def all_estimates(match, mu, r) -> dict:
    rho = ratios(match, mu)
    out = {"replay": replay(rho, r), "is": trajectory_is(rho, r),
           "pdis": pdis(rho, r), "wpdis": wpdis(rho, r)}
    for k in TRUNC_K:
        out[f"tpdis_k{k}"] = tpdis(rho, r, k)
    return out
