"""Check that the live pipeline and its analysis run on saul with this repository alone.

  python real/check_saul_native.py

1. Imports: with the joint_hv_autoscaler modules blocked (envs, eval_baselines, common,
   load, ope.sim) and that repository off sys.path, the harness, realog, the baselines,
   the twin, the queueing model and the M5/M6/M8 reports all import.
2. Traces: traces/ holds byte-identical copies of the joint repository's files.
3. Controllers: ope.controllers takes the same decision as eval_baselines on every logged
   step of every live run (each target fed the run's own (m, s) sequence), and on 200,000
   random states.
4. Analysis, with the joint repository blocked: twin v2 and the four off-policy baselines
   reproduce the committed W4 cells of real/runs/m6_cells.csv, the M8 report reproduces
   all 16 cells of real/runs/m8_cells.csv, and real/m8_dev.py reproduces the queueing
   fits of real/runs/m8_dev.md.
Checks 2 and 3 import the originals for comparison; checks 1 and 4 run in a subprocess
that cannot.
"""
import hashlib
import importlib.abc
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
JOINT = os.path.expanduser("~/joint_hv_autoscaler")
BLOCKED = {"envs", "eval_baselines", "common", "load", "ope.sim"}


class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name in BLOCKED or name.split(".")[0] in {"envs", "eval_baselines"}:
            raise ImportError(f"blocked: {name} belongs to joint_hv_autoscaler")
        return None


def blocked_child():
    sys.meta_path.insert(0, Block())
    sys.path[:] = [p for p in sys.path if "joint_hv_autoscaler" not in p]
    sys.path.insert(0, HERE)
    sys.path.insert(0, REPO)
    import importlib
    for mod in ("ope.controllers", "ope.traces", "ope.policies", "ope.twin", "ope.queue_baseline", "ope.mb",
                "ope.estimators", "ope.model", "ope.logger", "kube", "windowload", "realog", "overnight_report",
                "m5_report", "m6_report", "m8_report", "harness"):
        importlib.import_module(mod)
    print("imports OK (joint_hv_autoscaler blocked)")
    import contextlib
    import io
    import runpy
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        runpy.run_path(os.path.join(HERE, "m8_dev.py"), run_name="__main__")
    import pandas as pd
    import m8_report
    # Since M8 the W4 truth is the mean of two runs, so compare the estimates, scored
    # against M6's one-run truth, not the error columns.
    w4 = m8_report.evaluate("w4").set_index("target")
    ref = pd.read_csv(os.path.join(HERE, "runs", "m6_cells.csv"))
    ref = ref[ref.test == "W4"].set_index("target")
    w4 = w4.loc[ref.index]
    worst = max(abs(w4.twin_sla - ref.twin_sla).max(), abs(w4.twin_cost - ref.twin_cost).max())
    for b in ("replay", "sntpdis_k4", "mbcalq_trees", "drmb_k4"):
        worst = max(worst, abs(abs(w4[f"{b}_sla"] - ref.truth_sla) - ref[f"{b}_sla_err"]).max())
    assert worst < 1e-9, f"W4 estimates differ from real/runs/m6_cells.csv by {worst}"
    print("estimators OK: twin v2 and all four baselines reproduce the M6 W4 cells exactly")
    cells = pd.read_csv(os.path.join(HERE, "runs", "m8_cells.csv")).set_index(["window", "target"])
    new = pd.concat([m8_report.evaluate(w) for w in ("w4", "w5")]).set_index(["window", "target"]).loc[cells.index]
    num = [c for c in cells.columns if cells[c].dtype.kind == "f"]
    diff = (cells[num] - new[num]).abs().max().max()
    assert diff < 1e-9, f"M8 cells differ from real/runs/m8_cells.csv by {diff}"
    print("M8 OK: all 16 cells of real/runs/m8_cells.csv reproduced exactly")
    print("m8_dev:" + buf.getvalue(), end="")


def check_traces():
    pairs = [("azure", "traces"), ("bitbrains", "traces_bitbrains")]
    for fam, sub in pairs:
        for wl in ("cpu-bound", "io-bound"):
            a = open(os.path.join(REPO, "traces", fam, f"{wl}.npz"), "rb").read()
            b = open(os.path.join(JOINT, "phase1", sub, f"{wl}.npz"), "rb").read()
            assert hashlib.sha256(a).digest() == hashlib.sha256(b).digest(), (fam, wl)
    print("traces OK: 4 files byte-identical to joint_hv_autoscaler phase1")


