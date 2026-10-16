# Why twin v2 misses hpa85's cost (diagnosis after M9, 2026-10-16)

This is analysis of existing runs only. No estimator changed, and the frozen M8/M9 results
stand.

## The miss

| Window | Truth cost | Twin cost | Error | SLA (truth / twin) |
|---|---|---|---|---|
| web W5 | 0.491 | 0.231 | 53% (0.26 vCPU, about 1 pod) | 1.0 / 0 |
| api W1 | 0.584 | 0.344 | 41% (0.24 vCPU) | 0 / 0 |
| api W4 | 0.288 | 0.240 | 17% (0.05 vCPU) | 45.2 / 42.2 |
| web W4 | 0.337 | 0.337 | 0.2% | 49.5 / 50.6 |

The twin's SLA estimate stays right. Its cost is too low: it ends hpa85 at 1-2 pods, while
the live run holds 2-4.

## Mechanism (`saturated_cpu.py`, `streaks.py`, `rollout_trace.py`)

1. **The CPU reading lags saturation by about 2 steps.** A metrics-server sample averages
   about 16 s and is about 13 s old when read. The saturated cpu_util therefore climbs with
   the number of consecutive saturated steps (truth runs: 0.48, 0.74, 0.85, 0.86, 0.87 for
   streaks of 1, 2, 3, 4 and 5+). The logs show the same curve.
2. **The behaviour policy seldom stays saturated.** Dithered HPA-70 leaves saturation
   within a few steps. The logs hold 117 steps with a saturation streak of 5 or more; the
   truth runs of hpa85, hpa95, slo_cost and stab0 hold 1,533.
3. **hpa85 sits on both of its thresholds when saturated.**
   - It scales in after 3 steps below 0.765. Truth readings are about 0.83, so it never
     scales in. The twin draws donors that are mostly short streaks (mean 0.71-0.76; 17-38%
     below 0.765), so it scales in.
   - It scales out only above 0.935. That happens in 1-4% of truth steps and never in the
     logs, so the twin never scales out (0 per rollout on W5 and api W1, against 2 live).
   - In sustained saturation each live scale-out is permanent, because the reading never
     drops below 0.765 again. One rare high reading therefore buys a pod for the rest of the
     run.
4. **Where the load leaves saturation often** (W4, both apps), the pod count oscillates in
   the twin and live alike, and the error averages out.

So the twin has coverage in demand space but not in history. The target reaches a
state, long sustained saturation, that the behaviour's logs barely contain, and its cost
there hinges on rare readings at a threshold.

## A second demand lag does not fix it (`twin_lag2.py`, `eval_lag2.py`, `lag2_cells.csv`)

This adds log D at t-2 to the matching key, over the 32 held-out cells:

| | Median SLA err | Max SLA err | Gate | Interval coverage |
|---|---|---|---|---|
| twin v2 (frozen) | 0.81 | 4.47 | 26/32 | 30/32 |
| with the t-2 lag | 0.82 | 7.01 | 24/32 | 30/32 |

The hpa85 errors are unchanged (41% and 47%). The logs have too few long-streak donors,
and those few read low (0.80 against 0.87 live). The missing information is in the logs'
coverage, not in the key.
