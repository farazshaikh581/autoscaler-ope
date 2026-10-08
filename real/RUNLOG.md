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
| 2026-10-07 12:12 | OPE harness on_w1_log_eps0.1_r1: dithered eps=0.1, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-07 13:05 |
| 2026-10-07 12:14 | Overnight batch STOPPED during run 1 (on_w1_log_eps0.1_r1, SIGTERM, scaled back to 2) to fix rho counting terminating pods; partial run in real/runs/aborted/ | - |
| 2026-10-07 12:14 | OPE harness smoke_hard2_w1_hpa95: hpa95 eps=0, bitbrains/io-bound start 4725, 20 steps x 15s, CPU limit 200m | 2026-10-07 12:22 |
| 2026-10-07 12:21 | OPE harness on_w1_log_eps0.1_r1: dithered eps=0.1, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-07 13:14 |
| 2026-10-07 13:12 | OPE harness on_w1_log_eps0_r1: dithered eps=0, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-07 14:05 |
| 2026-10-07 14:03 | OPE harness on_w1_truth_hpa85: hpa85 eps=0, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-07 14:56 |
| 2026-10-07 14:55 | OPE harness on_w1_truth_slo_cost: slo_cost eps=0, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-07 15:48 |
| 2026-10-07 15:47 | OPE harness on_w1_truth_hpa30: hpa30 eps=0, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-07 16:40 |
| 2026-10-07 16:38 | OPE harness on_w1_truth_hpa70_stab0: hpa70_stab0 eps=0, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-07 17:31 |
| 2026-10-07 17:29 | OPE harness on_w1_log_eps0.1_r2: dithered eps=0.1, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-07 18:22 |
| 2026-10-07 18:21 | OPE harness on_w1_log_eps0_r2: dithered eps=0, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-07 19:14 |
| 2026-10-07 19:13 | OPE harness on_w1_truth_hpa50: hpa50 eps=0, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-07 20:06 |
| 2026-10-07 20:04 | OPE harness on_w1_truth_hpa70_stab10: hpa70_stab10 eps=0, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-07 20:57 |
| 2026-10-07 20:56 | OPE harness on_w1_truth_pred70: pred70 eps=0, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-07 21:49 |
| 2026-10-07 21:47 | OPE harness on_w2_log_eps0.1_r1: dithered eps=0.1, azure/cpu-bound start 1200, 200 steps x 15s, CPU limit 200m | 2026-10-07 22:40 |
| 2026-10-07 22:39 | OPE harness on_w2_log_eps0_r1: dithered eps=0, azure/cpu-bound start 1200, 200 steps x 15s, CPU limit 200m | 2026-10-07 23:32 |
| 2026-10-07 23:30 | OPE harness on_w2_log_eps0.1_r2: dithered eps=0.1, azure/cpu-bound start 1200, 200 steps x 15s, CPU limit 200m | 2026-10-08 00:23 |
| 2026-10-08 00:21 | OPE harness on_w2_log_eps0_r2: dithered eps=0, azure/cpu-bound start 1200, 200 steps x 15s, CPU limit 200m | 2026-10-08 01:14 |
| 2026-10-08 01:13 | OPE harness on_w1_truth_hpa95: hpa95 eps=0, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-08 02:06 |
| 2026-10-08 08:57 | Overnight batch finished 02:04 UTC: 16/16 runs exit 0, 0 step overruns; report real/runs/overnight_report.md. Cluster idle, web-service 2/2, CPU limit still 200m. | - |