def check_controllers():
    import numpy as np
    import pandas as pd
    from types import SimpleNamespace
    sys.path.insert(0, REPO)
    import ope.controllers as V
    sys.path.insert(0, os.path.join(JOINT, "phase1"))
    sys.dont_write_bytecode = True
    import eval_baselines as O
    pairs = {
        "hpa30": (lambda: V.ClassicalController(False, 0.3), lambda: O.ClassicalController(False, 0.3)),
        "hpa50": (lambda: V.ClassicalController(False, 0.5), lambda: O.ClassicalController(False, 0.5)),
        "hpa70": (lambda: V.ClassicalController(False, 0.7), lambda: O.ClassicalController(False, 0.7)),
        "hpa85": (lambda: V.ClassicalController(False, 0.85), lambda: O.ClassicalController(False, 0.85)),
        "hpa95": (lambda: V.ClassicalController(False, 0.95), lambda: O.ClassicalController(False, 0.95)),
        "slo_cost": (lambda: V.SloCostAwareController(False), lambda: O.SloCostAwareController(False)),
        "pred70": (lambda: V.PredictiveController(False, 0.7), lambda: O.PredictiveController(False, 0.7)),
    }
    runs = sorted(f for f in os.listdir(os.path.join(HERE, "runs")) if f.startswith("on_w") and f.endswith(".csv") and "_pods" not in f)
    n = 0
    for f in runs:
        d = pd.read_csv(os.path.join(HERE, "runs", f))
        ms = [dict(load_frac=r.load_frac, rho=r.rho if np.isfinite(r.rho) else 0.0, latency=r.latency_mean_ms,
                   success=r.success, cpu_util=r.cpu_util if np.isfinite(r.cpu_util) else 0.0, mem_pressure=0.0)
              for r in d.itertuples()]
        ss = [SimpleNamespace(replicas=int(r.ready_replicas), target_replicas=int(r.requested_replicas), cpu_req=int(r.cpu_req),
                              steps_to_ready=int(r.steps_to_ready), mem_req=128, mem_need_now=0.0) for r in d.itertuples()]
        for name, (fv, fo) in pairs.items():
            cv, co = fv(), fo()
            for m, s in zip(ms, ss):
                assert cv.act(m, s) == co.act(m, s), (f, name)
                n += 1
    rng = np.random.default_rng(0)
    for name, (fv, fo) in pairs.items():
        cv, co = fv(), fo()
        for _ in range(200000 // len(pairs)):
            m = dict(load_frac=float(rng.uniform(0, 1.5)), rho=float(rng.uniform(0, 2)), latency=float(rng.exponential(30)),
                     success=float(rng.choice([1.0, 0.995, 0.9])), cpu_util=float(rng.uniform(0, 1.5)), mem_pressure=0.0)
            s = SimpleNamespace(replicas=int(rng.integers(1, 13)), target_replicas=int(rng.integers(1, 13)), cpu_req=200,
                                steps_to_ready=int(rng.integers(0, 2)), mem_req=128, mem_need_now=0.0)
            assert cv.act(m, s) == co.act(m, s), name
            n += 1
    print(f"controllers OK: {n} decisions identical over {len(runs)} live runs and random states")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--blocked":
        blocked_child()
        return
    child = subprocess.run([sys.executable, os.path.abspath(__file__), "--blocked"], capture_output=True, text=True, cwd=REPO)
    if child.returncode != 0:
        print(child.stdout, child.stderr)
        sys.exit("FAIL: the pipeline needs joint_hv_autoscaler")
    head, _, m8 = child.stdout.partition("m8_dev:")
    print(head.strip())
    ref = open(os.path.join(HERE, "runs", "m8_dev.md")).read()
    # The W4 error columns of m8_dev.md predate the second W4 truth run (M8), so W4 rows
    # are compared on the fitted parameters only; W1-W3 rows must match in full.
    def rows(text):
        return [[c.strip() for c in l.strip("|").split("|")] for l in text.splitlines() if l[:4] in ("| w1", "| w2", "| w3", "| w4")]
    got, want = rows(m8), rows(ref)
    assert len(got) == len(want) == 8, "m8_dev table has the wrong number of rows"
    for g, r in zip(got, want):
        assert (g[:4] == r[:4]) if r[0] == "w4" else (g == r), f"m8_dev row differs: {g} vs {r}"
    print("analysis OK: m8_dev fits reproduced exactly (W1-W3 rows in full, W4 parameters) with joint_hv_autoscaler blocked")
    check_traces()
    check_controllers()
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
