# M8: second pre-registered held-out window, queueing baseline, W4 repeat (saul)

Criteria: real/PLAN_M8.md (fixed before the M8 runs).

## A. W5 (Bitbrains io-bound 6150), held out

| target | truth_runs | truth_sla | twin_sla | twin_sla_err | truth_cost | twin_cost | twin_cost_err | in_pi | queue_sla | queue_sla_err |
|---|---|---|---|---|---|---|---|---|---|---|
| hpa30 | 1 | 98 | 98.1 | 0.101 | 2.07 | 2.19 | 5.71 | True | 98.5 | 0.503 |
| hpa50 | 1 | 97.5 | 98 | 0.503 | 1.68 | 1.76 | 4.58 | True | 98.5 | 1.01 |
| hpa95 | 1 | 0 | 0 | 0 | 0.202 | 0.202 | 0.124 | True | 0 | 0 |
| hpa70_stab0 | 1 | 37.7 | 37.5 | 0.214 | 1.22 | 1.17 | 3.97 | True | 54.8 | 17.1 |
| hpa70_stab10 | 1 | 75.4 | 75.2 | 0.201 | 1.39 | 1.39 | 0.409 | True | 79.4 | 4.02 |
| slo_cost | 1 | 0 | 0 | 0 | 0.4 | 0.4 | 1.39e-14 | True | 0 | 0 |
| pred70 | 1 | 72.4 | 70.5 | 1.9 | 1.38 | 1.37 | 0.415 | True | 60.3 | 12.1 |
| hpa85 | 1 | 1.01 | 0 | 1.01 | 0.491 | 0.231 | 53.1 | False | 25.1 | 24.1 |

| estimator | median SLA err | max SLA err | median cost err % | within 3 pts & 15% |
|---|---|---|---|---|
| twin | 0.2 | 1.9 | 2.2 | 7/8 |
| replay | 36.1 | 61.7 | 29.5 | 0/8 |
| sntpdis_k4 | 12.2 | 56.4 | 22.4 | 0/8 |
| mbcalq_trees | 6.2 | 25.0 | 13.0 | 2/8 |
| drmb_k4 | 4.3 | 15.4 | 9.7 | 2/8 |
| queue | 2.5 | 24.1 | 3.8 | 3/8 |

- Q1 median |SLA err| <= 3 and median cost err <= 10%: PASS
- Q2 beats every baseline (incl. the queueing model) on median SLA error and gate count: PASS
- Q3 truth inside the v2 interval in >= 80% of cells: 88% -> PASS

## B. W4 with two truth runs per target

| estimator | median SLA err | max SLA err | median cost err % | within 3 pts & 15% |
|---|---|---|---|---|
| twin | 1.3 | 1.9 | 2.5 | 8/8 |
| replay | 12.3 | 28.3 | 57.9 | 0/8 |
| sntpdis_k4 | 11.2 | 43.1 | 38.1 | 0/8 |
| mbcalq_trees | 4.5 | 9.8 | 9.3 | 3/8 |
| drmb_k4 | 5.3 | 10.2 | 9.4 | 2/8 |
| queue | 7.0 | 35.9 | 9.2 | 2/8 |

- v2 interval coverage 100%

## C. Pooled pre-registered held-out cells (W4 + W5, 16 cells), bootstrap

| estimator | median SLA err | 95% CI | baseline - twin, 95% CI |
|---|---|---|---|
| twin | 0.5 | [0.2, 1.4] | - |
| replay | 21.0 | [10.7, 35.8] | [10.1, 35.3] |
| sntpdis_k4 | 12.2 | [8.6, 31.6] | [7.5, 31.2] |
| mbcalq_trees | 5.3 | [2.4, 7.8] | [1.3, 7.5] |
| drmb_k4 | 4.8 | [3.1, 7.7] | [2.6, 7.5] |
| queue | 4.8 | [1.0, 12.3] | [0.5, 11.8] |

- Q4 for every baseline, the 95% CI of (baseline - twin) median error is above 0: PASS

Per-cell table: real/runs/m8_cells.csv.
