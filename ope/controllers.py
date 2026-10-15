"""Target controllers and shared constants, self-contained.

ClassicalController (HPA), SloCostAwareController and PredictiveController are copied
from joint-hv-autoscaler phase1/eval_baselines.py at commit de86f80, decision logic
unchanged, so the OPE pipeline runs on saul without that repository.
real/check_saul_native.py checks that these copies take the same decision as the
originals on every logged step of every live run. The constants are the values of
phase1/envs/joint_hv_env.py at the same commit.
"""
from types import SimpleNamespace

REPLICA_MIN, REPLICA_MAX = 1, 12
MEM_MIN, MEM_MAX = 64, 512
SCALE_DELAY_STEPS = 2
SLA_MEAN_LATENCY_MS = 20.0
EPISODE_LEN = 200
D_REPS = (-1, 0, 1)                   # replica actions; index into these is the action id
M_KEYS = ("load_frac", "rho", "latency", "success", "mem_pressure", "cpu_util")
S_KEYS = ("replicas", "target_replicas", "cpu_req", "mem_req", "mem_need_now", "steps_to_ready")

HPA_TARGET_UTIL = 0.70   # standard HPA CPU target
HPA_TOLERANCE = 0.10     # HPA default: no action within 10% of target
HPA_SCALEDOWN_STAB = 3   # steps util must stay low before scaling in (anti-flap)
VPA_MEM_HEADROOM = 1.15  # keep the memory request ~15% above the working set


def in_bounds(d_rep: int, s) -> bool:
    """Same bound test the controllers use before emitting a replica delta."""
    return not ((d_rep > 0 and s.replicas >= REPLICA_MAX) or (d_rep < 0 and s.replicas <= REPLICA_MIN))


def snapshot(s) -> SimpleNamespace:
    """Copy of the fields a controller reads, so later steps cannot mutate it."""
    return SimpleNamespace(**{k: getattr(s, k) for k in S_KEYS})


def outcome(m: dict, s) -> tuple[float, float, float]:
    """(sla_ok, cost, latency) of one step."""
    sla_ok = float(m["latency"] < SLA_MEAN_LATENCY_MS and m["success"] >= 0.99)
    return sla_ok, s.replicas * s.cpu_req / 1000.0, m["latency"]


def _vpa_mem(s) -> int:
    target_mem = s.mem_need_now * VPA_MEM_HEADROOM
    if target_mem > s.mem_req:
        return +64
    if target_mem < s.mem_req - 64:
        return -64
    return 0


def _clamp(d_rep, d_mem, s):
    if (d_rep > 0 and s.replicas >= REPLICA_MAX) or (d_rep < 0 and s.replicas <= REPLICA_MIN):
        d_rep = 0
    if (d_mem > 0 and s.mem_req >= MEM_MAX) or (d_mem < 0 and s.mem_req <= MEM_MIN):
        d_mem = 0
    return (d_rep, 0, d_mem)


class ClassicalController:
    """HPA replica control (+ optional VPA memory right-sizing)."""

    def __init__(self, vpa: bool, target_util: float = HPA_TARGET_UTIL):
        self.vpa = vpa
        self.target_util = target_util
        self.reset()

    def reset(self) -> None:
        self._down = 0

    def act(self, m, s) -> tuple[int, int, int]:
        d_rep = 0
        ratio = m["cpu_util"] / self.target_util
        if s.steps_to_ready > 0:
            self._down = 0                       # a scale is in flight; HPA waits
        elif ratio > 1.0 + HPA_TOLERANCE:
            d_rep, self._down = +1, 0            # scale out immediately
        elif ratio < 1.0 - HPA_TOLERANCE:
            self._down += 1                      # scale in only after stabilisation
            if self._down >= HPA_SCALEDOWN_STAB:
                d_rep, self._down = -1, 0
        else:
            self._down = 0
        return _clamp(d_rep, _vpa_mem(s) if self.vpa else 0, s)


SLO_SCALE_DOWN_UTIL = 0.5   # scale in only when comfortably under the SLO
SLO_SCALEDOWN_STAB = 3      # same stabilisation window as the HPA baseline


class SloCostAwareController:
    """Rule-based SLO- and cost-aware controller: reconstruction of the five-stage
    pipeline of "An SLO Driven and Cost-Aware Autoscaling Framework for Kubernetes"
    (arXiv 2512.23415). A latency/success violation scales out only when demand exceeds
    capacity (rho > 1); scale-in needs no violation, CPU below 0.5 and a 3-step
    stabilisation window."""

    def __init__(self, vpa: bool = False):
        self.vpa = vpa
        self.reset()

    def reset(self) -> None:
        self._down = 0

    def act(self, m, s) -> tuple[int, int, int]:
        d_rep = 0
        if s.steps_to_ready > 0:
            self._down = 0
        else:
            viol = max(0.0, (m["latency"] - SLA_MEAN_LATENCY_MS) / SLA_MEAN_LATENCY_MS) + (1.0 - m["success"])
            backlog = max(0.0, m["rho"] - 1.0)
            if viol > 0 and backlog > 0:
                d_rep, self._down = +1, 0
            elif viol == 0 and m["cpu_util"] < SLO_SCALE_DOWN_UTIL:
                self._down += 1
                if self._down >= SLO_SCALEDOWN_STAB:
                    d_rep, self._down = -1, 0
            else:
                self._down = 0
        return _clamp(d_rep, _vpa_mem(s) if self.vpa else 0, s)


HOLT_ALPHA = 0.3                     # level smoothing
HOLT_BETA = 0.1                      # trend smoothing
FORECAST_LEAD = SCALE_DELAY_STEPS    # scale ahead so a fresh replica lands with the spike


class PredictiveController:
    """Forecast-then-scale: Holt's linear trend on load_frac, converted to a forecast
    utilisation with this tick's rho / load_frac, then the HPA trigger and
    stabilisation rules."""

    def __init__(self, vpa: bool, target_util: float = HPA_TARGET_UTIL):
        self.vpa = vpa
        self.target_util = target_util
        self.reset()

    def reset(self) -> None:
        self._down = 0
        self._level = None
        self._trend = 0.0

    def _forecast_load_frac(self, load_frac: float) -> float:
        if self._level is None:
            self._level = load_frac
            return load_frac
        prev_level = self._level
        self._level = HOLT_ALPHA * load_frac + (1 - HOLT_ALPHA) * (prev_level + self._trend)
        self._trend = HOLT_BETA * (self._level - prev_level) + (1 - HOLT_BETA) * self._trend
        return self._level + FORECAST_LEAD * self._trend

    def act(self, m, s) -> tuple[int, int, int]:
        load_frac_hat = self._forecast_load_frac(m["load_frac"])
        k_now = m["rho"] / max(m["load_frac"], 1e-6)
        forecast_util = min(max(k_now * load_frac_hat, 0.0), 1.5)
        d_rep = 0
        ratio = forecast_util / self.target_util
        if s.steps_to_ready > 0:
            self._down = 0
        elif ratio > 1.0 + HPA_TOLERANCE:
            d_rep, self._down = +1, 0
        elif ratio < 1.0 - HPA_TOLERANCE:
            self._down += 1
            if self._down >= HPA_SCALEDOWN_STAB:
                d_rep, self._down = -1, 0
        else:
            self._down = 0
        return _clamp(d_rep, _vpa_mem(s) if self.vpa else 0, s)
