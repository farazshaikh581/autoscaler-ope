# M4 pilot gate report (W1 = Bitbrains io-bound, start 4725)

## (a) load generator at the windows' peaks (12 replicas, driver on even CPUs 0-14)

- 958 rps: achieved 958.0 (+0.0%), success 1.0000, p99 6.0 ms; driver core busy mean max 11.6%, peak 19.0% -> rate PASS, CPU PASS
- 1253 rps: achieved 1253.0 (+0.0%), success 1.0000, p99 7.3 ms; driver core busy mean max 15.5%, peak 21.2% -> rate PASS, CPU PASS

## (b) live SLA gap and (c) live vs simulation

| run | rows | live SLA% | sim SLA% | live cost vCPU | sim cost vCPU | replicas min-max (mean) | scale actions |
|---|---|---|---|---|---|---|---|
| W1 hpa70 | 200 | 67.5 | 91.0 | 1.338 | 1.756 | 2-10 (6.69) | 34 |
| W1 hpa95 | 200 | 0.0 | 30.5 | 0.396 | 1.306 | 1-2 (1.98) | 0 |

Live SLA gap HPA-70 minus HPA-95: 67.5 points (sim: 60.5) -> gate (b) PASS (needs >= 10).
Rows log the window measured before each decision (one-step offset vs the simulator); on outcome-aligned rows 1-199: hpa70 SLA 67.8% cost 1.343, hpa95 SLA 0.0% cost 0.396

## (d) metric lag and readiness delay

- hpa70: metrics-server sample age median 12.8 s (p90 16.5 s), averaging window 16.2 s; new pods 21, creation-to-Ready median 8.0 s (max 10.0 s); steps with a scale still pending 0 (simulator: 2 steps per scale)
- hpa95: metrics-server sample age median 12.4 s (p90 20.7 s), averaging window 16.2 s; new pods 0, creation-to-Ready median nan s (max nan s); steps with a scale still pending 4 (simulator: 2 steps per scale)

## (e) harness health

- hpa70: 200/200 rows; achieved vs target rps median -0.1% (worst 0.3%); min window success 0.9501; median window p99 60.1 ms; steps without CPU metrics 0; step overruns > 15.5 s: 18 (max step 28.2 s); max actuation time 0.19 s
- hpa95: 200/200 rows; achieved vs target rps median -0.1% (worst 0.3%); min window success 0.5033; median window p99 4999.8 ms; steps without CPU metrics 0; step overruns > 15.5 s: 199 (max step 50.8 s); max actuation time 0.00 s
- pilot.log: 0 error/warning lines
