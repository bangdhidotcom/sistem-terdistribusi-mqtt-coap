# -*- coding: utf-8 -*-
"""Layout validator: node overlap, edge/node collision, bounds, text fit."""
import math
from .uml_core import Box, seg_hits_rect, seg_cross, bsize, wrap, lh


def _pt_seg_dist(p, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    wx, wy = p[0] - a[0], p[1] - a[1]
    L2 = vx * vx + vy * vy
    if L2 < 1e-12:
        return math.hypot(wx, wy)
    t = max(0.0, min(1.0, (wx * vx + wy * vy) / L2))
    return math.hypot(p[0] - (a[0] + t * vx), p[1] - (a[1] + t * vy))


def _junction_or_collinear(p1, p2, p3, p4, tol=0.03):
    """True when the two segments touch at an endpoint / T / are collinear."""
    for a in (p1, p2):
        if _pt_seg_dist(a, p3, p4) <= tol:
            return True
    for a in (p3, p4):
        if _pt_seg_dist(a, p1, p2) <= tol:
            return True
    # collinear overlap?
    d1 = abs((p2[0] - p1[0]) * (p3[1] - p1[1]) - (p2[1] - p1[1]) * (p3[0] - p1[0]))
    d2 = abs((p2[0] - p1[0]) * (p4[1] - p1[1]) - (p2[1] - p1[1]) * (p4[0] - p1[0]))
    scale = max(math.hypot(p2[0] - p1[0], p2[1] - p1[1]), 1e-6)
    if d1 / scale <= tol and d2 / scale <= tol:
        return True
    return False


def _owner_of(box, containers):
    """Return ids of containers that fully hold box."""
    return [cid for cid, c in containers.items() if c.contains(box)]


def validate(dg, verbose=True, allow_edge_crossings=True):
    problems = []
    warnings = []

    # 1. bounds
    for nid, b in list(dg.nodes.items()) + list(dg.containers.items()):
        if b.x < -0.02 or b.y < -0.02 or b.x2 > dg.w + 0.02 or b.y2 > dg.h + 0.02:
            problems.append(f"OUT-OF-BOUNDS {nid}: {b.t()} canvas=({dg.w},{dg.h})")

    # 2. node-node overlap (ignore nodes that live in different containers)
    ids = sorted(dg.nodes)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = dg.nodes[ids[i]], dg.nodes[ids[j]]
            if not a.overlaps(b):
                continue
            ia = set(_owner_of(a, dg.containers))
            ib = set(_owner_of(b, dg.containers))
            inter = ia & ib
            if inter:
                continue
            ov_x = min(a.x2, b.x2) - max(a.x, b.x)
            ov_y = min(a.y2, b.y2) - max(a.y, b.y)
            problems.append(
                f"NODE-OVERLAP {ids[i]} x {ids[j]} "
                f"({ov_x:.2f}x{ov_y:.2f}cm)")

    # 3. edge vs node
    label_boxes = [e["chip"] for e in dg.edges if e.get("chip")]
    for ei, e in enumerate(dg.edges):
        pts = e["pts"]
        for si in range(len(pts) - 1):
            p1, p2 = pts[si], pts[si + 1]
            for nid, b in dg.nodes.items():
                touch = False
                for p in (p1, p2):
                    if (b.x - 0.08 <= p[0] <= b.x2 + 0.08 and
                            b.y - 0.08 <= p[1] <= b.y2 + 0.08):
                        touch = True
                if touch:
                    continue
                if seg_hits_rect(p1, p2, b, margin=0.03):
                    problems.append(
                        f"EDGE-HITS-NODE edge#{ei} seg{si} -> node {nid}")

    # 4. edge vs edge crossings
    cross = 0
    for i in range(len(dg.edges)):
        a = dg.edges[i]["pts"]
        for j in range(i + 1, len(dg.edges)):
            b = dg.edges[j]["pts"]
            hit = False
            for x in range(len(a) - 1):
                for y in range(len(b) - 1):
                    if seg_cross(a[x], a[x + 1], b[y], b[y + 1]) and \
                            not _junction_or_collinear(a[x], a[x + 1],
                                                      b[y], b[y + 1]):
                        hit = True
                        break
                if hit:
                    break
            if hit:
                cross += 1
                warnings.append(
                    f"EDGE-CROSS {dg.edges[i]['src']}->{dg.edges[i]['dst']}"
                    f" x {dg.edges[j]['src']}->{dg.edges[j]['dst']}"
                    + (f"  [{dg.edges[i].get('label')}]" if dg.edges[i].get('label') else "")
                    + (f" [{dg.edges[j].get('label')}]" if dg.edges[j].get('label') else ""))
    if cross and not allow_edge_crossings:
        problems.append(f"{cross} edge-edge crossings")

    # 5. label chips vs nodes
    for ei, e in enumerate(dg.edges):
        chip = e.get("chip")
        if not chip:
            continue
        for nid, b in dg.nodes.items():
            if chip.overlaps(b):
                c = chip.shrunk(0.02)
                if not (c.x >= b.x2 - 0.02 or c.x2 <= b.x + 0.02 or
                        c.y >= b.y2 - 0.02 or c.y2 <= b.y + 0.02):
                    if b.overlaps(chip):
                        problems.append(
                            f"LABEL-OVER-NODE edge#{ei} label over {nid}")

    if verbose:
        print(f"[{dg.name}] nodes={len(dg.nodes)} edges={len(dg.edges)} "
              f"crossings={cross}")
        for p in problems:
            print("   ERROR  ", p)
        for w in warnings[:40]:
            print("   warn   ", w)
        if not problems:
            print("   OK - no structural problems")
    return problems, warnings


def report_text_fit(dg, verbose=True):
    """Check every text op against its own node box (should never happen)."""
    bad = []
    for op in dg.ops:
        if op["k"] != "text":
            continue
        box = op.get("box")
        if box is None:
            continue
        bw, bh = bsize(op["lines"], op["pt"], op.get("bold", False))
        pad = op.get("pad", 0.05)
        hpad = min(pad, 0.10)
        if bw > box.w - 2 * pad + 0.02:
            bad.append(("W", op["lines"][0][:34], round(bw, 2),
                        round(box.w - 2 * pad, 2)))
        if bh > box.h - 2 * hpad + 0.02:
            bad.append(("H", op["lines"][0][:34], round(bh, 2),
                        round(box.h - 2 * hpad, 2)))
    if verbose:
        for b in bad:
            print("   TEXT-FIT", b)
        if not bad:
            print("   OK - all text fits its box")
    return bad
