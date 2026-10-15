"""M4 real-cluster harness: one 15 s control loop on saul's hv-phase0/web-service
(or, with --app api-service, the second application; both in deploy/).

  # dry run (default): the simulator stands in for the cluster, kubectl commands are printed
  python real/harness.py --policy dithered --eps 0.1 --family bitbrains --workload io-bound --start 1234
  # live run: only after E1 has finished AND the go is given
  python real/harness.py --live --policy hpa85 --family bitbrains --workload io-bound --start 1234 --tag w1_hpa85_r0

Each step (period P = 15 s):
  1. drive HTTP load at rps = load_frac[t] * cpu_intensity * max_rps for L seconds
     (real/windowload.py: the phase1/loadgen.py pacing with a hard window end;
     unfinished requests count as failures) and summarise the window: mean / p50 / p95 / p99 latency, success, achieved rps;
  2. observe: ready and requested replicas (kubectl get deploy), CPU used
     (kubectl top pods), rho = used / (ready * cpu_req), cpu_util = min(rho, 1.5);
  3. decide with the policy (dithered HPA with exact action probabilities, or a
     deterministic target), seeing the same m / s fields as in the simulator;
  4. act: kubectl scale to clip(requested + delta, 1, 12) if it changed;
  5. sleep to the next period boundary.
The window measured at step t+1 is the outcome of the action at step t; rows keep
the raw per-step record and real/align.py (to be written with the M4 analysis) pairs them.

Load is windowed: the driver idles for P - L seconds while kubectl runs. max_rps
defaults to 2050 rps, a load scale for saul: its knee check (real/kneecheck.py) gives
1.727 mcores per request, so one 200m pod saturates near 116 rps, and the trace windows
then peak at 960-1420 rps, needing 8-12 pods. The 1-12 replica range therefore spans
under- and over-provisioning on saul's four workers.

The live mode needs only this repository and the cluster: traces from traces/
(ope.traces), controllers from ope.controllers, kubectl helpers from real/kube.py. The
dry run uses the joint_hv_autoscaler simulator (ope.sim), imported only in that mode.
"""
import argparse
import csv
import json
import os
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
from ope.policies import REAL_TARGETS, DitheredHPA  # noqa: E402
from ope import traces  # noqa: E402
from ope.controllers import D_REPS, SLA_MEAN_LATENCY_MS  # noqa: E402
from kube import guard_namespace, kubectl, kubectl_json, parse_cpu_millicores  # noqa: E402

NS = "hv-phase0"
# The applications under test, deployed from deploy/<app>/ (deploy/apply.sh). max_rps is
# each app's load scale: the same trace step asks for the same number of 200m pods.
APPS = {
    "web-service": dict(configmap="web-app-code", max_rps=2050.0),
    "api-service": dict(configmap="api-app-code", max_rps=1508.0),   # 2050 * 1.727 / 2.348 (kneecheck_api-service.json)
}
DEPLOY, SELECTOR = "web-service", "app=web-service"     # set by use_app()
REPLICA_LO, REPLICA_HI = 1, 12
CPU_REQ_M = 200                      # deploy/<app>/manifest.yaml request; read live in --live mode
CPU_LIMIT = "200m"                   # OPE runs: limit = request, as in the sim's knee calibration (set by hand)
TARGETS = REAL_TARGETS
FIELDS = ["step", "wall_s", "load_frac", "rps_target", "rps_achieved", "n_requests",
          "latency_mean_ms", "latency_p50_ms", "latency_p95_ms", "latency_p99_ms", "success",
          "cpu_used_m", "metrics_age_s", "metrics_window_s", "pods_with_metrics", "rho", "cpu_util", "ready_replicas", "requested_replicas", "cpu_req",
          "steps_to_ready", "sla_ok", "cost_vcpu", "d_rep", "mu_minus", "mu_zero", "mu_plus", "act_s"]


