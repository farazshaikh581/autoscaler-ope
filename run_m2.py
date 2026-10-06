"""M2: estimators for large policy changes.

  python run_m2.py --procs 8

Per log (same cells, seeds and dither seeds as M1b, so the logs are identical):
  replay, sntpdis_k4             importance-sampling reference points
  mb_trees, mb_knee              model-based replay: outcome model fitted to the
                                 log, target rolled forward on the logged load
  dr_k2, dr_k4, dr_k8            windowed per-decision DR, self-normalised weights,
                                 mb_trees as the baseline (n = 200 only)
MB is fitted and evaluated at n_episodes 10/50/200 (learning curve).

Writes results/raw/m2_estimates.csv.gz, results/raw/m2_vs_replay.csv.gz and
results/m2_model_fit.csv. Unpaired truth is the 2000-episode truth in
results/m1b_truth.csv (same simulator commit, deterministic).
"""
import argparse
import csv
import gzip
import os
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

from ope.estimators import all_estimates, per_episode_ratio_terms, ratios, step_weights
from ope.logger import collect, high_load_mask, logged_prob, subset
from ope.mb import _state, dr_per_step, rollout, shadow_with_snapshots, window_q
from ope.model import MODELS, training_data
from ope.sim import sim_commit, use_family
from run_m1b import CELLS, EPS as M1B_EPS, N_EPISODES, REPS, TARGETS, cell_key, log_seeds, paired_truth_job

EPS = (0.0, 0.05, 0.1)
DR_K = (2, 4, 8)
BOOT = 500
SCOPES = ("all", "high_load")
METRICS = ("sla", "cost")
HERE = os.path.dirname(os.path.abspath(__file__))


def mb_all(log, model):
    """MB rollout of every target from each episode start, in one batch.
    Returns {target: (sla (N,T), cost (N,T))}."""
    n, T = log["d_rep"].shape
    names = list(TARGETS)
    ctrls = []
    for name in names:
        for _ in range(n):
            c = TARGETS[name]()
            c.reset()
            ctrls.append(c)
    idx = [(i, 0) for i in range(n)]
    s0 = {k: np.tile(v, len(names)) for k, v in _state(log, idx).items()}
    m0 = [log["m"][i][0] for i in range(n)] * len(names)
    loads = np.tile(log["load"], (len(names), 1))
    sla, cost = rollout(model, ctrls, m0, s0, loads, np.ones_like(loads, bool))
    return {name: (sla[k * n:(k + 1) * n], cost[k * n:(k + 1) * n]) for k, name in enumerate(names)}


