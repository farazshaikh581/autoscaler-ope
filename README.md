# Evaluating Kubernetes autoscalers from their own logs

Can an operator estimate the SLA compliance and cost of a new autoscaling policy from
the logs of the policy that is running now, before deploying the new one?

This repository holds the code and data of our study on a k3s cluster. Replaying the
log gives wrong answers, because a new policy runs a different number of pods and each
pod then carries a different load. Our estimator, a twin built from the log, runs the
new policy's own code step by step and takes each step's outcome from logged steps with
a matching load per pod. On 32 test cases fixed before the runs, its median SLA error
was 0.8 percentage points, against 4.0 for the best baseline and 22.6 for replay.

All experiments are complete. Every number in the paper comes from the 128 live runs in
`real/runs/`.

## Contents

| Path | What it holds |
|---|---|
| `deploy/` | The two services under test (`web-service`, `api-service`) and `apply.sh` |
| `real/harness.py` | The live harness: a 15 s control loop that sends trace-driven load and scales the deployment |
| `ope/twin.py` | The twin |
| `ope/queue_baseline.py`, `real/overnight_report.py` | Baselines: replay, importance sampling, model-based, doubly robust, queueing |
| `ope/controllers.py` | The policies: HPA-style rules, SLO-cost rule, predictive HPA |
| `traces/` | The trace series behind windows W1 to W5, with checksums |
| `real/PLAN_M*.md` | Run plans with pass criteria, each committed before its runs |
| `real/m*_report.py`, `real/runs/m*_report.md` | The report of each batch, checked against its plan |
| `real/runs/` | Logs of all live runs and the per-case result tables |
| `real/RUNLOG.md` | One line per live run, written before the run started |

## The live runs

Cluster: k3s v1.35 on one server (Intel Xeon E5-2640 v4), with four KVM worker VMs of
two or three pinned cores. Each pod requests and is limited to 200 millicores, with 1
to 12 pods per service. A run is 200 steps of 15 s (50 minutes) on one trace window.

| Batch | Plan | Runs | What was run |
|---|---|---|---|
| M4 | `real/PLAN.md` | 16 | Pilot, logs and live runs on W1, logs on W2 |
| M5 | `real/PLAN_M5.md` | 28 | Logs and live runs on W3, live runs on W2, second live runs on W1 |
| M6 | `real/PLAN_M6.md` | 32 | Logs and live runs on W4, logs from HPA at 50% and 85% on W1, second live runs on W2 and W3 |
| M7 | `real/PLAN_M7.md` | 8 | Logs from HPA at 50% and 85% on W3 and W4 |
| M8 | `real/PLAN_M8.md` | 20 | Logs and live runs on W5, second live runs on W4 |
| M9 | `real/PLAN_M9.md` | 24 | Logs and live runs of the JSON API on W1 and W4 |

All six batches ran in full. The plans are kept as they were committed before their
runs, so they describe the runs in the future tense; the reports in `real/runs/` give
the outcomes.

Each run has three files, named `on_<window>_<role>_<policy>[_r<repeat>]`, where the
role is `log` (the logged policy, HPA at 70%) or `truth` (a target policy, run live as
ground truth); API runs start with `api_`:

- `.csv`: one row per step, with offered and achieved request rate, latency (mean, p50,
  p95, p99), success rate, CPU use and its metrics age, ready and requested pods, SLA
  outcome and cost;
- `.json`: the run's settings, the cluster state and the sha256 of the code that ran;
- `_pods.csv`: when each new pod was created and became ready.

Two runs were stopped early to fix the harness and then repeated in full. Their partial
files are kept for the record (`real/runs/ABORTED_*`, `real/runs/aborted/`) and are not
used anywhere; `real/RUNLOG.md` gives the reasons.

## Reproducing the results

The analysis needs Python 3.10 and `requirements.txt`, and no cluster:

```
pip install -r requirements.txt
python real/m8_report.py      # web service, test windows W4 and W5
python real/m9_report.py      # JSON API, test windows W1 and W4
```

Each report recomputes every estimator from the logs in `real/runs/` and prints the
tables of the matching `real/runs/m*_report.md`. The per-case results behind the
paper's Table I are `real/runs/m8_cells.csv` and `real/runs/m9_cells.csv`.
`python real/check_saul_native.py` checks that the pipeline runs from this repository
alone and reproduces the committed results.

To repeat a live run you need a Kubernetes cluster that can pull `python:3.10-slim`:

```
deploy/apply.sh
python real/harness.py --live --policy hpa30 --family azure --workload cpu-bound --start 4075
```

`deploy/README.md` describes the services and how to calibrate the load scale for
another cluster.

## Earlier simulation studies

`run_m1.py` to `run_m3.py` and `results/` hold three simulation studies (M1 to M3) that
came before the live runs. They compared importance sampling, model-based and doubly
robust estimators in a calibrated simulator, which lives in a separate repository and is
not included here. No result in the paper depends on them. `results/NOTES.md`
summarises their findings.
