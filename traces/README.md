# Workload traces

Four class-representative series used by the live runs, copied byte for byte from
joint-hv-autoscaler `phase1/traces/` (Azure) and `phase1/traces_bitbrains/` (Bitbrains) at
commit de86f80. Each `.npz` holds `cpu_norm`, `mem_MB` and `io` per 15 s step. Checksums:
`SHA256SUMS` (`sha256sum -c SHA256SUMS`).

| File | Windows used |
|---|---|
| `azure/cpu-bound.npz` | W2 (start 1200), W4 (start 4075) |
| `bitbrains/cpu-bound.npz` | W3 (start 950) |
| `bitbrains/io-bound.npz` | W1 (start 4725), W5 (start 6150) |
| `azure/io-bound.npz` | none (kept for `real/pick_w5.py`) |

Load: `rps_t = load_frac_t * intensity * 2050` with `load_frac` = `cpu_norm` over its
99th percentile, clipped to 1.5; intensity 1.0 for cpu-bound, 0.5 for io-bound
(`ope/traces.py`).
