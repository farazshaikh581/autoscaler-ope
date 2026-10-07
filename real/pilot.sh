#!/usr/bin/env bash
# M4 pilot, detached: W1 HPA-70 then W1 HPA-95 (one live run each, CPU limit = request
# = 200m), then the gate report. Survives logout:
#   setsid nohup real/pilot.sh > real/runs/pilot.log 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/.."
PY="$HOME/hv-venv/bin/python"
CPUS=0,2,4,6,8,10,12,14                       # live driver: even CPUs 0-14 only
log() { echo "[$(date -u +%FT%TZ)] $*"; }

log "pilot start (pid $$)"
for pol in hpa70 hpa95; do
  log "W1 $pol: start"
  if ! taskset -c "$CPUS" "$PY" real/harness.py --live --policy "$pol" --family bitbrains --workload io-bound \
       --start 4725 --steps 200 --tag "pilot_w1_${pol}"; then
    log "W1 $pol: FAILED, stopping the pilot"
    break
  fi
  log "W1 $pol: done"
done

"$PY" real/pilot_report.py > real/runs/pilot_report.md 2>&1 && log "report: real/runs/pilot_report.md"
log "PILOT DONE"
