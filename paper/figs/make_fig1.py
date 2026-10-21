"""Fig. 1, system overview, drawn in draw.io's own idiom (default palette, Kubernetes
icons, classic arrows, dashed groups, circled steps) plus a notation strip.
Writes paper/figs/fig1_overview.drawio (the editable source) and fig1_overview.{svg,pdf,png}
from the same description. After editing the .drawio by hand, export the PDF from draw.io
(File > Export as > PDF, crop) instead of re-running this script.

Run from anywhere:  python paper/figs/make_fig1.py"""
import html
import os
import sys
import math
import re

W, H = 1040, 448
FONT = "Helvetica"
INK, MUTED = "#222222", "#555555"
# draw.io default palette: (fill, stroke)
BLUE = ("#dae8fc", "#6c8ebf")
GREEN = ("#d5e8d4", "#82b366")
ORANGE = ("#ffe6cc", "#d79b00")
YELLOW = ("#fff2cc", "#d6b656")
PURPLE = ("#e1d5e7", "#9673a6")
GREY = ("#f5f5f5", "#666666")
K8S = "#326ce5"

cells = []


def rect(x, y, w, h, fill="#ffffff", stroke=INK, sw=1, r=0, dashed=False):
    cells.append(("rect", dict(x=x, y=y, w=w, h=h, fill=fill, stroke=stroke, sw=sw, r=r, dashed=dashed)))


def ellipse(x, y, w, h, fill="#ffffff", stroke=INK, sw=1):
    cells.append(("ellipse", dict(x=x, y=y, w=w, h=h, fill=fill, stroke=stroke, sw=sw)))


def cylinder(x, y, w, h, fill, stroke, sw=1, cap=14):
    cells.append(("cyl", dict(x=x, y=y, w=w, h=h, fill=fill, stroke=stroke, sw=sw, cap=cap)))


def pod(x, y, s=22, ghost=False):
    cells.append(("pod", dict(x=x, y=y, w=s, h=s, ghost=ghost)))


def actor(x, y, w, h):
    cells.append(("actor", dict(x=x, y=y, w=w, h=h)))


def tri(x, y, w, h, fill, stroke, direction="north"):
    cells.append(("tri", dict(x=x, y=y, w=w, h=h, fill=fill, stroke=stroke, dir=direction)))


def text(x, y, w, h, s, size=13, color=INK, bold=False, align="center", valign="middle", italic=False, rot=False):
    cells.append(("text", dict(x=x, y=y, w=w, h=h, s=s, size=size, color=color, bold=bold,
                               align=align, valign=valign, italic=italic, rot=rot)))


def line(pts, color=INK, sw=1, end=True, dashed=False):
    cells.append(("line", dict(pts=pts, color=color, sw=sw, end=end, dashed=dashed)))


def box(x, y, w, h, s, pal, size=13, bold=False, r=8, color=INK, dashed=False, sw=1):
    rect(x, y, w, h, fill=pal[0], stroke=pal[1], r=r, dashed=dashed, sw=sw)
    text(x + 4, y, w - 8, h, s, size=size, bold=bold, color=color)


def step_no(x, y, n):
    ellipse(x, y, 22, 22, fill=INK, stroke=INK)
    text(x, y, 22, 22, str(n), size=13, bold=True, color="#ffffff")


def spark(x0, x1, y0, y1, vals, color, sw=1.5):
    line([(x0 + (x1 - x0) * i / (len(vals) - 1), y1 - (y1 - y0) * v) for i, v in enumerate(vals)],
         color=color, sw=sw, end=False)


