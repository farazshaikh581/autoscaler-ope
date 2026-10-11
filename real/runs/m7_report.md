# M7: knee-share flag on new loggers (W3, W4)

Criteria: real/PLAN_M7.md. Flag: knee_share > 0.2; large error: |SLA err| > 6.0.

## W3, logs from dithered HPA-85 (eps 0.1, 2 runs)

| target | truth_runs | truth_sla | twin_sla | twin_sla_err | twin_cost_err | knee_share | far_share | flagged |
|---|---|---|---|---|---|---|---|---|
| hpa30 | 2 | 93.2 | 88.5 | 4.75 | 36.2 | 0.148 | 0.674 | False |
| hpa50 | 2 | 87.9 | 89.7 | 1.73 | 43.8 | 0.14 | 0.648 | False |
| hpa95 | 2 | 7.29 | 7.9 | 0.616 | 0.5 | 0.08 | 0.035 | False |
| hpa70_stab0 | 2 | 34.7 | 45.8 | 11.1 | 0.766 | 0.312 | 0.414 | True |
| hpa70_stab10 | 2 | 66.6 | 86.2 | 19.6 | 16.6 | 0.139 | 0.398 | False |
| slo_cost | 2 | 41.2 | 39.3 | 1.9 | 1.39e-14 | 0.06 | 0.09 | False |
| pred70 | 2 | 69.8 | 80.2 | 10.3 | 4.87 | 0.171 | 0.383 | False |
| hpa85 | 2 | 10.3 | 9.96 | 0.339 | 16.1 | 0.0774 | 0.0318 | False |

| estimator | median SLA err | max SLA err | median cost err % | within 3 pts & 15% |
|---|---|---|---|---|
| twin | 3.3 | 19.6 | 10.5 | 2/8 |
| replay | 43.6 | 82.9 | 66.3 | 0/8 |
| sntpdis_k4 | 9.4 | 33.3 | 71.0 | 0/8 |
| mbcalq_trees | 38.4 | 61.8 | 27.8 | 1/8 |
| drmb_k4 | 39.8 | 65.1 | 26.6 | 1/8 |

## W3, logs from dithered HPA-50 (eps 0.1, 2 runs)

| target | truth_runs | truth_sla | twin_sla | twin_sla_err | twin_cost_err | knee_share | far_share | flagged |
|---|---|---|---|---|---|---|---|---|
| hpa30 | 2 | 93.2 | 93.9 | 0.704 | 4.31 | 0.0296 | 0.115 | False |
| hpa50 | 2 | 87.9 | 91.6 | 3.66 | 1.71 | 0.0364 | 0.0581 | False |
| hpa95 | 2 | 7.29 | 10.9 | 3.63 | 0.5 | 0.025 | 0.62 | False |
| hpa70_stab0 | 2 | 34.7 | 30.4 | 4.27 | 10.8 | 0.15 | 0.2 | False |
| hpa70_stab10 | 2 | 66.6 | 76.8 | 10.2 | 3.65 | 0.237 | 0.099 | True |
| slo_cost | 2 | 41.2 | 44.3 | 3.1 | 1.39e-14 | 0.05 | 0.55 | False |
| pred70 | 2 | 69.8 | 72.3 | 2.49 | 1.37 | 0.208 | 0.104 | True |
| hpa85 | 2 | 10.3 | 17.2 | 6.93 | 77.2 | 0.0467 | 0.276 | False |

| estimator | median SLA err | max SLA err | median cost err % | within 3 pts & 15% |
|---|---|---|---|---|
| twin | 3.6 | 10.2 | 2.7 | 2/8 |
| replay | 32.0 | 78.6 | 40.7 | 1/8 |
| sntpdis_k4 | 17.5 | 75.3 | 63.9 | 1/8 |
| mbcalq_trees | 13.8 | 42.0 | 10.6 | 1/8 |
| drmb_k4 | 19.2 | 50.2 | 9.9 | 2/8 |

## W4, logs from dithered HPA-85 (eps 0.1, 2 runs)

