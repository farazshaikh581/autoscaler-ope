#!/usr/bin/env bash
# Deploy the OPE study's applications into the hv-phase0 namespace of the current
# kubectl context. Needs only kubectl and a cluster that can pull python:3.10-slim.
#   deploy/apply.sh                  # both apps
#   deploy/apply.sh api-service      # one app
# The live harness checks that the cluster runs exactly deploy/<app>/app.py.
set -euo pipefail
cd "$(dirname "$0")"
declare -A CM=([web-service]=web-app-code [api-service]=api-app-code)
apps=("${@:-web-service api-service}")
read -r -a apps <<< "${apps[*]}"
kubectl create namespace hv-phase0 --dry-run=client -o yaml | kubectl apply -f -
for app in "${apps[@]}"; do
  [ -n "${CM[$app]:-}" ] || { echo "unknown app $app" >&2; exit 1; }
  kubectl -n hv-phase0 create configmap "${CM[$app]}" --from-file=app.py="$app/app.py" \
    --dry-run=client -o yaml | kubectl apply -f -
  kubectl apply -f "$app/manifest.yaml"
  kubectl -n hv-phase0 rollout status deploy/"$app" --timeout=180s
done
