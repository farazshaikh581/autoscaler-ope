# Results note: off-policy evaluation of autoscalers (simulation, M1-M3)

Setup in one line: logs of a dithered HPA (u = 0.7; with probability eps its replica
delta is replaced by a uniform draw) on the calibrated Phase 1 simulator. The task is
to estimate SLA% and cost of eight replica-only targets from 200 logged 200-step
episodes. Each estimate is checked against the target run on the same episode starts
(paired truth). "Main cells" are Azure and Bitbrains cpu-bound and io-bound x 8
targets = 32 cells. Headline numbers use the pre-specified eps = 0.1, k = 4. The
simulator is deterministic and low-dimensional, so model-based methods are flattered
here; the real cluster (M4) decides between them. Simulator commit baf51c2.

**1. Ignoring the policy change (replay) can be badly wrong.**
At eps = 0.1 replay misses by 42 SLA points at worst (median 0.76) and 33% of cost
(`m2_summary.csv`). The bad cases are on Bitbrains io-bound: HPA-90 by 30 points and
HPA-95 by 42 points; on high-load steps, by 46 and 60 points
(`m3_hard_cells.csv`). In 43 main cell x metric x scope combinations replay misses by
at least 3 SLA points or 15% cost (`m1b_go_nogo.csv`). On Azure the SLA errors are
small but cost errors reach 15-22%. Within each Azure workload the targets' true
SLA spans only 1.4-3.5 points (`m1b_truth.csv`).

**2. Full-horizon importance sampling dies.**
Over 200 decisions the cumulative weight collapses. At eps = 0.1:
- trajectory IS errs by 92-94 SLA points, PDIS by 45-52 and weighted PDIS by
  31-34 (medians per target, `raw/m1_estimates.csv.gz`);
- even for the behaviour's own controller (HPA-70), PDIS errs by 41 points;
- at eps = 0 trajectory IS errs by 46-57 points on every target that differs from
  the HPA.

**3. Windowed IS: only the self-normalised version is usable, and only for moderate
shifts.**
- Plain truncated PDIS looks good in 15 cells, but 14 of those are targets worse
  or cheaper than the behaviour: its finite-sample weights average 0.84-0.92 at
  k = 4, which drags every estimate down (`m1b_go_nogo.csv`). At eps = 0.05, k = 4
  it is significantly worse than replay in 9 of 29 qualifying cells
  (`m1b_fixed_setting.csv`).
- Self-normalised truncated PDIS at eps = 0.1, k = 4 beats replay in 33 of 35
  qualifying cells. It halves the error in 12 (11 with a 95% interval below 0) and
  is never significantly worse (`m1b_fixed_setting.csv`).
- But it removes only 13-34% of the error on HPA-90/95 (Bitbrains io-bound): those
  targets settle at a different replica level, which takes more than 4 decisions
  to show.

**4. Model-based replay (MB) fixes the large shifts, but has a bias floor and a
knife-edge failure.**
Gradient-boosted trees are fitted to the log; each target is rolled forward on the
logged load, with the platform's replica mechanics known.
- Hard cells: on HPA-90/95, MB errs by 1.8 and 0.7 SLA points and 0.2-0.3% cost,
  against replay's 30/42 points and 26/33% (`m3_hard_cells.csv`).
- Bias floor: it errs by up to 2.9 points on HPA-70 itself (`m2_sanity.csv`).
- Knife-edge failure: the SLO-cost target scales in only when predicted success is
  exactly 1.0. The trees predict 0.993-0.999, so in the rollout it never scales
  in, and its cost is overestimated by 87-171% on Azure and 36% on Bitbrains
  cpu-bound (`m2_gate.csv`). This was deliberately left untuned.
- Dithering does not help the model: MB error is flat across eps = 0 / 0.05 / 0.1
  (`m2_summary.csv`). Even undithered logs span 1-12 replicas in most cells
  (`m2_model_fit.csv`).
- A sigmoid-knee model does better (max 3.1 points), but its form matches the
  simulator's own, so it is only an optimistic bound.

**5. Hybrids.** All at eps = 0.1, over the 32 main cells (`m3_summary.csv`,
`m3_gate.csv`).
- *Calibrated MB* subtracts the model's bias on the behaviour's own trajectory,
  per load quartile (`mbcalq_trees`). Median / max SLA error drops from
  1.23 / 4.26 to 0.07 / 1.85, and the HPA-70 error from 2.94 to 0.14
  (`m3_sanity.csv`). The knife-edge cost errors remain, so 4 cells are outside
  the gate.
- *DR anchored on the full MB rollout* (`drmb_k4`) behaves the same: median /
  max 0.09 / 2.03, still the same 4 cost failures.
- *Agreement switch*: windowed DR (k = 4) when the target agrees with the logged
  actions on at least tau of the steps, MB otherwise. Tau chosen on Azure is 0.83.
  - At that tau, every main cell is within the gate on all steps, including
    Bitbrains, which was not used to pick tau (`m3_gate.csv`).
  - But this is fragile. Every tau from 0.50 to 0.92 gives zero Azure failures,
    and Bitbrains passes only for tau 0.80-0.92 (13 of those 43 values,
    `m3_switch_sensitivity.csv`). 0.83 won on a tie-break.
  - The switch also avoids the knife-edge only because the SLO-cost target
    happens to agree with the logs (0.94-0.95) where MB-trees fails.
  - On high-load steps it misses 4 cells (3.1-4.0 SLA points).
- *Calibrated knee model* (`mbcalq_knee`): no cell outside the gate in either
  scope. This is the best case for an operator who knows the system's
  functional form.

**Bottom line.** Replay can be off by 30-60 SLA points. No single estimator passes
every cell honestly:
- windowed IS and DR handle small and moderate changes;
- calibrated MB or DR-MB handle large ones, unless the target has a knife-edge
  rule;
- the switch combines them, but its threshold is not identified by the data.

Whether MB's advantage survives noise, hidden state and warm-up on the real cluster
is the M4 question.