# ======================================================================== live system
def live():
    rect(14, 12, 790, 186, fill="none", stroke="#999999", dashed=True, r=0)
    text(22, 16, 400, 18, "Live system: k3s cluster, 4 worker VMs", size=13, bold=True, align="left")
    mid = 106
    # workload trace
    tx, tw, th = 28, 106, 74
    rect(tx, mid - th / 2, tw, th, fill=GREEN[0], stroke=GREEN[1], r=4)
    text(tx, mid - th / 2 + 2, tw, 18, "workload trace", size=13)
    spark(tx + 10, tx + tw - 10, mid - 10, mid + 16,
          [0.3, 0.45, 0.35, 0.5, 0.7, 0.6, 0.85, 0.7, 0.95, 0.75, 0.8, 0.55, 0.62, 0.45, 0.5], "#4d7a3a")
    text(tx, mid + 18, tw, 16, "(Bitbrains, Azure)", size=11, color=MUTED, italic=True)
    # load generator
    gx, gw = 152, 82
    box(gx, mid - 22, gw, 44, "load\ngenerator", GREEN, r=4)
    line([(tx + tw, mid), (gx, mid)])
    # deployment
    dx, dy, dw, dh = 272, 40, 196, 128
    rect(dx, dy, dw, dh, fill=BLUE[0], stroke=BLUE[1], r=6)
    text(dx, dy + 4, dw, 18, "service (Deployment)", size=13, bold=True)
    for k in range(7):
        pod(dx + 11 + k * 25, dy + 34, 22, ghost=k >= 5)
    text(dx, dy + 62, dw, 18, "n_{t} ready pods, 1 to 12", size=13)
    text(dx, dy + 80, dw, 18, "200m CPU each", size=12, color=MUTED)
    line([(gx + gw, mid), (dx, mid)])
    text(gx + gw, mid - 19, dx - gx - gw, 16, "λ_{t}", size=13)
    # metrics-server and the HPA
    mx, my, mw, mh = 496, 50, 104, 32
    box(mx, my, mw, mh, "metrics-server", GREY, r=4, size=12)
    line([(dx + dw, my + mh / 2), (mx, my + mh / 2)])
    hx, hy, hw, hh = 620, 82, 96, 56
    box(hx, hy, hw, hh, "HPA at 70%\n(policy π_{0})", ORANGE, r=4)
    line([(mx + mw, my + mh / 2), (hx + hw / 2, my + mh / 2), (hx + hw / 2, hy)])
    text(hx + hw / 2 + 4, my + mh / 2 + 2, 60, 16, "ρ_{t}", size=13, align="left")
    line([(hx + hw / 2, hy + hh), (hx + hw / 2, 184), (dx + dw / 2, 184), (dx + dw / 2, dy + dh)])
    text(dx + dw / 2 + 60, 168, 220, 16, "scale by ±1 pod every 15 s", size=12, color=MUTED, align="left")
    # log
    lx, ly, lw, lh = 734, 62, 64, 92
    cylinder(lx, ly, lw, lh, fill=YELLOW[0], stroke=YELLOW[1], cap=14)
    text(lx, ly + 18, lw, 36, "log\nof π_{0}", size=13, bold=True)
    text(lx, ly + 56, lw, 30, "one row\nper step", size=11, color=MUTED, italic=True)
    line([(hx + hw, hy + hh / 2), (lx, hy + hh / 2)])
    return (lx + lw / 2, ly + lh)


# ======================================================================== operator
def operator():
    ax, ay = 900, 22
    actor(ax, ay, 26, 50)
    text(ax - 30, ay + 52, 86, 16, "operator", size=12, color=MUTED)
    bx, by, bw, bh = 826, 108, 196, 56
    rect(bx, by, bw, bh, fill="#ffffff", stroke=INK, r=10)
    tri(ax + 4, by - 11, 16, 12, fill="#ffffff", stroke=INK, direction="north")
    rect(ax + 5, by - 1, 14, 3, fill="#ffffff", stroke="none")       # hides the bubble edge under the tail
    text(bx + 6, by, bw - 12, bh, "Would a new policy π_{1}\nmeet the SLA? At what cost?", size=13, italic=True)
    return bx + bw / 2, by + bh


