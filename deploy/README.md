# Applications under test

Both applications run on any Kubernetes cluster that can pull the public
`python:3.10-slim` image. The code is mounted from a ConfigMap, so nothing is built and
no registry is needed. Nothing here depends on another repository or cluster.

```
deploy/apply.sh                # namespace hv-phase0 and both apps
deploy/apply.sh api-service    # one app
```

| App | Request | Per-request CPU | Latency without CPU work |
|---|---|---|---|
| `web-service` | 250 chained SHA-256 hashes of 1 KiB | fixed | none |
| `api-service` | build N JSON records (log-normal N, median 40, sigma 0.9), serialise, parse, sort, hash | heavy-tailed | downstream wait, exponential, mean 3 ms |

Both run with CPU request = limit = 200m, 2 replicas at rest, on port 8080 behind a
ClusterIP service on port 80, with `/health` as the readiness probe.

`real/harness.py --app <app>` refuses to start unless the cluster's ConfigMap holds
exactly `deploy/<app>/app.py`. It records that file's sha256 in each run's metadata.

`web-service` was first deployed from the joint_hv_autoscaler repository (phase0). The
files here reproduce the deployment on saul with no difference (`kubectl diff`,
2026-10-15). The one change from that repository is the CPU limit: 200m here, the value of
every OPE live run, against 500m there.

Load scale: `real/kneecheck.py --app <app>` measures the CPU per request on 2 pods and
where the latency knee sits. Each app's `max_rps` in `real/harness.py` (`APPS`) is set so
that the same trace step asks for the same number of 200m pods:

    max_rps(app) = 2050 * 1.727 / m_per_rps(app)

Here 1.727 mcores per rps is web-service's measured cost.
