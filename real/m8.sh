#!/usr/bin/env bash
# M8 batch on saul, detached (about 17.7 h):
#   setsid nohup bash real/m8.sh > real/runs/m8.log 2>&1 < /dev/null &
# A second pre-registered held-out window W5 (logs + truth) and a second truth run on W4,
# for twin v2 and the queueing baseline (both frozen with real/PLAN_M8.md). A failed run is
# logged and skipped; complete runs are skipped on a restart. Ends with
# real/runs/m8_report.md.
set -uo pipefail
cd "$(dirname "$0")/.."
PY="$HOME/hv-venv/bin/python"
LIVE_CPUS=0,2,4,6,8,10,12,14
ANALYSIS_CPUS=16,18,20,22,24,26,28,30,32,34,36,38
IDX=real/runs/m8_index.csv
log() { echo "[$(date -u +%FT%TZ)] $*"; }

W4="--family azure --workload cpu-bound --start 4075"
W5="--family bitbrains --workload io-bound --start 6150"
TARGETS=(hpa30 hpa50 hpa85 hpa95 hpa70_stab0 hpa70_stab10 slo_cost pred70)
RUNS=()
# dither seed = 10000*window + 100*eps_index + rep, as in M5/M6
RUNS+=("on_w5_log_eps0.1_r1|$W5 --policy dithered --eps 0.1 --seed 50301"
       "on_w5_log_eps0_r1|$W5 --policy dithered --eps 0 --seed 50001"
       "on_w5_log_eps0.1_r2|$W5 --policy dithered --eps 0.1 --seed 50302"
       "on_w5_log_eps0_r2|$W5 --policy dithered --eps 0 --seed 50002")
for t in "${TARGETS[@]}"; do RUNS+=("on_w5_truth_$t|$W5 --policy $t"); done
for t in "${TARGETS[@]}"; do RUNS+=("on_w4_truth_${t}_r2|$W4 --policy $t"); done

log "M8 runner start (pid $$), ${#RUNS[@]} runs"
[ -f "$IDX" ] || echo "n,tag,start_utc,end_utc,exit_code,ope_commit,harness_blob" > "$IDX"
n=0
for spec in "${RUNS[@]}"; do
  n=$((n + 1)); tag="${spec%%|*}"; args="${spec#*|}"
  if [ -s "real/runs/${tag}.csv" ] && [ "$(wc -l < "real/runs/${tag}.csv")" -ge 201 ]; then
    log "[$n/${#RUNS[@]}] $tag already complete, skipping"; continue
  fi
  commit=$(git rev-parse --short HEAD); hblob=$(git hash-object real/harness.py)
  start=$(date -u +%FT%TZ); log "[$n/${#RUNS[@]}] $tag start (commit $commit, harness $hblob)"
  # shellcheck disable=SC2086
  taskset -c "$LIVE_CPUS" "$PY" real/harness.py --live $args --steps 200 --tag "$tag"
  rc=$?
  echo "$n,$tag,$start,$(date -u +%FT%TZ),$rc,$commit,$hblob" >> "$IDX"
  if [ $rc -ne 0 ]; then log "[$n/${#RUNS[@]}] $tag FAILED (exit $rc); skipping to the next run"; else log "[$n/${#RUNS[@]}] $tag done"; fi
done
log "batch finished; analysis on CPUs $ANALYSIS_CPUS at nice 19"
OMP_NUM_THREADS=1 taskset -c "$ANALYSIS_CPUS" nice -n 19 "$PY" real/m8_report.py > real/runs/m8_report.md 2>&1
log "report exit $?: real/runs/m8_report.md"
log "M8 DONE"
