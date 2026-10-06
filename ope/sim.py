"""Read-only access to the calibrated Phase 1 simulator and its controllers.

The simulator lives in the joint_hv_autoscaler clone and is imported from there,
never copied or modified. Bytecode writing is disabled so importing it leaves no
files in the clone.
"""
import os
import subprocess
import sys
from types import SimpleNamespace

sys.dont_write_bytecode = True
PHASE1 = os.path.expanduser("~/joint_hv_autoscaler/phase1")
if PHASE1 not in sys.path:
    sys.path.insert(0, PHASE1)

from envs.joint_hv_env import (ACTIONS, REPLICA_MAX, REPLICA_MIN,  # noqa: E402
                               SLA_MEAN_LATENCY_MS, JointHVEnv)
from eval_baselines import ClassicalController, PredictiveController  # noqa: E402

WORKLOADS = ["cpu-bound", "io-bound", "mixed"]
EPISODE_LEN = 200
D_REPS = (-1, 0, 1)                   # replica actions; index into these is the action id
M_KEYS = ("load_frac", "rho", "latency", "success", "mem_pressure", "cpu_util")
S_KEYS = ("replicas", "target_replicas", "cpu_req", "mem_req", "mem_need_now", "steps_to_ready")


def sim_commit() -> str:
    return subprocess.check_output(
        ["git", "-C", os.path.dirname(PHASE1), "rev-parse", "HEAD"], text=True).strip()


def make_env(workload: str) -> JointHVEnv:
    return JointHVEnv(workload=workload, episode_len=EPISODE_LEN)


def snapshot(s) -> SimpleNamespace:
    """Copy of the fields a controller reads, so later steps cannot mutate it."""
    return SimpleNamespace(**{k: getattr(s, k) for k in S_KEYS})


def outcome(m: dict, s) -> tuple[float, float, float]:
    """(sla_ok, cost, latency) exactly as eval_baselines.evaluate_policy scores a step."""
    sla_ok = float(m["latency"] < SLA_MEAN_LATENCY_MS and m["success"] >= 0.99)
    return sla_ok, s.replicas * s.cpu_req / 1000.0, m["latency"]


def in_bounds(d_rep: int, s) -> bool:
    """Same bound test the controllers use before emitting a replica delta."""
    return not ((d_rep > 0 and s.replicas >= REPLICA_MAX) or (d_rep < 0 and s.replicas <= REPLICA_MIN))


def step_action(d_rep: int) -> int:
    return ACTIONS.index((d_rep, 0, 0))
