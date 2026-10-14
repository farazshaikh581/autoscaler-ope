# M4 run plan: OPE on saul's real cluster (proposal, nothing run yet)

Preconditions: E1 has finished (its EXIT trap restores the stock VPA profile and
uncordons the workers), AND the go is given. `harness.py --live` refuses to start
while E1's runner is alive or any HPA/VPA object exists in hv-phase0.

## Harness (`real/harness.py`)

- Every 15 s it does one control step:
  1. Drive the CPU-burn web-service at rps = load_frac x cpu_intensity x 2050
     for 12 s (`real/windowload.py`: the `phase1/loadgen.py` pacing with a hard
     window end; request timeouts are capped at the time left in the window and
     unfinished requests count as failures, so a saturated step stays within 15 s).
  2. Read ready and requested replicas (`kubectl get deploy`) and pod CPU
     (`kubectl top`).
  3. Let the policy decide, seeing the same m / s fields as in the simulator.
  4. `kubectl scale` within 1-12 replicas if the decision changes the count.
- max_rps 2050 = node0's 1200 x 205/120, so per-pod CPU matches node0 and the
  simulator's calibration. (Later note: the value stands on saul alone. The knee check
  gives 1.727 mcores per request, so a 200m pod saturates near 116 rps and the windows
  need 8-12 pods at peak; see the harness docstring.)
- Policies:
  - `dithered`: the logging policy, HPA u = 0.7, stabilisation 3, eps dither;
    logs exact action probabilities.
  - Any target name (hpa30/50/85/95, hpa70_stab0/10, slo_cost, pred70, hpa70) for
    ground-truth runs. Same controller code as the simulator. On the real cluster
    hpa85 replaces the simulation's hpa90 on both windows.
  - **hpa95 under limit = request with 12 s windows** (smoke `smoke_hard2_w1_hpa95`,
    W1, 20 steps): measured utilisation stays at 0.70-0.93 of the request while the
    service is saturated (success 0.25-0.6, mean latency 280-820 ms), because CPU
    is capped at the limit and the 12 s on / 3 s off load and metrics-server's
    averaging pull the reading down. HPA-95's scale-up threshold is 0.95 x 1.1 =
    1.045, which is never reached. It scaled in once (2 -> 1 after 3 steps below
    0.855) and then stayed at 1 replica with rho 0.77-0.93 to the end. It has no
    real signal to scale back up.
- web-service runs with CPU limit = request = 200m for OPE runs (the simulator's
  knee calibration). The harness refuses to start otherwise and records the limit.
  Knee check: latency midpoint at demand rho 0.944 (sim 0.91), 20 ms SLA crossed
  at 0.900 (`real/runs/kneecheck.json`).
- Per-step log, one CSV plus a JSON of metadata per run under `real/runs/`:
  - trace step and load;
  - target and achieved rps, request count;
  - mean, p50, p95 and p99 latency, success;
  - CPU used, rho, cpu_util;
  - ready and requested replicas, cpu_req, pending flag;
  - SLA ok, cost;
  - action and the three action probabilities;
  - actuation time.
- The window at step t+1 is the outcome of the action at step t.
- Dry-run (default) puts the simulator in the cluster's place and prints the
  kubectl commands. HPA-95 on W1 gives 30.0% SLA / 1.299 vCPU, against 30.5% /
  1.306 from the simulator. The difference is the documented one-step offset
  (rows log the window before acting).

## Trace windows (`real/pick_windows.py`, `real/windows_*.csv`)

| | W1 | W2 |
|---|---|---|
| Trace | Bitbrains io-bound, start 4725 | Azure cpu-bound, start 1200 |
| Simulated SLA% | HPA-70 91.0, HPA-30 94.5, HPA-90 49.5, HPA-95 30.5, SLO-cost 64.5 | HPA-70 87.5, HPA-30 93.5, HPA-90 79.5, HPA-95 77.0, SLO-cost 86.0 |
| Simulated cost (vCPU) | 1.31-2.28 | 0.67-1.29 |
| Peak / mean rps at saul's scale | 958 / 605 | 1253 / 237 |

- W1 is the largest HPA-70 vs HPA-95 gap with peak <= 1500 rps; it gives the
  "replay badly wrong" case.
- W2 is the largest HPA-30 vs HPA-95 cost gap with mean >= 150 rps; it gives a
  moderate-shift case.

## Runs

Each run is 200 steps x 15 s = 50 min, plus about 3 min reset and settle (scale to
2, wait for ready, 60 s idle), so about 53 min.

| Block | Runs | Cluster time |
|---|---|---|
| Pilot: load-generator check at 958 and 1253 rps (2 min each), then W1 with HPA-70 and HPA-95 once each | 2 | about 2 h |
| Per window, logs: dithered at eps 0 x 2 seeds and eps 0.1 x 2 seeds | 4 | 3.5 h |
| Per window, truth: 8 targets x 1 (HPA-70's truth is the eps-0 logs) | 8 | 7.1 h |
| Per window, optional second truth rep | 8 | 7.1 h |

Totals:
- pilot plus both windows, one truth rep: about 23 h;
- with two truth reps: about 37 h.

Runs are sequential and unattended (a queue script will be written at the go).

**Pilot gate.** Proceed to the full plan only if:
- the load generator reaches the window's peak rate with success >= 0.99 while
  unsaturated; and
- on W1 the real HPA-70 vs HPA-95 SLA gap is >= 10 points.

Otherwise re-pick the window or the rps scale before spending 20+ h.

## Known differences from the simulator (why M4 matters)

- **Capacity:** with the 500m limit pods burst to 2.5x the request and the first
  pilot showed no SLA gap (both 100%); OPE runs therefore use limit = request.
- **Readiness delay:** the image is cached, so it may be shorter than the
  simulator's 2 steps. It is measured from the logs (ready vs requested).
- **Load gaps and CPU lag:** the load is windowed (12 s on, about 3 s off), and
  `kubectl top` lags (metrics-server resolution), so the HPA's utilisation
  signal is noisier and later than in the simulator.
- **Episode count:** only 2 logged episodes per eps (vs 200 in simulation).
  IS-type estimators will be noisy. MB is fitted on about 800 logged steps. If
  the pilot looks good, the plan can trade length for count (e.g. 4 x 100-step
  runs).
- **Topology:** Phase 0's 2-worker topology (k8s-worker3/4 cordoned) keeps
  results comparable with node0. (Later note: every OPE live run used all four workers
  schedulable, as each run's metadata records.) With 6 vCPU on k8s-worker1/2, 12 replicas x
  500m fit.
