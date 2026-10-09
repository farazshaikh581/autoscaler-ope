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
| 2026-10-08 09:22 | OPE harness on_w2_truth_hpa30: hpa30 eps=0, azure/cpu-bound start 1200, 200 steps x 15s, CPU limit 200m | 2026-10-08 10:15 |
| 2026-10-08 10:13 | OPE harness on_w2_truth_hpa50: hpa50 eps=0, azure/cpu-bound start 1200, 200 steps x 15s, CPU limit 200m | 2026-10-08 11:06 |
| 2026-10-08 11:05 | OPE harness on_w2_truth_hpa85: hpa85 eps=0, azure/cpu-bound start 1200, 200 steps x 15s, CPU limit 200m | 2026-10-08 11:58 |
| 2026-10-08 11:56 | OPE harness on_w2_truth_hpa95: hpa95 eps=0, azure/cpu-bound start 1200, 200 steps x 15s, CPU limit 200m | 2026-10-08 12:49 |
| 2026-10-08 12:47 | OPE harness on_w2_truth_hpa70_stab0: hpa70_stab0 eps=0, azure/cpu-bound start 1200, 200 steps x 15s, CPU limit 200m | 2026-10-08 13:40 |
| 2026-10-08 13:39 | OPE harness on_w2_truth_hpa70_stab10: hpa70_stab10 eps=0, azure/cpu-bound start 1200, 200 steps x 15s, CPU limit 200m | 2026-10-08 14:32 |
| 2026-10-08 14:30 | OPE harness on_w2_truth_slo_cost: slo_cost eps=0, azure/cpu-bound start 1200, 200 steps x 15s, CPU limit 200m | 2026-10-08 15:23 |
| 2026-10-08 15:21 | OPE harness on_w2_truth_pred70: pred70 eps=0, azure/cpu-bound start 1200, 200 steps x 15s, CPU limit 200m | 2026-10-08 16:14 |
| 2026-10-08 16:12 | OPE harness on_w3_log_eps0.1_r1: dithered eps=0.1, bitbrains/cpu-bound start 950, 200 steps x 15s, CPU limit 200m | 2026-10-08 17:05 |
| 2026-10-08 17:03 | OPE harness on_w3_log_eps0_r1: dithered eps=0, bitbrains/cpu-bound start 950, 200 steps x 15s, CPU limit 200m | 2026-10-08 17:56 |
| 2026-10-08 17:55 | OPE harness on_w3_log_eps0.1_r2: dithered eps=0.1, bitbrains/cpu-bound start 950, 200 steps x 15s, CPU limit 200m | 2026-10-08 18:48 |
| 2026-10-08 18:46 | OPE harness on_w3_log_eps0_r2: dithered eps=0, bitbrains/cpu-bound start 950, 200 steps x 15s, CPU limit 200m | 2026-10-08 19:39 |
| 2026-10-08 19:38 | OPE harness on_w3_truth_hpa30: hpa30 eps=0, bitbrains/cpu-bound start 950, 200 steps x 15s, CPU limit 200m | 2026-10-08 20:31 |
| 2026-10-08 20:30 | OPE harness on_w3_truth_hpa50: hpa50 eps=0, bitbrains/cpu-bound start 950, 200 steps x 15s, CPU limit 200m | 2026-10-08 21:23 |
| 2026-10-08 21:21 | OPE harness on_w3_truth_hpa85: hpa85 eps=0, bitbrains/cpu-bound start 950, 200 steps x 15s, CPU limit 200m | 2026-10-08 22:14 |
| 2026-10-08 22:13 | OPE harness on_w3_truth_hpa95: hpa95 eps=0, bitbrains/cpu-bound start 950, 200 steps x 15s, CPU limit 200m | 2026-10-08 23:06 |
| 2026-10-08 23:04 | OPE harness on_w3_truth_hpa70_stab0: hpa70_stab0 eps=0, bitbrains/cpu-bound start 950, 200 steps x 15s, CPU limit 200m | 2026-10-08 23:57 |
| 2026-10-08 23:55 | OPE harness on_w3_truth_hpa70_stab10: hpa70_stab10 eps=0, bitbrains/cpu-bound start 950, 200 steps x 15s, CPU limit 200m | 2026-10-09 00:48 |
| 2026-10-09 00:47 | OPE harness on_w3_truth_slo_cost: slo_cost eps=0, bitbrains/cpu-bound start 950, 200 steps x 15s, CPU limit 200m | 2026-10-09 01:40 |
| 2026-10-09 01:38 | OPE harness on_w3_truth_pred70: pred70 eps=0, bitbrains/cpu-bound start 950, 200 steps x 15s, CPU limit 200m | 2026-10-09 02:31 |
| 2026-10-09 02:29 | OPE harness on_w1_truth_hpa30_r2: hpa30 eps=0, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-09 03:22 |
| 2026-10-09 03:21 | OPE harness on_w1_truth_hpa50_r2: hpa50 eps=0, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-09 04:14 |
| 2026-10-09 04:13 | OPE harness on_w1_truth_hpa85_r2: hpa85 eps=0, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-09 05:06 |
| 2026-10-09 05:04 | OPE harness on_w1_truth_hpa95_r2: hpa95 eps=0, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-09 05:57 |
| 2026-10-09 05:56 | OPE harness on_w1_truth_hpa70_stab0_r2: hpa70_stab0 eps=0, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-09 06:49 |
| 2026-10-09 06:47 | OPE harness on_w1_truth_hpa70_stab10_r2: hpa70_stab10 eps=0, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-09 07:40 |
| 2026-10-09 07:39 | OPE harness on_w1_truth_slo_cost_r2: slo_cost eps=0, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-09 08:32 |
| 2026-10-09 08:30 | OPE harness on_w1_truth_pred70_r2: pred70 eps=0, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-09 09:23 |
| 2026-10-09 09:56 | M5 batch finished 09:21 UTC: 28/28 runs exit 0; report real/runs/m5_report.md. Cluster idle, web-service 2/2, CPU limit still 200m. | - |