# ======================================================================== offline twin
def twin(log_bottom, bubble_bottom):
    gy, gh = 214, 172
    rect(14, gy, W - 28, gh, fill="none", stroke=PURPLE[1], dashed=True, sw=1.5)
    text(22, gy + 4, 400, 18, "Twin from the log (offline)", size=13, bold=True, align="left",
         color="#6c4f80")
    sy, sh = gy + 28, gh - 38
    # (1) index
    ix, iw = 28, 236
    rect(ix, sy, iw, sh, fill="#ffffff", stroke=PURPLE[1], r=4)
    step_no(ix + 8, sy + 8, 1)
    text(ix + 36, sy + 8, iw - 44, 22, "index logged steps", size=13, bold=True, align="left")
    rect(ix + 10, sy + 36, iw - 20, 44, fill=PURPLE[0], stroke="none", r=4)
    text(ix + 10, sy + 37, iw - 20, 22, "D = λ m / (n c)", size=14)
    text(ix + 10, sy + 57, iw - 20, 20, "load per pod; 1 = pod fully busy", size=11, color=MUTED, italic=True)
    gx0, gy0, gw, gh2 = ix + 64, sy + 88, 110, 40
    rect(gx0, gy0, gw, gh2, fill="#fffdf3", stroke="#cccccc")
    pts = [((math.sin(i * 12.9898) * 43758.5453) % 1, (math.sin(i * 78.233) * 12345.678) % 1) for i in range(1, 40)]
    for p, q in pts:
        ellipse(gx0 + 3 + p * (gw - 6) - 2, gy0 + 3 + q * (gh2 - 6) - 2, 4, 4, fill=YELLOW[1], stroke="none")
    text(gx0 - 58, gy0 + 4, 54, 16, "D_{t−1}", size=11, color=MUTED, align="right")
    text(gx0 + gw + 4, gy0 + gh2 - 16, 40, 16, "D_{t}", size=11, color=MUTED, align="left")
    line([log_bottom, (log_bottom[0], 204), (ix + iw - 22, 204), (ix + iw - 22, sy)], color=YELLOW[1], sw=1.5)
    text(log_bottom[0] - 126, 160, 118, 16, "all logged steps", size=12, color="#9c7d1e", align="right", italic=True)
    # (2) rollout
    rx, rw = 282, 452
    rect(rx, sy, rw, sh, fill="#ffffff", stroke=PURPLE[1], r=4)
    step_no(rx + 8, sy + 8, 2)
    text(rx + 36, sy + 8, rw - 44, 22, "run the target step by step", size=13, bold=True, align="left")
    nw, nh = 162, 36
    nL, nR = rx + 22, rx + rw - 22 - nw
    tY, bY = sy + 38, sy + 92
    box(nR, tY, nw, nh, "π_{1}, its own code", PURPLE, bold=True, r=4)
    box(nL, tY, nw, nh, "D_{t} = λ_{t} m / (n_{t} c)", PURPLE, r=4)
    box(nL, bY, nw, nh, "10 logged steps\nnearest in (D_{t}, D_{t−1})", YELLOW, r=4, size=12)
    box(nR, bY, nw, nh, "their ρ, ℓ, s", YELLOW, r=4)
    line([(nR, tY + nh / 2), (nL + nw, tY + nh / 2)])
    text(nL + nw, tY + nh / 2 - 17, nR - nL - nw, 16, "n_{t}", size=13)
    line([(nL + nw / 2, tY + nh), (nL + nw / 2, bY)])
    line([(nL + nw, bY + nh / 2), (nR, bY + nh / 2)])
    text(nL + nw, bY + nh / 2 - 17, nR - nL - nw, 16, "pick one", size=12, color=MUTED)
    line([(nR + nw / 2, bY), (nR + nw / 2, tY + nh)])
    text(nR + nw / 2 + 4, tY + nh + 2, 80, 16, "next step", size=11, color=MUTED, italic=True, align="left")
    line([(ix + iw, bY + nh / 2), (nL, bY + nh / 2)], color=YELLOW[1], sw=1.5)
    # (3) estimate
    ex, ew = 752, 136
    rect(ex, sy, ew, sh, fill="#ffffff", stroke=PURPLE[1], r=4)
    step_no(ex + 8, sy + 8, 3)
    text(ex + 36, sy + 8, ew - 44, 22, "average", size=13, bold=True, align="left")
    g0, g1, h0, h1 = ex + 12, ex + ew - 12, sy + 40, sy + 92
    for k, off in enumerate([0.0, 0.1, -0.08, 0.16, -0.13]):
        vals = [min(0.95, max(0.05, 0.5 + off + 0.22 * math.sin(i * 0.8 + k))) for i in range(10)]
        spark(g0, g1, h0, h1, vals, "#9673a6" if k == 0 else "#c9b6d6", sw=1.4 if k == 0 else 1)
    text(ex, h1 + 4, ew, 30, "40 rollouts,\nmean and interval", size=11, color=MUTED, italic=True)
    line([(nR + nw, bY + nh / 2), (ex, bY + nh / 2)])
    # output, back to the operator
    ox, ow = 904, 118
    box(ox, sy + 28, ow, 56, "SLA and cost\nof π_{1}", GREEN, bold=True, r=4)
    line([(ex + ew, sy + 56), (ox, sy + 56)])
    line([(ox + ow / 2, sy + 28), (ox + ow / 2, bubble_bottom[1])])
    box(ox, sy + 96, ow, 36, "checked against\nlive runs of π_{1}", GREY, r=4, size=11, dashed=True, color=MUTED)


