# -*- coding: utf-8 -*-
"""Core model for JUMP2 UML diagrams: palette, metrics, geometry, primitives."""
import os
import math
from PIL import ImageFont

EMU_PER_CM = 360000
FONT_DIR = r"C:\Windows\Fonts"

C = {
    "ink": "22304C", "blue": "3A7BFD", "blue_d": "2A5FD4",
    "card": "2A3B5F", "border": "4A5A81", "teal": "1ABC9C",
    "teal_d": "0E7C66", "purple": "9B59B6", "purple_d": "7D3C98",
    "orange": "E67E22", "orange_d": "CA6F1E", "green": "2ECC71",
    "green_d": "27AE60", "red": "E74C3C", "red_d": "C0392B",
    "gray": "95A5A6", "gray_d": "7F8C8D", "white": "FFFFFF",
    "paper": "FFFFFF", "line": "5A6B8C", "text": "22304C",
    "muted": "6B7A99", "gblue": "4285F4", "docs": "34A853",
    "dark": "2C3E50", "sky": "2980B9",
}
FILL = {
    "blue": "E3ECFF", "teal": "D5F5EC", "purple": "EBDEF0",
    "orange": "FDEBD0", "green": "D8F5E4", "red": "FADBD8",
    "gray": "EEF1F5", "card": "E7EBF5", "panel": "F2F6FE",
    "sky": "D6EAF8", "dark": "E8EDF7",
}

_fc = {}


def _font(pt, bold=False, dpi=300):
    key = (round(pt, 2), bool(bold), int(dpi))
    if key not in _fc:
        name = "segoeuib.ttf" if bold else "segoeui.ttf"
        _fc[key] = ImageFont.truetype(os.path.join(FONT_DIR, name),
                                      int(round(pt / 72.0 * float(dpi))))
    return _fc[key]


def tw(s, pt, bold=False):
    """Text width in cm (dpi independent, measured at 300 dpi)."""
    return _font(pt, bold, 300).getlength(s) / 300.0 * 2.54


def lh(pt):
    """Line height in cm."""
    return pt * 1.22 / 72.0 * 2.54


def wrap(text, max_w, pt, bold=False):
    out = []
    for raw in str(text).split("\n"):
        cur = ""
        for w in raw.split(" "):
            cand = w if not cur else cur + " " + w
            if tw(cand, pt, bold) <= max_w or not cur:
                cur = cand
            else:
                out.append(cur)
                cur = w
        out.append(cur)
    return out


def bsize(lines, pt, bold=False):
    return (max((tw(s, pt, bold) for s in lines), default=0.0),
            len(lines) * lh(pt))


class Box:
    __slots__ = ("x", "y", "w", "h")

    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

    x2 = property(lambda s: s.x + s.w)
    y2 = property(lambda s: s.y + s.h)
    cx = property(lambda s: s.x + s.w / 2.0)
    cy = property(lambda s: s.y + s.h / 2.0)

    def t(self):
        return (self.x, self.y, self.w, self.h)

    def contains(self, o):
        return (o.x >= self.x - 1e-6 and o.y >= self.y - 1e-6
                and o.x2 <= self.x2 + 1e-6 and o.y2 <= self.y2 + 1e-6)

    def overlaps(self, o):
        return not (o.x >= self.x2 or o.x2 <= self.x
                    or o.y >= self.y2 or o.y2 <= self.y)

    def shrunk(self, d):
        return Box(self.x + d, self.y + d, self.w - 2 * d, self.h - 2 * d)


def seg_hits_rect(p1, p2, r, margin=0.0):
    """True when segment travels through the interior of r."""
    x1, y1, x2, y2 = p1[0], p1[1], p2[0], p2[1]
    rx1, ry1 = r.x + margin, r.y + margin
    rx2, ry2 = r.x2 - margin, r.y2 - margin
    if rx2 <= rx1 or ry2 <= ry1:
        return False
    if (x1 < rx1 and x2 < rx1) or (x1 > rx2 and x2 > rx2):
        return False
    if (y1 < ry1 and y2 < ry1) or (y1 > ry2 and y2 > ry2):
        return False
    dx, dy = x2 - x1, y2 - y1
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x1 - rx1), (dx, rx2 - x1), (-dy, y1 - ry1), (dy, ry2 - y1)):
        if abs(p) < 1e-12:
            if q < 0:
                return False
        else:
            r_ = q / p
            if p < 0:
                if r_ > t1:
                    return False
                t0 = max(t0, r_)
            else:
                if r_ < t0:
                    return False
                t1 = min(t1, r_)
    if t1 - t0 < 1e-9:
        return False
    return math.hypot(dx, dy) * (t1 - t0) > 0.02


