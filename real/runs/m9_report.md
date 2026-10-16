# M9: a second application, api-service (saul)

Criteria: real/PLAN_M9.md (fixed before the M9 runs). Estimators frozen.

## A. api_w1: Bitbrains io-bound 4725

From the logs: CPU per rps 2.076 mcores, linear-regime bound D < 0.59.

| target | truth_sla | twin_sla | twin_sla_err | truth_cost | twin_cost | twin_cost_err | in_pi | replay_sla | replay_sla_err | queue_sla | queue_sla_err |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hpa30 | 98 | 98.7 | 0.716 | 2.2 | 2.22 | 1.1 | True | 44.1 | 53.9 | 99 | 1.01 |
| hpa50 | 96 | 96.9 | 0.879 | 1.8 | 1.89 | 5.13 | True | 44.1 | 51.9 | 98.5 | 2.51 |
| hpa95 | 0 | 0 | 0 | 0.202 | 0.205 | 1.26 | True | 44.1 | 44.1 | 0 | 0 |
| hpa70_stab0 | 19.1 | 23.2 | 4.1 | 1.22 | 1.21 | 0.554 | True | 44.1 | 25 | 19.6 | 0.503 |
| hpa70_stab10 | 65.3 | 61.7 | 3.63 | 1.41 | 1.42 | 0.288 | True | 44.1 | 21.2 | 46.2 | 19.1 |
| slo_cost | 0 | 0 | 0 | 0.4 | 0.4 | 1.39e-14 | True | 44.1 | 44.1 | 0 | 0 |
| pred70 | 47.7 | 49.9 | 2.19 | 1.4 | 1.38 | 1.18 | True | 44.1 | 3.64 | 25.1 | 22.6 |
| hpa85 | 0 | 0 | 0 | 0.584 | 0.344 | 41.1 | False | 44.1 | 44.1 | 3.02 | 3.02 |

| estimator | median SLA err | max SLA err | median cost err % | within 3 pts & 15% |
|---|---|---|---|---|
| twin | 0.8 | 4.1 | 1.1 | 5/8 |
| replay | 44.1 | 53.9 | 32.2 | 0/8 |
| sntpdis_k4 | 16.2 | 98.0 | 39.6 | 0/8 |
| mbcalq_trees | 4.3 | 37.6 | 6.0 | 0/8 |
| drmb_k4 | 4.5 | 28.9 | 5.3 | 1/8 |
| queue | 1.8 | 22.6 | 4.8 | 4/8 |

- Q1 median |SLA err| <= 3 and median cost err <= 10%: PASS
- Q2 beats every baseline (incl. the queueing model) on median SLA error and gate count: PASS
- Q3 truth inside the v2 interval in >= 80% of cells: 88% -> PASS

## B. api_w4: Azure cpu-bound 4075

From the logs: CPU per rps 2.615 mcores, linear-regime bound D < 0.01.

| target | truth_sla | twin_sla | twin_sla_err | truth_cost | twin_cost | twin_cost_err | in_pi | replay_sla | replay_sla_err | queue_sla | queue_sla_err |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hpa30 | 80.4 | 79.7 | 0.741 | 1.6 | 1.64 | 2.32 | True | 69.7 | 10.7 | 81.9 | 1.51 |
| hpa50 | 78.4 | 77.8 | 0.553 | 1.48 | 1.51 | 1.71 | True | 69.7 | 8.67 | 81.4 | 3.02 |
| hpa95 | 43.7 | 41.2 | 2.56 | 0.214 | 0.211 | 1.51 | True | 69.7 | 26 | 41.7 | 2.01 |
| hpa70_stab0 | 57.3 | 57.6 | 0.302 | 0.69 | 0.683 | 1.1 | True | 69.7 | 12.4 | 69.3 | 12.1 |
| hpa70_stab10 | 77.9 | 79.9 | 2 | 1.84 | 1.89 | 2.44 | True | 69.7 | 8.17 | 83.9 | 6.03 |
| slo_cost | 53.8 | 52.6 | 1.18 | 0.4 | 0.4 | 1.39e-14 | True | 69.7 | 16 | 41.7 | 12.1 |
| pred70 | 69.8 | 74.3 | 4.47 | 1.34 | 1.4 | 4.36 | True | 69.7 | 0.126 | 73.9 | 4.02 |
| hpa85 | 45.2 | 42.2 | 3.04 | 0.288 | 0.24 | 16.7 | True | 69.7 | 24.5 | 75.4 | 30.2 |

| estimator | median SLA err | max SLA err | median cost err % | within 3 pts & 15% |
|---|---|---|---|---|
| twin | 1.6 | 4.5 | 2.0 | 6/8 |
| replay | 11.6 | 26.0 | 50.4 | 0/8 |
| sntpdis_k4 | 11.4 | 44.9 | 57.1 | 0/8 |
| mbcalq_trees | 4.4 | 9.7 | 5.3 | 2/8 |
| drmb_k4 | 4.6 | 9.0 | 5.3 | 3/8 |
| queue | 5.0 | 30.2 | 8.6 | 2/8 |

- Q1 median |SLA err| <= 3 and median cost err <= 10%: PASS
- Q2 beats every baseline (incl. the queueing model) on median SLA error and gate count: PASS
- Q3 truth inside the v2 interval in >= 80% of cells: 100% -> PASS

## Replay on both applications (not gated)

| window | api-service median | api-service max | web-service median | web-service max |
|---|---|---|---|---|
| api_w1 | 44.1 | 53.9 | 34.8 | 63.4 |
| api_w4 | 11.6 | 26.0 | 12.3 | 28.3 |

## C. Pooled (16 cells), bootstrap

| estimator | median SLA err | 95% CI | baseline - twin, 95% CI |
|---|---|---|---|
| twin | 1.0 | [0.5, 2.6] | - |
| replay | 22.9 | [10.7, 44.1] | [9.0, 43.3] |
| sntpdis_k4 | 14.6 | [7.3, 32.6] | [5.2, 31.4] |
| mbcalq_trees | 4.3 | [3.9, 5.0] | [1.6, 4.0] |
| drmb_k4 | 4.6 | [2.7, 6.4] | [0.8, 5.3] |
| queue | 3.0 | [1.5, 12.1] | [0.0, 10.0] |

- Q4 for every baseline, the 95% CI of (baseline - twin) median error is above 0: PASS

Per-cell table: real/runs/m9_cells.csv.