class LiveCluster:
    def __init__(self, load_seconds):
        guard_namespace(NS)
        svc = kubectl_json(["get", "svc", DEPLOY, "-n", NS])
        self.url = f"http://{svc['spec']['clusterIP']}:{svc['spec']['ports'][0]['port']}/"
        self.load_seconds = load_seconds
        from windowload import run_load, summarize   # hard 12 s window: a saturated step stays inside 15 s
        self._run_load, self._summarize = run_load, summarize
        self.cpu_req = self._cpu_req()
        self._seen = set()

    def _cpu_req(self):
        d = kubectl_json(["get", "deploy", DEPLOY, "-n", NS])
        return int(round(parse_cpu_millicores(d["spec"]["template"]["spec"]["containers"][0]
                                              ["resources"]["requests"]["cpu"])))

    def reset(self, replicas=2, settle_s=60):
        kubectl(["scale", "deploy", DEPLOY, "-n", NS, f"--replicas={replicas}"], timeout=30)
        deadline = time.time() + 300
        while time.time() < deadline:
            ready, req = self.replicas()
            pods = kubectl(["get", "pods", "-n", NS, "-l", SELECTOR, "--no-headers"]).strip().splitlines()
            if ready == replicas == req and len(pods) == replicas:
                break
            time.sleep(5)
        time.sleep(settle_s)
        self.new_ready_pods()                # pods present before step 0 are not timed

    def load_window(self, rps):
        samples = self._run_load(self.url, max(1, int(rps)), self.load_seconds, quiet=True)
        return self._summarize(samples), len(samples) / self.load_seconds

    def replicas(self):
        d = kubectl_json(["get", "deploy", DEPLOY, "-n", NS])
        return int(d.get("status", {}).get("readyReplicas", 0) or 0), int(d["spec"]["replicas"])

    def cpu_used(self):
        """Total CPU of the serving pods (Ready, not terminating) from the metrics API,
        with the age of the newest sample, its averaging window and the pod count, as
        the HPA counts them: a terminating pod's usage must not land on fewer ready pods."""
        try:
            raw = kubectl(["get", "--raw", f"/apis/metrics.k8s.io/v1beta1/namespaces/{NS}/pods"
                           f"?labelSelector=app%3D{DEPLOY}"])
            items = json.loads(raw)["items"]
        except (RuntimeError, ValueError, KeyError):
            return float("nan"), float("nan"), float("nan"), 0
        live = self.serving_pods()
        items = [it for it in items if it["metadata"]["name"] in live]
        if not items:
            return float("nan"), float("nan"), float("nan"), 0
        try:
            used = sum(parse_cpu_millicores(c["usage"]["cpu"]) for it in items for c in it["containers"])
            now = time.time()
            ages = [now - _ts(it["timestamp"]) for it in items]
            windows = [_duration_s(it["window"]) for it in items]
        except (KeyError, ValueError) as e:            # a malformed sample must not end the run
            print(f"  [warn] metrics parse: {e}")
            return float("nan"), float("nan"), float("nan"), 0
        return used, min(ages), float(np.mean(windows)), len(items)

    def serving_pods(self):
        try:
            pods = kubectl_json(["get", "pods", "-n", NS, "-l", SELECTOR])["items"]
        except RuntimeError:
            return set()
        return {p["metadata"]["name"] for p in pods if not p["metadata"].get("deletionTimestamp")
                and any(c["type"] == "Ready" and c["status"] == "True" for c in p.get("status", {}).get("conditions", []))}

    def new_ready_pods(self):
        """Pods that became Ready since the last call: (name, created, ready, delay_s)."""
        try:
            pods = kubectl_json(["get", "pods", "-n", NS, "-l", SELECTOR])["items"]
        except RuntimeError:
            return []
        out = []
        for p in pods:
            name = p["metadata"]["name"]
            if name in self._seen:
                continue
            cond = {c["type"]: c for c in p.get("status", {}).get("conditions", [])}
            if cond.get("Ready", {}).get("status") == "True":
                self._seen.add(name)
                created, ready = _ts(p["metadata"]["creationTimestamp"]), _ts(cond["Ready"]["lastTransitionTime"])
                out.append((name, created, ready, ready - created))
        return out

    def scale(self, n):
        kubectl(["scale", "deploy", DEPLOY, "-n", NS, f"--replicas={n}"], timeout=30)


