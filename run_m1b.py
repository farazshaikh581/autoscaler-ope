"""M1b: is there a regime where ignoring the policy change (replay) is badly wrong,
and does truncated PDIS fix it?

  python run_m1b.py --procs 8

Changes from M1: Azure and Bitbrains trace families; targets that differ more;
paired truth (each target on the logged episode starts) plus an unpaired
2000-episode truth; error relative to replay with episode-bootstrap 95% intervals;
high-load steps (top load quartile per episode) as a second scope.

Mixed traces are 199 points long in both families, so a 200-step episode always
starts at index 0. Those cells are dropped; mixed is run as an extra cell with
100-step episodes (98 distinct starts), labelled mixed_L100.
"""
import argparse
import csv
import os
import time
from multiprocessing import Pool

import numpy as np

from ope.estimators import (all_estimates, per_episode_ratio_terms, per_episode_terms, ratios,
                            step_weights, wpdis)
from ope.logger import collect, high_load_mask, logged_prob, subset
from ope.policies import SANITY_TARGETS, TARGETS_M1B, shadow_actions
from ope.sim import sim_commit, use_family
from ope.truth import TRUTH_SEED0, run_episodes, summarise

CELLS = [  # family, label, workload, episode_len, main (counts for the go/no-go headline)
    ("azure", "cpu-bound", "cpu-bound", 200, True),
    ("azure", "io-bound", "io-bound", 200, True),
    ("bitbrains", "cpu-bound", "cpu-bound", 200, True),
    ("bitbrains", "io-bound", "io-bound", 200, True),
    ("azure", "mixed_L100", "mixed", 100, False),
    ("bitbrains", "mixed_L100", "mixed", 100, False),
]
EPS = (0.0, 0.02, 0.05, 0.1, 0.2)
N_EPISODES = (10, 50, 200)
REPS = 5
UNPAIRED_EPISODES, UNPAIRED_CHUNK = 2000, 500
BOOT = 500
LOG_SEED0 = 10_000_000
TARGETS = {**TARGETS_M1B, **SANITY_TARGETS}
SCOPES = ("all", "high_load")
METRICS = ("sla", "cost")
HERE = os.path.dirname(os.path.abspath(__file__))


def log_seeds(rep):
    return [LOG_SEED0 + rep * 10_000 + i for i in range(max(N_EPISODES))]


def cell_key(c):
    return c[0], c[1]


def paired_truth_job(args):
    cell, rep, name = args
    use_family(cell[0])
    return cell_key(cell), rep, name, run_episodes(cell[2], TARGETS[name], log_seeds(rep), cell[3])


def unpaired_truth_job(args):
    cell, name, chunk = args
    use_family(cell[0])
    seeds = [TRUTH_SEED0 + chunk * UNPAIRED_CHUNK + i for i in range(UNPAIRED_CHUNK)]
    return cell_key(cell), name, run_episodes(cell[2], TARGETS[name], seeds, cell[3])


