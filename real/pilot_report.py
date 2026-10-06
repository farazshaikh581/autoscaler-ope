"""M4 pilot gate report from real/runs (written by real/pilot.sh at the end).

  python real/pilot_report.py > real/runs/pilot_report.md
"""
import glob
import json
import os
import re

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "runs")
SIM = pd.read_csv(os.path.join(HERE, "windows_bitbrains_io-bound.csv")).set_index("start")
START = 4725
PERIOD = 15.0


def run_stats(tag):
    p = os.path.join(RUNS, f"{tag}.csv")
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p)
    pods = pd.read_csv(os.path.join(RUNS, f"{tag}_pods.csv"))
    gaps = 100 * (d.rps_achieved - d.rps_target) / d.rps_target
    step_dt = d.wall_s.diff().dropna()
    return dict(
        rows=len(d), sla_pct=100 * d.sla_ok.mean(), cost_vcpu=d.cost_vcpu.mean(),
        sla_pct_outcomes=100 * d.sla_ok.iloc[1:].mean(), cost_outcomes=d.cost_vcpu.iloc[1:].mean(),
        replicas_min=int(d.ready_replicas.min()), replicas_max=int(d.ready_replicas.max()),
        replicas_mean=d.ready_replicas.mean(), scale_actions=int((d.d_rep != 0).sum()),
        latency_p99_median_ms=d.latency_p99_ms.median(), success_min=d.success.min(),
        rps_gap_median_pct=gaps.median(), rps_gap_worst_pct=gaps.abs().max(),
        metrics_age_median_s=d.metrics_age_s.median(), metrics_age_p90_s=d.metrics_age_s.quantile(0.9),
        metrics_window_median_s=d.metrics_window_s.median(), cpu_nan_steps=int(d.cpu_used_m.isna().sum()),
        pending_steps=int(d.steps_to_ready.sum()), new_pods=len(pods),
        readiness_median_s=pods.readiness_delay_s.median() if len(pods) else np.nan,
        readiness_max_s=pods.readiness_delay_s.max() if len(pods) else np.nan,
        step_overruns=int((step_dt > PERIOD + 0.5).sum()), step_dt_max_s=step_dt.max(),
        act_s_max=d.act_s.max())


def main():
    print("# M4 pilot gate report (W1 = Bitbrains io-bound, start 4725)\n")
    lc = os.path.join(RUNS, "loadcheck.json")
    print("## (a) load generator at the windows' peaks (12 replicas, driver on even CPUs 0-14)\n")
    if os.path.exists(lc):
        for c in json.load(open(lc))["checks"]:
            print(f"- {c['rps_target']} rps: achieved {c['rps_achieved']} ({c['gap_pct']:+.1f}%), success "
                  f"{c['success']:.4f}, p99 {c['p99_ms']:.1f} ms; driver core busy mean max "
                  f"{max(c['core_busy_mean_pct'].values()):.1f}%, peak {max(c['core_busy_max_pct'].values()):.1f}% "
                  f"-> rate {'PASS' if c['pass_rate'] else 'FAIL'}, CPU {'PASS' if c['pass_cpu'] else 'FAIL'}")
    stats = {pol: run_stats(f"pilot_w1_{pol}") for pol in ("hpa70", "hpa95")}
    print("\n## (b) live SLA gap and (c) live vs simulation\n")
    print("| run | rows | live SLA% | sim SLA% | live cost vCPU | sim cost vCPU | replicas min-max (mean) | scale actions |")
    print("|---|---|---|---|---|---|---|---|")
    for pol, s in stats.items():
        if s is None:
            print(f"| {pol} | missing | | | | | | |")
            continue
        print(f"| W1 {pol} | {s['rows']} | {s['sla_pct']:.1f} | {SIM.loc[START, f'sla_{pol}']:.1f} | "
              f"{s['cost_vcpu']:.3f} | {SIM.loc[START, f'cost_{pol}']:.3f} | {s['replicas_min']}-{s['replicas_max']} "
              f"({s['replicas_mean']:.2f}) | {s['scale_actions']} |")
    if all(stats.values()):
        gap = stats["hpa70"]["sla_pct"] - stats["hpa95"]["sla_pct"]
        print(f"\nLive SLA gap HPA-70 minus HPA-95: {gap:.1f} points (sim: "
              f"{SIM.loc[START, 'sla_hpa70'] - SIM.loc[START, 'sla_hpa95']:.1f}) -> gate (b) "
              f"{'PASS' if gap >= 10 else 'FAIL'} (needs >= 10).")
        print("Rows log the window measured before each decision (one-step offset vs the simulator); "
              "on outcome-aligned rows 1-199: " + ", ".join(
                  f"{p} SLA {s['sla_pct_outcomes']:.1f}% cost {s['cost_outcomes']:.3f}" for p, s in stats.items()))
    print("\n## (d) metric lag and readiness delay\n")
    for pol, s in stats.items():
        if s:
            print(f"- {pol}: metrics-server sample age median {s['metrics_age_median_s']:.1f} s (p90 "
                  f"{s['metrics_age_p90_s']:.1f} s), averaging window {s['metrics_window_median_s']:.1f} s; "
                  f"new pods {s['new_pods']}, creation-to-Ready median {s['readiness_median_s']:.1f} s "
                  f"(max {s['readiness_max_s']:.1f} s); steps with a scale still pending {s['pending_steps']} "
                  f"(simulator: 2 steps per scale)")
    print("\n## (e) harness health\n")
    for pol, s in stats.items():
        if s:
            print(f"- {pol}: {s['rows']}/200 rows; achieved vs target rps median {s['rps_gap_median_pct']:+.1f}% "
                  f"(worst {s['rps_gap_worst_pct']:.1f}%); min window success {s['success_min']:.4f}; "
                  f"median window p99 {s['latency_p99_median_ms']:.1f} ms; steps without CPU metrics "
                  f"{s['cpu_nan_steps']}; step overruns > 15.5 s: {s['step_overruns']} (max step {s['step_dt_max_s']:.1f} s); "
                  f"max actuation time {s['act_s_max']:.2f} s")
    log = os.path.join(RUNS, "pilot.log")
    if os.path.exists(log):
        txt = open(log).read()
        errs = [l for l in txt.splitlines() if re.search(r"Traceback|Error|FAILED|warn", l)]
        print(f"- pilot.log: {len(errs)} error/warning lines" + ("" if not errs else ":\n  " + "\n  ".join(errs[:20])))


if __name__ == "__main__":
    main()
