# M5: held-out validation of the demand-space twin (saul)

Fixed before any M5 run. The estimator is `ope/twin.py` as committed with this file;
it is not changed during or after the batch. Analysis: `real/m5_report.py`.

## Why

The overnight M4 batch (`real/runs/overnight_report.md`) showed:

- replay misses every W1 target, by up to 63 SLA points and 545% cost;
- the M3 estimators fix the large misses but not to within 3 points / 15%
  (best: drmb_k4 at eps 0.1, 3 of 8 targets; median SLA error 3.8);
- the cause is coverage: 4 of 8 targets spend 60-65% of their steps in
  (replicas, load) cells the HPA-70 logs never visit;
- measured utilisation saturates at about 0.85 while per-pod demand goes to 4x,
  and the SLA collapses at demand 0.8-0.9 (measured utilisation about 0.69);
- a single truth run is noisy: two HPA-70 runs gave 67.3% and 61.3% SLA.

## Estimator

Rollout of the target's own controller in per-pod demand coordinates
(D = rps x 1.727 m / (ready x 200m)), with logged steps as donors matched on
(log D, log D at t-1, replica change), rho rescaled with D below D = 0.7, and
one-step readiness. 40 rollouts give the point estimate and a single-run 90%
prediction interval. Rollouts with measured rho shifted by -0.03 and +0.03 give
the sensitivity interval, which shows targets whose decisions sit on a threshold.
Donors are all four log runs of the same window (eps 0.1 and eps 0).

Development on W1 (looking at its truth): median SLA error 0.4, max 10.3, median
cost error 3.3%, 4/8 targets within 3 points and 15%. W2's HPA-70 sanity row: twin
78.6% vs truth 77.6% (mbcalq 18.6, drmb_k4 13.3 off).

## Runs (`real/m5.sh`, 28 x about 52 min = about 24 h)

| Block | Runs |
|---|---|
| W2 (Azure cpu-bound 1200) truth: hpa30, hpa50, hpa85, hpa95, hpa70_stab0, hpa70_stab10, slo_cost, pred70 | 8 |
| W3 (Bitbrains cpu-bound 950, new): logs eps 0.1 x 2 and eps 0 x 2 | 4 |
| W3 truth: the same 8 targets | 8 |
| W1 truth, second rep (`_r2`): the same 8 targets | 8 |

W3 is the most variable 200-step Bitbrains cpu-bound window with peak <= 1500 rps
and mean >= 300 rps (peak 960, mean 471). Same harness as the overnight batch
(CPU limit = request = 200m, hard 12 s load windows, rho over serving pods).

## Criteria (held-out cells: W2 and W3, 8 targets each; hpa70 excluded)

- **P1:** twin median |SLA error| <= 3 points and median cost error <= 10%.
- **P2:** twin beats the best non-replay baseline (sntpdis_k4, mbcalq_trees,
  drmb_k4 at either eps) on median |SLA error| and on the count of cells within
  3 points and 15% cost.
- **P3:** live truth inside the twin's sensitivity interval in >= 80% of cells.

Also reported, not gated:
- the same table for W1 with truth averaged over two runs;
- run-to-run spread of every repeated target;
- each baseline's numbers.

If a criterion fails, it is reported as failed. Any later change to the twin is
new development and needs new held-out runs.