| target | truth_runs | truth_sla | twin_sla | twin_sla_err | twin_cost_err | knee_share | far_share | flagged |
|---|---|---|---|---|---|---|---|---|
| hpa30 | 1 | 81.9 | 82.4 | 0.49 | 4.18 | 0.361 | 0.267 | True |
| hpa50 | 1 | 80.4 | 80.4 | 0.0126 | 0.622 | 0.328 | 0.237 | True |
| hpa95 | 1 | 43.7 | 42.2 | 1.53 | 0.775 | 0.09 | 0.0431 | False |
| hpa70_stab0 | 1 | 59.8 | 62.9 | 3.14 | 8.8 | 0.195 | 0.139 | False |
| hpa70_stab10 | 1 | 80.9 | 79 | 1.87 | 1.23 | 0.538 | 0.435 | True |
| slo_cost | 1 | 53.8 | 52.3 | 1.49 | 5.77 | 0.145 | 0.0897 | False |
| pred70 | 1 | 76.4 | 76.9 | 0.565 | 0.444 | 0.343 | 0.244 | True |
| hpa85 | 1 | 49.7 | 47.5 | 2.26 | 4.5 | 0.102 | 0.043 | False |

| estimator | median SLA err | max SLA err | median cost err % | within 3 pts & 15% |
|---|---|---|---|---|
| twin | 1.5 | 3.1 | 2.7 | 7/8 |
| replay | 20.1 | 33.9 | 65.6 | 1/8 |
| sntpdis_k4 | 8.1 | 76.3 | 53.6 | 1/8 |
| mbcalq_trees | 11.6 | 18.8 | 18.2 | 0/8 |
| drmb_k4 | 13.4 | 20.9 | 18.1 | 1/8 |

## W4, logs from dithered HPA-50 (eps 0.1, 2 runs)

| target | truth_runs | truth_sla | twin_sla | twin_sla_err | twin_cost_err | knee_share | far_share | flagged |
|---|---|---|---|---|---|---|---|---|
| hpa30 | 1 | 81.9 | 85 | 3.08 | 4.66 | 0.128 | 0.0442 | False |
| hpa50 | 1 | 80.4 | 82.6 | 2.21 | 2.25 | 0.134 | 0.0442 | False |
| hpa95 | 1 | 43.7 | 42.4 | 1.27 | 5.39 | 0.055 | 0.438 | False |
| hpa70_stab0 | 1 | 59.8 | 58.8 | 1.03 | 13.5 | 0.111 | 0.229 | False |
| hpa70_stab10 | 1 | 80.9 | 81.6 | 0.666 | 5.01 | 0.108 | 0.0965 | False |
| slo_cost | 1 | 53.8 | 55 | 1.19 | 1.39e-14 | 0.065 | 0.26 | False |
| pred70 | 1 | 76.4 | 77.8 | 1.37 | 3.74 | 0.117 | 0.053 | False |
| hpa85 | 1 | 49.7 | 42.8 | 6.96 | 37.1 | 0.0541 | 0.417 | False |

| estimator | median SLA err | max SLA err | median cost err % | within 3 pts & 15% |
|---|---|---|---|---|
| twin | 1.3 | 7.0 | 4.8 | 6/8 |
| replay | 11.8 | 36.2 | 71.7 | 2/8 |
| sntpdis_k4 | 26.8 | 50.3 | 51.0 | 1/8 |
| mbcalq_trees | 5.3 | 13.1 | 22.6 | 3/8 |
| drmb_k4 | 6.2 | 14.6 | 22.1 | 3/8 |

## Criteria (32 cells)

- large errors: 6; flagged: 7; flagged with |SLA err| <= 3: 5
- D1 every cell with |SLA err| > 6.0 is flagged: FAIL (2/6 caught)
- D2 unflagged cells median |SLA err| <= 3: 2.2 -> PASS
- unflagged cells: median 2.2, max 19.6, within 3 pts & 15% 12/25
- flagged cells: median 1.9, max 11.1

Per-cell table: real/runs/m7_cells.csv.
