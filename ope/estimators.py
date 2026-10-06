"""Off-policy estimators of a per-step mean outcome (SLA% or cost).

Inputs are (N, T) arrays: match = target delta equals logged delta, mu = behaviour
probability of the logged delta, r = outcome after the logged action. The targets
are deterministic, so the per-step ratio is rho = match / mu.

Convention for the self-normalised estimator: a step where every episode has
zero weight contributes 0 (no logged support for the target there).

An optional (N, T) 0/1 mask restricts the estimand to a subset of steps (e.g. the
high-load steps): the target is each episode's mean outcome over its masked steps,
averaged over episodes. Internally the mask becomes per-step weights q that sum to
1 within each episode; with no mask q = 1/T and every estimator reduces to its
plain per-step-mean form.
"""
import numpy as np

TRUNC_K = (1, 2, 4, 8)


def ratios(match: np.ndarray, mu: np.ndarray) -> np.ndarray:
    return np.where(match, 1.0 / mu, 0.0)


def step_weights(r, mask):
    m = np.ones_like(r) if mask is None else mask.astype(float)
    return m / m.sum(axis=1, keepdims=True)


def replay(rho, r, q):
    """Naive: the logged average, ignoring the policy change."""
    return float((r * q).sum() / len(r))


def trajectory_is(rho, r, q):
    return float(np.mean(np.prod(rho, axis=1) * (r * q).sum(axis=1)))


def pdis(rho, r, q):
    return float((np.cumprod(rho, axis=1) * r * q).sum() / len(r))


def wpdis(rho, r, q):
    w = np.cumprod(rho, axis=1) * q
    den = w.sum(axis=0)
    num = (w * r).sum(axis=0)
    per_step = np.divide(num, den, out=np.zeros_like(num), where=den > 0)
    return float((per_step * q.sum(axis=0)).sum() / len(r))


def truncated_weights(rho, k):
    """w[t] = product of the ratios of decisions t-k+1 .. t."""
    w = rho.copy()
    for d in range(1, k):
        shifted = np.ones_like(rho)
        shifted[:, d:] = rho[:, :-d]
        w *= shifted
    return w


def tpdis(rho, r, q, k):
    return float((truncated_weights(rho, k) * r * q).sum() / len(r))


def sn_tpdis(rho, r, q, k):
    """Self-normalised truncated PDIS: the truncated weights rescaled to mean 1, so a
    weight deficit in a finite sample does not shrink the estimate towards 0."""
    w = truncated_weights(rho, k) * q
    return float((w * r).sum() / w.sum()) if w.sum() > 0 else 0.0


def all_estimates(match, mu, r, mask=None) -> dict:
    rho, q = ratios(match, mu), step_weights(r, mask)
    out = {"replay": replay(rho, r, q), "is": trajectory_is(rho, r, q),
           "pdis": pdis(rho, r, q), "wpdis": wpdis(rho, r, q)}
    for k in TRUNC_K:
        out[f"tpdis_k{k}"] = tpdis(rho, r, q, k)
    for k in TRUNC_K:
        out[f"sntpdis_k{k}"] = sn_tpdis(rho, r, q, k)
    return out


def per_episode_terms(match, mu, r, mask=None) -> dict:
    """For every estimator except weighted PDIS, the estimate is the mean over
    episodes of a per-episode term; returns {name: terms (N,)} so episodes can be
    resampled cheaply (bootstrap)."""
    rho, q = ratios(match, mu), step_weights(r, mask)
    out = {"replay": (r * q).sum(axis=1),
           "is": np.prod(rho, axis=1) * (r * q).sum(axis=1),
           "pdis": (np.cumprod(rho, axis=1) * r * q).sum(axis=1)}
    for k in TRUNC_K:
        out[f"tpdis_k{k}"] = (truncated_weights(rho, k) * r * q).sum(axis=1)
    return out


def per_episode_ratio_terms(match, mu, r, mask=None) -> dict:
    """Self-normalised truncated PDIS as sum(num) / sum(den) over episodes."""
    rho, q = ratios(match, mu), step_weights(r, mask)
    out = {}
    for k in TRUNC_K:
        w = truncated_weights(rho, k) * q
        out[f"sntpdis_k{k}"] = ((w * r).sum(axis=1), w.sum(axis=1))
    return out