def notation():
    y = 394
    rect(14, y, W - 28, 46, fill=GREY[0], stroke="#cccccc")
    text(24, y + 4, W - 48, 38,
         "λ_{t}: offered load (req/s)    n_{t}: ready pods    m: CPU per request (from the log)    c: CPU per pod (200m)"
         "\nρ: measured CPU utilisation    ℓ: mean latency    s: share of requests that succeed    "
         "π_{0}: logged policy    π_{1}: policy to evaluate", size=12, align="left")


# ======================================================================== outputs
SUB = re.compile(r"_\{([^}]*)\}")


def to_html(s):
    s = html.escape(s, quote=False)
    s = SUB.sub(r"<sub>\1</sub>", s)
    return s.replace("\n", "<br>")


def geom(a):
    return (f'<mxGeometry x="{a["x"]:.1f}" y="{a["y"]:.1f}" width="{a["w"]:.1f}" height="{a["h"]:.1f}" '
            f'as="geometry"/>')


def drawio():
    out = ['<mxfile host="app.diagrams.net" agent="make_fig1.py" version="24.7.17">',
           '  <diagram name="Fig. 1 system overview" id="fig1-overview">',
           f'    <mxGraphModel dx="{W}" dy="{H}" grid="1" gridSize="2" guides="1" tooltips="1" connect="1" '
           f'arrows="1" fold="1" page="1" pageScale="1" pageWidth="{W}" pageHeight="{H}" math="0" shadow="0">',
           '      <root>', '        <mxCell id="0"/>', '        <mxCell id="1" parent="0"/>']
    for n, (kind, a) in enumerate(cells, start=2):
        cid = f"c{n}"
        if kind in ("rect", "ellipse", "cyl", "tri"):
            if kind == "rect":
                st = f"rounded=1;arcSize={a['r']};absoluteArcSize=1;" if a["r"] else "rounded=0;"
            elif kind == "ellipse":
                st = "ellipse;"
            elif kind == "cyl":
                st = f"shape=cylinder3;boundedLbl=1;backgroundOutline=1;size={a['cap'] / 2};"
            else:
                st = f"triangle;direction={a['dir']};"
            st += f"whiteSpace=wrap;html=1;fillColor={a['fill']};strokeColor={a['stroke']};strokeWidth={a.get('sw', 1)};"
            if a.get("dashed"):
                st += "dashed=1;"
            out.append(f'        <mxCell id="{cid}" value="" style="{st}" vertex="1" parent="1">{geom(a)}</mxCell>')
        elif kind == "pod":
            st = ("sketch=0;html=1;dashed=0;whiteSpace=wrap;shape=mxgraph.kubernetes.icon;prIcon=pod;"
                  + ("fillColor=#ffffff;strokeColor=#326ce5;opacity=45;" if a["ghost"] else "fillColor=#326CE5;strokeColor=#ffffff;"))
            out.append(f'        <mxCell id="{cid}" value="" style="{st}" vertex="1" parent="1">{geom(a)}</mxCell>')
        elif kind == "actor":
            st = "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fillColor=#ffffff;strokeColor=#222222;"
            out.append(f'        <mxCell id="{cid}" value="" style="{st}" vertex="1" parent="1">{geom(a)}</mxCell>')
        elif kind == "text":
            st = (f"text;html=1;whiteSpace=wrap;overflow=visible;spacing=0;fontFamily={FONT};fontSize={a['size']};"
                  f"fontColor={a['color']};align={a['align']};verticalAlign={a['valign']};"
                  f"fontStyle={(1 if a['bold'] else 0) + (2 if a['italic'] else 0)};strokeColor=none;fillColor=none;")
            if a["rot"]:
                st += "horizontal=0;"
            out.append(f'        <mxCell id="{cid}" value="{html.escape(to_html(a["s"]), quote=True)}" style="{st}" '
                       f'vertex="1" parent="1">{geom(a)}</mxCell>')
        elif kind == "line":
            p = a["pts"]
            st = (f"edgeStyle=none;html=1;rounded=0;strokeColor={a['color']};strokeWidth={a['sw']};"
                  f"endArrow={'classic' if a['end'] else 'none'};endFill=1;startArrow=none;")
            if a["dashed"]:
                st += "dashed=1;"
            mids = "".join(f'<mxPoint x="{px:.1f}" y="{py:.1f}"/>' for px, py in p[1:-1])
            arr = f'<Array as="points">{mids}</Array>' if mids else ""
            out.append(f'        <mxCell id="{cid}" value="" style="{st}" edge="1" parent="1">'
                       f'<mxGeometry relative="1" as="geometry">'
                       f'<mxPoint x="{p[0][0]:.1f}" y="{p[0][1]:.1f}" as="sourcePoint"/>'
                       f'<mxPoint x="{p[-1][0]:.1f}" y="{p[-1][1]:.1f}" as="targetPoint"/>{arr}</mxGeometry></mxCell>')
    out += ['      </root>', '    </mxGraphModel>', '  </diagram>', '</mxfile>']
    return "\n".join(out)