def log_job(args):
    cell, eps, rep, paired = args          # paired: {target: per-episode truth dict} for this rep
    use_family(cell[0])
    dither_seed = (CELLS.index(cell), EPS.index(eps), rep)
    log = collect(cell[2], eps, log_seeds(rep), dither_seed, cell[3])
    shadow = {name: shadow_actions(log, f) for name, f in TARGETS.items()}
    hi_full = high_load_mask(log["load"])
    rows = []
    for n in N_EPISODES:
        sub = subset(log, n)
        mu = logged_prob(sub)
        for name in TARGETS:
            match = shadow[name][:n] == sub["d_rep"]
            for scope in SCOPES:
                mask = hi_full[:n] if scope == "high_load" else None
                sfx = "_hi" if scope == "high_load" else ""
                est = {met: all_estimates(match, mu, (100.0 if met == "sla" else 1.0) * sub[met], mask)
                       for met in METRICS}
                for e in est["sla"]:
                    rows.append(dict(estimator=e, target=name, eps=eps, n_episodes=n, rep=rep, scope=scope,
                                     sla_estimate=est["sla"][e], cost_estimate=est["cost"][e],
                                     sla_truth_paired=float(paired[name]["sla" + sfx][:n].mean()),
                                     cost_truth_paired=float(paired[name]["cost" + sfx][:n].mean()),
                                     match_frac=float(match.mean())))

    # Episode bootstrap at n = 200 of |err_est| - |err_replay|, resampling logged
    # episodes together with their paired truth.
    rng = np.random.default_rng((99,) + dither_seed)
    n = max(N_EPISODES)
    idx = rng.integers(0, n, size=(BOOT, n))
    mu = logged_prob(log)
    boot = {}
    for name in TARGETS:
        match = shadow[name] == log["d_rep"]
        for scope in SCOPES:
            mask = hi_full if scope == "high_load" else None
            sfx = "_hi" if scope == "high_load" else ""
            for met in METRICS:
                r = (100.0 if met == "sla" else 1.0) * log[met]
                truth_b = paired[name][met + sfx][idx].mean(axis=1)
                terms = per_episode_terms(match, mu, r, mask)
                est_b = {e: v[idx].mean(axis=1) for e, v in terms.items()}
                for e, (num, den) in per_episode_ratio_terms(match, mu, r, mask).items():
                    dsum = den[idx].sum(axis=1)
                    est_b[e] = np.divide(num[idx].sum(axis=1), dsum, out=np.zeros(len(idx)), where=dsum > 0)
                rho, q = ratios(match, mu), step_weights(r, mask)
                est_b["wpdis"] = np.array([wpdis(rho[b], r[b], q[b]) for b in idx])
                base = np.abs(est_b["replay"] - truth_b)
                for e, v in est_b.items():
                    if e != "replay":
                        boot[(name, scope, met, e)] = np.abs(v - truth_b) - base
    beh = dict(eps=eps, rep=rep, sla=float(100 * log["sla"].mean()), cost=float(log["cost"].mean()))
    return cell_key(cell), rows, boot, beh


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, default=8)
    args = ap.parse_args()
    commit = sim_commit()
    res = os.path.join(HERE, "results")
    os.makedirs(res, exist_ok=True)
    t0 = time.time()
    with Pool(args.procs) as pool:
        unpaired_async = pool.map_async(unpaired_truth_job, [
            (c, name, k) for c in CELLS for name in TARGETS for k in range(UNPAIRED_EPISODES // UNPAIRED_CHUNK)])
        paired = {}
        for key, rep, name, per_ep in pool.imap_unordered(
                paired_truth_job, [(c, rep, name) for c in CELLS for rep in range(REPS) for name in TARGETS]):
            paired.setdefault((key, rep), {})[name] = per_ep
        print(f"paired truth done {time.time() - t0:.0f}s", flush=True)
        log_out = pool.map(log_job, [(c, e, rep, paired[(cell_key(c), rep)])
                                     for c in CELLS for e in EPS for rep in range(REPS)])
        print(f"logs done {time.time() - t0:.0f}s", flush=True)
        unpaired_parts = unpaired_async.get()
    print(f"simulation done in {time.time() - t0:.0f}s", flush=True)

    unpaired = {}
    for key, name, per_ep in unpaired_parts:
        acc = unpaired.setdefault((key, name), {k: [] for k in per_ep})
        for k, v in per_ep.items():
            acc[k].append(v)
    unpaired = {k: summarise({m: np.concatenate(v) for m, v in d.items()}) for k, d in unpaired.items()}

    with open(os.path.join(res, "m1b_truth.csv"), "w", newline="") as f:
        cols = ["family", "workload", "episode_len", "target", "truth", "episodes",
                "sla", "sla_se", "cost", "cost_se", "sla_hi", "sla_hi_se", "cost_hi", "cost_hi_se", "sim_commit"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for c in CELLS:
            for name in TARGETS:
                w.writerow(dict(family=c[0], workload=c[1], episode_len=c[3], target=name, truth="unpaired",
                                episodes=UNPAIRED_EPISODES, sim_commit=commit, **unpaired[(cell_key(c), name)]))
                for rep in range(REPS):
                    w.writerow(dict(family=c[0], workload=c[1], episode_len=c[3], target=name,
                                    truth=f"paired_rep{rep}", episodes=max(N_EPISODES), sim_commit=commit,
                                    **summarise(paired[(cell_key(c), rep)][name])))

    fields = ["family", "workload", "episode_len", "estimator", "target", "eps", "n_episodes", "rep", "scope",
              "sla_estimate", "sla_truth_paired", "sla_abs_err", "sla_truth_unpaired",
              "cost_estimate", "cost_truth_paired", "cost_abs_err", "cost_rel_err_pct", "cost_truth_unpaired",
              "match_frac", "sim_commit"]
    with open(os.path.join(res, "m1b_estimates.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for key, rows, _, _ in log_out:
            c = next(c for c in CELLS if cell_key(c) == key)
            for r in rows:
                u = unpaired[(key, r["target"])]
                sfx = "_hi" if r["scope"] == "high_load" else ""
                cost_err = abs(r["cost_estimate"] - r["cost_truth_paired"])
                w.writerow({**r, "family": key[0], "workload": key[1], "episode_len": c[3],
                            "sla_abs_err": abs(r["sla_estimate"] - r["sla_truth_paired"]),
                            "cost_abs_err": cost_err, "cost_rel_err_pct": 100 * cost_err / r["cost_truth_paired"],
                            "sla_truth_unpaired": u["sla" + sfx], "cost_truth_unpaired": u["cost" + sfx],
                            "sim_commit": commit})

    # |err_est| - |err_replay| at n = 200: mean over reps, 95% interval from the
    # episode bootstrap (each replicate averages one resample per rep).
    with open(os.path.join(res, "m1b_vs_replay.csv"), "w", newline="") as f:
        cols = ["family", "workload", "target", "eps", "scope", "metric", "estimator",
                "diff_mean", "ci_lo", "ci_hi", "units", "boot", "sim_commit"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for c in CELLS:
            for e in EPS:
                outs = [o for o in log_out if o[0] == cell_key(c) and o[3]["eps"] == e]
                for key in outs[0][2]:
                    name, scope, met, est = key
                    stack = np.stack([o[2][key] for o in outs])          # (REPS, BOOT)
                    point = []
                    for o in outs:
                        rs = [r for r in o[1] if r["target"] == name and r["scope"] == scope
                              and r["n_episodes"] == max(N_EPISODES) and r["estimator"] in (est, "replay")]
                        err = {r["estimator"]: abs(r[met + "_estimate"] - r[met + "_truth_paired"]) for r in rs}
                        point.append(err[est] - err["replay"])
                    lo, hi = np.percentile(stack.mean(axis=0), [2.5, 97.5])
                    w.writerow(dict(family=c[0], workload=c[1], target=name, eps=e, scope=scope, metric=met,
                                    estimator=est, diff_mean=float(np.mean(point)), ci_lo=lo, ci_hi=hi,
                                    units="SLA points" if met == "sla" else "vCPU", boot=BOOT, sim_commit=commit))

    with open(os.path.join(res, "m1b_dither_cost.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["family", "workload", "eps", "sla", "cost", "sla_change_vs_eps0",
                                          "cost_change_vs_eps0", "cost_change_pct", "episodes", "sim_commit"])
        w.writeheader()
        for c in CELLS:
            beh = [o[3] for o in log_out if o[0] == cell_key(c)]
            b0 = [b for b in beh if b["eps"] == 0.0]
            s0, c0 = np.mean([b["sla"] for b in b0]), np.mean([b["cost"] for b in b0])
            for e in EPS:
                bs = [b for b in beh if b["eps"] == e]
                s, cst = np.mean([b["sla"] for b in bs]), np.mean([b["cost"] for b in bs])
                w.writerow(dict(family=c[0], workload=c[1], eps=e, sla=s, cost=cst, sla_change_vs_eps0=s - s0,
                                cost_change_vs_eps0=cst - c0, cost_change_pct=100 * (cst - c0) / c0,
                                episodes=REPS * max(N_EPISODES), sim_commit=commit))
    print(f"wrote results/m1b_*.csv in {time.time() - t0:.0f}s (sim commit {commit[:7]})")


if __name__ == "__main__":
    main()
