# saul live runs (OPE). One line per run, appended before it starts.

| start (UTC) | what | expected end (UTC) |
|---|---|---|
| 2026-10-06 15:39 | OPE load check: [958, 1253] rps x 60s against 12 replicas | 2026-10-06 15:45 |
| 2026-10-06 15:43 | OPE harness smoke_live_w1_hpa70: hpa70 eps=0, bitbrains/io-bound start 4725, 5 steps x 15s | 2026-10-06 15:47 |
| 2026-10-06 15:46 | OPE harness smoke_live_w1_hpa70: hpa70 eps=0, bitbrains/io-bound start 4725, 6 steps x 15s | 2026-10-06 15:50 |
| 2026-10-06 15:49 | OPE harness pilot_w1_hpa70: hpa70 eps=0, bitbrains/io-bound start 4725, 200 steps x 15s | 2026-10-06 16:42 |
| 2026-10-06 15:51 | pilot_w1_hpa70 ABORTED at 15:52 (SIGTERM, scaled back to 2) to fix CSV write buffering for unattended runs; relaunching | - |
| 2026-10-06 15:52 | OPE harness pilot_w1_hpa70: hpa70 eps=0, bitbrains/io-bound start 4725, 200 steps x 15s | 2026-10-06 16:45 |
| 2026-10-06 16:43 | OPE harness pilot_w1_hpa95: hpa95 eps=0, bitbrains/io-bound start 4725, 200 steps x 15s | 2026-10-06 17:36 |
| 2026-10-06 17:30 | VPA webhook namespaceSelector pinned to In [hv-phase0] (install procedure, after pilot runs); after 60 s: {"matchExpressions":[{"key":"kubernetes.io/metadata.name","operator":"In","values":["hv-phase0"]}]} | - |
| 2026-10-06 17:31 | Overnight batch NOT started: pilot gate (e) failed (pilot_w1_hpa95 crashed at row 177 on a '803ms' metrics window; fixed in 64c7d14, not relaunched). Gate (b): live HPA-70 vs HPA-95 SLA gap 0.0 pts (both 100%; sim 60.5). Cluster idle, web-service 2/2. | - |
| 2026-10-07 08:45 | OPE knee check: 2 replicas, CPU limit 200m, 9 rps levels | 2026-10-07 08:59 |
| 2026-10-07 08:57 | OPE harness pilot_w1_hpa70: hpa70 eps=0, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-07 09:50 |
| 2026-10-07 09:49 | OPE harness pilot_w1_hpa95: hpa95 eps=0, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-07 10:42 |
| 2026-10-07 11:44 | Overnight batch NOT started: re-pilot (200m) gate (b) PASS 67.5 pts, gate (e) FAIL (step overruns: hpa70 18, hpa95 199). Cluster idle, web-service 2/2, CPU limit still 200m. | - |
| 2026-10-07 12:05 | OPE harness smoke_hard_w1_hpa95: hpa95 eps=0, bitbrains/io-bound start 4725, 20 steps x 15s, CPU limit 200m | 2026-10-07 12:13 |
