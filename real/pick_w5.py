"""Pick the M8 held-out window W5 by the rule fixed in real/PLAN_M8.md, before any W5 run.

The rule is the one behind W3 and W4: in a trace class, the most variable 200-step window
(largest SD of the request rate) whose peak fits saul (<= 1500 rps) with mean >= 300 rps,
using the harness's own load normalisation (stride 25). Applied per class it gives W3
(Bitbrains cpu-bound, 950) and W4 (Azure cpu-bound, 4075, the only passing window). The
memory-bound and Azure io-bound classes have no passing window, and Azure "mixed" is 199
steps long. W5 is the best passing window of the remaining class that does not overlap a
used window.

  python real/pick_w5.py
"""
import importlib
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from ope.sim import use_family  # noqa: E402

STEPS, STRIDE, MAX_RPS = 200, 25, 2050.0
USED = {("bitbrains", "io-bound"): [4725], ("azure", "cpu-bound"): [1200, 4075], ("bitbrains", "cpu-bound"): [950]}


def windows(family, workload):
    use_family(family)
    import envs.joint_hv_env as J
    importlib.reload(J)
    p = os.path.join(J.trace_dir("traces"), f"{workload}.npz")
    if not os.path.exists(p):
        return []
    cpu = np.nan_to_num(np.load(p)["cpu_norm"]).astype(np.float32)
    load = np.clip(cpu / (np.percentile(cpu, 99) or 1.0), 0, 1.5)
    k = J.INTENSITY[workload]["cpu"] * MAX_RPS
    return [(s, float(load[s:s + STEPS].max() * k), float(load[s:s + STEPS].mean() * k), float(load[s:s + STEPS].std() * k))
            for s in range(0, len(load) - STEPS - 1, STRIDE)]


def main():
    best = None
    for fam in ("azure", "bitbrains"):
        for wl in ("cpu-bound", "io-bound", "memory-bound", "mixed"):
            rows = windows(fam, wl)
            ok = [r for r in rows if r[1] <= 1500 and r[2] >= 300]
            free = [r for r in ok if all(abs(r[0] - u) >= STEPS for u in USED.get((fam, wl), []))]
            top = max(free, key=lambda r: r[3]) if free else None
            print(f"{fam} {wl}: {len(rows)} windows, {len(ok)} pass, {len(free)} unused"
                  + (f"; best unused start {top[0]} (peak {top[1]:.0f}, mean {top[2]:.0f}, sd {top[3]:.0f})" if top else ""))
            if top and (best is None or top[3] > best[2][3]):
                best = (fam, wl, top)
    fam, wl, (s, pk, mn, sd) = best
    print(f"W5 = {fam} {wl} start {s} (peak {pk:.0f} rps, mean {mn:.0f}, sd {sd:.0f})")


if __name__ == "__main__":
    main()
