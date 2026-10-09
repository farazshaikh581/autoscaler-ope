# M6: log-only twin on a new window, other loggers, repeated truth (saul)

Fixed before any M6 run. The estimator is `ope.twin.twin_v2` with `interval_v2`, as
committed with this file; it is not changed during or after the batch. Analysis:
`real/m6_report.py`.

## What changed since M5 (development on W1-W3, 24 cells; `real/runs/m6_dev.md`)

Ablations of the M5 twin (median / max |SLA error|, median cost error):

| Variant | Median / max SLA err | Median cost err | Notes |
|---|---|---|---|
| M5 twin | 1.8 / 6.8 | 3.7% | |
| Without the lagged demand | 2.6 / 14.9 | 10.2% | The lag is essential. |
| Without the replica-change flag | 1.6 / 6.7 | 3.4% | |
| Without the below-knee rescaling | 1.7 / 6.5 | 2.7% | |
| One 200-step eps = 0 log as donors (instead of four logs) | 1.5 / 6.3 | 3.6% | |
| CPU per request and the linear-regime bound from the logs (no knee check), no change flag (**twin v2**) | 1.5 / 6.3 | 2.2% | |

Interval coverage on these 24 cells:
- sensitivity interval alone: 71%;
- widened by the live run-to-run noise (SD 2.7 SLA points, 3% cost; `interval_v2`):
  92%.

Twin v2:
- matching on (log D, log D at t-1), K = 10;
- D = rps x m / (ready x cpu_req), where m (CPU per rps) is estimated from
  unsaturated logged steps;
- below-knee rescaling up to the bound read off the logged SLA profile;
- 40 rollouts and rho shifts of +-0.03;
- `far_share` = share of rollout steps whose nearest donor is further than 0.25 in
  the matching metric (outside the logs' support).

## Runs (`real/m6.sh`, 32 x about 52 min = about 27.5 h)

| Block | Runs |
|---|---|
| W4 (Azure cpu-bound, start 4075; peak 1421 rps, mean 376): logs eps 0.1 x 2, eps 0 x 2 | 4 |
| W4 truth: hpa30, hpa50, hpa85, hpa95, hpa70_stab0, hpa70_stab10, slo_cost, pred70 | 8 |
| W1 logs from other behaviours: dithered HPA-85 x 2, dithered HPA-50 x 2 (eps 0.1) | 4 |
| W2 and W3 second truth run (`_r2`) for the 8 targets | 16 |

Same harness as M5 (CPU limit = request = 200m, hard 12 s windows, rho over serving
pods). It adds a `--behaviour-util` flag for the dithered HPA, used only by the new
W1 logger runs.

## Criteria

W4 is the only held-out window; the 8 targets, excluding hpa70, are its cells.

- **P1:** twin v2 median |SLA error| <= 3 points and median cost error <= 10%.
- **P2:** twin v2 beats the best non-replay baseline (sntpdis_k4, mbcalq_trees,
  drmb_k4, from W4's logs) on median |SLA error| and on the count of cells within
  3 points and 15% cost.
- **P3:** the live truth falls inside `interval_v2` in >= 80% of cells.

Logger transport (W1 targets; the truth is the two W1 runs per target, the logs are
new):

- **L1:** from the HPA-85 logs, twin v2 median |SLA error| <= 3 points.
- **L2:** from the HPA-50 logs, every cell with |SLA error| > 5 points is flagged
  (far_share > 0.10). HPA-50 rarely visits the knee, so this tests whether the
  support diagnostic catches the estimates it can't support.

Also reported, not gated:
- the M5 twin (v1) on W4;
- W2/W3 errors against two truth runs;
- the run-to-run SD from all repeated targets (W1-W3).

A failed criterion is reported as failed. Any later change to the twin is new
development.
