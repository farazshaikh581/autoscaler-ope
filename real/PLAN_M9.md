# M9: a second application (saul)

Fixed before any M9 run. The estimators are frozen:
- `ope.twin.twin_v2` with `interval_v2`, unchanged since M6 (commit 25c7555);
- `ope.queue_baseline.QueueModel` and the four off-policy baselines, unchanged since M8.

Analysis: `real/m9_report.py`.

## Why

Every live result so far is on one application, `web-service`, a fixed CPU-bound hash
loop. M9 asks whether the results carry over to an application with a different
latency-load curve:
- replay misleads;
- twin v2 is accurate and beats every baseline.

Nothing is tuned on the new application.

## The application (`deploy/api-service/`)

A JSON API with a downstream call, written for this study and deployed from this
repository alone (`deploy/apply.sh api-service`, image `python:3.10-slim`). Each request:
1. builds N JSON records, N log-normal (median 40, sigma 0.9), then serialises, parses,
   sorts and hashes them;
2. waits for a downstream call, exponential with mean 3 ms.

CPU request = limit = 200m, as for web-service.

Knee check on saul (`real/runs/kneecheck_api-service.json`, 2 pods, 2026-10-15):

| | web-service | api-service |
|---|---|---|
| CPU per rps (mcores) | 1.727 | 2.348 |
| latency at low load | 2.7 ms | 6.9 ms |
| 20 ms SLA crossed at demand | 0.900 | 0.845 |
| latency-midpoint knee at demand | 0.944 | 0.904 |
| p99 at demand ~0.85 | 41 ms | 94-228 ms |

**Load scale (rule fixed before the runs):** max_rps = 2050 x 1.727 / 2.348 = 1508 rps, so
each trace step asks for the same number of 200m pods as for web-service.

Two frozen settings were tuned on web-service and are kept:
- the twin's "unsaturated" filter, mean latency < 10 ms (api-service is flat at 6-9 ms
  up to demand ~0.8);
- the run-to-run noise in `interval_v2`.

Q3 tests whether the interval transfers.

## Windows

Two windows, one per trace family, both used with web-service:

| Key | Window | Role with web-service |
|---|---|---|
| `api_w1` | W1 = Bitbrains io-bound 4725 | the headline window, where replay misleads |
| `api_w4` | W4 = Azure cpu-bound 4075 | pre-registered held out (M6) |

No estimator was developed on api-service, so both windows are held out for this
application.

## Runs (`real/m9.sh`, 24 x about 53 min = about 21 h)

Per window:

| Block | Runs |
|---|---|
| logs: dithered HPA-70, eps 0.1 x 2 and eps 0 x 2 | 4 |
| truth: hpa30, hpa50, hpa85, hpa95, hpa70_stab0, hpa70_stab10, slo_cost, pred70 | 8 |

- **Seeds:** 100000 + 10000 x window + 100 x eps_index + rep. W1: 110301, 110302, 110001,
  110002. W4: 140301, 140302, 140001, 140002.
- **Tags:** `on_api_w1_...` and `on_api_w4_...`.
- **Harness:** unchanged except `--app api-service`, which selects the deployment and the
  load scale. web-service stays at 2 idle pods throughout.

## Criteria

**Per window** (8 cells, one truth run each):

- **Q1:** twin v2 median |SLA error| <= 3 points and median cost error <= 10%.
- **Q2:** twin v2 beats every baseline on both of:
  - median |SLA error|;
  - the count of cells within 3 points and 15% cost.

  The baselines are replay, sntpdis_k4, mbcalq_trees, drmb_k4 and the queueing model.
- **Q3:** the live truth falls inside `interval_v2` in >= 80% of cells.

**Pooled** (16 cells):

- **Q4:** for every baseline, the 95% percentile-bootstrap interval of (baseline median
  |SLA error| - twin median |SLA error|) is above 0. Resampling is over cells, 10,000
  resamples, seed 2027.

Also reported, not gated:
- replay's error on api-service next to its error on web-service, window by window;
- the CPU per request and the linear-regime bound that `log_scale` derives from the
  api-service logs.

A failed criterion is reported as failed. Any later change to an estimator is new
development.