def svg_text(a):
    lines = a["s"].split("\n")
    lh = a["size"] * 1.25
    x, y, w, h = a["x"], a["y"], a["w"], a["h"]
    y0 = (y + a["size"] * 0.95) if a["valign"] == "top" else (y + h / 2 - (len(lines) - 1) * lh / 2 + a["size"] * 0.35)
    anchor = {"left": "start", "center": "middle", "right": "end"}[a["align"]]
    xx = {"left": x, "center": x + w / 2, "right": x + w}[a["align"]]
    out = []
    for i, ln in enumerate(lines):
        parts, pos = [], 0
        for m in SUB.finditer(ln):
            parts.append(html.escape(ln[pos:m.start()]))
            parts.append(f'<tspan baseline-shift="sub" font-size="{a["size"] * 0.72:.1f}">{html.escape(m.group(1))}</tspan>')
            pos = m.end()
        parts.append(html.escape(ln[pos:]))
        style = (' font-weight="bold"' if a["bold"] else "") + (' font-style="italic"' if a["italic"] else "")
        out.append(f'<text x="{xx:.1f}" y="{y0 + i * lh:.1f}" font-family="Helvetica, Arial, sans-serif" '
                   f'font-size="{a["size"]}" fill="{a["color"]}" text-anchor="{anchor}" xml:space="preserve"{style}>{"".join(parts)}</text>')
    return "\n".join(out)


