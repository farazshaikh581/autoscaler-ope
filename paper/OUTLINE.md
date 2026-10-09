# Paper outline (NOMS 2027 short paper, 4 pages + references)

Deadline (per conference listings, to confirm on the official CFP): 9 Nov 2026, AoE.

## Working title

**Replay Misleads: Evaluating Kubernetes Autoscaling Policies from Logs on a Real Cluster**

Alternatives: "Counterfactual Evaluation of Autoscalers from Logs via Policy-Invariant
Stitching"; "Which HPA Setting Would Have Met the SLA? Off-Policy Evaluation of
Autoscalers on a Real Cluster".

## One-sentence claim

Logs of a running autoscaler can predict how a *different* autoscaling policy would
have performed, to within the live system's own run-to-run noise. Replay and
standard off-policy estimators can't. It works if the logs are re-indexed by per-pod
demand, a coordinate the policy doesn't change.

## Contributions (as they will be stated)

1. **Measurement on a real cluster.** It is the first quantification (to our
   knowledge) of how wrong log-based evaluation of autoscaling policies is against
   live ground truth: k3s, 3 trace windows, 8 target policies, 52 one-hour runs.
   - Replay is off by up to 64 SLA points and 545% on cost.
   - Importance-sampling, model-based and doubly-robust estimators are off by
     9-12 points (median) on held-out windows.
2. **Diagnosis.**
   - Two mechanisms make autoscaler logs non-transportable:
     - support mismatch in (replicas, load): targets spend 60-65% of their steps in
       cells the behaviour never visits;
     - signal saturation: measured utilisation is capped near 0.85 while per-pod
       demand reaches 4x, so utilisation-driven controllers act on a compressed
       signal.
   - Both vanish in per-pod-demand coordinates, which the behaviour covers.
3. **Method: demand-space stitching.**
   - The target's own controller code is rolled forward over the window's
     exogenous load.
   - Each step reuses a logged step matched on per-pod demand, lagged demand and
     replica change, with proportional CPU rescaling below the knee.
   - It needs no randomised logging, no propensities and no randomised control
     trial (RCT) across policies. It also works from deterministic (eps = 0) logs.
4. **Pre-registered held-out validation.** The estimator and the pass criteria were
   committed before the validation runs.
   - On 16 held-out cells: median SLA error 2.6 points (run-to-run noise of the live
     system is about 2.7), worst 5.9, median cost error 5.2%.
   - The best baseline: median 9.3, worst 27-52.
   - The interval criterion failed (69% coverage vs 80% required) and is reported
     as such.

## Positioning (related work)

