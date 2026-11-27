# -*- coding: utf-8 -*-
"""PNG renderer for Diagram display lists (PIL)."""
import os
import math
from PIL import Image, ImageDraw
from .uml_core import C, _font, lh, Box


def render_png(dg, path, dpi=300, bg=None):
    S = dpi / 2.54
    W = int(round(dg.w * S))
    H = int(round(dg.h * S))
    img = Image.new("RGB", (W, H), "#" + (bg or C["paper"]))
    d = ImageDraw.Draw(img)
    for op in dg.ops:
        k = op["k"]
        if k == "shape":
            _shape(d, op, S)
        elif k == "circle":
            xy = [(op["cx"] - op["r"]) * S, (op["cy"] - op["r"]) * S,
                  (op["cx"] + op["r"]) * S, (op["cy"] + op["r"]) * S]
            d.ellipse(xy, fill="#" + op["fill"] if op["fill"] else None,
                      outline="#" + op["line"] if op["line"] else None,
                      width=_w(op["lw"], S))
            if op.get("inner"):
                rr = op["r"] * 0.5
                d.ellipse([(op["cx"] - rr) * S, (op["cy"] - rr) * S,
                           (op["cx"] + rr) * S, (op["cy"] + rr) * S],
                          fill="#" + op["line"])
        elif k == "seg":
            _seg(d, op["p1"], op["p2"], op["color"], op["lw"], op["dash"], S)
        elif k == "path":
            pts = op["pts"]
            n = len(pts) - 1
            for i in range(n):
                a0 = op["arrow0"] if i == 0 else None
                a1 = op["arrow"] if i == n - 1 else None
                _seg(d, pts[i], pts[i + 1], op["color"], op["lw"], op["dash"],
                     S, a0, a1)
        elif k == "text":
            _text(d, op, S, dpi)
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    img.save(path, dpi=(dpi, dpi))
    return path


def _w(lw, S):
    """lw is in points -> pixels."""
    return max(1, int(round(lw * 2.54 / 72.0 * S)))


def _shape(d, op, S):
    b = op["box"]
    xy = [b.x * S, b.y * S, b.x2 * S, b.y2 * S]
    fill = "#" + op["fill"] if op["fill"] else None
    out = "#" + op["line"] if op["line"] else None
    w = _w(op["lw"], S)
    dash = op.get("dash")
    g = op["geom"]
    if g == "rect":
        if dash:
            _dash_rect(d, xy, out or "#000000", w, dash, S)
        else:
            d.rectangle(xy, fill=fill, outline=out, width=w)
    elif g == "roundRect":
        r = (op.get("radius") or 0.15) * S
        if dash:
            _dash_rrect(d, xy, r, out or "#000000", w, dash, S)
        else:
            d.rounded_rectangle(xy, radius=max(r, 1), fill=fill, outline=out,
                                width=w)
    elif g == "ellipse":
        d.ellipse(xy, fill=fill, outline=out, width=w)
    elif g == "diamond":
        pts = [(xy[0], (xy[1] + xy[3]) / 2), ((xy[0] + xy[2]) / 2, xy[1]),
               (xy[2], (xy[1] + xy[3]) / 2), ((xy[0] + xy[2]) / 2, xy[3])]
        d.polygon(pts, fill=fill, outline=out, width=w)
    elif g == "cylinder":
        x1, y1, x2, y2 = xy
        ry = (y2 - y1) * 0.13
        d.rectangle([x1, y1 + ry, x2, y2 - ry], fill=fill, outline=out, width=w)
        d.ellipse([x1, y1, x2, y1 + 2 * ry], fill=fill, outline=out, width=w)
        d.ellipse([x1, y2 - 2 * ry, x2, y2], fill=fill, outline=out, width=w)


