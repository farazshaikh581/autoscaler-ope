# Diagnosis of the hpa85 cost miss (real/diag_hpa85/README.md). Run from the repo root.
import sys, numpy as np, pandas as pd
sys.path.insert(0, "real"); sys.path.insert(0, ".")
import ope.twin as T
from m5_report import frames
from ope.policies import REAL_TARGETS
from ope.twin import twin_v2, demand
w = sys.argv[1]
logs = [d for _, d in frames([f"on_{w}_log_eps{e}_r{r}" for e in ("0.1", "0") for r in (1, 2)])]
tw = twin_v2(logs); rps, lf = logs[0].rps_target.values, logs[0].load_frac.values
truth = pd.read_csv(f"real/runs/on_{w}_truth_hpa85.csv")
# instrument: record ready, rho and action per step of several rollouts
rec = []
orig = REAL_TARGETS["hpa85"]
class Spy:
    def __init__(self): self.p = orig(); self.log = []
    def reset(self): self.p.reset()
    def act(self, m, s):
        a = self.p.act(m, s); self.log.append((s.replicas, m["cpu_util"], a[0])); return a
rng = np.random.default_rng(0); runs = []
for _ in range(40):
    sp = Spy(); tw.rollout(lambda: sp, rps, lf, rng); runs.append(sp.log)
R = np.array(runs)                               # (40, T, 3)
print(f"{w}: twin mean ready {R[:,:,0].mean():.2f}, truth {truth.ready_replicas.mean():.2f}")
print("twin: scale-outs/run %.1f, scale-ins/run %.1f | truth: %d, %d" % ((R[:,:,2]>0).sum(1).mean(), (R[:,:,2]<0).sum(1).mean(), (truth.d_rep>0).sum(), (truth.d_rep<0).sum()))
D_tw = demand(rps[None,:], R[:,:,0], 200, tw.m_per_rps)
print("twin cpu_util when D>1: mean %.3f, share < 0.765: %.2f" % (R[:,:,1][D_tw>1].mean(), (R[:,:,1][D_tw>1] < 0.765).mean()))
Dt = demand(truth.rps_achieved.values, truth.ready_replicas.values, 200, tw.m_per_rps)
print("truth cpu_util when D>1: mean %.3f, share < 0.765: %.2f" % (truth.cpu_util[Dt>1].mean(), (truth.cpu_util[Dt>1] < 0.765).mean()))
# where do twin scale-ins happen: by D
ins = R[:,:,2] < 0
print("twin scale-ins at D: quartiles", np.percentile(D_tw[ins], [25,50,75]).round(2) if ins.any() else "none")
# per-step comparison first 40 steps: truth ready vs twin median ready
print("step: truth_ready/twin_median_ready  (D_truth)")
print(" ".join(f"{t}:{int(truth.ready_replicas[t])}/{np.median(R[:,t,0]):.0f}({Dt[t]:.1f})" for t in range(0, 200, 8)))
