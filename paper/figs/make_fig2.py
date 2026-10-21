"""Fig. 2 (Section III): why the log misleads, from the live run logs.

(a) web service, all logged steps: median CPU reading (with interquartile band) and SLA
    compliance against load per pod D = rps * m / (n * c), m = 1.727 mCPU per req/s.
(b) window W1: share of each target's live steps that the HPA-70 log covers, indexed by
    (ready pods, load decile) or by D within 10% (log distance < 0.1).

Run from the repo root:  python paper/figs/make_fig2.py
Writes paper/figs/fig2_mislead.{svg,pdf,png}."""
import math
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path[:0] = [os.path.join(ROOT, "real"), ROOT, os.path.dirname(os.path.abspath(__file__))]
from m5_report import frames  # noqa: E402
from ope.twin import demand  # noqa: E402
from svgrender import Svg  # noqa: E402

RUNS = os.path.join(ROOT, "real", "runs")
M_WEB, CPU_POD = 1.727, 200
EDGES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.15, 1.3, 1.5, 1.75, 2, 2.5, 3, 4, 5]
TARGETS = [("hpa30", "HPA-30"), ("hpa50", "HPA-50"), ("slo_cost", "SLO-cost"),
           ("hpa85", "HPA-85"), ("hpa95", "HPA-95")]


def profile():
    """All logged web-service steps (every run, first step dropped) binned by D."""
    parts = []
    for f in sorted(os.listdir(RUNS)):
        if not f.startswith("on_") or not f.endswith(".csv") or f.endswith("_pods.csv") or "api" in f:
            continue
        d = pd.read_csv(os.path.join(RUNS, f)).iloc[1:]
        parts.append(d[["rps_achieved", "ready_replicas", "rho", "sla_ok"]])
    a = pd.concat(parts).apply(pd.to_numeric, errors="coerce").dropna()
    a["D"] = a.rps_achieved * M_WEB / (a.ready_replicas.clip(lower=1) * CPU_POD)
    a = a[a.D > 0]
    rows = []
    for lo, hi in zip(EDGES[:-1], EDGES[1:]):
        s = a[(a.D >= lo) & (a.D < hi)]
        if len(s) < 30:
            continue
        rows.append(dict(D=s.D.median(), rho=s.rho.median(), q25=s.rho.quantile(0.25),
                         q75=s.rho.quantile(0.75), sla=s.sla_ok.mean(), n=len(s)))
    return len(a), rows


def coverage(w="w1"):
    logs = pd.concat([d for _, d in frames([f"on_{w}_log_eps{e}_r{r}" for e in ("0.1", "0") for r in (1, 2)])])
    edges = np.quantile(logs.rps_target, np.linspace(0, 1, 11))
    lb = lambda x: np.clip(np.searchsorted(edges, x, side="right") - 1, 0, 9)  # noqa: E731
    seen = set(zip(logs.ready_replicas.astype(int), lb(logs.rps_target.values)))
    D = lambda d: demand(d.rps_achieved.values, d.ready_replicas.values, CPU_POD, M_WEB)  # noqa: E731
    Dl = np.sort(np.log(np.maximum(D(logs), 1e-3)))
    out = []
    for t, name in TARGETS:
        d = frames([f"on_{w}_truth_{t}"])[0][1]
        raw = np.mean([c in seen for c in zip(d.ready_replicas.astype(int), lb(d.rps_target.values))])
        Dt = np.log(np.maximum(D(d), 1e-3))
        i = np.clip(np.searchsorted(Dl, Dt), 1, len(Dl) - 1)
        near = np.minimum(np.abs(Dl[i] - Dt), np.abs(Dl[i - 1] - Dt))
        out.append((name, 100 * raw, 100 * np.mean(near < 0.1)))
    return out


INK, MUTED, GRID = "#222222", "#555555", "#e3e3e3"
BLUE, BLUE_L, ORANGE, GREY = "#6c8ebf", "#dae8fc", "#d79b00", "#b8b8b8"


