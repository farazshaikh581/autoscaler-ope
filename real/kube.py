"""kubectl helpers and the namespace guard for the live harness.

Copied from joint-hv-autoscaler phase0/common.py at commit de86f80, so the harness runs
on saul without that repository.
"""
import json
import subprocess
import sys

PROTECTED = {"default", "kube-system", "kube-public", "kube-node-lease"}


def guard_namespace(ns: str) -> None:
    if ns in PROTECTED:
        sys.exit(f"REFUSING to run against protected namespace '{ns}'. "
                 f"The OPE runs must target their own isolated namespace (hv-phase0).")


def kubectl(args: list[str], timeout: int = 15) -> str:
    """Run kubectl and return stdout (raises on non-zero)."""
    out = subprocess.run(["kubectl", *args, f"--request-timeout={timeout}s"],
                         capture_output=True, text=True, timeout=timeout + 5)
    if out.returncode != 0:
        raise RuntimeError(f"kubectl {' '.join(args)} failed: {out.stderr.strip()}")
    return out.stdout


def kubectl_json(args: list[str], timeout: int = 15) -> dict:
    return json.loads(kubectl([*args, "-o", "json"], timeout=timeout))


def parse_cpu_millicores(val: str) -> float:
    """Parse a k8s CPU quantity ('250m', '1', '1500m') into millicores (float)."""
    val = str(val).strip()
    if val.endswith("m"):
        return float(val[:-1])
    if val.endswith("n"):  # nanocores (kubectl top sometimes)
        return float(val[:-1]) / 1e6
    if val.endswith("u"):  # microcores
        return float(val[:-1]) / 1e3
    return float(val) * 1000.0
