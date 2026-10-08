# Overnight OPE report (saul, real cluster)

harness.py blob now 6d3b791c67, at the pilot (c7e0679) f616a33c5c: DIFFERENT, pilot runs excluded.

Runs in the batch: 16 attempted, 16 exit 0. Failed: none.

## W1: bitbrains io-bound, start 4725

### 1. Live truth vs simulator (same window)

| target | live runs | live SLA% | live cost vCPU | sim SLA% | sim cost vCPU |
|---|---|---|---|---|---|
| hpa30 | 1 (on_w1_truth_hpa30) | 98.5 | 2.199 | 94.5 | 2.283 |
| hpa50 | 1 (on_w1_truth_hpa50) | 98.5 | 1.839 | 94.5 | 2.031 |
| hpa95 | 1 (on_w1_truth_hpa95) | 0.0 | 0.208 | 30.5 | 1.306 |
| hpa70_stab0 | 1 (on_w1_truth_hpa70_stab0) | 38.7 | 1.220 | 86.5 | 1.657 |
| hpa70_stab10 | 1 (on_w1_truth_hpa70_stab10) | 74.4 | 1.389 | 93.0 | 1.800 |
| slo_cost | 1 (on_w1_truth_slo_cost) | 0.0 | 0.400 | 64.5 | 1.452 |
| pred70 | 1 (on_w1_truth_pred70) | 65.8 | 1.362 | 90.0 | 1.689 |
| hpa85 | 1 (on_w1_truth_hpa85) | 0.0 | 0.536 | 65.5 | 1.447 |
| hpa70 | 2 (on_w1_log_eps0_r1, on_w1_log_eps0_r2) | 64.3 [67.3, 61.3] | 1.344 | 91.0 | 1.756 |

### 2. Estimates from the live logs (error vs live truth)

**eps = 0.1**: 2 log run(s) x 199 decisions; readiness delay 1 step(s) (99% of 111 scale decisions visible at the next window); replay SLA 62.6%.

| target | agreement | replay SLA err | sntpdis_k4 SLA err | mb_trees SLA err | mbcalq_trees SLA err | drmb_k4 SLA err | replay cost err % | sntpdis_k4 cost err % | mb_trees cost err % | mbcalq_trees cost err % | drmb_k4 cost err % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hpa30 | 0.18 | 35.9 | 14.7 | 11.1 | 5.8 | 11.3 | 38.9 | 5.6 | 6.6 | 6.6 | 6.4 |
| hpa50 | 0.26 | 35.9 | 14.7 | 11.6 | 6.3 | 12.6 | 27.0 | 12.8 | 21.4 | 21.3 | 21.1 |
| hpa95 | 0.51 | 62.6 | 0.7 | 0.0 | 5.3 | 1.5 | 545.4 | 487.1 | 2.9 | 3.6 | 1.7 |
| hpa70_stab0 | 0.68 | 23.9 | 12.6 | 10.1 | 4.8 | 3.3 | 10.0 | 2.2 | 1.5 | 1.6 | 0.3 |
| hpa70_stab10 | 0.86 | 11.8 | 9.7 | 13.1 | 7.8 | 2.0 | 3.3 | 11.7 | 2.4 | 2.5 | 0.3 |
| slo_cost | 0.72 | 62.6 | 84.5 | 0.0 | 5.3 | 2.5 | 235.7 | 309.0 | 0.0 | 0.4 | 0.1 |
| pred70 | 0.79 | 3.3 | 12.4 | 17.1 | 11.8 | 5.3 | 1.4 | 3.6 | 3.3 | 3.4 | 1.7 |
| hpa85 | 0.56 | 62.6 | 3.9 | 0.0 | 5.3 | 4.3 | 150.7 | 124.9 | 61.0 | 61.3 | 58.2 |
| hpa70 | 0.94 | 1.8 | 2.2 | 16.1 | 10.8 | 4.5 | 0.1 | 0.2 | 4.3 | 4.4 | 1.6 |

**eps = 0**: 2 log run(s) x 199 decisions; readiness delay 1 step(s) (100% of 78 scale decisions visible at the next window); replay SLA 64.3%.

