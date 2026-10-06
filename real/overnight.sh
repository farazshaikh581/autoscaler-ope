#!/usr/bin/env bash
# Overnight OPE batch on saul, detached:
#   setsid nohup real/overnight.sh > real/runs/overnight.log 2>&1 < /dev/null &
# Waits for the pilot (PILOT DONE), checks its gate, runs the 15 live runs in the
# pre-authorised order, then writes real/runs/overnight_report.md. A failed run is
# logged and skipped (no retries). The harness does its own preflight, RUNLOG line
# and scale-back-to-2 for every run.
set -uo pipefail
cd "$(dirname "$0")/.."
PY="$HOME/hv-venv/bin/python"
LIVE_CPUS=0,2,4,6,8,10,12,14
ANALYSIS_CPUS=16,18,20,22,24,26,28,30,32,34,36,38
IDX=real/runs/overnight_index.csv
log() { echo "[$(date -u +%FT%TZ)] $*"; }

log "overnight runner start (pid $$); waiting for PILOT DONE"
while ! grep -q "PILOT DONE" real/runs/pilot.log 2>/dev/null; do
  if ! pgrep -f '^bash real/pilot.sh' >/dev/null; then
    log "pilot runner is gone without PILOT DONE: not starting the batch"; exit 1
  fi
  sleep 60
done
log "pilot done; gate check"
if ! "$PY" real/gate_check.py; then
  log "GATE FAILED ((a) load or (e) harness): batch not started"
  echo "# Overnight batch NOT started: pilot gate (a) or (e) failed. See real/runs/overnight.log and pilot_report.md." \
    > real/runs/overnight_report.md
  exit 1
fi

# window: family workload start; dither seed int = 10000*window + 100*eps_index + rep,
# the simulation scheme (window/cell, index of eps in (0,.02,.05,.1,.2), rep).
W1="--family bitbrains --workload io-bound --start 4725"
W2="--family azure --workload cpu-bound --start 1200"
RUNS=(
  "on_w1_log_eps0.1_r1|$W1 --policy dithered --eps 0.1 --seed 10301"
  "on_w1_log_eps0_r1|$W1 --policy dithered --eps 0 --seed 10001"
  "on_w1_truth_hpa90|$W1 --policy hpa90"
  "on_w1_truth_slo_cost|$W1 --policy slo_cost"
  "on_w1_truth_hpa30|$W1 --policy hpa30"
  "on_w1_truth_hpa70_stab0|$W1 --policy hpa70_stab0"
  "on_w1_log_eps0.1_r2|$W1 --policy dithered --eps 0.1 --seed 10302"
  "on_w1_log_eps0_r2|$W1 --policy dithered --eps 0 --seed 10002"
  "on_w1_truth_hpa50|$W1 --policy hpa50"
  "on_w1_truth_hpa70_stab10|$W1 --policy hpa70_stab10"
  "on_w1_truth_pred70|$W1 --policy pred70"
  "on_w2_log_eps0.1_r1|$W2 --policy dithered --eps 0.1 --seed 20301"
  "on_w2_log_eps0_r1|$W2 --policy dithered --eps 0 --seed 20001"
  "on_w2_log_eps0.1_r2|$W2 --policy dithered --eps 0.1 --seed 20302"
  "on_w2_log_eps0_r2|$W2 --policy dithered --eps 0 --seed 20002"
)
[ -f "$IDX" ] || echo "n,tag,start_utc,end_utc,exit_code,ope_commit,harness_blob" > "$IDX"
n=0
for spec in "${RUNS[@]}"; do
  n=$((n + 1)); tag="${spec%%|*}"; args="${spec#*|}"
  if [ -s "real/runs/${tag}.csv" ] && [ "$(wc -l < "real/runs/${tag}.csv")" -ge 201 ]; then
    log "[$n/15] $tag already complete, skipping"; continue
  fi
  commit=$(git rev-parse --short HEAD); hblob=$(git hash-object real/harness.py)
  start=$(date -u +%FT%TZ); log "[$n/15] $tag start (commit $commit, harness $hblob)"
  # shellcheck disable=SC2086
  taskset -c "$LIVE_CPUS" "$PY" real/harness.py --live $args --steps 200 --tag "$tag"
  rc=$?
  echo "$n,$tag,$start,$(date -u +%FT%TZ),$rc,$commit,$hblob" >> "$IDX"
  if [ $rc -ne 0 ]; then log "[$n/15] $tag FAILED (exit $rc); skipping to the next run"; else log "[$n/15] $tag done"; fi
done
log "batch finished; analysis on CPUs $ANALYSIS_CPUS at nice 19"
OMP_NUM_THREADS=1 taskset -c "$ANALYSIS_CPUS" nice -n 19 "$PY" real/overnight_report.py > real/runs/overnight_report.md 2>&1
log "report exit $?: real/runs/overnight_report.md"
log "OVERNIGHT DONE"