def _dash_line(d, p1, p2, col, w, style, S=None):
    x1, y1 = p1
    x2, y2 = p2
    L = math.hypot(x2 - x1, y2 - y1)
    if L < 1e-9:
        return
    if style in ("sysDot", "dot", "roundDot"):
        on_cm, off_cm = 0.05, 0.08
    elif style in ("sysDash", "dash"):
        on_cm, off_cm = 0.17, 0.11
    else:
        on_cm, off_cm = 0.30, 0.12
    k = (S or 10.0)
    on, off = on_cm * k, off_cm * k
    ux, uy = (x2 - x1) / L, (y2 - y1) / L
    t = 0.0
    while t < L:
        t2 = min(t + on, L)
        d.line([x1 + ux * t, y1 + uy * t, x1 + ux * t2, y1 + uy * t2],
               fill=col, width=w)
        t = t2 + off


def _dash_rect(d, xy, col, w, style, S=None):
    x1, y1, x2, y2 = xy
    for a, b in (((x1, y1), (x2, y1)), ((x2, y1), (x2, y2)),
                 ((x2, y2), (x1, y2)), ((x1, y2), (x1, y1))):
        _dash_line(d, a, b, col, w, style, S)


def _dash_rrect(d, xy, r, col, w, style, S=None):
    x1, y1, x2, y2 = xy
    r = min(r, (x2 - x1) / 2, (y2 - y1) / 2)
    pts = [(x1 + r, y1), (x2 - r, y1), (x2, y1 + r), (x2, y2 - r),
           (x2 - r, y2), (x1 + r, y2), (x1, y2 - r), (x1, y1 + r)]
    for i in range(len(pts)):
        _dash_line(d, pts[i], pts[(i + 1) % len(pts)], col, w, style, S)


def _seg(d, p1, p2, color, lw, dash, S, a0=None, a1=None):
    col = "#" + color
    w = _w(lw, S)
    q1 = (p1[0] * S, p1[1] * S)
    q2 = (p2[0] * S, p2[1] * S)
    if dash:
        _dash_line(d, q1, q2, col, w, dash, S)
    else:
        d.line([q1[0], q1[1], q2[0], q2[1]], fill=col, width=w)
    if a1:
        _arrow(d, q1, q2, col, lw, a1, S)
    if a0:
        _arrow(d, q2, q1, col, lw, a0, S)


def _arrow(d, frm, to, col, lw, kind, S):
    ang = math.atan2(to[1] - frm[1], to[0] - frm[0])
    L = max(0.20 * S, lw * 2.54 / 72.0 * S * 4.6)
    W = L * 0.42
    c, s = math.cos(ang), math.sin(ang)
    p1 = to
    p2 = (to[0] - L * c + W * s, to[1] - L * s - W * c)
    p3 = (to[0] - L * c - W * s, to[1] - L * s + W * c)
    if kind in ("triangle", "stealth", "diamond", "oval"):
        d.polygon([p1, p2, p3], fill=col)
    else:
        d.line([p2[0], p2[1], p1[0], p1[1], p3[0], p3[1]], fill=col,
               width=max(1, _w(lw, S)), joint="curve")


def _text(d, op, S, dpi=300):
    pt = op["pt"]
    bold = op.get("bold", False)
    f = _font(pt, bold, dpi)
    col = "#" + op.get("color", C["text"])
    line_h = lh(pt) * S
    box = op.get("box")
    pad = op.get("pad", 0.0)
    align = op.get("align", "center")
    if box is not None:
        bw = box.w * S
        bx = box.x * S
        ih = box.h * S - 2 * pad * S
        bh = len(op["lines"]) * line_h
        if op.get("valign") == "top":
            by = box.y * S + pad * S
        elif op.get("valign") == "bottom":
            by = box.y2 * S - pad * S - bh
        else:
            by = box.y * S + (box.h * S - bh) / 2.0
    else:
        bw = op["w"] * S
        bx = op["x"] * S
        by = op["y"] * S
    asc, desc = f.getmetrics()
    for i, ln in enumerate(op["lines"]):
        if not ln:
            continue
        wpx = f.getlength(ln)
        if align == "center":
            lx = bx + (bw - wpx) / 2.0
        elif align == "right":
            lx = bx + bw - wpx
        else:
            lx = bx + pad * S
        base = by + i * line_h + (line_h - (asc + desc)) / 2.0 + asc
        d.text((lx, base), ln, font=f, fill=col, anchor="ls")