| target | agreement | replay SLA err | sntpdis_k4 SLA err | mb_trees SLA err | mbcalq_trees SLA err | drmb_k4 SLA err | replay cost err % | sntpdis_k4 cost err % | mb_trees cost err % | mbcalq_trees cost err % | drmb_k4 cost err % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hpa30 | 0.13 | 34.2 | 98.5 | 7.0 | 2.0 | 7.5 | 38.9 | 72.7 | 6.6 | 6.6 | 6.6 |
| hpa50 | 0.21 | 34.2 | 98.5 | 7.0 | 2.0 | 8.8 | 26.9 | 69.6 | 25.7 | 25.6 | 25.1 |
| hpa95 | 0.57 | 64.3 | 40.7 | 0.0 | 5.0 | 1.5 | 545.9 | 316.6 | 2.9 | 3.4 | 1.9 |
| hpa70_stab0 | 0.71 | 25.6 | 27.7 | 38.7 | 33.7 | 31.2 | 10.1 | 20.4 | 30.1 | 30.2 | 27.5 |
| hpa70_stab10 | 0.92 | 10.1 | 0.6 | 47.7 | 42.7 | 32.7 | 3.3 | 1.5 | 15.4 | 15.5 | 11.1 |
| slo_cost | 0.80 | 64.3 | 67.4 | 0.0 | 5.0 | 3.5 | 235.9 | 251.4 | 0.0 | 0.3 | 0.4 |
| pred70 | 0.84 | 1.5 | 4.4 | 23.1 | 18.1 | 13.8 | 1.3 | 1.8 | 3.2 | 3.2 | 0.7 |
| hpa85 | 0.57 | 64.3 | 38.1 | 0.0 | 5.0 | 3.8 | 150.8 | 47.6 | 62.3 | 62.5 | 57.6 |
| hpa70 | 1.00 | 0.0 | 0.0 | 38.2 | 33.2 | 22.1 | 0.0 | 0.0 | 12.8 | 12.9 | 8.6 |

### 3. Real-cluster gate (cells where replay misses: >= 3 SLA pts or >= 15% cost)

- eps=0.1, mbcalq_trees: replay misses 8 target(s) ['hpa30', 'hpa50', 'hpa95', 'hpa70_stab0', 'hpa70_stab10', 'slo_cost', 'pred70', 'hpa85']; mbcalq_trees brings 0 within 3 pts / 15% []
- eps=0.1, drmb_k4: replay misses 8 target(s) ['hpa30', 'hpa50', 'hpa95', 'hpa70_stab0', 'hpa70_stab10', 'slo_cost', 'pred70', 'hpa85']; drmb_k4 brings 3 within 3 pts / 15% ['hpa95', 'hpa70_stab10', 'slo_cost']
- eps=0, mbcalq_trees: replay misses 7 target(s) ['hpa30', 'hpa50', 'hpa95', 'hpa70_stab0', 'hpa70_stab10', 'slo_cost', 'hpa85']; mbcalq_trees brings 1 within 3 pts / 15% ['hpa30']
- eps=0, drmb_k4: replay misses 7 target(s) ['hpa30', 'hpa50', 'hpa95', 'hpa70_stab0', 'hpa70_stab10', 'slo_cost', 'hpa85']; drmb_k4 brings 1 within 3 pts / 15% ['hpa95']

### 4. Does eps = 0.1 change MB's accuracy on the real cluster?

- mb_trees: median |SLA err| eps=0 7.04, eps=0.1 10.55; max 47.74 vs 17.09 (over 8 targets)
- mbcalq_trees: median |SLA err| eps=0 5.03, eps=0.1 5.53; max 42.71 vs 11.81 (over 8 targets)
- drmb_k4: median |SLA err| eps=0 8.17, eps=0.1 3.76; max 32.66 vs 12.56 (over 8 targets)

### 5. Caveats

- Log episodes: eps=0.1: 2, eps=0: 2 run(s) of 199 decisions (simulation used 200 episodes).
- Run-to-run variability, eps=0.1 r1 vs r2: SLA 59.3 vs 65.8, cost 1.327 vs 1.359
- Run-to-run variability, eps=0 r1 vs r2: SLA 67.3 vs 61.3, cost 1.352 vs 1.336
- HPA-70 repeated runs (pilot and eps=0 logs): SLA [67.3, 61.3]
- Truth for the other targets is a single live run each, so its own noise is not estimated.
- Real vs simulator: CPU limit = request = 200m as in the sim calibration; load windows hard-stopped at 12 s (unfinished requests fail); readiness within one step (sim: 2); load is windowed (12 s on, ~3 s off); CPU comes from metrics-server with a 10-25 s lag and a ~15 s window; latency is real HTTP latency; 4 workers schedulable; one trace window per workload.

