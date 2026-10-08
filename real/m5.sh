#!/usr/bin/env bash
# M5 batch on saul, detached (about 24 h):
#   setsid nohup bash real/m5.sh > real/runs/m5.log 2>&1 < /dev/null &
# Held-out validation of the demand-space twin (ope/twin.py, frozen before this batch):
# W2 truth runs, W3 logs and truth runs, then a second truth rep on W1. A failed run is
# logged and skipped (no retries); complete runs are skipped on a restart. The harness
# does its own preflight, RUNLOG line and scale-back-to-2 for every run. Ends with
# real/runs/m5_report.md.
set -uo pipefail
cd "$(dirname "$0")/.."
PY="$HOME/hv-venv/bin/python"
LIVE_CPUS=0,2,4,6,8,10,12,14
ANALYSIS_CPUS=16,18,20,22,24,26,28,30,32,34,36,38
IDX=real/runs/m5_index.csv
log() { echo "[$(date -u +%FT%TZ)] $*"; }

W1="--family bitbrains --workload io-bound --start 4725"
W2="--family azure --workload cpu-bound --start 1200"
W3="--family bitbrains --workload cpu-bound --start 950"
TARGETS=(hpa30 hpa50 hpa85 hpa95 hpa70_stab0 hpa70_stab10 slo_cost pred70)
RUNS=()
for t in "${TARGETS[@]}"; do RUNS+=("on_w2_truth_$t|$W2 --policy $t"); done
# dither seed = 10000*window + 100*eps_index + rep, as in the overnight batch
RUNS+=("on_w3_log_eps0.1_r1|$W3 --policy dithered --eps 0.1 --seed 30301"
       "on_w3_log_eps0_r1|$W3 --policy dithered --eps 0 --seed 30001"
       "on_w3_log_eps0.1_r2|$W3 --policy dithered --eps 0.1 --seed 30302"
       "on_w3_log_eps0_r2|$W3 --policy dithered --eps 0 --seed 30002")
for t in "${TARGETS[@]}"; do RUNS+=("on_w3_truth_$t|$W3 --policy $t"); done
for t in "${TARGETS[@]}"; do RUNS+=("on_w1_truth_${t}_r2|$W1 --policy $t"); done

log "M5 runner start (pid $$), ${#RUNS[@]} runs"
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
OMP_NUM_THREADS=1 taskset -c "$ANALYSIS_CPUS" nice -n 19 "$PY" real/m5_report.py > real/runs/m5_report.md 2>&1
log "report exit $?: real/runs/m5_report.md"
log "M5 DONE"
