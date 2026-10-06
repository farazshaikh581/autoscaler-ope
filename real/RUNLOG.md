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