def seg_cross(p1, p2, p3, p4):
    def o(a, b, c):
        v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        return 0 if abs(v) < 1e-9 else (1 if v > 0 else -1)
    o1, o2 = o(p1, p2, p3), o(p1, p2, p4)
    o3, o4 = o(p3, p4, p1), o(p3, p4, p2)
    if o1 == o2 or o3 == o4:
        return False
    for a in (p1, p2):
        for b in (p3, p4):
            if abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6:
                return False
    return True


def polyline_len(pts):
    return sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
               for i in range(len(pts) - 1))


def point_at(pts, frac):
    total = polyline_len(pts)
    if total <= 0:
        return pts[0]
    target = total * frac
    acc = 0.0
    for i in range(len(pts) - 1):
        d = math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
        if acc + d >= target or i == len(pts) - 2:
            t = 0.0 if d == 0 else (target - acc) / d
            t = min(max(t, 0.0), 1.0)
            return (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t,
                    pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t)
        acc += d
    return pts[-1]


class Diagram:
    """A diagram is an ordered display list plus node/edge registries."""

    def __init__(self, name, w, h):
        self.name = name
        self.w = w
        self.h = h
        self.ops = []
        self.nodes = {}
        self.containers = {}
        self.edges = []

    # ---------- raw ops ----------
    def _shape(self, geom, box, fill, line, lw, dash=None, radius=None):
        self.ops.append({"k": "shape", "geom": geom, "box": box, "fill": fill,
                         "line": line, "lw": lw, "dash": dash, "radius": radius})

    def _text(self, box, lines, pt, color, bold, align, valign, pad=0.05):
        if not lines:
            return
        bw, bh = bsize(lines, pt, bold)
        ih = box.h - 2 * pad
        iw = box.w - 2 * pad
        if valign == "top":
            ty = box.y + pad
        elif valign == "bottom":
            ty = box.y2 - pad - bh
        else:
            ty = box.y + (box.h - bh) / 2.0
        if align == "left":
            tx = box.x + pad
        elif align == "right":
            tx = box.x2 - pad - bw
        else:
            tx = box.x + (box.w - bw) / 2.0
        self.ops.append({"k": "text", "x": tx, "y": ty, "w": max(bw, 0.01),
                         "h": max(bh, 0.01), "lines": lines, "pt": pt,
                         "color": color, "bold": bold, "align": align,
                         "valign": valign, "pad": pad, "box": box})

    def seg(self, p1, p2, color, lw=1.1, dash=None):
        self.ops.append({"k": "seg", "p1": p1, "p2": p2, "color": color,
                         "lw": lw, "dash": dash})

    def circle(self, cx, cy, r, fill, line, lw=1.4, inner=False):
        self.ops.append({"k": "circle", "cx": cx, "cy": cy, "r": r, "fill": fill,
                         "line": line, "lw": lw, "inner": inner})

    # ---------- shape builders ----------
    def rect(self, nid, x, y, w, h, fill=None, line=None, lw=1.2, dash=None,
             text=None, tsize=9, tcolor=None, bold=False, align="center",
             valign="center", pad=0.10, container=False, tw_override=None):
        b = Box(x, y, w, h)
        if nid:
            (self.containers if container else self.nodes)[nid] = b
        self._shape("rect", b, fill, line, lw, dash)
        if text:
            self._text(b, wrap(text, tw_override or (w - 2 * pad), tsize, bold),
                       tsize, tcolor or C["text"], bold, align, valign, pad)
        return b

    def rrect(self, nid, x, y, w, h, radius=0.16, **kw):
        b = Box(x, y, w, h)
        nid_ = nid
        fill = kw.get("fill")
        line = kw.get("line")
        lw = kw.pop("lw", 1.2)
        dash = kw.pop("dash", None)
        text = kw.pop("text", None)
        tsize = kw.pop("tsize", 9)
        tcolor = kw.pop("tcolor", None)
        bold = kw.pop("bold", False)
        align = kw.pop("align", "center")
        valign = kw.pop("valign", "center")
        pad = kw.pop("pad", 0.10)
        container = kw.pop("container", False)
        if nid_:
            (self.containers if container else self.nodes)[nid_] = b
        self._shape("roundRect", b, fill, line, lw, dash, radius)
        if text:
            self._text(b, wrap(text, w - 2 * pad, tsize, bold), tsize,
                       tcolor or C["text"], bold, align, valign, pad)
        return b

    def ellipse(self, nid, x, y, w, h, fill=None, line=None, lw=1.4, text=None,
                tsize=8.5, tcolor=None, bold=False, pad=0.12):
        b = Box(x, y, w, h)
        if nid:
            self.nodes[nid] = b
        self._shape("ellipse", b, fill, line, lw)
        if text:
            self._text(b, wrap(text, max(w - 2 * pad, 0.4), tsize, bold),
                       tsize, tcolor or C["text"], bold, "center", "center", pad)
        return b

    def diamond(self, nid, x, y, w, h, fill=None, line=None, lw=1.5, text=None,
                tsize=8, tcolor=None, bold=False, pad=0.10):
        b = Box(x, y, w, h)
        if nid:
            self.nodes[nid] = b
        self._shape("diamond", b, fill, line, lw)
        if text:
            iw = max(w * 0.55 - 2 * pad, 0.5)
            self._text(b, wrap(text, iw, tsize, bold), tsize,
                       tcolor or C["text"], bold, "center", "center", pad)
        return b

    def cylinder(self, nid, x, y, w, h, text, fill, line, tsize=8.0):
        b = Box(x, y, w, h)
        if nid:
            self.nodes[nid] = b
        self._shape("cylinder", b, fill, line, 1.5)
        self._text(b, wrap(text, w - 0.55, tsize, True), tsize, C["ink"],
                   True, "center", "center", 0.14)
        return b

    def label_chip(self, x, y, text, pt=8, bold=True, color=None, fill=None,
                   pad_x=0.10, pad_y=0.05):
        lines = wrap(text, 99, pt, bold)
        bw, bh = bsize(lines, pt, bold)
        bw += 2 * pad_x
        bh += 2 * pad_y
        box = Box(x, y, bw, bh)
        self._shape("roundRect", box, fill or C["paper"], None, 0, None, 0.05)
        self._text(box, lines, pt, color or C["text"], bold, "center", "center", 0.02)
        return box

    def label_at(self, cx, cy, text, pt=8, bold=True, color=None, fill=None):
        lines = wrap(text, 99, pt, bold)
        bw, bh = bsize(lines, pt, bold)
        bw += 0.20
        bh += 0.10
        box = Box(cx - bw / 2.0, cy - bh / 2.0, bw, bh)
        self._shape("roundRect", box, fill if fill is not None else C["paper"],
                    None, 0, None, 0.05)
        self._text(box, lines, pt, color or C["text"], bold, "center", "center", 0.02)
        return box

    # ---------- edges ----------
    def edge(self, pts, color=None, lw=1.3, dash=None, arrow=None, arrow0=None,
             label=None, lsize=7.5, lcolor=None, label_at=0.5, src=None, dst=None):
        color = color or C["line"]
        self.ops.append({"k": "path", "pts": pts, "color": color, "lw": lw,
                         "dash": dash, "arrow": arrow, "arrow0": arrow0})
        chip = None
        if label:
            px, py = point_at(pts, label_at)
            chip = self.label_at(px, py, label, pt=lsize, bold=True,
                                 color=lcolor or color)
        self.edges.append({"pts": list(pts), "chip": chip, "src": src, "dst": dst,
                           "color": color, "label": label})
        return chip

    # ---------- composite ----------
    def actor(self, aid, cx, top, body_h, label, color, fill, tsize=8.0,
              label_w=2.5):
        r = 0.26
        head = top + r
        sh = head + r + 0.05
        hip = sh + body_h * 0.55
        foot = sh + body_h
        arm = sh + body_h * 0.30
        a = 0.50
        self.circle(cx, head, r, C["white"], color, 1.8)
        self.seg((cx, sh), (cx, hip), color, 1.8)
        self.seg((cx, hip), (cx, foot), color, 1.8)
        self.seg((cx - a, arm), (cx + a, arm), color, 1.8)
        self.seg((cx - 0.36, foot), (cx, hip), color, 1.8)
        self.seg((cx + 0.36, foot), (cx, hip), color, 1.8)
        lines = wrap(label, label_w, tsize, True)
        bw, bh = bsize(lines, tsize, True)
        bw += 0.24
        bh += 0.16
        box = Box(cx - bw / 2.0, foot + 0.10, bw, bh)
        self._shape("roundRect", box, fill, color, 1.4, None, 0.10)
        self._text(box, lines, tsize, C["white"], True, "center", "center", 0.04)
        self.nodes[aid] = box
        return box

    def class_box(self, cid, x, y, w, name, attrs, methods, header, border,
                  tsize=8.4, msize=7.0):
        nl = wrap(name, w - 0.16, tsize, True)
        head_h = max(0.40, bsize(nl, tsize, True)[1] + 0.14)
        al = []
        for a in attrs:
            al.extend(wrap(a, w - 0.24, msize))
        ml = []
        for m in methods:
            ml.extend(wrap(m, w - 0.24, msize))
        r = lh(msize)
        att_h = len(al) * r + 0.10 if al else 0.0
        met_h = len(ml) * r + 0.10 if ml else 0.0
        h = head_h + att_h + met_h
        box = Box(x, y, w, h)
        self.nodes[cid] = box
        self._shape("rect", box, C["white"], border, 1.5)
        self._shape("rect", Box(x, y, w, head_h), header, border, 1.5)
        self._text(box=Box(x, y, w, head_h), lines=nl, pt=tsize,
                   color=C["ink"], bold=True, align="center", valign="center",
                   pad=0.03)
        y2 = y + head_h
        if al:
            self.seg((x, y2), (x + w, y2), border, 1.0)
            self._text(Box(x + 0.12, y2, w - 0.24, att_h), al, msize, C["text"],
                       False, "left", "center", 0.03)
            y2 += att_h
        if ml:
            self.seg((x, y2), (x + w, y2), border, 1.0)
            self._text(Box(x + 0.12, y2, w - 0.24, met_h), ml, msize, C["text"],
                       False, "left", "center", 0.03)
        return box

    def lifeline(self, lid, cx, top, bottom, w, label, color, fill, tsize=7.4):
        lines = wrap(label, w - 0.14, tsize, True)
        bh = max(bsize(lines, tsize, True)[1] + 0.18, 0.70)
        box = Box(cx - w / 2.0, top, w, bh)
        self.nodes[lid] = box
        self._shape("roundRect", box, fill, color, 1.6, None, 0.10)
        self._text(box, lines, tsize, "000000", True, "center", "center", 0.04)
        self.seg((cx, box.y2), (cx, bottom), C["gray"], 1.0, "sysDash")
        self.containers[lid + "_ll"] = Box(cx - 0.03, box.y2, 0.06,
                                           bottom - box.y2)
        return box

    def activation(self, cx, y0, y1, w=0.32):
        self._shape("rect", Box(cx - w / 2.0, y0, w, y1 - y0), C["white"],
                    C["dark"], 1.3)


def class_height(name, attrs, methods, w, tsize=8.4, msize=6.5):
    """Height (cm) a class_box would occupy."""
    nl = wrap(name, w - 0.16, tsize, True)
    head_h = max(0.40, bsize(nl, tsize, True)[1] + 0.14)
    al = []
    for a in attrs:
        al.extend(wrap(a, w - 0.24, msize))
    ml = []
    for m in methods:
        ml.extend(wrap(m, w - 0.24, msize))
    r = lh(msize)
    att_h = len(al) * r + 0.10 if al else 0.0
    met_h = len(ml) * r + 0.10 if ml else 0.0
    return head_h + att_h + met_h
