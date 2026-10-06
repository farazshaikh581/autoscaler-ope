"""M3: hybrid estimators.

  python run_m3.py --procs 8

Same logs as M1b/M2 (eps 0, 0.05, 0.1; 5 logging seeds; n = 200). Per log and target:
  replay, sntpdis_k4, mb_trees, mb_knee, dr_k2/4/8    as in M2
  mbcal_<model>   MB minus the model's mean bias on the behaviour's own trajectory
                  (the logged actions replayed through the model vs the logged outcomes)
  mbcalq_<model>  the same bias, estimated per quartile of logged load and subtracted
                  per step according to that step's load quartile
  drmb_k2/4/8     windowed DR anchored on the full-horizon MB value (trees)
The agreement switch (sntpdis/DR vs MB by action agreement) is decided in
analyse_m3.py, because its threshold is chosen on Azure and applied to Bitbrains.

Writes results/raw/m3_estimates.csv.gz.
"""
import argparse
import csv
import gzip
import os
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

from ope.estimators import all_estimates, ratios, step_weights
from ope.logger import collect, high_load_mask, logged_prob
from ope.mb import dr_mb_per_step, dr_per_step, mb_logged, shadow_with_snapshots, window_q
from ope.model import MODELS, training_data
from ope.sim import sim_commit, use_family
from run_m1b import CELLS, EPS as M1B_EPS, REPS, TARGETS, cell_key, log_seeds, paired_truth_job
from run_m2 import mb_all

EPS = (0.0, 0.05, 0.1)
DR_K = (2, 4, 8)
SCOPES = ("all", "high_load")
METRICS = ("sla", "cost")
HERE = os.path.dirname(os.path.abspath(__file__))


def bias_terms(pred, obs, load):
    """Mean model bias on the behaviour trajectory: overall, and per quartile of
    the logged load. Returns (overall, per-step bias by the step's quartile)."""
    diff = pred - obs
    edges = np.quantile(load, [0.25, 0.5, 0.75])
    qi = np.searchsorted(edges, load, side="right")
    per_q = np.array([diff[qi == b].mean() if (qi == b).any() else diff.mean() for b in range(4)])
    return float(diff.mean()), per_q[qi]


def job(args):
    cell, eps, rep, paired = args
    t0 = time.time()
    use_family(cell[0])
    dither_seed = (CELLS.index(cell), M1B_EPS.index(eps), rep)      # identical logs to M1b/M2
    log = collect(cell[2], eps, log_seeds(rep), dither_seed, cell[3])
    mu = logged_prob(log)
    hi = high_load_mask(log["load"])
    x, y = training_data(log)
    models = {k: M().fit(x, y) for k, M in MODELS.items()}
    mb = {k: mb_all(log, m) for k, m in models.items()}
    bias = {}
    for k, m in models.items():
        p_sla, p_cost = mb_logged(log, m)
        for met, pred in (("sla", p_sla), ("cost", p_cost)):
            bias[(k, met)] = bias_terms(pred, log[met], log["load"])
    rows = []
    for name, f in TARGETS.items():
        acts, snaps = shadow_with_snapshots(log, f)
        match = acts == log["d_rep"]
        rho = ratios(match, mu)
        wq = window_q(log, models["trees"], snaps, max(DR_K))
        per_step = {}
        for met in METRICS:
            idx = 0 if met == "sla" else 1
            for mk in MODELS:
                full = mb[mk][name][idx]
                b_all, b_q = bias[(mk, met)]
                per_step[(f"mb_{mk}", met)] = full
                per_step[(f"mbcal_{mk}", met)] = full - b_all
                per_step[(f"mbcalq_{mk}", met)] = full - b_q
            for k in DR_K:
                dr = dr_per_step(rho, log[met], wq[f"v_{met}"], wq[f"q_{met}"], k)
                per_step[(f"dr_k{k}", met)] = dr
                per_step[(f"drmb_k{k}", met)] = dr_mb_per_step(dr, wq[f"v_{met}"], k, mb["trees"][name][idx])
        for scope in SCOPES:
            mask = hi if scope == "high_load" else None
            q = step_weights(log["sla"], mask)
            sfx = "_hi" if scope == "high_load" else ""
            est = {}
            for met in METRICS:
                scale = 100.0 if met == "sla" else 1.0
                ie = all_estimates(match, mu, scale * log[met], mask)
                vals = {"replay": ie["replay"], "sntpdis_k4": ie["sntpdis_k4"]}
                for (e, m_), v in per_step.items():
                    if m_ == met:
                        vals[e] = float((scale * v * q).sum(axis=1).mean())
                est[met] = vals
            for e in est["sla"]:
                rows.append(dict(estimator=e, target=name, eps=eps, n_episodes=len(log["seeds"]), rep=rep,
                                 scope=scope, agreement=float(match.mean()),
                                 sla_estimate=est["sla"][e], cost_estimate=est["cost"][e],
                                 sla_truth_paired=float(paired[name]["sla" + sfx].mean()),
                                 cost_truth_paired=float(paired[name]["cost" + sfx].mean())))
    return cell_key(cell), eps, rep, rows, time.time() - t0


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
            print(f"[{k + 1}/{len(jobs)}] {o[0]} eps={o[1]} rep={o[2]} {o[4]:.0f}s", flush=True)
    unpaired = pd.read_csv(os.path.join(res, "m1b_truth.csv"))
    unpaired = unpaired[unpaired.truth == "unpaired"].set_index(["family", "workload", "target"])
    fields = ["family", "workload", "episode_len", "estimator", "target", "eps", "n_episodes", "rep", "scope",
              "agreement", "sla_estimate", "sla_truth_paired", "sla_abs_err", "sla_truth_unpaired",
              "cost_estimate", "cost_truth_paired", "cost_abs_err", "cost_rel_err_pct", "cost_truth_unpaired",
              "sim_commit"]
    with gzip.open(os.path.join(res, "raw", "m3_estimates.csv.gz"), "wt", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for key, eps, rep, rows, _ in out:
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
    print(f"wrote results in {time.time() - t0:.0f}s (sim commit {commit[:7]})")


if __name__ == "__main__":
    main()
