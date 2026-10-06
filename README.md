# Off-policy evaluation of autoscaling policies

Question: can an operator estimate a new autoscaler's SLA and cost from the logs of
the current one, before deploying it?

Simulation only. The environment and controllers are the calibrated Phase 1
simulator from `joint_hv_autoscaler/phase1`, imported read-only
(`ope/sim.py`); every results file records that repository's commit.

## M1: feasibility in simulation

Run: `python run_m1.py --procs 8 && python plot_m1.py` (about 70 s on 8 cores).

| Piece | Module |
|---|---|
| Simulator access, step scoring (same as `eval_baselines.evaluate_policy`) | `ope/sim.py` |
| Behaviour (dithered HPA), targets, shadow replay | `ope/policies.py` |
| Log collection | `ope/logger.py` |
| Estimators | `ope/estimators.py` |
| On-policy ground truth | `ope/truth.py` |
| Experiment driver, figures | `run_m1.py`, `plot_m1.py` |

**Setup**

- Environment: `JointHVEnv`, Azure trace family, episodes of 200 steps (15 s
  each), workloads cpu-bound, io-bound and mixed. A step is SLA-ok if mean
  latency < 20 ms and success >= 0.99; cost = replicas x cpu_req / 1000 (vCPU).
  Both are averaged over steps. Memory-bound is left out, because replica-only
  control cannot serve it.
- Behaviour: HPA at u = 0.70 (`ClassicalController(vpa=False)`). With
  probability eps its replica delta is replaced by a uniform draw from {-1, 0, +1};
  a draw outside the replica bounds becomes 0, so the logged probabilities of all
  three deltas are exact.
- Targets, all deterministic and replica-only: HPA at u = 0.5, 0.6, 0.8 and 0.9,
  and the Holt predictive controller at u = 0.7. A sanity target, HPA at u = 0.7
  (the behaviour's own base controller), is also evaluated; every IS estimator
  is unbiased for it. Target actions come from shadow replay: each target is fed
  the logged metrics and state in order, so its internal state follows the
  logged history.
- Estimators of the per-step mean:
  - replay: the logged mean;
  - trajectory IS;
  - PDIS;
  - weighted PDIS: a step with zero total weight contributes 0;
  - truncated PDIS with window k in {1, 2, 4, 8}: each outcome is weighted by
    the ratios of its last k decisions.
- Grid: eps in {0, 0.02, 0.05, 0.1, 0.2} x {10, 50, 200} logged episodes x 3
  workloads x 5 logging seeds. The logs for n = 10 and 50 are prefixes of the
  n = 200 log. Episode starts are shared across eps (common random numbers).
- Ground truth: each target run on-policy, 200 episodes per workload, with seeds
  disjoint from the logging seeds (`results/m1_truth.csv`, with standard errors).

**Outputs**

- `results/m1_estimates.csv`: one row per estimator x target x workload x eps x
  n_episodes x rep, with the estimate, truth and absolute error for SLA% and cost.
- `results/m1_truth.csv`: on-policy SLA% and cost of each target.
- `results/m1_dither_cost.csv`: the behaviour's own SLA% and cost per eps, with
  the change relative to eps = 0.
- `results/m1_err_vs_eps.png`: median SLA% error vs eps per estimator, n = 200.
- `results/m1_dither_cost.png`: dither cost vs eps.

**Findings and caveats**

- *IS fails at eps = 0, as expected.* Trajectory IS errs by 46-57 points and PDIS
  by 31-45 points on every target that differs from the HPA.
- *Full-horizon IS also fails at eps > 0.* Over 200 steps the cumulative weight
  dies, so trajectory IS, PDIS and weighted PDIS stay at 30-90 points of error up
  to eps = 0.2. Even for the sanity target at eps = 0.1, PDIS errs by 41 points.
  Only the truncated estimators are usable.
- *The targets barely differ, so M1 cannot rank estimators.* Within each
  workload, the true SLA% of the five targets spans only 0.6-2.1 points, and
  true cost spans only 0.03-0.08 vCPU. For cpu-bound, the ground truth's own
  standard error (0.8 SLA points, 0.03 vCPU) is about the size of those gaps.
  Naive replay is therefore already within 1 SLA point at every eps, and no
  estimator beats it in this setup.
- *Dithering raises cost and slightly raises SLA.* Its +1 draws scale out at once,
  while scale-in is slowed by stabilisation, so the policy runs more replicas. At
  eps = 0.05 cost rises by 0.013-0.023 vCPU (3-8%); at eps = 0.2 by 0.08-0.13 vCPU
  (20-41%).
- *The mixed trace has 199 points.* Episodes are 200 steps, so every mixed
  episode starts at index 0. Its ground truth is a single deterministic trajectory
  (standard error 0).
