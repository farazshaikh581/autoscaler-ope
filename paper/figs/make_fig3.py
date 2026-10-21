"""Fig. 3 and Table I (Section V): accuracy on the 32 test cases.

Reads real/runs/m8_cells.csv (web service, W4 and W5) and real/runs/m9_cells.csv
(JSON API, W1 and W4): 8 targets per window, live truth from one or two runs.
Prints the Table I numbers and writes paper/figs/fig3_errors.{svg,pdf,png}.

Run from anywhere:  python paper/figs/make_fig3.py"""
import math
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from svgrender import Svg  # noqa: E402

RUN_SD = 2.4                  # SD of SLA% between repeated live runs of one target (24 pairs)
GATE_SLA, GATE_COST = 3.0, 15.0
EST = [("twin", "Twin"), ("queue", "Queueing model"), ("mbcalq_trees", "Model-based"),
       ("drmb_k4", "Doubly robust"), ("sntpdis_k4", "Importance sampl."), ("replay", "Replay")]


def cases():
    web = pd.read_csv(os.path.join(ROOT, "real", "runs", "m8_cells.csv")).assign(service="web")
    api = pd.read_csv(os.path.join(ROOT, "real", "runs", "m9_cells.csv")).assign(service="api")
    return pd.concat([web, api], ignore_index=True)


def table(c):
    print(f"{len(c)} test cases")
    print(f"{'estimator':18s} {'median':>6s} {'worst':>6s} {'cost':>6s} {'gate':>5s} {'web':>5s} {'api':>5s}")
    for key, name in EST:
        e, ce = c[f"{key}_sla_err"], c[f"{key}_cost_err"]
        gate = int(((e <= GATE_SLA) & (ce <= GATE_COST)).sum())
        by = c.groupby("service")[f"{key}_sla_err"].median()
        print(f"{name:18s} {e.median():6.1f} {e.max():6.1f} {ce.median():5.1f}% {gate:2d}/{len(c)} "
              f"{by['web']:5.1f} {by['api']:5.1f}")
    print(f"twin interval contains the live result: {int(c.in_pi.sum())}/{len(c)}")
    print(f"twin errors within one live-run SD ({RUN_SD}): {int((c.twin_sla_err <= RUN_SD).sum())}/{len(c)}")


INK, MUTED, GRID = "#222222", "#555555", "#e3e3e3"
PURPLE, RED, GREY, BAND = "#9673a6", "#b85450", "#8c8c8c", "#efefef"


def draw(c, base):
    W, H = 252, 118
    g = Svg(W, H)
    x0, x1, y0, rh = 74, 226, 16, 14.0
    lo, hi = 0.1, 100.0
    X = lambda v: x0 + math.log10(max(v, lo) / lo) / math.log10(hi / lo) * (x1 - x0)  # noqa: E731
    yb = y0 + rh * len(EST)
    # band: one SD of the variation between repeated live runs
    g.add(f'<rect x="{x0}" y="{y0 - 3}" width="{X(RUN_SD) - x0:.2f}" height="{yb - y0 + 3}" fill="{BAND}"/>')
    g.text(x0 + 2, y0 - 5.5, "live runs, 1 SD", 5.6, "start", MUTED, italic=True)
    for v in (0.1, 1, 10, 100):
        g.add(f'<line x1="{X(v):.2f}" x2="{X(v):.2f}" y1="{y0 - 3}" y2="{yb}" stroke="{GRID}" stroke-width="0.5"/>')
        g.text(X(v), yb + 8, f"{v:g}", 6, "middle", MUTED)
    g.add(f'<line x1="{x0}" x2="{x1}" y1="{yb}" y2="{yb}" stroke="{MUTED}" stroke-width="0.6"/>')
    g.text((x0 + x1) / 2, yb + 16.5, "absolute SLA error (points, log scale)", 6.3, "middle")
    g.text(x1 + 13, y0 - 5.5, "median", 5.6, "middle", MUTED)
    for i, (key, name) in enumerate(EST):
        yc = y0 + i * rh + rh / 2 - 1.5
        col = PURPLE if key == "twin" else RED if key == "replay" else GREY
        g.text(x0 - 4, yc + 2.2, name, 6.3, "end", INK, "bold" if key == "twin" else "normal")
        for svc, dy in (("web", -2.6), ("api", 2.6)):
            vals = sorted(c.loc[c.service == svc, f"{key}_sla_err"])
            for k, v in enumerate(vals):
                jit = ((k * 7) % 5 - 2) * 0.55          # small fixed vertical spread
                cx, cy = X(v), yc + dy + jit
                if svc == "web":
                    g.add(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="1.55" fill="{col}" fill-opacity="0.85"/>')
                else:
                    g.add(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="1.35" fill="#ffffff" stroke="{col}" stroke-width="0.7"/>')
        med = c[f"{key}_sla_err"].median()
        g.add(f'<line x1="{X(med):.2f}" x2="{X(med):.2f}" y1="{yc - 6}" y2="{yc + 6}" stroke="{INK}" stroke-width="1.1"/>')
        g.text(x1 + 13, yc + 2.2, f"{med:.1f}", 6.2, "middle", INK, "bold" if key == "twin" else "normal")
    # legend
    lx = x0 + 92
    g.add(f'<circle cx="{lx}" cy="{y0 - 7.6}" r="1.55" fill="{GREY}"/>')
    g.text(lx + 3.5, y0 - 5.5, "web", 5.8, "start", MUTED)
    g.add(f'<circle cx="{lx + 22}" cy="{y0 - 7.6}" r="1.35" fill="#ffffff" stroke="{GREY}" stroke-width="0.7"/>')
    g.text(lx + 25.5, y0 - 5.5, "JSON API", 5.8, "start", MUTED)
    g.save(base)


if __name__ == "__main__":
    c = cases()
    table(c)
    draw(c, os.path.join(HERE, "fig3_errors"))
    print("wrote paper/figs/fig3_errors.{svg,pdf,png}")
