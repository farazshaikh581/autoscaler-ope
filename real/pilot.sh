#!/usr/bin/env bash
# M4 pilot, detached: W1 HPA-70 then W1 HPA-95 (one live run each), then the webhook
# pin requested by the node0 session (only in this gap, no live run active), then the
# gate report. Survives logout:
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

# Webhook pin (node0 session's request, b578fff): only now, with no live run active.
if pgrep -f "real/harness.py --live" >/dev/null; then
  log "webhook pin skipped: a live harness is still running"
else
  git -C "$HOME/joint_hv_autoscaler" pull --ff-only -q && log "joint_hv_autoscaler at $(git -C "$HOME/joint_hv_autoscaler" rev-parse --short HEAD)"
  before=$(kubectl get mutatingwebhookconfiguration vpa-webhook-config -o jsonpath='{.webhooks[0].namespaceSelector}')
  kubectl patch mutatingwebhookconfiguration vpa-webhook-config --type json -p \
    '[{"op":"replace","path":"/webhooks/0/namespaceSelector","value":{"matchExpressions":[{"key":"kubernetes.io/metadata.name","operator":"In","values":["hv-phase0"]}]}}]'
  sleep 60
  after=$(kubectl get mutatingwebhookconfiguration vpa-webhook-config -o jsonpath='{.webhooks[0].namespaceSelector}')
  log "webhook selector before: $before"
  log "webhook selector after 60 s: $after"
  echo "| $(date -u '+%Y-%m-%d %H:%M') | VPA webhook namespaceSelector pinned to In [hv-phase0] (node0 request, after pilot runs); after 60 s: $after | - |" >> real/RUNLOG.md
fi

"$PY" real/pilot_report.py > real/runs/pilot_report.md 2>&1 && log "report: real/runs/pilot_report.md"
log "PILOT DONE"
