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

- `results/raw/m1_estimates.csv.gz`: one row per estimator x target x workload x eps x
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

## M1b: is there a regime where replay is badly wrong?

Run: `python run_m1b.py --procs 8 && python analyse_m1b.py && python plot_m1b.py`
(about 10 min on 8 cores).

**Changes from M1**

- Both trace families, reported separately. Bitbrains is selected with
  `set_trace_family("bitbrains", "ope_bb")`.
- Targets that differ more, all replica-only: HPA at u = 0.3, 0.5, 0.9 and
  0.95; HPA-70 with a scale-in stabilisation of 0 or 10 steps (`StabilisedHPA`,
  a subclass, so the clone is untouched); `SloCostAwareController`; and the
  predictive controller at 0.7. HPA-70 remains the sanity target.
- Two ground truths:
  - paired: each target run on the same episode seeds (same starts) as each
    logging seed's 200 episodes;
  - unpaired: 2000 episodes on disjoint seeds.

  Both are in `m1b_truth.csv` with standard errors. All errors in M1b are
  against the paired truth.
- Mixed: both families' mixed traces have 199 points. Any episode of 197 or
  more steps therefore always starts at index 0, so the 200-step mixed cells are
  dropped. Mixed is kept as an extra cell, `mixed_L100`, with 100-step episodes
  (98 starts); it is not part of the headline go/no-go.
- Main metric: `|err_est| - |err_replay|` at n = 200, as the mean over 5
  logging seeds, with 95% intervals from an episode bootstrap (500 resamples,
  logged episodes resampled together with their paired truth).
  File: `raw/m1b_vs_replay.csv.gz`.
- Two scopes:
  - all steps;
  - high-load steps: the top quartile of `load_frac` within each episode. The
    estimand is each episode's mean over its masked steps, averaged over
    episodes.
- New estimator: self-normalised truncated PDIS (`sntpdis_k`), i.e. the
  truncated weights rescaled to mean 1. See the findings for why it is needed.

**Go/no-go** (`analyse_m1b.py`, `m1b_go_nogo.csv`)

- Units: a cell is family x workload x target. Gates are applied per metric
  (SLA, cost) and per scope.
- Qualifies: replay's error is at least 3 SLA points or at least 15% of the true
  cost, at some 0 < eps <= 0.1.
- Passes: truncated PDIS with k <= 4 at that eps has at most half of replay's
  error. "Significant" additionally needs the bootstrap interval of the
  difference to lie below 0.
- eps = 0 is excluded: with no support, truncated PDIS just zeroes the outcome on
  mismatched steps.

**Findings**

- *Replay can be badly wrong.* On Bitbrains io-bound, replay's SLA error is
  31 points for HPA-90 and 43 for HPA-95. On high-load steps it is 48 and 61.
  Its cost error is 26-32%. In 43 of the main (200-step) cell-metric-scopes,
  replay misses by at least 3 SLA points or 15% of cost. On Bitbrains
  cpu-bound no cell qualifies: there the targets are within 1.2 SLA points and
  14% cost of each other.
- *Plain truncated PDIS's apparent wins are an artifact.* It halves the error in
  15 of the 43 main cells, 10 of them significantly. But in 14 of those 15, the
  target's truth lies below the logged average. At k = 4 the mean truncated
  weight in a finite sample is only 0.84-0.92 (0.24-0.29 at k = 8), so the
  estimate shrinks towards 0 and lands near a worse or cheaper target by
  accident. As k grows the estimate keeps falling past the truth: for HPA-90 on
  Bitbrains io-bound (true SLA 57%) it goes 88.6, 86.1, 71.3, 20.6 for k = 1, 2,
  4, 8. At a fixed eps = 0.05 and k = 4 it is significantly *worse* than replay
  in 9 of 29 qualifying cells.
- *Self-normalised truncated PDIS helps on moderate shifts.* It halves the error
  in 20 of the 43 main cells, all 20 with the interval below 0, and in both
  directions (targets better and worse than the behaviour). At a fixed eps = 0.1
  and k = 4 it beats replay in 33 of 35 qualifying cells, halves the error in 12
  (11 significant), and is significantly worse in none.
