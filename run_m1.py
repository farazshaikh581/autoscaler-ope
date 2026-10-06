"""M1 experiment driver: log the dithered HPA, estimate every target off-policy,
compare with on-policy ground truth.

  python run_m1.py --procs 8

Writes results/m1_estimates.csv, results/m1_dither_cost.csv, results/m1_truth.csv.
Every row carries the simulator commit (sim_commit).
"""
import argparse
import csv
import os
import time
from multiprocessing import Pool

import numpy as np

from ope.estimators import all_estimates
from ope.logger import collect, logged_prob, subset
from ope.policies import SANITY_TARGETS, TARGETS
from ope.sim import WORKLOADS, sim_commit
from ope.truth import run_on_policy

EPS = (0.0, 0.02, 0.05, 0.1, 0.2)
N_EPISODES = (10, 50, 200)
REPS = 5
TRUTH_EPISODES = 200
LOG_SEED0 = 10_000_000        # episode seed = LOG_SEED0 + rep*10_000 + i (same starts for every eps)
ALL_TARGETS = {**TARGETS, **SANITY_TARGETS}
HERE = os.path.dirname(os.path.abspath(__file__))


def log_job(args):
    wl, eps, rep = args
    seeds = [LOG_SEED0 + rep * 10_000 + i for i in range(max(N_EPISODES))]
    log = collect(wl, eps, seeds, dither_seed=(WORKLOADS.index(wl), EPS.index(eps), rep))
    from ope.policies import shadow_actions
    shadow = {name: shadow_actions(log, f) for name, f in ALL_TARGETS.items()}
    rows = []
    for n in N_EPISODES:
        sub = subset(log, n)
        mu = logged_prob(sub)
        for name in ALL_TARGETS:
            match = shadow[name][:n] == sub["d_rep"]
            est_sla = all_estimates(match, mu, 100.0 * sub["sla"])
            est_cost = all_estimates(match, mu, sub["cost"])
            for est in est_sla:
                rows.append(dict(estimator=est, target=name, workload=wl, eps=eps, n_episodes=n,
                                 rep=rep, sla_estimate=est_sla[est], cost_estimate=est_cost[est],
                                 match_frac=float(match.mean())))
    beh = dict(workload=wl, eps=eps, rep=rep, sla=float(100 * log["sla"].mean()),
               cost=float(log["cost"].mean()), dithered_frac=float(
                   (log["d_rep"] != shadow["hpa70"]).mean()))
    return rows, beh


def truth_job(args):
    wl, name = args
    return dict(workload=wl, target=name, **run_on_policy(wl, ALL_TARGETS[name], TRUTH_EPISODES))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, default=8)
    args = ap.parse_args()
    commit = sim_commit()
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    t0 = time.time()
    with Pool(args.procs) as pool:
        truth_async = pool.map_async(truth_job, [(wl, n) for wl in WORKLOADS for n in ALL_TARGETS])
        log_out = pool.map(log_job, [(wl, e, r) for wl in WORKLOADS for e in EPS for r in range(REPS)])
        truth = truth_async.get()
    print(f"simulation done in {time.time() - t0:.0f}s")

    tmap = {(t["workload"], t["target"]): t for t in truth}
    with open(os.path.join(HERE, "results", "m1_truth.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["workload", "target", "sla", "sla_se", "cost", "cost_se",
                                          "episodes", "sim_commit"])
        w.writeheader()
        for t in truth:
            w.writerow({**t, "episodes": TRUTH_EPISODES, "sim_commit": commit})

    fields = ["estimator", "target", "workload", "eps", "n_episodes", "rep", "sla_estimate",
              "sla_truth", "sla_abs_err", "cost_estimate", "cost_truth", "cost_abs_err",
              "match_frac", "sim_commit"]
    with open(os.path.join(HERE, "results", "m1_estimates.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for rows, _ in log_out:
            for r in rows:
                tr = tmap[(r["workload"], r["target"])]
                w.writerow({**r, "sla_truth": tr["sla"], "sla_abs_err": abs(r["sla_estimate"] - tr["sla"]),
                            "cost_truth": tr["cost"], "cost_abs_err": abs(r["cost_estimate"] - tr["cost"]),
                            "sim_commit": commit})

    beh = [b for _, b in log_out]
    with open(os.path.join(HERE, "results", "m1_dither_cost.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["workload", "eps", "sla", "sla_sd_reps", "cost", "cost_sd_reps",
                                          "sla_drop_vs_eps0", "cost_change_vs_eps0", "dithered_frac",
                                          "episodes", "sim_commit"])
        w.writeheader()
        for wl in WORKLOADS:
            base = [b for b in beh if b["workload"] == wl and b["eps"] == 0.0]
            base_sla, base_cost = np.mean([b["sla"] for b in base]), np.mean([b["cost"] for b in base])
            for e in EPS:
                bs = [b for b in beh if b["workload"] == wl and b["eps"] == e]
                sla, cost = np.mean([b["sla"] for b in bs]), np.mean([b["cost"] for b in bs])
                w.writerow(dict(workload=wl, eps=e, sla=sla, sla_sd_reps=np.std([b["sla"] for b in bs], ddof=1),
                                cost=cost, cost_sd_reps=np.std([b["cost"] for b in bs], ddof=1),
                                sla_drop_vs_eps0=base_sla - sla, cost_change_vs_eps0=cost - base_cost,
                                dithered_frac=np.mean([b["dithered_frac"] for b in bs]),
                                episodes=REPS * max(N_EPISODES), sim_commit=commit))
    print(f"wrote results/ in {time.time() - t0:.0f}s (sim commit {commit[:7]})")


if __name__ == "__main__":
    main()