def svg():
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
         'orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L10,5 L0,10 L3,5 z" fill="context-stroke"/></marker></defs>',
         f'<rect width="{W}" height="{H}" fill="#ffffff"/>']
    for kind, a in cells:
        if kind == "rect":
            dash = ' stroke-dasharray="3 3"' if a["dashed"] else ""
            o.append(f'<rect x="{a["x"]:.1f}" y="{a["y"]:.1f}" width="{a["w"]:.1f}" height="{a["h"]:.1f}" rx="{a["r"]}" '
                     f'fill="{a["fill"]}" stroke="{a["stroke"]}" stroke-width="{a["sw"]}"{dash}/>')
        elif kind == "ellipse":
            o.append(f'<ellipse cx="{a["x"] + a["w"] / 2:.1f}" cy="{a["y"] + a["h"] / 2:.1f}" rx="{a["w"] / 2:.1f}" '
                     f'ry="{a["h"] / 2:.1f}" fill="{a["fill"]}" stroke="{a["stroke"]}" stroke-width="{a["sw"]}"/>')
        elif kind == "cyl":
            x, y, w, h, c = a["x"], a["y"], a["w"], a["h"], a["cap"]
            rx, ry = w / 2, c / 2
            o.append(f'<path d="M{x},{y + ry} A{rx},{ry} 0 0 1 {x + w},{y + ry} V{y + h - ry} A{rx},{ry} 0 0 1 {x},{y + h - ry} Z" '
                     f'fill="{a["fill"]}" stroke="{a["stroke"]}" stroke-width="{a["sw"]}"/>')
            o.append(f'<path d="M{x},{y + ry} A{rx},{ry} 0 0 0 {x + w},{y + ry}" fill="none" stroke="{a["stroke"]}"/>')
        elif kind == "tri":
            x, y, w, h = a["x"], a["y"], a["w"], a["h"]
            o.append(f'<path d="M{x},{y + h} L{x + w / 2},{y} L{x + w},{y + h} Z" fill="{a["fill"]}" stroke="{a["stroke"]}"/>')
        elif kind == "pod":
            x, y, s = a["x"], a["y"], a["w"]
            cx, cy, r = x + s / 2, y + s / 2, s / 2
            hept = " ".join(f"{cx + r * math.sin(2 * math.pi * k / 7):.1f},{cy - r * math.cos(2 * math.pi * k / 7):.1f}" for k in range(7))
            if a["ghost"]:
                o.append(f'<polygon points="{hept}" fill="#ffffff" stroke="{K8S}" stroke-opacity="0.45" stroke-dasharray="2 2"/>')
            else:
                o.append(f'<polygon points="{hept}" fill="{K8S}" stroke="#ffffff"/>')
                o.append(f'<rect x="{cx - 4:.1f}" y="{cy - 4:.1f}" width="8" height="8" fill="none" stroke="#ffffff" stroke-width="1.3"/>')
        elif kind == "actor":
            x, y, w, h = a["x"], a["y"], a["w"], a["h"]
            cx = x + w / 2
            o.append(f'<circle cx="{cx}" cy="{y + h * 0.13}" r="{h * 0.13}" fill="#fff" stroke="{INK}"/>')
            o.append(f'<path d="M{cx},{y + h * 0.26} V{y + h * 0.62} M{x},{y + h * 0.38} H{x + w} '
                     f'M{cx},{y + h * 0.62} L{x},{y + h} M{cx},{y + h * 0.62} L{x + w},{y + h}" stroke="{INK}" fill="none"/>')
        elif kind == "text":
            o.append(svg_text(a))
        elif kind == "line":
            d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in a["pts"])
            dash = ' stroke-dasharray="3 3"' if a["dashed"] else ""
            mk = ' marker-end="url(#ah)"' if a["end"] else ""
            o.append(f'<path d="{d}" fill="none" stroke="{a["color"]}" stroke-width="{a["sw"]}"{dash}{mk}/>')
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    log_bottom = live()
    bubble_bottom = operator()
    twin(log_bottom, bubble_bottom)
    notation()
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    from svgrender import render
    base = os.path.join(here, "fig1_overview")
    open(base + ".drawio", "w").write(drawio())
    open(base + ".svg", "w").write(svg())
    render(base + ".svg", W, H, pdf=base + ".pdf", png=base + ".png", png_scale=2)
    print(len(cells), "cells; wrote paper/figs/fig1_overview.{drawio,svg,pdf,png}")