- *It does not fix the large shifts.* For the cells with the largest replay
  errors (HPA-90 and HPA-95 on Bitbrains io-bound), self-normalised truncated
  PDIS at k = 4 (eps = 0.05) removes only 13-34% of the error. These targets settle at a
  different replica level, and that effect builds up over more than 4
  decisions. At k = 8, which is outside the go/no-go, the error is roughly
  halved (HPA-90: 30.8 to 15.0), but variance grows. Model-based or doubly
  robust estimators (M2) are the natural next step for this case.
- *Sanity target.* HPA-70's error stays at or below 1 SLA point in every main
  cell. In the extra Azure mixed_L100 high-load scope it reaches 4-5 points, for
  replay as well, because on that short trace the dithered behaviour itself
  drifts from HPA-70.
- *Dither cost* is in `m1b_dither_cost.csv`.

## Repository layout and size

Large per-run tables are kept gzipped under `results/raw/` (`*.csv.gz`, marked
binary in `.gitattributes`, so they are not diffed); pandas reads them directly.
Small summary tables stay as plain CSV in `results/`. `.deps/` holds scikit-learn
and scipy installed with `uv pip install --target .deps --no-deps` (numpy comes from
the venv) and is not committed.

## M2: estimators for large policy changes

Run: `python run_m2.py --procs 8 && python analyse_m2.py && python plot_m2.py`
(about 12 min on 8 cores).

**Setup**

- Logs are the same as M1b's (same cells, episode seeds and dither seeds) at
  eps = 0, 0.05 and 0.1, with five logging seeds each.
- The logger also records what an operator sees after each decision: serving and
  requested replicas, CPU request, steps until a pending scale lands, latency,
  success, CPU utilisation and rho.
- *Model-based replay (MB)* (`ope/model.py`, `ope/mb.py`). The model is fitted to
  the log only. The load sequence is exogenous and taken from the log. The
  replica mechanics are treated as known platform semantics: +/-1 per decision,
  bounds 1-12, a 2-step readiness delay. Each target is rolled forward from every
  logged episode start, and the SLA and cost of the predicted trajectory are
  scored. Two outcome models:
  - `mb_trees`: gradient-boosted trees (scikit-learn HistGradientBoosting, 300
    iterations) on (load, replicas, cpu_req, steps_to_ready, pending), one per
    output. The trees only split on their per-feature bin edges, so they are
    evaluated through an exact lookup table over the bin grid (checked equal to
    `predict`).
  - `mb_knee`: latency and success as a sigmoid knee in load per vCPU, rho linear
    in it, fitted with `curve_fit`. Caveat: this functional form matches the
    simulator's own, which the author had read, so `mb_knee` is an optimistic
    case. `mb_trees` is the generic one.
- *Windowed DR* (`dr_k2/4/8`): per-decision DR over the last k decisions with
  self-normalised weights. The baseline is `mb_trees`, using k-step rollouts
  from every logged state, both under the target and with the logged action
  first. Run at n = 200 only.
- Errors are against the paired truth. `results/raw/m2_vs_replay.csv.gz` holds
  the bootstrap of |err| - |err_replay|; it is conditional on the fitted model
  and on DR's normalising constants.

**Findings** (n = 200; "main cells" = 4 workloads x 8 targets; numbers are
median / max over cells of the error averaged over five logging seeds)

- *MB fixes the large shifts.* On Bitbrains io-bound, replay's SLA error is 30
  points (HPA-90) and 42 points (HPA-95) at eps = 0.1; with MB it is 1.8 / 0.7
  (trees) and 1.6 / 1.2 (knee). MB's cost error is 0.2-0.3% (trees) and 0.0%
  (knee), against replay's 26-33%. Windowed DR cannot do this: its window starts
  from the behaviour's state, so it keeps the truncation bias (k = 8 still errs
  by 12-19 points).
- *Overall at eps = 0.1, all steps, SLA points:*

  | Estimator | Median | Max |
  |---|---|---|
  | replay | 0.76 | 42.4 |
  | SN truncated PDIS k=4 | 0.80 | 38.4 |
  | MB trees | 1.23 | 4.3 |
  | MB knee | 0.64 | 3.1 |
  | DR k=4 | 0.26 | 31.6 |
  | DR k=8 | 0.19 | 18.7 |

  DR has the lowest median, because it corrects the model's bias on small
  shifts. MB has by far the lowest maximum.
