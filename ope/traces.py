"""Workload traces for the live runs, shipped in this repository (traces/).

Each file holds the class-representative series of joint-hv-autoscaler phase1 at commit
de86f80 (traces/ for Azure, traces_bitbrains/ for Bitbrains), copied byte for byte;
traces/SHA256SUMS lists the checksums. The live load is
    rps_t = load_frac_t * INTENSITY[workload] * max_rps,
with load_frac the CPU series normalised by its 99th percentile and clipped to 1.5,
the same normalisation as the simulator.
"""
import hashlib
import os

import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "traces")
INTENSITY = {"cpu-bound": 1.0, "io-bound": 0.5}     # CPU intensity per class (joint_hv_env.INTENSITY)


def path(family: str, workload: str) -> str:
    return os.path.join(ROOT, family, f"{workload}.npz")


def load_frac(family: str, workload: str) -> np.ndarray:
    cpu = np.nan_to_num(np.load(path(family, workload))["cpu_norm"]).astype(np.float32)
    return np.clip(cpu / (np.percentile(cpu, 99) or 1.0), 0, 1.5)


def sha256(family: str, workload: str) -> str:
    with open(path(family, workload), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()
