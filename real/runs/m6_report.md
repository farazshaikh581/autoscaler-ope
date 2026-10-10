# M6: log-only twin, new window, other loggers, repeated truth (saul)

Criteria: real/PLAN_M6.md (fixed before the M6 runs).

## A. W4 (Azure cpu-bound 4075), held out

| target | truth_runs | truth_sla | twin_sla | twin_sla_err | truth_cost | twin_cost | twin_cost_err | in_pi | far_share | v1_sla_err |
|---|---|---|---|---|---|---|---|---|---|---|
| hpa30 | 1 | 81.9 | 84.3 | 2.44 | 1.61 | 1.7 | 5.09 | True | 0.107 | 1.97 |
| hpa50 | 1 | 80.4 | 82.3 | 1.87 | 1.47 | 1.52 | 2.98 | True | 0.0909 | 0.917 |
| hpa95 | 1 | 43.7 | 42 | 1.67 | 0.214 | 0.208 | 3.03 | True | 0.319 | 1.27 |
| hpa70_stab0 | 1 | 59.8 | 59.2 | 0.603 | 0.665 | 0.666 | 0.11 | True | 0.109 | 0.251 |
| hpa70_stab10 | 1 | 80.9 | 82.2 | 1.28 | 1.94 | 1.93 | 0.313 | True | 0.16 | 2.32 |
| slo_cost | 1 | 53.8 | 53.3 | 0.427 | 0.4 | 0.4 | 1.39e-14 | True | 0.14 | 1.47 |
| pred70 | 1 | 76.4 | 77.9 | 1.51 | 1.44 | 1.42 | 0.977 | True | 0.0542 | 1.14 |
| hpa85 | 1 | 49.7 | 46.3 | 3.4 | 0.337 | 0.31 | 7.89 | True | 0.195 | 3.58 |

| estimator | median SLA err | max SLA err | median cost err % | within 3 pts & 15% |
|---|---|---|---|---|
| twin | 1.6 | 3.4 | 2.0 | 7/8 |
| v1 | 1.4 | 3.6 | 3.8 | 7/8 |
| replay | 11.1 | 28.0 | 55.1 | 0/8 |
| sntpdis_k4 | 10.6 | 42.8 | 38.0 | 0/8 |
| mbcalq_trees | 4.0 | 11.8 | 9.5 | 3/8 |
| drmb_k4 | 5.0 | 12.2 | 10.0 | 2/8 |

- P1 median |SLA err| <= 3 and median cost err <= 10%: PASS
- P2 beats the best non-replay baseline (median 4.0) on median SLA error and gate count: PASS
- P3 truth inside the v2 prediction interval in >= 80% of cells: 100% -> PASS

## B. Other behaviour policies on W1 (truth: the two W1 runs per target)

### logs from dithered HPA-85 (eps 0.1, 2 runs)

| target | truth_runs | truth_sla | twin_sla | twin_sla_err | truth_cost | twin_cost | twin_cost_err | in_pi | far_share |
|---|---|---|---|---|---|---|---|---|---|
| hpa30 | 2 | 98.5 | 69.3 | 29.2 | 2.21 | 2.35 | 6.69 | False | 0.825 |
| hpa50 | 2 | 98 | 69.3 | 28.7 | 1.84 | 2.35 | 27.6 | False | 0.823 |
| hpa95 | 2 | 0 | 0 | 0 | 0.206 | 0.206 | 0.147 | True | 0.585 |
| hpa70_stab0 | 2 | 40.2 | 42.8 | 2.61 | 1.24 | 1.32 | 6.29 | True | 0.0116 |
| hpa70_stab10 | 2 | 77.9 | 58.3 | 19.6 | 1.41 | 1.44 | 2.01 | False | 0.0529 |
| slo_cost | 2 | 0 | 0 | 0 | 0.4 | 0.4 | 1.39e-14 | True | 0 |
| pred70 | 2 | 68.8 | 66.7 | 2.1 | 1.38 | 1.81 | 31.6 | True | 0.499 |
| hpa85 | 2 | 0 | 0 | 0 | 0.52 | 0.485 | 6.73 | True | 0.000875 |

| estimator | median SLA err | max SLA err | median cost err % | within 3 pts & 15% |
|---|---|---|---|---|
| twin | 2.4 | 29.2 | 6.5 | 4/8 |
| replay | 52.3 | 96.2 | 56.8 | 0/8 |
| sntpdis_k4 | 45.6 | 98.5 | 73.6 | 0/8 |
| mbcalq_trees | 50.0 | 88.9 | 23.3 | 2/8 |
| drmb_k4 | 51.0 | 90.5 | 22.8 | 2/8 |

- flagged (far share > 0.1): 4/8 cells; median |SLA err| flagged 15.4, unflagged 1.3
- L1 median |SLA err| <= 3 from HPA-85 logs: PASS

### logs from dithered HPA-50 (eps 0.1, 2 runs)

