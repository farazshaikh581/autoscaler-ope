"""Pilot gate for the overnight batch: (a) load generator, (e) harness health and
(b) a live HPA-70 vs HPA-95 SLA gap of at least 10 points are all required.
Exit 0 = proceed, 1 = stop. Prints one line per item.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pilot_report import RUNS, run_stats  # noqa: E402


def main():
    ok = True
    lc = json.load(open(os.path.join(RUNS, "loadcheck.json")))
    a = all(c["pass_rate"] and c["pass_cpu"] for c in lc["checks"])
    print(f"(a) load generator: {'PASS' if a else 'FAIL'}")
    ok &= a
    s = {p: run_stats(f"pilot_w1_{p}") for p in ("hpa70", "hpa95")}
    errs = [l for l in open(os.path.join(RUNS, "pilot.log")).read().splitlines()
            if re.search(r"Traceback|FAILED", l)]
    e_items = []
    for p, st in s.items():
        if st is None:
            e_items.append(f"{p} missing")
            continue
        if st["rows"] != 200:
            e_items.append(f"{p} has {st['rows']} rows")
        if st["step_overruns"] > 4:
            e_items.append(f"{p} {st['step_overruns']} step overruns")
        if st["cpu_nan_steps"] > 4:
            e_items.append(f"{p} {st['cpu_nan_steps']} steps without CPU metrics")
        if abs(st["rps_gap_median_pct"]) > 5:
            e_items.append(f"{p} median rps gap {st['rps_gap_median_pct']:.1f}%")
    e_items += errs
    e = not e_items
    print(f"(e) harness: {'PASS' if e else 'FAIL: ' + '; '.join(e_items)}")
    ok &= e
    if all(s.values()):
        gap = s["hpa70"]["sla_pct"] - s["hpa95"]["sla_pct"]
        print(f"(b) live SLA gap HPA-70 minus HPA-95: {gap:.1f} points: {'PASS' if gap >= 10 else 'FAIL (needs >= 10)'}")
        ok &= gap >= 10
    else:
        ok = False
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