## W2: azure cpu-bound, start 1200

### 1. Live truth vs simulator (same window)

| target | live runs | live SLA% | live cost vCPU | sim SLA% | sim cost vCPU |
|---|---|---|---|---|---|
| hpa30 | not run | | | 93.5 | 1.291 |
| hpa50 | not run | | | 91.5 | 1.031 |
| hpa95 | not run | | | 77.0 | 0.673 |
| hpa70_stab0 | not run | | | 76.0 | 0.631 |
| hpa70_stab10 | not run | | | 92.5 | 1.427 |
| slo_cost | not run | | | 86.0 | 0.835 |
| pred70 | not run | | | 82.0 | 0.789 |
| hpa85 | not run | | | 80.0 | 0.754 |
| hpa70 | 2 (on_w2_log_eps0_r1, on_w2_log_eps0_r2) | 77.6 [77.4, 77.9] | 0.641 | 87.5 | 0.913 |

### 2. Estimates from the live logs (error vs live truth)

**eps = 0.1**: 2 log run(s) x 199 decisions; readiness delay 1 step(s) (100% of 114 scale decisions visible at the next window); replay SLA 78.4%.

| target | agreement | replay SLA err | sntpdis_k4 SLA err | mb_trees SLA err | mbcalq_trees SLA err | drmb_k4 SLA err | replay cost err % | sntpdis_k4 cost err % | mb_trees cost err % | mbcalq_trees cost err % | drmb_k4 cost err % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hpa70 | 0.95 | 0.8 | 3.1 | 22.4 | 18.6 | 13.3 | 4.0 | 2.0 | 47.0 | 47.0 | 35.7 |

**eps = 0**: 2 log run(s) x 199 decisions; readiness delay 1 step(s) (98% of 102 scale decisions visible at the next window); replay SLA 77.6%.

| target | agreement | replay SLA err | sntpdis_k4 SLA err | mb_trees SLA err | mbcalq_trees SLA err | drmb_k4 SLA err | replay cost err % | sntpdis_k4 cost err % | mb_trees cost err % | mbcalq_trees cost err % | drmb_k4 cost err % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hpa70 | 1.00 | 0.0 | 0.0 | 26.4 | 24.6 | 16.8 | 0.0 | 0.0 | 59.7 | 59.9 | 47.4 |

### 3. Real-cluster gate (cells where replay misses: >= 3 SLA pts or >= 15% cost)

- eps=0.1, mbcalq_trees: replay misses 0 target(s) []; mbcalq_trees brings 0 within 3 pts / 15% []
- eps=0.1, drmb_k4: replay misses 0 target(s) []; drmb_k4 brings 0 within 3 pts / 15% []
- eps=0, mbcalq_trees: replay misses 0 target(s) []; mbcalq_trees brings 0 within 3 pts / 15% []
- eps=0, drmb_k4: replay misses 0 target(s) []; drmb_k4 brings 0 within 3 pts / 15% []

### 4. Does eps = 0.1 change MB's accuracy on the real cluster?


### 5. Caveats

- Log episodes: eps=0.1: 2, eps=0: 2 run(s) of 199 decisions (simulation used 200 episodes).
- Run-to-run variability, eps=0.1 r1 vs r2: SLA 80.4 vs 76.4, cost 0.687 vs 0.645
- Run-to-run variability, eps=0 r1 vs r2: SLA 77.4 vs 77.9, cost 0.655 vs 0.626
- HPA-70 repeated runs (pilot and eps=0 logs): SLA [77.4, 77.9]
- Truth for the other targets is a single live run each, so its own noise is not estimated.
- Real vs simulator: CPU limit = request = 200m as in the sim calibration; load windows hard-stopped at 12 s (unfinished requests fail); readiness within one step (sim: 2); load is windowed (12 s on, ~3 s off); CPU comes from metrics-server with a 10-25 s lag and a ~15 s window; latency is real HTTP latency; 4 workers schedulable; one trace window per workload.

