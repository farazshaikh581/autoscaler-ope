"""Morning report for the overnight W1/W2 batch: live truth vs simulator, OPE
estimates from the live logs, the real-cluster gate, eps effect, caveats.

  taskset -c 16,18,...,38 nice -n 19 python real/overnight_report.py > real/runs/overnight_report.md

Works on a partial night: missing runs are reported as such. Pilot runs
pilot_w1_hpa70 / pilot_w1_hpa95 count as W1 truth runs when their harness.py blob
equals the overnight one (checked here and stated).
"""
import os
import subprocess
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, HERE)
from ope.estimators import all_estimates, ratios  # noqa: E402
from ope.logger import logged_prob  # noqa: E402
from ope.mb import dr_mb_per_step, dr_per_step, mb_estimate, mb_logged, shadow_with_snapshots, window_q  # noqa: E402
from ope.model import TreeModel, training_data  # noqa: E402
from ope.policies import REAL_TARGETS  # noqa: E402
from ope.sim import make_env, outcome, step_action, use_family  # noqa: E402
from realog import load_run, readiness_delay_steps, to_log, truth  # noqa: E402
from run_m3 import bias_terms  # noqa: E402

TARGETS = REAL_TARGETS
WINDOWS = {"w1": ("bitbrains", "io-bound", 4725), "w2": ("azure", "cpu-bound", 1200)}
ESTIMATORS = ["replay", "sntpdis_k4", "mb_trees", "mbcalq_trees", "drmb_k4"]
SLA_GATE, COST_GATE = 3.0, 15.0
PILOT_HARNESS_COMMIT = "c7e0679"


def blob(rev_path):
    return subprocess.run(["git", "-C", REPO, "rev-parse", rev_path], capture_output=True, text=True).stdout.strip()


def sim_value(window, name, steps=200):
    fam, wl, start = WINDOWS[window]
    use_family(fam)
    env = make_env(wl, steps)
    _, info = env.reset(seed=0, options={"start": start})
    c = TARGETS[name]()
    c.reset()
    m = info["metrics"]
    sla, cost = [], []
    for _ in range(steps):
        d = c.act(m, env._backend.s)[0]
        _, _, _, _, info = env.step(step_action(d))
        m = info["metrics"]
        ok, cst, _ = outcome(m, env._backend.s)
        sla.append(ok)
        cost.append(cst)
    return 100 * np.mean(sla), np.mean(cost)


def truth_runs(window):
    """{target: [DataFrame, ...]} of live runs of that target on the window."""
    out = {}
    for name in TARGETS:
        frames = []
        for tag in ([f"on_{window}_truth_{name}"] + ([f"pilot_{window}_{name}"] if window == "w1" else [])):
            r = load_run(tag)
            if r is not None and len(r[0]) >= 100:
                frames.append((tag, r[0]))
        if name == "hpa70":                       # eps = 0 logs are HPA-70 runs too
            for rep in (1, 2):
                r = load_run(f"on_{window}_log_eps0_r{rep}")
                if r is not None and len(r[0]) >= 100:
                    frames.append((f"on_{window}_log_eps0_r{rep}", r[0]))
        if frames:
            out[name] = frames
    return out


def estimate(log, delay):
    mu = logged_prob(log)
    model = TreeModel().fit(*training_data(log))
    p_sla, p_cost = mb_logged(log, model, delay)
    b = {"sla": bias_terms(p_sla, log["sla"], log["load"])[1], "cost": bias_terms(p_cost, log["cost"], log["load"])[1]}
    res = {}
    for name, f in TARGETS.items():
        acts, snaps = shadow_with_snapshots(log, f)
        match = acts == log["d_rep"]
        rho = ratios(match, mu)
        full = dict(zip(("sla", "cost"), mb_estimate(log, model, f, delay)))
        wq = window_q(log, model, snaps, 4, delay)
        row = {"agreement": float(match.mean())}
        for met in ("sla", "cost"):
            scale = 100.0 if met == "sla" else 1.0
            ie = all_estimates(match, mu, scale * log[met])
            dr = dr_per_step(rho, log[met], wq[f"v_{met}"], wq[f"q_{met}"], 4)
            row[(met, "replay")] = ie["replay"]
            row[(met, "sntpdis_k4")] = ie["sntpdis_k4"]
            row[(met, "mb_trees")] = scale * full[met].mean()
            row[(met, "mbcalq_trees")] = scale * (full[met] - b[met]).mean()
            row[(met, "drmb_k4")] = scale * dr_mb_per_step(dr, wq[f"v_{met}"], 4, full[met]).mean()
        res[name] = row
    return res


