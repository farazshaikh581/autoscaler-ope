# M8: second held-out window, queueing baseline, W4 repeat (saul)

Fixed before any M8 run. Target venue: IEEE Networking Letters. The estimator is
`ope.twin.twin_v2` with `interval_v2`, unchanged since M6 (commit 25c7555). The new
baseline `ope.queue_baseline.QueueModel` is frozen with this file. Analysis:
`real/m8_report.py`.

## Why

- Twin v2 has one pre-registered held-out test so far (W4, 8 cells, one truth run each).
  M8 adds a second fresh window and a second truth run on W4, so the pooled held-out set
  is 16 cells with a bootstrap interval.
- A reviewer's first question is "why not a queueing model fitted to the logs?". M8 adds
  that baseline.

## W5 (`real/pick_w5.py`)

W5 is picked by the rule behind W3 and W4: in a trace class, the most variable 200-step
window (largest SD of the request rate) with peak <= 1500 rps and mean >= 300 rps.

- Applied per class, the rule gives W3 (Bitbrains cpu-bound 950) and W4 (Azure cpu-bound
  4075, the only passing window).
- These classes have no passing window: memory-bound and Azure io-bound. Azure "mixed" is
  199 steps long.
- The only class with unused passing windows is Bitbrains io-bound.

**W5 = Bitbrains io-bound, start 6150:** peak 1143 rps, mean 582, SD 253. It does not
overlap W1 (start 4725).

## Queueing baseline (`ope/queue_baseline.py`, development in `real/runs/m8_dev.md`)

- Each ready pod is an M/M/1 server with utilisation D, the per-pod demand, using the
  CPU per request from the logs as in twin v2.
- Latency = a + b / (1 - D), fitted by least squares on unsaturated logged steps.
- The controller sees CPU = min(D, 1). A step meets the SLA when latency < 20 ms and
  D < 1.
- The target's own controller code is rolled forward with one-step readiness.

The unconstrained fit is kept because it is the more accurate on W1-W4: median SLA error
6.7, against 8.9 for a non-negative fit. The comparison is meant to be generous to the
baseline.

## Runs (`real/m8.sh`, 20 x about 53 min = about 17.7 h)

| Block | Runs |
|---|---|
| W5 logs: dithered HPA-70, eps 0.1 x 2 and eps 0 x 2 (seeds 50301, 50302, 50001, 50002) | 4 |
| W5 truth: hpa30, hpa50, hpa85, hpa95, hpa70_stab0, hpa70_stab10, slo_cost, pred70 | 8 |
| W4 truth, second run (`_r2`): the same 8 targets | 8 |

The harness is unchanged since M6:
- CPU limit = request = 200m;
- hard 12 s load windows;
- rho over serving pods.

## Criteria

**W5** (8 cells, one truth run each):

- **Q1:** twin v2 median |SLA error| <= 3 points and median cost error <= 10%.
- **Q2:** twin v2 beats every baseline on both of:
  - median |SLA error|;
  - the count of cells within 3 points and 15% cost.

  The baselines are replay, sntpdis_k4, mbcalq_trees, drmb_k4 and the queueing model.
- **Q3:** the live truth falls inside `interval_v2` in >= 80% of cells.

**Pooled W4 + W5** (16 cells; W4 truth = mean of its two runs):

- **Q4:** for every baseline, the 95% percentile-bootstrap interval of (baseline median
  |SLA error| - twin median |SLA error|) is above 0. Resampling is over cells, 10,000
  resamples, seed 2027.

Also reported, not gated:
- W4 errors against the two-run truth;
- the queueing baseline's fitted parameters.

A failed criterion is reported as failed. Any later change to an estimator is new
development.