def job(args):
    cell, eps, rep, paired = args
    t0 = time.time()
    use_family(cell[0])
    dither_seed = (CELLS.index(cell), M1B_EPS.index(eps), rep)      # identical logs to M1b
    log = collect(cell[2], eps, log_seeds(rep), dither_seed, cell[3])
    mu_full = logged_prob(log)
    snaps, acts = {}, {}
    for name, f in TARGETS.items():
        acts[name], snaps[name] = shadow_with_snapshots(log, f)
    hi_full = high_load_mask(log["load"])
    rows, fits = [], []
    per_ep = {}                                    # n=200 per-episode terms for the bootstrap
    for n in N_EPISODES:
        sub = subset(log, n)
        mu = mu_full[:n]
        x, y = training_data(sub)
        models = {k: M().fit(x, y) for k, M in MODELS.items()}
        fits.append(dict(n_episodes=n, knee_fit_ok=models["knee"].fit_ok,
                         knee_lat=" ".join(f"{v:.4g}" for v in models["knee"].lat_p),
                         knee_suc=" ".join(f"{v:.4g}" for v in models["knee"].suc_p),
                         knee_rho_slope=models["knee"].h,
                         logged_replicas_min=int(sub["out"]["replicas"].min()),
                         logged_replicas_max=int(sub["out"]["replicas"].max())))
        mb = {k: mb_all(sub, m) for k, m in models.items()}
        dr = {}
        if n == max(N_EPISODES):
            for name in TARGETS:
                wq = window_q(sub, models["trees"], snaps[name], max(DR_K))
                rho = ratios(acts[name][:n] == sub["d_rep"], mu)
                for met in METRICS:
                    r = sub[met]
                    for k in DR_K:
                        dr[(name, met, k)] = dr_per_step(rho, r, wq[f"v_{met}"], wq[f"q_{met}"], k)
        for name in TARGETS:
            match = acts[name][:n] == sub["d_rep"]
            for scope in SCOPES:
                mask = hi_full[:n] if scope == "high_load" else None
                q = step_weights(sub["sla"], mask)
                sfx = "_hi" if scope == "high_load" else ""
                est = {}
                for met in METRICS:
                    scale = 100.0 if met == "sla" else 1.0
                    ie = all_estimates(match, mu, scale * sub[met], mask)
                    vals = {"replay": ie["replay"], "sntpdis_k4": ie["sntpdis_k4"]}
                    terms = {"replay": (scale * sub[met] * q).sum(axis=1)}
                    for mk in MODELS:
                        t_ep = (scale * mb[mk][name][0 if met == "sla" else 1] * q).sum(axis=1)
                        vals[f"mb_{mk}"] = float(t_ep.mean())
                        terms[f"mb_{mk}"] = t_ep
                    if dr:
                        for k in DR_K:
                            t_ep = (scale * dr[(name, met, k)] * q).sum(axis=1)
                            vals[f"dr_k{k}"] = float(t_ep.mean())
                            terms[f"dr_k{k}"] = t_ep
                    est[met] = vals
                    if n == max(N_EPISODES):
                        num, den = per_episode_ratio_terms(match, mu, scale * sub[met], mask)["sntpdis_k4"]
                        per_ep[(name, scope, met)] = (terms, num, den)
                for e in est["sla"]:
                    rows.append(dict(estimator=e, target=name, eps=eps, n_episodes=n, rep=rep, scope=scope,
                                     sla_estimate=est["sla"][e], cost_estimate=est["cost"][e],
                                     sla_truth_paired=float(paired[name]["sla" + sfx][:n].mean()),
                                     cost_truth_paired=float(paired[name]["cost" + sfx][:n].mean())))

    # Episode bootstrap at n = 200 of |err_est| - |err_replay|. Conditional on the
    # fitted models and on DR's normalising constants (both held fixed).
    rng = np.random.default_rng((77,) + dither_seed)
    n = max(N_EPISODES)
    idx = rng.integers(0, n, size=(BOOT, n))
    boot = {}
    for (name, scope, met), (terms, num, den) in per_ep.items():
        sfx = "_hi" if scope == "high_load" else ""
        truth_b = paired[name][met + sfx][idx].mean(axis=1)
        est_b = {e: v[idx].mean(axis=1) for e, v in terms.items()}
        dsum = den[idx].sum(axis=1)
        est_b["sntpdis_k4"] = np.divide(num[idx].sum(axis=1), dsum, out=np.zeros(BOOT), where=dsum > 0)
        base = np.abs(est_b["replay"] - truth_b)
        for e, v in est_b.items():
            if e != "replay":
                boot[(name, scope, met, e)] = np.abs(v - truth_b) - base
    return cell_key(cell), eps, rep, rows, boot, fits, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, default=8)
    args = ap.parse_args()
    commit = sim_commit()
    res = os.path.join(HERE, "results")
    os.makedirs(os.path.join(res, "raw"), exist_ok=True)
    t0 = time.time()
    with Pool(args.procs) as pool:
        paired = {}
        for key, rep, name, per_ep in pool.imap_unordered(
                paired_truth_job, [(c, rep, name) for c in CELLS for rep in range(REPS) for name in TARGETS]):
            paired.setdefault((key, rep), {})[name] = per_ep
        print(f"paired truth done {time.time() - t0:.0f}s", flush=True)
        jobs = [(c, e, rep, paired[(cell_key(c), rep)]) for c in CELLS for e in EPS for rep in range(REPS)]
        out = []
        for k, o in enumerate(pool.imap_unordered(job, jobs)):
            out.append(o)
            print(f"[{k + 1}/{len(jobs)}] {o[0]} eps={o[1]} rep={o[2]} {o[6]:.0f}s", flush=True)
    print(f"simulation done in {time.time() - t0:.0f}s", flush=True)

    unpaired = pd.read_csv(os.path.join(res, "m1b_truth.csv"))
    unpaired = unpaired[unpaired.truth == "unpaired"].set_index(["family", "workload", "target"])
    fields = ["family", "workload", "episode_len", "estimator", "target", "eps", "n_episodes", "rep", "scope",
              "sla_estimate", "sla_truth_paired", "sla_abs_err", "sla_truth_unpaired",
              "cost_estimate", "cost_truth_paired", "cost_abs_err", "cost_rel_err_pct", "cost_truth_unpaired",
              "sim_commit"]
    with gzip.open(os.path.join(res, "raw", "m2_estimates.csv.gz"), "wt", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for key, eps, rep, rows, _, _, _ in out:
            c = next(c for c in CELLS if cell_key(c) == key)
            for r in rows:
                u = unpaired.loc[(key[0], key[1], r["target"])]
                sfx = "_hi" if r["scope"] == "high_load" else ""
                cerr = abs(r["cost_estimate"] - r["cost_truth_paired"])
                w.writerow({**r, "family": key[0], "workload": key[1], "episode_len": c[3],
                            "sla_abs_err": abs(r["sla_estimate"] - r["sla_truth_paired"]),
                            "sla_truth_unpaired": u["sla" + sfx], "cost_abs_err": cerr,
                            "cost_rel_err_pct": 100 * cerr / r["cost_truth_paired"],
                            "cost_truth_unpaired": u["cost" + sfx], "sim_commit": commit})

    with gzip.open(os.path.join(res, "raw", "m2_vs_replay.csv.gz"), "wt", newline="") as f:
        cols = ["family", "workload", "target", "eps", "scope", "metric", "estimator",
                "diff_mean", "ci_lo", "ci_hi", "units", "boot", "sim_commit"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for c in CELLS:
            for e in EPS:
                outs = [o for o in out if o[0] == cell_key(c) and o[1] == e]
                for key in outs[0][4]:
                    name, scope, met, est = key
                    stack = np.stack([o[4][key] for o in outs])
                    point = []
                    for o in outs:
                        rs = {r["estimator"]: r for r in o[3] if r["target"] == name and r["scope"] == scope
                              and r["n_episodes"] == max(N_EPISODES)}
                        err = {k: abs(rs[k][met + "_estimate"] - rs[k][met + "_truth_paired"]) for k in (est, "replay")}
                        point.append(err[est] - err["replay"])
                    lo, hi = np.percentile(stack.mean(axis=0), [2.5, 97.5])
                    w.writerow(dict(family=c[0], workload=c[1], target=name, eps=e, scope=scope, metric=met,
                                    estimator=est, diff_mean=float(np.mean(point)), ci_lo=lo, ci_hi=hi,
                                    units="SLA points" if met == "sla" else "vCPU", boot=BOOT, sim_commit=commit))

    with open(os.path.join(res, "m2_model_fit.csv"), "w", newline="") as f:
        cols = ["family", "workload", "eps", "rep", "n_episodes", "knee_fit_ok", "knee_lat", "knee_suc",
                "knee_rho_slope", "logged_replicas_min", "logged_replicas_max", "sim_commit"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for key, eps, rep, _, _, fits, _ in out:
            for fi in fits:
                w.writerow(dict(family=key[0], workload=key[1], eps=eps, rep=rep, sim_commit=commit, **fi))
    print(f"wrote results in {time.time() - t0:.0f}s (sim commit {commit[:7]})")


if __name__ == "__main__":
    main()