def main():
    print("# Overnight OPE report (saul, real cluster)\n")
    cur, pilot = blob("HEAD:real/harness.py"), blob(f"{PILOT_HARNESS_COMMIT}:real/harness.py")
    print(f"harness.py blob now {cur[:10]}, at the pilot ({PILOT_HARNESS_COMMIT}) {pilot[:10]}: "
          f"{'identical, so the pilot runs count as W1 truth runs' if cur == pilot else 'DIFFERENT, pilot runs excluded'}.\n")
    idx = os.path.join(HERE, "runs", "overnight_index.csv")
    if os.path.exists(idx):
        ix = pd.read_csv(idx)
        print(f"Runs in the batch: {len(ix)} attempted, {int((ix.exit_code == 0).sum())} exit 0. "
              f"Failed: {', '.join(ix[ix.exit_code != 0].tag) or 'none'}.\n")
    for window in ("w1", "w2"):
        fam, wl, start = WINDOWS[window]
        print(f"## {window.upper()}: {fam} {wl}, start {start}\n")
        tr = truth_runs(window)
        if cur != pilot:
            tr = {k: [(t, d) for t, d in v if not t.startswith("pilot")] for k, v in tr.items()}
            tr = {k: v for k, v in tr.items() if v}
        print("### 1. Live truth vs simulator (same window)\n")
        print("| target | live runs | live SLA% | live cost vCPU | sim SLA% | sim cost vCPU |")
        print("|---|---|---|---|---|---|")
        live = {}
        for name in TARGETS:
            s_sla, s_cost = sim_value(window, name)
            if name in tr:
                vals = [truth(d) for _, d in tr[name]]
                live[name] = dict(sla=np.mean([v["sla"] for v in vals]), cost=np.mean([v["cost"] for v in vals]),
                                  runs=len(vals), sla_list=[round(v["sla"], 1) for v in vals])
                print(f"| {name} | {len(vals)} ({', '.join(t for t, _ in tr[name])}) | {live[name]['sla']:.1f}"
                      f"{' ' + str(live[name]['sla_list']) if len(vals) > 1 else ''} | {live[name]['cost']:.3f} | "
                      f"{s_sla:.1f} | {s_cost:.3f} |")
            else:
                print(f"| {name} | not run | | | {s_sla:.1f} | {s_cost:.3f} |")
        logs = {}
        for eps in ("0.1", "0"):
            frames = [load_run(f"on_{window}_log_eps{eps}_r{rep}") for rep in (1, 2)]
            frames = [f[0] for f in frames if f is not None and len(f[0]) >= 100]
            if frames:
                logs[eps] = frames
        if not logs:
            print("\nNo log runs for this window yet.\n")
            continue
        print("\n### 2. Estimates from the live logs (error vs live truth)\n")
        results = {}
        for eps, frames in logs.items():
            delay, share, n_scale = readiness_delay_steps(frames)
            log = to_log(frames)
            results[eps] = estimate(log, delay)
            print(f"**eps = {eps}**: {len(frames)} log run(s) x {log['d_rep'].shape[1]} decisions; readiness delay "
                  f"{delay} step(s) ({share:.0%} of {n_scale} scale decisions visible at the next window); "
                  f"replay SLA {100 * log['sla'].mean():.1f}%.\n")
            print("| target | agreement | " + " | ".join(f"{e} SLA err" for e in ESTIMATORS) + " | "
                  + " | ".join(f"{e} cost err %" for e in ESTIMATORS) + " |")
            print("|---|---|" + "---|" * (2 * len(ESTIMATORS)))
            for name, row in results[eps].items():
                if name not in live:
                    continue
                se = [abs(row[("sla", e)] - live[name]["sla"]) for e in ESTIMATORS]
                ce = [100 * abs(row[("cost", e)] - live[name]["cost"]) / live[name]["cost"] for e in ESTIMATORS]
                print(f"| {name} | {row['agreement']:.2f} | " + " | ".join(f"{v:.1f}" for v in se) + " | "
                      + " | ".join(f"{v:.1f}" for v in ce) + " |")
            print()
        print("### 3. Real-cluster gate (cells where replay misses: >= 3 SLA pts or >= 15% cost)\n")
        for eps, res in results.items():
            for est in ("mbcalq_trees", "drmb_k4"):
                miss, fixed = [], []
                for name, row in res.items():
                    if name not in live or name == "hpa70":
                        continue
                    rs = abs(row[("sla", "replay")] - live[name]["sla"])
                    rc = 100 * abs(row[("cost", "replay")] - live[name]["cost"]) / live[name]["cost"]
                    if rs >= SLA_GATE or rc >= COST_GATE:
                        es = abs(row[("sla", est)] - live[name]["sla"])
                        ec = 100 * abs(row[("cost", est)] - live[name]["cost"]) / live[name]["cost"]
                        miss.append(name)
                        if es <= SLA_GATE and ec <= COST_GATE:
                            fixed.append(name)
                print(f"- eps={eps}, {est}: replay misses {len(miss)} target(s) {miss}; {est} brings "
                      f"{len(fixed)} within 3 pts / 15% {fixed}" + (" -> ALL" if miss and len(fixed) == len(miss) else ""))
        if "0" in results and "0.1" in results:
            print("\n### 4. Does eps = 0.1 change MB's accuracy on the real cluster?\n")
            for est in ("mb_trees", "mbcalq_trees", "drmb_k4"):
                d0, d1 = [], []
                for name in results["0"]:
                    if name in live and name != "hpa70":
                        d0.append(abs(results["0"][name][("sla", est)] - live[name]["sla"]))
                        d1.append(abs(results["0.1"][name][("sla", est)] - live[name]["sla"]))
                if d0:
                    print(f"- {est}: median |SLA err| eps=0 {np.median(d0):.2f}, eps=0.1 {np.median(d1):.2f}; "
                          f"max {max(d0):.2f} vs {max(d1):.2f} (over {len(d0)} targets)")
        print("\n### 5. Caveats\n")
        print(f"- Log episodes: {', '.join(f'eps={e}: {len(f)}' for e, f in logs.items())} run(s) of 199 decisions "
              "(simulation used 200 episodes).")
        for eps in logs:
            if len(logs[eps]) == 2:
                a, b = (truth(f) for f in logs[eps])
                print(f"- Run-to-run variability, eps={eps} r1 vs r2: SLA {a['sla']:.1f} vs {b['sla']:.1f}, "
                      f"cost {a['cost']:.3f} vs {b['cost']:.3f}")
        if "hpa70" in live and live["hpa70"]["runs"] > 1:
            print(f"- HPA-70 repeated runs (pilot and eps=0 logs): SLA {live['hpa70']['sla_list']}")
        print("- Truth for the other targets is a single live run each, so its own noise is not estimated.")
        print("- Real vs simulator: CPU limit = request = 200m as in the sim calibration; load windows hard-stopped at 12 s (unfinished requests fail); readiness within one step "
              "(sim: 2); load is windowed (12 s on, ~3 s off); CPU comes from metrics-server with a 10-25 s lag "
              "and a ~15 s window; latency is real HTTP latency; 4 workers schedulable; one trace window per workload.\n")


if __name__ == "__main__":
    main()