- *MB has a bias floor of about 3 SLA points.* On the sanity target HPA-70, MB
  errs by up to 2.9 (trees) and 3.05 (knee) points; DR and IS by 0.1-0.5. The
  model's small errors around the SLA threshold add up over the rollout.
- *MB-trees is fragile for a controller with a knife-edge rule.* The SLO-cost
  target scales in only when its violation measure is exactly 0, i.e. predicted
  success is exactly 1.0. The trees predict 0.993-0.999 where the truth is 1.0,
  so in the rollout the target never scales in. On Azure io-bound this gives 3.3
  replicas against a true 1.2, a cost error of 171% (87% on Azure cpu-bound,
  36% on Bitbrains cpu-bound). The knee model reproduces success = 1.0 exactly,
  by construction. This was not tuned away.
- *No estimator gets every main cell within 3 SLA points and 15% cost at
  eps = 0.1:*
  - MB-knee misses 7 cells, all on Azure io-bound at 3.0-3.1 SLA points, which
    is its bias floor.
  - MB-trees misses 4: the SLO-cost cost blow-ups, plus Azure io-bound
    predictive-70 at 18% cost.
  - SN truncated PDIS and DR k=4/8 each miss 3: the hard cells.
  - On high-load steps all estimators miss 5-13 cells.
- *Dithering does not help MB here.* MB's error is flat in eps: median 1.02 /
  1.06 / 1.23 (trees) and 0.66 / 0.64 / 0.64 (knee) at eps = 0 / 0.05 / 0.1, and
  the hard cells are just as good at eps = 0. Even without dither, the HPA's logs
  span replicas 1-12 in most cells (Azure io-bound 1-6, Bitbrains io-bound
  2-12): load swings and the 2-step delay already decouple replicas from load,
  so the (load, replicas) region the targets visit is covered. The hypothesis
  "a little randomness makes the learned model identifiable" is not supported
  in this simulator; it may hold where the behaviour's replicas track load
  tightly.
- *Learning curve:* MB is as accurate with 10 logged episodes as with 200
  (median 0.47-1.23 SLA points across n = 10/50/200). The simulator is
  deterministic and low-dimensional, so this is optimistic for a real system.

Files: `results/m2_summary.csv`, `m2_hard_cells.csv`, `m2_gate.csv`,
`m2_learning_curve.csv`, `m2_model_fit.csv` (knee parameters and logged replica
range per log), `m2_summary.png`, and `raw/m2_estimates.csv.gz` /
`raw/m2_vs_replay.csv.gz`.

## M3: hybrid estimators

Run: `python run_m3.py --procs 8 && python analyse_m3.py && python plot_m3.py`
(about 9 min on 8 cores).

Same logs as M1b/M2, n = 200, eps 0 / 0.05 / 0.1. New estimators:

- `mbcal_*` / `mbcalq_*`: MB minus the model's bias on the behaviour's own
  trajectory. The logged actions are replayed through the model and compared with
  the logged outcomes; the bias is taken overall, or per quartile of logged load.
- `drmb_k*`: windowed DR anchored on the full-horizon MB rollout, i.e. MB plus
  the windowed DR residual. At full horizon it reduces to ordinary DR.
- Agreement switch: windowed DR (or SN truncated PDIS) when the target's action
  agreement with the logged actions is at least tau, MB-trees otherwise. Tau is
  chosen on Azure only and applied to Bitbrains.
  `results/m3_switch_sensitivity.csv` shows how the result depends on tau.

The current story with every number tied to its CSV is in `results/NOTES.md`.

## M4 preparation: real cluster (not run)

`real/harness.py` is a 15 s control loop on saul's hv-phase0/web-service: a
dithered HPA or a target controller, `kubectl scale`, and trace-driven load at
saul's calibrated scale. It dry-runs against the simulator by default; `--live`
is gated on E1 having finished and no HPA/VPA object existing in hv-phase0.

`real/pick_windows.py` chooses the trace windows. `real/PLAN.md` holds the run
plan and cluster-time budget.
