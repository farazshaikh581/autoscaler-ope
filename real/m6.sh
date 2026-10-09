#!/usr/bin/env bash
# M6 batch on saul, detached (about 27 h):
#   setsid nohup bash real/m6.sh > real/runs/m6.log 2>&1 < /dev/null &
# Tests the log-only twin (ope.twin.twin_v2, frozen before this batch): a new window W4
# (logs + truth), logs from two other behaviour policies on W1, and a second truth run on
# W2 and W3. A failed run is logged and skipped; complete runs are skipped on a restart.
# Ends with real/runs/m6_report.md.
set -uo pipefail
cd "$(dirname "$0")/.."
PY="$HOME/hv-venv/bin/python"
LIVE_CPUS=0,2,4,6,8,10,12,14
ANALYSIS_CPUS=16,18,20,22,24,26,28,30,32,34,36,38
IDX=real/runs/m6_index.csv
log() { echo "[$(date -u +%FT%TZ)] $*"; }

W1="--family bitbrains --workload io-bound --start 4725"
W2="--family azure --workload cpu-bound --start 1200"
W3="--family bitbrains --workload cpu-bound --start 950"
W4="--family azure --workload cpu-bound --start 4075"
TARGETS=(hpa30 hpa50 hpa85 hpa95 hpa70_stab0 hpa70_stab10 slo_cost pred70)
RUNS=()
# dither seed = 10000*window + 100*eps_index + rep (+10 / +20 for the other loggers on W1)
RUNS+=("on_w4_log_eps0.1_r1|$W4 --policy dithered --eps 0.1 --seed 40301"
       "on_w4_log_eps0_r1|$W4 --policy dithered --eps 0 --seed 40001"
       "on_w4_log_eps0.1_r2|$W4 --policy dithered --eps 0.1 --seed 40302"
       "on_w4_log_eps0_r2|$W4 --policy dithered --eps 0 --seed 40002")
for t in "${TARGETS[@]}"; do RUNS+=("on_w4_truth_$t|$W4 --policy $t"); done
RUNS+=("on_w1_log_b85_eps0.1_r1|$W1 --policy dithered --eps 0.1 --behaviour-util 0.85 --seed 10321"
       "on_w1_log_b85_eps0.1_r2|$W1 --policy dithered --eps 0.1 --behaviour-util 0.85 --seed 10322"
       "on_w1_log_b50_eps0.1_r1|$W1 --policy dithered --eps 0.1 --behaviour-util 0.50 --seed 10311"
       "on_w1_log_b50_eps0.1_r2|$W1 --policy dithered --eps 0.1 --behaviour-util 0.50 --seed 10312")
for t in "${TARGETS[@]}"; do RUNS+=("on_w2_truth_${t}_r2|$W2 --policy $t"); done
for t in "${TARGETS[@]}"; do RUNS+=("on_w3_truth_${t}_r2|$W3 --policy $t"); done

log "M6 runner start (pid $$), ${#RUNS[@]} runs"
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
OMP_NUM_THREADS=1 taskset -c "$ANALYSIS_CPUS" nice -n 19 "$PY" real/m6_report.py > real/runs/m6_report.md 2>&1
log "report exit $?: real/runs/m6_report.md"
log "M6 DONE"