| target | truth_runs | truth_sla | twin_sla | twin_sla_err | truth_cost | twin_cost | twin_cost_err | in_pi | far_share |
|---|---|---|---|---|---|---|---|---|---|
| hpa30 | 2 | 98.5 | 99 | 0.477 | 2.21 | 2.25 | 2.06 | True | 0.235 |
| hpa50 | 2 | 98 | 98.5 | 0.553 | 1.84 | 1.87 | 1.45 | True | 0.00462 |
| hpa95 | 2 | 0 | 0 | 0 | 0.206 | 0.202 | 1.71 | True | 0.98 |
| hpa70_stab0 | 2 | 40.2 | 24.8 | 15.4 | 1.24 | 1.09 | 12.2 | True | 0.186 |
| hpa70_stab10 | 2 | 77.9 | 71.1 | 6.8 | 1.41 | 1.4 | 0.793 | True | 0.0126 |
| slo_cost | 2 | 0 | 0 | 0 | 0.4 | 0.4 | 1.39e-14 | True | 0.75 |
| pred70 | 2 | 68.8 | 57.1 | 11.8 | 1.38 | 1.32 | 3.97 | True | 0.0401 |
| hpa85 | 2 | 0 | 0 | 0 | 0.52 | 0.25 | 51.9 | False | 0.845 |

| estimator | median SLA err | max SLA err | median cost err % | within 3 pts & 15% |
|---|---|---|---|---|
| twin | 0.5 | 15.4 | 1.9 | 4/8 |
| replay | 40.7 | 95.2 | 39.4 | 1/8 |
| sntpdis_k4 | 33.6 | 96.9 | 30.8 | 2/8 |
| mbcalq_trees | 18.6 | 59.3 | 33.7 | 1/8 |
| drmb_k4 | 11.6 | 66.8 | 33.3 | 1/8 |

- flagged (far share > 0.1): 5/8 cells; median |SLA err| flagged 0.0, unflagged 6.8
- L2 every cell with |SLA err| > 5 is flagged: FAIL (3 such cells)

## C. W2 and W3 with two truth runs per target (development for v2)

### W2

| estimator | median SLA err | max SLA err | median cost err % | within 3 pts & 15% |
|---|---|---|---|---|
| twin | 1.7 | 3.6 | 6.3 | 4/8 |
| v1 | 1.7 | 3.6 | 5.7 | 6/8 |

- v2 interval coverage 100%

### W3

| estimator | median SLA err | max SLA err | median cost err % | within 3 pts & 15% |
|---|---|---|---|---|
| twin | 1.4 | 4.8 | 3.4 | 5/8 |
| v1 | 1.9 | 4.3 | 5.1 | 4/8 |

- v2 interval coverage 75%

## D. Run-to-run noise of the live system

| window | target | sla_r1 | sla_r2 | d_sla | d_cost_pct |
|---|---|---|---|---|---|
| w1 | hpa30 | 98.5 | 98.5 | 0 | 0.729 |
| w1 | hpa50 | 98.5 | 97.5 | 1.01 | 0.0547 |
| w1 | hpa95 | 0 | 0 | 0 | 2.44 |
| w1 | hpa70_stab0 | 38.7 | 41.7 | 3.02 | 3.64 |
| w1 | hpa70_stab10 | 74.4 | 81.4 | 7.04 | 2.57 |
| w1 | slo_cost | 0 | 0 | 0 | 0 |
| w1 | pred70 | 65.8 | 71.9 | 6.03 | 2.19 |
| w1 | hpa85 | 0 | 0 | 0 | 5.99 |
| w2 | hpa30 | 93 | 93 | 0 | 0.173 |
| w2 | hpa50 | 85.9 | 86.4 | 0.503 | 1.13 |
| w2 | hpa95 | 47.7 | 46.7 | 1.01 | 0.499 |
| w2 | hpa70_stab0 | 63.8 | 60.8 | 3.02 | 5.86 |
| w2 | hpa70_stab10 | 88.9 | 88.4 | 0.503 | 4.11 |
| w2 | slo_cost | 74.4 | 74.4 | 0 | 0 |
| w2 | pred70 | 86.9 | 78.9 | 8.04 | 7.32 |
| w2 | hpa85 | 53.3 | 48.7 | 4.52 | 27.3 |
| w3 | hpa30 | 93 | 93.5 | 0.503 | 0.526 |
| w3 | hpa50 | 86.4 | 89.4 | 3.02 | 1.6 |
| w3 | hpa95 | 7.04 | 7.54 | 0.503 | 1 |
| w3 | hpa70_stab0 | 31.2 | 38.2 | 7.04 | 7.61 |
| w3 | hpa70_stab10 | 67.3 | 65.8 | 1.51 | 2.15 |
| w3 | slo_cost | 41.2 | 41.2 | 0 | 0 |
| w3 | pred70 | 69.3 | 70.4 | 1.01 | 0.969 |
| w3 | hpa85 | 8.04 | 12.6 | 4.52 | 1.2 |

SD of one run's SLA% (from 24 pairs): 2.39; of cost: 4.5%

Per-cell table: real/runs/m6_cells.csv.
