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
| 2026-10-09 10:55 | OPE harness on_w4_log_eps0.1_r1: dithered eps=0.1, azure/cpu-bound start 4075, 200 steps x 15s, CPU limit 200m | 2026-10-09 11:48 |
| 2026-10-09 11:46 | OPE harness on_w4_log_eps0_r1: dithered eps=0, azure/cpu-bound start 4075, 200 steps x 15s, CPU limit 200m | 2026-10-09 12:39 |
| 2026-10-09 12:37 | OPE harness on_w4_log_eps0.1_r2: dithered eps=0.1, azure/cpu-bound start 4075, 200 steps x 15s, CPU limit 200m | 2026-10-09 13:30 |
| 2026-10-09 13:28 | OPE harness on_w4_log_eps0_r2: dithered eps=0, azure/cpu-bound start 4075, 200 steps x 15s, CPU limit 200m | 2026-10-09 14:21 |
| 2026-10-09 14:20 | OPE harness on_w4_truth_hpa30: hpa30 eps=0, azure/cpu-bound start 4075, 200 steps x 15s, CPU limit 200m | 2026-10-09 15:13 |
| 2026-10-09 15:11 | OPE harness on_w4_truth_hpa50: hpa50 eps=0, azure/cpu-bound start 4075, 200 steps x 15s, CPU limit 200m | 2026-10-09 16:04 |
| 2026-10-09 16:02 | OPE harness on_w4_truth_hpa85: hpa85 eps=0, azure/cpu-bound start 4075, 200 steps x 15s, CPU limit 200m | 2026-10-09 16:55 |
| 2026-10-09 16:53 | OPE harness on_w4_truth_hpa95: hpa95 eps=0, azure/cpu-bound start 4075, 200 steps x 15s, CPU limit 200m | 2026-10-09 17:46 |
| 2026-10-09 17:44 | OPE harness on_w4_truth_hpa70_stab0: hpa70_stab0 eps=0, azure/cpu-bound start 4075, 200 steps x 15s, CPU limit 200m | 2026-10-09 18:37 |
| 2026-10-09 18:36 | OPE harness on_w4_truth_hpa70_stab10: hpa70_stab10 eps=0, azure/cpu-bound start 4075, 200 steps x 15s, CPU limit 200m | 2026-10-09 19:29 |
| 2026-10-09 19:27 | OPE harness on_w4_truth_slo_cost: slo_cost eps=0, azure/cpu-bound start 4075, 200 steps x 15s, CPU limit 200m | 2026-10-09 20:20 |
| 2026-10-09 20:18 | OPE harness on_w4_truth_pred70: pred70 eps=0, azure/cpu-bound start 4075, 200 steps x 15s, CPU limit 200m | 2026-10-09 21:11 |
| 2026-10-09 21:09 | OPE harness on_w1_log_b85_eps0.1_r1: dithered eps=0.1, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-09 22:02 |
| 2026-10-09 22:01 | OPE harness on_w1_log_b85_eps0.1_r2: dithered eps=0.1, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-09 22:54 |
| 2026-10-09 22:52 | OPE harness on_w1_log_b50_eps0.1_r1: dithered eps=0.1, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-09 23:45 |
| 2026-10-09 23:44 | OPE harness on_w1_log_b50_eps0.1_r2: dithered eps=0.1, bitbrains/io-bound start 4725, 200 steps x 15s, CPU limit 200m | 2026-10-10 00:37 |
| 2026-10-10 00:35 | OPE harness on_w2_truth_hpa30_r2: hpa30 eps=0, azure/cpu-bound start 1200, 200 steps x 15s, CPU limit 200m | 2026-10-10 01:28 |
| 2026-10-10 01:27 | OPE harness on_w2_truth_hpa50_r2: hpa50 eps=0, azure/cpu-bound start 1200, 200 steps x 15s, CPU limit 200m | 2026-10-10 02:20 |
| 2026-10-10 02:19 | OPE harness on_w2_truth_hpa85_r2: hpa85 eps=0, azure/cpu-bound start 1200, 200 steps x 15s, CPU limit 200m | 2026-10-10 03:12 |
| 2026-10-10 03:10 | OPE harness on_w2_truth_hpa95_r2: hpa95 eps=0, azure/cpu-bound start 1200, 200 steps x 15s, CPU limit 200m | 2026-10-10 04:03 |
| 2026-10-10 04:01 | OPE harness on_w2_truth_hpa70_stab0_r2: hpa70_stab0 eps=0, azure/cpu-bound start 1200, 200 steps x 15s, CPU limit 200m | 2026-10-10 04:54 |
| 2026-10-10 04:52 | OPE harness on_w2_truth_hpa70_stab10_r2: hpa70_stab10 eps=0, azure/cpu-bound start 1200, 200 steps x 15s, CPU limit 200m | 2026-10-10 05:45 |
| 2026-10-10 05:43 | OPE harness on_w2_truth_slo_cost_r2: slo_cost eps=0, azure/cpu-bound start 1200, 200 steps x 15s, CPU limit 200m | 2026-10-10 06:36 |
| 2026-10-10 06:35 | OPE harness on_w2_truth_pred70_r2: pred70 eps=0, azure/cpu-bound start 1200, 200 steps x 15s, CPU limit 200m | 2026-10-10 07:28 |
| 2026-10-10 07:26 | OPE harness on_w3_truth_hpa30_r2: hpa30 eps=0, bitbrains/cpu-bound start 950, 200 steps x 15s, CPU limit 200m | 2026-10-10 08:19 |
| 2026-10-10 08:17 | OPE harness on_w3_truth_hpa50_r2: hpa50 eps=0, bitbrains/cpu-bound start 950, 200 steps x 15s, CPU limit 200m | 2026-10-10 09:10 |
| 2026-10-10 09:08 | OPE harness on_w3_truth_hpa85_r2: hpa85 eps=0, bitbrains/cpu-bound start 950, 200 steps x 15s, CPU limit 200m | 2026-10-10 10:01 |
| 2026-10-10 10:00 | OPE harness on_w3_truth_hpa95_r2: hpa95 eps=0, bitbrains/cpu-bound start 950, 200 steps x 15s, CPU limit 200m | 2026-10-10 10:53 |
| 2026-10-10 10:51 | OPE harness on_w3_truth_hpa70_stab0_r2: hpa70_stab0 eps=0, bitbrains/cpu-bound start 950, 200 steps x 15s, CPU limit 200m | 2026-10-10 11:44 |
| 2026-10-10 11:42 | OPE harness on_w3_truth_hpa70_stab10_r2: hpa70_stab10 eps=0, bitbrains/cpu-bound start 950, 200 steps x 15s, CPU limit 200m | 2026-10-10 12:35 |
| 2026-10-10 12:34 | OPE harness on_w3_truth_slo_cost_r2: slo_cost eps=0, bitbrains/cpu-bound start 950, 200 steps x 15s, CPU limit 200m | 2026-10-10 13:27 |
| 2026-10-10 13:26 | OPE harness on_w3_truth_pred70_r2: pred70 eps=0, bitbrains/cpu-bound start 950, 200 steps x 15s, CPU limit 200m | 2026-10-10 14:19 |
| 2026-10-10 18:56 | M6 batch finished 14:17 UTC: 32/32 runs exit 0; report real/runs/m6_report.md. Cluster idle, web-service 2/2, CPU limit still 200m. | - |
| 2026-10-10 21:49 | OPE harness on_w3_log_b85_eps0.1_r1: dithered eps=0.1, bitbrains/cpu-bound start 950, 200 steps x 15s, CPU limit 200m | 2026-10-10 22:42 |
| 2026-10-10 22:40 | OPE harness on_w3_log_b85_eps0.1_r2: dithered eps=0.1, bitbrains/cpu-bound start 950, 200 steps x 15s, CPU limit 200m | 2026-10-10 23:33 |
| 2026-10-10 23:31 | OPE harness on_w4_log_b85_eps0.1_r1: dithered eps=0.1, azure/cpu-bound start 4075, 200 steps x 15s, CPU limit 200m | 2026-10-11 00:24 |
| 2026-10-11 00:22 | OPE harness on_w4_log_b85_eps0.1_r2: dithered eps=0.1, azure/cpu-bound start 4075, 200 steps x 15s, CPU limit 200m | 2026-10-11 01:15 |
| 2026-10-11 01:13 | OPE harness on_w3_log_b50_eps0.1_r1: dithered eps=0.1, bitbrains/cpu-bound start 950, 200 steps x 15s, CPU limit 200m | 2026-10-11 02:06 |
| 2026-10-11 02:05 | OPE harness on_w3_log_b50_eps0.1_r2: dithered eps=0.1, bitbrains/cpu-bound start 950, 200 steps x 15s, CPU limit 200m | 2026-10-11 02:58 |
| 2026-10-11 02:56 | OPE harness on_w4_log_b50_eps0.1_r1: dithered eps=0.1, azure/cpu-bound start 4075, 200 steps x 15s, CPU limit 200m | 2026-10-11 03:49 |
| 2026-10-11 03:48 | OPE harness on_w4_log_b50_eps0.1_r2: dithered eps=0.1, azure/cpu-bound start 4075, 200 steps x 15s, CPU limit 200m | 2026-10-11 04:41 |
| 2026-10-11 19:45 | M7 batch finished 04:39 UTC: 8/8 runs exit 0; report real/runs/m7_report.md (D1 FAIL, D2 PASS). Cluster idle, web-service 2/2, CPU limit still 200m. | - |
| 2026-10-14 12:34 | OPE harness on_w5_log_eps0.1_r1: dithered eps=0.1, bitbrains/io-bound start 6150, 200 steps x 15s, CPU limit 200m | 2026-10-14 13:27 |
| 2026-10-14 13:25 | OPE harness on_w5_log_eps0_r1: dithered eps=0, bitbrains/io-bound start 6150, 200 steps x 15s, CPU limit 200m | 2026-10-14 14:18 |
| 2026-10-14 14:17 | OPE harness on_w5_log_eps0.1_r2: dithered eps=0.1, bitbrains/io-bound start 6150, 200 steps x 15s, CPU limit 200m | 2026-10-14 15:10 |
| 2026-10-14 15:08 | OPE harness on_w5_log_eps0_r2: dithered eps=0, bitbrains/io-bound start 6150, 200 steps x 15s, CPU limit 200m | 2026-10-14 16:01 |
| 2026-10-14 16:00 | OPE harness on_w5_truth_hpa30: hpa30 eps=0, bitbrains/io-bound start 6150, 200 steps x 15s, CPU limit 200m | 2026-10-14 16:53 |
| 2026-10-14 16:52 | OPE harness on_w5_truth_hpa50: hpa50 eps=0, bitbrains/io-bound start 6150, 200 steps x 15s, CPU limit 200m | 2026-10-14 17:45 |
| 2026-10-14 17:43 | OPE harness on_w5_truth_hpa85: hpa85 eps=0, bitbrains/io-bound start 6150, 200 steps x 15s, CPU limit 200m | 2026-10-14 18:36 |
| 2026-10-14 18:35 | OPE harness on_w5_truth_hpa95: hpa95 eps=0, bitbrains/io-bound start 6150, 200 steps x 15s, CPU limit 200m | 2026-10-14 19:28 |
| 2026-10-14 19:27 | OPE harness on_w5_truth_hpa70_stab0: hpa70_stab0 eps=0, bitbrains/io-bound start 6150, 200 steps x 15s, CPU limit 200m | 2026-10-14 20:20 |
| 2026-10-14 20:18 | OPE harness on_w5_truth_hpa70_stab10: hpa70_stab10 eps=0, bitbrains/io-bound start 6150, 200 steps x 15s, CPU limit 200m | 2026-10-14 21:11 |
| 2026-10-14 21:09 | OPE harness on_w5_truth_slo_cost: slo_cost eps=0, bitbrains/io-bound start 6150, 200 steps x 15s, CPU limit 200m | 2026-10-14 22:02 |
| 2026-10-14 22:01 | OPE harness on_w5_truth_pred70: pred70 eps=0, bitbrains/io-bound start 6150, 200 steps x 15s, CPU limit 200m | 2026-10-14 22:54 |
| 2026-10-14 22:52 | OPE harness on_w4_truth_hpa30_r2: hpa30 eps=0, azure/cpu-bound start 4075, 200 steps x 15s, CPU limit 200m | 2026-10-14 23:45 |
| 2026-10-14 23:44 | OPE harness on_w4_truth_hpa50_r2: hpa50 eps=0, azure/cpu-bound start 4075, 200 steps x 15s, CPU limit 200m | 2026-10-15 00:37 |
| 2026-10-15 00:35 | OPE harness on_w4_truth_hpa85_r2: hpa85 eps=0, azure/cpu-bound start 4075, 200 steps x 15s, CPU limit 200m | 2026-10-15 01:28 |
| 2026-10-15 01:26 | OPE harness on_w4_truth_hpa95_r2: hpa95 eps=0, azure/cpu-bound start 4075, 200 steps x 15s, CPU limit 200m | 2026-10-15 02:19 |
| 2026-10-15 02:18 | OPE harness on_w4_truth_hpa70_stab0_r2: hpa70_stab0 eps=0, azure/cpu-bound start 4075, 200 steps x 15s, CPU limit 200m | 2026-10-15 03:11 |
| 2026-10-15 03:09 | OPE harness on_w4_truth_hpa70_stab10_r2: hpa70_stab10 eps=0, azure/cpu-bound start 4075, 200 steps x 15s, CPU limit 200m | 2026-10-15 04:02 |
| 2026-10-15 04:00 | OPE harness on_w4_truth_slo_cost_r2: slo_cost eps=0, azure/cpu-bound start 4075, 200 steps x 15s, CPU limit 200m | 2026-10-15 04:53 |
| 2026-10-15 04:52 | OPE harness on_w4_truth_pred70_r2: pred70 eps=0, azure/cpu-bound start 4075, 200 steps x 15s, CPU limit 200m | 2026-10-15 05:45 |
| 2026-10-15 08:36 | M8 batch finished 05:43 UTC: 20/20 runs exit 0; report real/runs/m8_report.md (Q1 PASS, Q2 PASS, Q3 PASS 88%, Q4 PASS). Cluster idle, web-service 2/2, CPU limit still 200m. | - |
| 2026-10-15 08:45 | OPE harness smoke_saul_native: dithered eps=0, bitbrains/io-bound start 6150, 8 steps x 15s, CPU limit 200m | 2026-10-15 08:50 |
| 2026-10-15 08:48 | saul-native merged into main; smoke run (harness 2870ed6, joint_hv_autoscaler imports blocked) OK (same load and scaling as on_w5_log_eps0_r1 steps 0-7). Cluster idle, web-service 2/2, CPU limit still 200m. | - |