class DryRunCluster:
    """The simulator in the cluster's place, with the same observation path. kubectl
    commands are printed, not run. Used to check the loop, the logging and the
    policy wiring end to end before any cluster time is spent."""

    def __init__(self, family, workload, start, episode_len, load_seconds, quiet):
        from ope.sim import JointHVEnv, use_family
        use_family(family)
        self.env = JointHVEnv(workload=workload, episode_len=episode_len)
        self.env.reset(seed=0, options={"start": start})
        self.b = self.env._backend
        self.b.reset(start)                  # rewind: reset() already ran one physics step
        self.cpu_req, self.load_seconds, self.quiet = CPU_REQ_M, load_seconds, quiet
        self.url = "http://<clusterIP>:80/"
        self.m = None

    def _print(self, cmd):
        if not self.quiet:
            print("  [dry-run] kubectl " + " ".join(cmd))

    def reset(self, replicas=2, settle_s=60):
        self._print(["scale", "deploy", DEPLOY, "-n", NS, f"--replicas={replicas}"])

    def load_window(self, rps):
        self.m = self.b.step_physics()
        lat, ok = self.m["latency"], self.m["success"]
        summ = dict(n=int(rps * self.load_seconds), success=ok, mean_ms=lat, p50_ms=lat, p90_ms=lat,
                    p95_ms=lat, p99_ms=lat)
        return summ, rps

    def replicas(self):
        return self.b.s.replicas, self.b.s.target_replicas

    def cpu_used(self):
        return self.m["rho"] * self.b.s.replicas * self.cpu_req, 0.0, 0.0, self.b.s.replicas

    def new_ready_pods(self):
        return []

    def scale(self, n):
        self._print(["scale", "deploy", DEPLOY, "-n", NS, f"--replicas={n}"])
        self.b.apply(n - self.b.s.target_replicas, 0, 0)


def _duration_s(text):
    """Go duration as reported by metrics-server ('16.4s', '803ms', '1m2.5s') -> seconds."""
    import re
    units = {"h": 3600.0, "m": 60.0, "s": 1.0, "ms": 1e-3, "us": 1e-6, "µs": 1e-6, "ns": 1e-9}
    parts = re.findall(r"([0-9.]+)(ms|us|µs|ns|h|m|s)", text)
    if not parts or "".join(n + u for n, u in parts) != text:
        raise ValueError(f"unparsed duration {text!r}")
    return sum(float(n) * units[u] for n, u in parts)


def _ts(iso):
    """RFC 3339 timestamp from the API server or a kubelet -> epoch seconds."""
    from datetime import datetime, timezone
    return datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()


def cluster_state():
    """Node schedulability and this process's CPU affinity, for the run metadata."""
    nodes = kubectl_json(["get", "nodes"])["items"]
    return dict(nodes={n["metadata"]["name"]: ("cordoned" if n["spec"].get("unschedulable") else "schedulable")
                       for n in nodes},
                cpu_affinity=sorted(os.sched_getaffinity(0)))


STOCK_VPA_ARGS = ["--vpa-object-namespace=hv-phase0"]     # install_vpa.sh stock profile
RUNLOG = os.path.join(HERE, "RUNLOG.md")


def vpa_args():
    out = {}
    for d in ("vpa-recommender", "vpa-updater"):
        out[d] = json.loads(kubectl(["get", "deploy", d, "-n", "kube-system", "-o",
                                     "jsonpath={.spec.template.spec.containers[0].args}"]) or "[]")
    return out


def runlog(what, expected_s):
    """One line per live run, written before it starts (Faraz's standing rule)."""
    if not os.path.exists(RUNLOG):
        with open(RUNLOG, "w") as f:
            f.write("# saul live runs (OPE). One line per run, appended before it starts.\n\n"
                    "| start (UTC) | what | expected end (UTC) |\n|---|---|---|\n")
    now = time.time()
    fmt = lambda t: time.strftime("%Y-%m-%d %H:%M", time.gmtime(t))  # noqa: E731
    with open(RUNLOG, "a") as f:
        f.write(f"| {fmt(now)} | {what} | {fmt(now + expected_s)} |\n")


def live_cpu_limit():
    return kubectl(["get", "deploy", DEPLOY, "-n", NS, "-o",
                    "jsonpath={.spec.template.spec.containers[0].resources.limits.cpu}"]).strip()


def _sigterm(signum, frame):
    raise SystemExit(f"terminated by signal {signum}")    # runs the finally: scale back to 2


def e1_running():
    return subprocess.run(["pgrep", "-f", "run_vpa_matrix.sh"], capture_output=True).returncode == 0


