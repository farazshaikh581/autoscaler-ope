"""Read-only access to the calibrated Phase 1 simulator, for the simulation studies
(M1-M3) and the harness's dry-run mode only. The live pipeline and its analysis never
import this module: controllers and constants live in ope.controllers.

The simulator lives in the joint_hv_autoscaler clone and is imported from there,
never copied or modified. Bytecode writing is disabled so importing it leaves no
files in the clone.
"""
import os
import subprocess
import sys

sys.dont_write_bytecode = True
PHASE1 = os.path.expanduser("~/joint_hv_autoscaler/phase1")
if PHASE1 not in sys.path:
    sys.path.insert(0, PHASE1)

from envs.joint_hv_env import ACTIONS, JointHVEnv, set_trace_family  # noqa: E402

from .controllers import (D_REPS, EPISODE_LEN, M_KEYS, REPLICA_MAX, REPLICA_MIN,  # noqa: E402,F401
                          S_KEYS, SLA_MEAN_LATENCY_MS, ClassicalController, PredictiveController,
                          SloCostAwareController, in_bounds, outcome, snapshot)

WORKLOADS = ["cpu-bound", "io-bound", "mixed"]


def sim_commit() -> str:
    return subprocess.check_output(
        ["git", "-C", os.path.dirname(PHASE1), "rev-parse", "HEAD"], text=True).strip()


def use_family(family: str) -> None:
    """Select the trace family for this process. The simulator requires a 'bb' tag
    token for Bitbrains and forbids it for Azure."""
    set_trace_family(family, "ope_bb" if family == "bitbrains" else "ope")


def make_env(workload: str, episode_len: int = EPISODE_LEN) -> JointHVEnv:
    return JointHVEnv(workload=workload, episode_len=episode_len)


def step_action(d_rep: int) -> int:
    return ACTIONS.index((d_rep, 0, 0))
