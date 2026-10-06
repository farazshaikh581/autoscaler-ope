# M4 pilot gate report (W1 = Bitbrains io-bound, start 4725)

## (a) load generator at the windows' peaks (12 replicas, driver on even CPUs 0-14)

- 958 rps: achieved 958.0 (+0.0%), success 1.0000, p99 6.0 ms; driver core busy mean max 11.6%, peak 19.0% -> rate PASS, CPU PASS
- 1253 rps: achieved 1253.0 (+0.0%), success 1.0000, p99 7.3 ms; driver core busy mean max 15.5%, peak 21.2% -> rate PASS, CPU PASS

## (b) live SLA gap and (c) live vs simulation

| run | rows | live SLA% | sim SLA% | live cost vCPU | sim cost vCPU | replicas min-max (mean) | scale actions |
|---|---|---|---|---|---|---|---|
| W1 hpa70 | 200 | 100.0 | 91.0 | 1.322 | 1.756 | 2-10 (6.61) | 35 |
| W1 hpa95 | 177 | 100.0 | 30.5 | 0.931 | 1.306 | 2-7 (4.66) | 29 |

Live SLA gap HPA-70 minus HPA-95: 0.0 points (sim: 60.5) -> gate (b) FAIL (needs >= 10).
Rows log the window measured before each decision (one-step offset vs the simulator); on outcome-aligned rows 1-199: hpa70 SLA 100.0% cost 1.327, hpa95 SLA 100.0% cost 0.934

## (d) metric lag and readiness delay

- hpa70: metrics-server sample age median 4.5 s (p90 7.7 s), averaging window 16.4 s; new pods 21, creation-to-Ready median 8.0 s (max 10.0 s); steps with a scale still pending 0 (simulator: 2 steps per scale)
- hpa95: metrics-server sample age median 13.1 s (p90 17.6 s), averaging window 16.2 s; new pods 17, creation-to-Ready median 8.0 s (max 9.0 s); steps with a scale still pending 0 (simulator: 2 steps per scale)

## (e) harness health

- hpa70: 200/200 rows; achieved vs target rps median -0.1% (worst 0.3%); min window success 1.0000; median window p99 6.0 ms; steps without CPU metrics 0; step overruns > 15.5 s: 0 (max step 15.0 s); max actuation time 0.15 s
- hpa95: 177/200 rows; achieved vs target rps median -0.1% (worst 0.3%); min window success 1.0000; median window p99 6.0 ms; steps without CPU metrics 0; step overruns > 15.5 s: 0 (max step 15.0 s); max actuation time 0.27 s
- pilot.log: 3 error/warning lines:
  Traceback (most recent call last):
  ValueError: could not convert string to float: '803m'
  [2026-10-06T17:29:13Z] W1 hpa95: FAILED, stopping the pilot