def draw(prof, cov, base):
    W, H = 252, 126                                    # points; one IEEE column is 252 pt
    g = Svg(W, H)
    # (a) ------------------------------------------------------------------
    ax0, ax1, ay0, ay1 = 27, 124, 13, 100
    dmin, dmax = 0.1, 5.0
    X = lambda d: ax0 + math.log(d / dmin) / math.log(dmax / dmin) * (ax1 - ax0)  # noqa: E731
    Y = lambda v: ay1 - v * (ay1 - ay0)  # noqa: E731
    g.text(1, 7.5, "(a)", 7, weight="bold")
    for v in (0, 0.25, 0.5, 0.75, 1.0):
        g.add(f'<line x1="{ax0}" x2="{ax1}" y1="{Y(v):.2f}" y2="{Y(v):.2f}" stroke="{GRID}" stroke-width="0.5"/>')
        g.text(ax0 - 2.5, Y(v) + 2.1, f"{v:g}", 6, "end", MUTED)
    g.text(6, (ay0 + ay1) / 2, "fraction", 6.2, "middle", INK, rotate=-90)
    for d in (0.1, 0.3, 1, 3):
        g.add(f'<line x1="{X(d):.2f}" x2="{X(d):.2f}" y1="{ay1}" y2="{ay1 + 2}" stroke="{MUTED}" stroke-width="0.5"/>')
        g.text(X(d), ay1 + 8.5, f"{d:g}", 6, "middle", MUTED)
    g.add(f'<line x1="{ax0}" x2="{ax1}" y1="{ay1}" y2="{ay1}" stroke="{MUTED}" stroke-width="0.6"/>')
    g.text((ax0 + ax1) / 2, ay1 + 17.5,
           'load per pod <tspan font-style="italic">D</tspan> (log scale)', 6.3, "middle")
    g.add(f'<line x1="{X(1):.2f}" x2="{X(1):.2f}" y1="{ay0}" y2="{ay1}" stroke="{MUTED}" '
          f'stroke-width="0.5" stroke-dasharray="1.2 1.6"/>')
    up = " ".join(f"{X(p['D']):.2f},{Y(p['q75']):.2f}" for p in prof)
    dn = " ".join(f"{X(p['D']):.2f},{Y(p['q25']):.2f}" for p in reversed(prof))
    g.add(f'<polygon points="{up} {dn}" fill="{BLUE_L}" stroke="none"/>')
    ref = " ".join(f"{X(d):.2f},{Y(d):.2f}" for d in (dmin * (1 / dmin) ** (k / 80) for k in range(81)))
    g.add(f'<polyline points="{ref}" fill="none" stroke="{MUTED}" stroke-width="0.7" stroke-dasharray="3 2"/>')
    for key, col in (("rho", BLUE), ("sla", ORANGE)):
        pts = " ".join(f"{X(p['D']):.2f},{Y(p[key]):.2f}" for p in prof)
        g.add(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="1.6" '
              f'stroke-linejoin="round" stroke-linecap="round"/>')
    g.text(X(0.2), Y(1.0) - 3.2, "SLA met", 6.4, "middle", ORANGE, "bold")
    g.text(X(2.4), Y(0.57), "CPU reading", 6.4, "middle", BLUE, "bold")
    g.text(X(1) + 2.5, Y(0.97) + 1, "CPU = load", 5.9, "start", MUTED, italic=True)
    g.text(X(1) + 2, Y(0.05), "pod full", 5.9, "start", MUTED)
    # (b) ------------------------------------------------------------------
    bx0, bx1, by0, row, bh = 170, 240, 23, 15.0, 5.2
    BX = lambda p: bx0 + p / 100 * (bx1 - bx0)  # noqa: E731
    g.text(132, 7.5, "(b)", 7, weight="bold")
    ybot = by0 + row * len(cov) - 3
    for p in (0, 50, 100):
        g.add(f'<line x1="{BX(p):.2f}" x2="{BX(p):.2f}" y1="{by0 - 2}" y2="{ybot}" stroke="{GRID}" stroke-width="0.5"/>')
        g.text(BX(p), ay1 + 8.5, f"{p}%", 6, "middle", MUTED)
    g.add(f'<line x1="{bx0}" x2="{bx0}" y1="{by0 - 2}" y2="{ybot}" stroke="{MUTED}" stroke-width="0.6"/>')
    g.text((bx0 + bx1) / 2, ay1 + 17.5, "W1 steps covered by the log", 6.3, "middle")
    for i, (name, raw, dem) in enumerate(cov):
        y = by0 + i * row
        g.text(bx0 - 3, y + bh + 2.3, name, 6.3, "end", INK)
        g.add(f'<rect x="{bx0}" y="{y:.2f}" width="{BX(raw) - bx0:.2f}" height="{bh}" fill="{GREY}"/>')
        g.add(f'<rect x="{bx0}" y="{y + bh + 0.8:.2f}" width="{BX(dem) - bx0:.2f}" height="{bh}" fill="{BLUE}"/>')
    g.add(f'<rect x="{bx0 - 2}" y="2" width="5" height="5" fill="{GREY}"/>')
    g.text(bx0 + 5, 6.6, "by pods and load", 5.9, "start", MUTED)
    g.add(f'<rect x="{bx0 - 2}" y="10" width="5" height="5" fill="{BLUE}"/>')
    g.text(bx0 + 5, 14.6, 'by load per pod <tspan font-style="italic">D</tspan>', 5.9, "start", MUTED)
    g.save(base)


if __name__ == "__main__":
    n, prof = profile()
    cov = coverage()
    print(f"{n} logged web steps")
    for p in prof:
        print(f"  D {p['D']:.2f}: n={p['n']} cpu {p['rho']:.2f} [{p['q25']:.2f}, {p['q75']:.2f}] sla {100 * p['sla']:.0f}%")
    for name, raw, dem in cov:
        print(f"  W1 {name}: covered {raw:.1f}% by pods+load, {dem:.1f}% by D")
    draw(prof, cov, os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig2_mislead"))
    print("wrote paper/figs/fig2_mislead.{svg,pdf,png}")
