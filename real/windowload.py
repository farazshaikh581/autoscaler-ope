"""Load window with a hard end, for the 15 s harness step.

Same paced constant-rate loop as phase0/load.py, fanned across processes as in
phase1/loadgen.py, but every request must finish inside the window:
  - each request's socket timeout is min(REQUEST_TIMEOUT_S, time left in the window);
  - requests still queued at the end are not sent, and requests still in flight
    after the grace period are abandoned; both count as failures;
  - each worker process returns its samples at end + GRACE_S and exits.
So a saturated window costs at most duration + GRACE_S + process overhead, instead
of draining a backlog of 5 s timeouts (which stretched pilot steps to ~36 s).
Samples are (latency_ms, ok); a failure's latency is not used by summarize().
"""
from __future__ import annotations

import multiprocessing as mp
import os
import queue
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

REQUEST_TIMEOUT_S = 5.0
GRACE_S = 0.3
RPS_PER_PROC = 250
WORKERS_PER_PROC = 128


# percentile() and summarize() are copied from joint-hv-autoscaler phase0/load.py at
# commit de86f80, so the harness runs without that repository.
def percentile(sorted_vals: list[float], p: float) -> float:
    if not sorted_vals:
        return float("nan")
    k = min(int(round((p / 100.0) * (len(sorted_vals) - 1))), len(sorted_vals) - 1)
    return sorted_vals[k]


def summarize(samples: list[tuple[float, bool]]) -> dict:
    lats = sorted(l for l, ok in samples if ok)
    n = len(samples)
    ok_n = len(lats)
    return {
        "n": n,
        "success": (ok_n / n) if n else float("nan"),
        "mean_ms": (sum(lats) / ok_n) if ok_n else float("nan"),
        "p50_ms": percentile(lats, 50),
        "p90_ms": percentile(lats, 90),
        "p95_ms": percentile(lats, 95),
        "p99_ms": percentile(lats, 99),
    }


def _worker(url, rps, t_start, t_end, q):
    samples, lock = [], threading.Lock()
    sent = [0]

    def hit():
        t0 = time.time()
        left = t_end - t0
        if left <= 0:
            return                      # never sent: counted as a failure below
        ok = True
        try:
            with urllib.request.urlopen(url, timeout=min(REQUEST_TIMEOUT_S, left)) as r:
                r.read()
        except Exception:
            ok = False
        ok = ok and time.time() <= t_end
        with lock:
            samples.append(((time.time() - t0) * 1000.0, ok))

    pool = ThreadPoolExecutor(max_workers=WORKERS_PER_PROC)
    gap = 1.0 / rps
    while time.time() < t_start:
        time.sleep(0.001)
    i = 0
    while True:                          # paced submissions until the window ends
        nxt = t_start + i * gap
        if nxt >= t_end:
            break
        pause = nxt - time.time()
        if pause > 0:
            time.sleep(pause)
        pool.submit(hit)
        i += 1
    sent[0] = i
    pool.shutdown(wait=False, cancel_futures=True)
    time.sleep(max(0.0, t_end + GRACE_S - time.time()))
    with lock:
        done = list(samples)
    done += [(float("nan"), False)] * (sent[0] - len(done))   # cancelled or still in flight
    q.put(done)
    q.close()
    q.join_thread()
    os._exit(0)                          # abandon in-flight threads


def run_load(url: str, rps: int, duration: float, quiet: bool = True):
    """Drive `rps` for `duration` s; returns (latency_ms, ok) samples, one per request
    scheduled in the window. Returns within about duration + GRACE_S + 0.5 s."""
    procs = max(1, min(os.cpu_count() or 1, -(-rps // RPS_PER_PROC)))
    shares = [rps // procs + (1 if i < rps % procs else 0) for i in range(procs)]
    t_start = time.time() + 0.2          # processes start together
    t_end = t_start + duration
    q: mp.Queue = mp.Queue()
    ps = [mp.Process(target=_worker, args=(url, r, t_start, t_end, q)) for r in shares if r > 0]
    for p in ps:
        p.start()
    samples: list[tuple[float, bool]] = []
    for p in ps:
        try:
            samples += q.get(timeout=max(1.0, t_end + GRACE_S + 2.0 - time.time()))
        except queue.Empty:
            pass
    for p in ps:
        p.join(timeout=1.0)
        if p.is_alive():
            p.kill()
    expected = sum(int(-(-duration * r // 1)) for r in shares if r > 0)
    if len(samples) < expected:          # a worker that never reported: all its requests failed
        samples += [(float("nan"), False)] * (expected - len(samples))
    return samples