| Work | What it does | Difference from ours |
|---|---|---|
| CausalSim (Alomar et al., NSDI '23) | Unbiased trace-driven simulation by learning policy-invariant latent factors; ABR (Puffer) | Needs an RCT across several policies and learns the invariance adversarially. We derive the invariant coordinate from system structure and need logs of one, possibly deterministic, policy. Closed-loop capacity control (replica count is the policy's own state) is not studied there. |
| Veritas (Bothra et al., SIGCOMM '23) | Causal what-if queries for ABR without RCT, via a domain model of latent bandwidth | Same "domain structure instead of RCT" philosophy, different domain. Autoscaling has no per-session latent to abduct; the exogenous input is the load trace itself. |
| Harvesting randomness (Lécuyer et al., HotNets '17); Sayer (SoCC '21) | IS-based counterfactual evaluation of system policies from randomised or implicit decisions | One-step (bandit-like) decisions. IS needs overlap, which long-horizon autoscaling lacks (our IS baselines fail as predicted). |
| MFMC (Fonteneau et al., AISTATS '10); MFMCi (McGregor et al., 2017) | Policy evaluation by stitching logged one-step transitions with a metric; MFMCi factors out exogenous state | Our estimator is an MFMC-type stitcher. The contribution is the metric (a policy-invariant per-pod demand coordinate plus lag and transition), the below-knee rescaling that extrapolates outside the logged support, and validation against live truth on a real system. |
| Hindsight learning / Exo-MDPs (Sinclair et al., ICML '23) | Exploits exogenous inputs (VM arrivals) with *known* endogenous dynamics to simulate counterfactuals | Here the endogenous outcome mechanism (latency, success and measured CPU vs demand) is unknown and learned from logs. |
| OPE beyond overlap (Khan et al., ICML '24); representation-balancing MB-OPE | Bounds or regularised models when target support exceeds the logging support | Our coverage argument is the systems instance. We report empirical interval coverage. |
| KAPETÁNIOS (Zerwas et al., NoF '22, demo); KubeTwin | Kubernetes digital twins; KAPETÁNIOS learns utilisation vs request rate and tunes HPA | Closest autoscaling twin. No reported test of counterfactual accuracy against live runs of the alternative configurations (to verify on the full text). We provide that test, held out and pre-registered. |
| Autopilot (EuroSys '20), Sinan (ASPLOS '21) | Production / ML autoscalers evaluated or trained on historical data | Sinan explicitly designs exploration to de-bias training data. This motivates our question of when logs suffice. |

The novelty to defend in review is not "a simulator from logs". It is:
- **(i)** a live-truth measurement showing standard OPE fails for autoscalers, and
  why;
- **(ii)** a structural invariance that removes the need for exploration;
- **(iii)** held-out, pre-registered evidence that it reaches the noise floor.

## Section plan (4 pages)

1. **Introduction** (0.6 p).
   - An operator wants to know the SLA and cost of an HPA change before rolling it
     out.
   - Replay of logs is the default answer, and it is wrong: W1 HPA-95, replay 64%,
     truth 0%.
   - Contributions 1-4.
2. **Problem and setup** (0.5 p).
   - Testbed: k3s v1.35, 4 KVM workers, CPU-burn web service, CPU limit = request
     = 200m, 1-12 replicas, 15 s control steps, 12 s load windows.
   - Traces: Bitbrains and Azure windows.
   - Behaviour: HPA-70 (eps 0 and 0.1).
   - Targets: HPA-30/50/85/95, stabilisation 0/10, SLO-cost, predictive.
   - SLA = mean latency < 20 ms and success >= 99%.
   - Truth = live run of the target.
3. **Why logs mislead** (0.6 p).
   - Fig. 1: measured utilisation and SLA vs per-pod demand (saturation and knee).
   - Fig. 2: per-target coverage in (replicas, load) vs in demand.
   - Short account of why IS (no overlap over 200 steps) and black-box MB (no
     support) fail.
4. **Demand-space stitching** (0.7 p).
   - Assumptions:
     - A1: open-loop exogenous load;
     - A2: the step outcome depends on demand and lagged demand, given the
       transition flag;
     - A3: the target's controller code is available, and readiness is one step
       (measured).
   - Algorithm box (10 lines).
   - Prediction and sensitivity intervals.
   - CPU-per-request constant: from the logs (unsaturated steps) or a 15-minute
     knee check.
5. **Evaluation** (1.2 p).
   - Pre-registration protocol: development W1; held-out W2/W3 (+W4).
   - Table 1: median/max SLA error, cost error and gate count, held out vs
     development, for replay, SNTPDIS, MB-calibrated, DR-MB and the twin.
   - Fig. 3: per-cell SLA error, held out, with the run-to-run noise band from
     repeat runs.
   - Noise floor: repeat runs (2.7-point SD; near-knee policies about 4).
   - Ablations (lag, transition flag, rescaling, K, donor episodes, eps = 0 vs 0.1).
   - Failure cases:
     - HPA-85 sits on its scale-in threshold, which the sensitivity interval
       flags;
     - interval under-coverage (P3).
   - Logger robustness (from M6): logs from a different behaviour policy.
6. **Limitations and outlook** (0.3 p).
   - Single service and resource (CPU); open-loop load; replica-only actions.
   - The coordinate is derived per system (it generalises to "capacity-normalised
     demand").
   - Next: vertical actions (pod size enters D through the request), closed-loop
     clients, multi-tier services.

## Figures and tables (all from data already collected, except where noted)

- **Fig. 1:** measured rho, mean latency and SLA vs per-pod demand, all W1-W3 runs
  (from M4 + M5).
- **Fig. 2:** coverage bars per target: % of target steps in logged (replicas,
  load) cells vs % within the donor range in demand space.
- **Fig. 3:** held-out per-cell |SLA error| (dots) for replay / best OPE / twin;
  grey band = run-to-run noise.
- **Table 1:** headline numbers, development vs held out.
- Optional, if space: inset of one rollout trajectory (replicas over time) vs the
  live run.

## Evidence still to collect (M6, to strengthen the claims)

| Experiment | Strengthens | Runs |
|---|---|---|
| W4, a fourth window (Azure cpu-bound 4075): logs x4 + 8 truth | held-out N (16 -> 24 cells) and the interval fix's first test | 12 |
| Repeat truth on W2 and W3 (`_r2`) | noise floor on held-out cells; fairer error | 16 |
| Logs from a different behaviour (dithered HPA-50 on W1, x2) | "works from any logger" vs coverage limits; validates a demand-space support diagnostic | 2 |
| Offline (no runs): ablations; CPU-per-request from logs only; interval with run-to-run noise added | method robustness; fully log-only estimator | 0 |

Total: about 30 runs, about 26 h of cluster time. All offline changes are frozen
(committed with a PLAN_M6 file) before the M6 runs start.