def preflight_live():
    problems = []
    if e1_running():
        problems.append("E1 (run_vpa_matrix.sh) is still running")
    for kind in ("hpa", "vpa"):
        try:
            out = kubectl(["get", kind, "-n", NS, "--no-headers"]).strip()
        except RuntimeError:
            out = ""
        if out and not out.startswith("No resources"):
            problems.append(f"a {kind} object exists in {NS}: {out.splitlines()[0]}")
    args = vpa_args()
    for d, a in args.items():
        if a != STOCK_VPA_ARGS:
            problems.append(f"{d} args are not the stock profile: {a}")
    state = cluster_state()
    state["vpa_args"] = args
    state["cpu_limit"] = live_cpu_limit()
    state["app"] = DEPLOY
    state["app_code_sha256"], same = app_code_sha256(DEPLOY)
    if not same:
        problems.append(f"the {DEPLOY} code in the cluster differs from deploy/{DEPLOY}/app.py; run deploy/apply.sh")
    if state["cpu_limit"] != CPU_LIMIT:
        problems.append(f"{DEPLOY} CPU limit is {state['cpu_limit']}, OPE runs need {CPU_LIMIT} (= request)")
    cordoned = [n for n, v in state["nodes"].items() if n.startswith("k8s-worker") and v != "schedulable"]
    if cordoned:
        problems.append(f"workers cordoned: {cordoned} (M4 uses all 4 workers schedulable)")
    if any(c % 2 for c in state["cpu_affinity"]):
        problems.append(f"process may run on odd CPUs {state['cpu_affinity']} (worker vCPU cores); use taskset")
    if problems:
        sys.exit("refusing to start live run: " + "; ".join(problems))
    return state


def use_app(app):
    global DEPLOY, SELECTOR
    if app not in APPS:
        sys.exit(f"unknown app {app!r}: {', '.join(APPS)}")
    DEPLOY, SELECTOR = app, f"app={app}"


def app_code_sha256(app):
    """sha256 of deploy/<app>/app.py, and whether the cluster's ConfigMap holds that code."""
    import hashlib
    with open(os.path.join(REPO, "deploy", app, "app.py"), "rb") as f:
        code = f.read()
    live = kubectl_json(["get", "configmap", APPS[app]["configmap"], "-n", NS])["data"]["app.py"].encode()
    return hashlib.sha256(code).hexdigest(), live == code


def make_policy(name, eps, seed, base_util=0.70):
    if name == "dithered":
        return DitheredHPA(eps, np.random.default_rng(seed), base_util), True
    return TARGETS[name](), False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="act on the cluster (default: dry run)")
    ap.add_argument("--policy", default="dithered", help="'dithered' or a target name: " + ", ".join(TARGETS))
    ap.add_argument("--eps", type=float, default=0.0)
    ap.add_argument("--behaviour-util", type=float, default=0.70, help="target utilisation of the dithered HPA")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--family", choices=("azure", "bitbrains"), required=True)
    ap.add_argument("--workload", required=True)
    ap.add_argument("--start", type=int, required=True, help="trace index of step 0")
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--period", type=float, default=15.0)
    ap.add_argument("--load-seconds", type=int, default=12)
    ap.add_argument("--app", default="web-service", help="application under test: " + ", ".join(APPS))
    ap.add_argument("--max-rps", type=float, default=None, help="load scale (default: the app's, see APPS)")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    use_app(args.app)
    if args.max_rps is None:
        args.max_rps = APPS[args.app]["max_rps"]
        if args.max_rps is None:
            sys.exit(f"{args.app} has no load scale yet: run real/kneecheck.py --app {args.app}, then set APPS")
    load = traces.load_frac(args.family, args.workload)   # same normalisation as the sim
    cpu_int = traces.INTENSITY[args.workload]

    state = None
    if args.live:
        state = preflight_live()
        signal.signal(signal.SIGTERM, _sigterm)
        cluster = LiveCluster(args.load_seconds)
    else:
        cluster = DryRunCluster(args.family, args.workload, args.start, args.steps, args.load_seconds, args.quiet)
    policy, dithered = make_policy(args.policy, args.eps, args.seed, args.behaviour_util)
    policy.reset()
    tag = args.tag or f"{'live' if args.live else 'dry'}_{args.family}_{args.workload}_{args.start}_{args.policy}_eps{args.eps:g}_s{args.seed}"
    out_dir = os.path.join(HERE, "runs" if args.live else "dryruns")
    os.makedirs(out_dir, exist_ok=True)
    meta = dict(vars(args), tag=tag, cpu_int=cpu_int, trace_sha256=traces.sha256(args.family, args.workload), cluster=state,
                topology="all 4 workers schedulable" if args.live else "dry-run (simulator)",
                ope_commit=subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"], capture_output=True,
                                          text=True).stdout.strip(), started=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    with open(os.path.join(out_dir, f"{tag}.json"), "w") as f:
        json.dump(meta, f, indent=1)

    if args.live:
        runlog(f"OPE harness {tag}: {'' if args.app == 'web-service' else args.app + ', '}{args.policy} eps={args.eps:g}, {args.family}/{args.workload} start "
               f"{args.start}, {args.steps} steps x {args.period:g}s, CPU limit {state['cpu_limit']}", args.steps * args.period + 180)
    cluster.reset()
    t0 = time.time()
    pods_f = open(os.path.join(out_dir, f"{tag}_pods.csv"), "w", newline="")
    pods_w = csv.writer(pods_f)
    pods_w.writerow(["step", "pod", "created_s", "ready_s", "readiness_delay_s"])
    try:
        run_steps(args, cluster, policy, dithered, load, cpu_int, out_dir, tag, t0, pods_w, pods_f.flush)
    finally:
        pods_f.close()
        if args.live:
            cluster.scale(2)                 # leave the deployment at its default size
    print(f"{tag}: {args.steps} steps in {time.time() - t0:.0f}s -> {out_dir}/{tag}.csv")


