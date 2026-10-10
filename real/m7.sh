#!/usr/bin/env bash
# M7 batch on saul, detached (about 7 h):
#   setsid nohup bash real/m7.sh > real/runs/m7.log 2>&1 < /dev/null &
# Tests the knee-share flag (ope.twin FLAG_KNEE, frozen before this batch) on logs from
# dithered HPA-85 and HPA-50 on W3 and W4, whose truth runs exist. A failed run is logged
# and skipped; complete runs are skipped on a restart. Ends with real/runs/m7_report.md.
set -uo pipefail
cd "$(dirname "$0")/.."
PY="$HOME/hv-venv/bin/python"
LIVE_CPUS=0,2,4,6,8,10,12,14
ANALYSIS_CPUS=16,18,20,22,24,26,28,30,32,34,36,38
IDX=real/runs/m7_index.csv
log() { echo "[$(date -u +%FT%TZ)] $*"; }

W1="--family bitbrains --workload io-bound --start 4725"
W2="--family azure --workload cpu-bound --start 1200"
W3="--family bitbrains --workload cpu-bound --start 950"
W4="--family azure --workload cpu-bound --start 4075"
# dither seed = 10000*window + 100*eps_index + rep, +10 (HPA-50) / +20 (HPA-85)
RUNS=("on_w3_log_b85_eps0.1_r1|$W3 --policy dithered --eps 0.1 --behaviour-util 0.85 --seed 30321"
      "on_w3_log_b85_eps0.1_r2|$W3 --policy dithered --eps 0.1 --behaviour-util 0.85 --seed 30322"
      "on_w4_log_b85_eps0.1_r1|$W4 --policy dithered --eps 0.1 --behaviour-util 0.85 --seed 40321"
      "on_w4_log_b85_eps0.1_r2|$W4 --policy dithered --eps 0.1 --behaviour-util 0.85 --seed 40322"
      "on_w3_log_b50_eps0.1_r1|$W3 --policy dithered --eps 0.1 --behaviour-util 0.50 --seed 30311"
      "on_w3_log_b50_eps0.1_r2|$W3 --policy dithered --eps 0.1 --behaviour-util 0.50 --seed 30312"
      "on_w4_log_b50_eps0.1_r1|$W4 --policy dithered --eps 0.1 --behaviour-util 0.50 --seed 40311"
      "on_w4_log_b50_eps0.1_r2|$W4 --policy dithered --eps 0.1 --behaviour-util 0.50 --seed 40312")

log "M7 runner start (pid $$), ${#RUNS[@]} runs"
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
OMP_NUM_THREADS=1 taskset -c "$ANALYSIS_CPUS" nice -n 19 "$PY" real/m7_report.py > real/runs/m7_report.md 2>&1
log "report exit $?: real/runs/m7_report.md"
log "M7 DONE"