def run_steps(args, cluster, policy, dithered, load, cpu_int, out_dir, tag, t0, pods_w, pods_flush):
    with open(os.path.join(out_dir, f"{tag}.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for step in range(args.steps):
            ts = time.time()
            lf = float(load[(args.start + step) % len(load)])
            rps = lf * cpu_int * args.max_rps
            summ, achieved = cluster.load_window(rps)
            ready, requested = cluster.replicas()
            used, age, window, n_met = cluster.cpu_used()
            for pod, created_at, ready_at, delay in cluster.new_ready_pods():   # distinct names: `ready` is the replica count
                pods_w.writerow([step, pod, round(created_at - t0, 1), round(ready_at - t0, 1), round(delay, 1)])
                pods_flush()
            rho = used / (n_met * cluster.cpu_req) if n_met else float("nan")   # over the pods measured
            lat = summ["mean_ms"] if summ["n"] and not np.isnan(summ["mean_ms"]) else 5000.0
            success = summ["success"] if summ["n"] else 0.0
            m = dict(load_frac=lf, rho=rho, latency=lat, success=success, cpu_util=min(rho, 1.5), mem_pressure=0.0)
            s = SimpleNamespace(replicas=ready, target_replicas=requested, cpu_req=cluster.cpu_req,
                                steps_to_ready=int(ready != requested), mem_req=128, mem_need_now=0.0)
            ta = time.time()
            if dithered:
                d, mu = policy.act(m, s)
            else:                                   # deterministic target: its action has probability 1
                d = policy.act(m, s)[0]
                mu = np.eye(3)[D_REPS.index(d)]
            new = int(np.clip(requested + d, REPLICA_LO, REPLICA_HI))
            if new != requested:
                cluster.scale(new)
            act_s = time.time() - ta
            w.writerow(dict(step=step, wall_s=round(ts - t0, 3), load_frac=lf, rps_target=round(rps, 1),
                            rps_achieved=round(achieved, 1), n_requests=summ["n"], latency_mean_ms=lat,
                            latency_p50_ms=summ["p50_ms"], latency_p95_ms=summ["p95_ms"], latency_p99_ms=summ["p99_ms"],
                            success=success, cpu_used_m=used, metrics_age_s=round(age, 1),
                            metrics_window_s=round(window, 1), pods_with_metrics=n_met, rho=rho, cpu_util=min(rho, 1.5), ready_replicas=ready,
                            requested_replicas=requested, cpu_req=cluster.cpu_req, steps_to_ready=s.steps_to_ready,
                            sla_ok=int(lat < SLA_MEAN_LATENCY_MS and success >= 0.99),
                            cost_vcpu=ready * cluster.cpu_req / 1000.0, d_rep=d,
                            mu_minus=mu[0], mu_zero=mu[1], mu_plus=mu[2], act_s=round(act_s, 3)))
            f.flush()                          # unattended runs: every row on disk at once
            if args.live:
                time.sleep(max(0.0, ts + args.period - time.time()))


if __name__ == "__main__":
    main()
