# -*- coding: utf-8 -*-
"""DrawingML (Word shape group) emitter for Diagram display lists."""
import math
from .uml_core import EMU_PER_CM, wrap, bsize, lh

NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
      'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" '
      'xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup"')

GEOM = {"rect": "rect", "roundRect": "roundRect", "ellipse": "ellipse",
        "diamond": "diamond", "cylinder": "can", "line": "line"}

CLAMPED = []   # teks yang box-nya dipaksa membesar (diagnostic)


def _esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


class Emitter:
    def __init__(self, dg, scale=1.0, origin=(0.0, 0.0)):
        self.dg = dg
        self.k = scale
        self.ox, self.oy = origin
        self.n = 0

    def e(self, v):
        return int(round((v * self.k) * EMU_PER_CM))

    def ox_(self, v):
        return int(round((v * self.k + self.ox) * EMU_PER_CM))

    def oy_(self, v):
        return int(round((v * self.k + self.oy) * EMU_PER_CM))

    # ------------------------------------------------------------------
    def emit_all(self, dg):
        out = []
        for op in dg.ops:
            k = op["k"]
            if k == "shape":
                out.append(self._shape(op))
            elif k == "circle":
                out.append(self._circle(op))
            elif k == "seg":
                out.append(self._path([(op["p1"], op["p2"])], op["color"],
                                      op["lw"], op["dash"], None, None))
            elif k == "path":
                segs = [(op["pts"][i], op["pts"][i + 1])
                        for i in range(len(op["pts"]) - 1)]
                out.append(self._path(segs, op["color"], op["lw"], op["dash"],
                                      op.get("arrow"), op.get("arrow0")))
            elif k == "text":
                out.append(self._text(op))
        return "".join(s for s in out if s)

    # ------------------------------------------------------------------
    def _nid(self):
        self.n += 1
        return self.n

    def _xfrm(self, x, y, w, h, fh=False, fv=False):
        f = ""
        if fh:
            f += ' flipH="1"'
        if fv:
            f += ' flipV="1"'
        return (f'<a:xfrm{f}><a:off x="{self.ox_(x)}" y="{self.oy_(y)}"/>'
                f'<a:ext cx="{max(self.e(w), 1)}" cy="{max(self.e(h), 1)}"/></a:xfrm>')

    def _fill(self, fill):
        if fill:
            return f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>'
        return "<a:noFill/>"

    def _ln(self, color, lw, dash, arrow=None, arrow0=None):
        if not color:
            return "<a:ln w=\"0\"><a:noFill/></a:ln>"
        parts = [f'<a:ln w="{max(int(round(lw * 12700)), 9525)}" cap="flat">']
        parts.append(f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>')
        if dash:
            parts.append(f'<a:prstDash val="{dash}"/>')
        parts.append('<a:round/>')
        if arrow0:
            parts.append(f'<a:headEnd type="{arrow0}" w="med" len="med"/>')
        if arrow:
            parts.append(f'<a:tailEnd type="{arrow}" w="med" len="med"/>')
        parts.append("</a:ln>")
        return "".join(parts)

    def _geom_xml(self, geom, box, radius):
        if geom == "roundRect":
            mn = max(min(box[2], box[3]), 1e-6)
            adj = int(round((radius or 0.15) / mn * 100000))
            adj = min(max(adj, 0), 50000)
            return (f'<a:prstGeom prst="roundRect"><a:avLst>'
                    f'<a:gd name="adj" fmla="val {adj}"/></a:avLst></a:prstGeom>')
        name = GEOM.get(geom, "rect")
        return f'<a:prstGeom prst="{name}"><a:avLst/></a:prstGeom>'

    def _wsp(self, box, geom, fill, line, lw, dash, radius=None, text="",
             arrow=None, arrow0=None, fh=False, fv=False, name="shape"):
        i = self._nid()
        return (f'<wps:wsp><wps:cNvSpPr><a:cNvPr id="{i}" name="{name} {i}"/>'
                f'<a:cNvSpPr/></wps:cNvSpPr><wps:spPr>'
                f'{self._xfrm(*box, fh, fv)}{self._geom_xml(geom, box, radius)}'
                f'{self._fill(fill)}{self._ln(line, lw, dash, arrow, arrow0)}'
                f'</wps:spPr>{text}<wps:bodyPr lIns="0" tIns="0" rIns="0" '
                f'bIns="0" anchor="ctr"><a:noAutofit/></wps:bodyPr></wps:wsp>')

    def _shape(self, op):
        b = op["box"].t()
        return self._wsp(b, op["geom"], op["fill"], op["line"], op["lw"],
                         op.get("dash"), op.get("radius"), name="shp")

    def _circle(self, op):
        r = op["r"]
        i = self._nid()
        xml = self._wsp((op["cx"] - r, op["cy"] - r, 2 * r, 2 * r), "ellipse",
                        op["fill"], op["line"], op["lw"], None, name="dot")
        if op.get("inner"):
            rr = r * 0.5
            xml += self._wsp((op["cx"] - rr, op["cy"] - rr, 2 * rr, 2 * rr),
                             "ellipse", op["line"], op["line"], 1.0, None,
                             name="dot")
        return xml

    def _path(self, segs, color, lw, dash, arrow, arrow0):
        out = []
        n = len(segs)
        for idx, (p1, p2) in enumerate(segs):
            fh = p2[0] < p1[0]
            fv = p2[1] < p1[1]
            x = min(p1[0], p2[0])
            y = min(p1[1], p2[1])
            w = abs(p2[0] - p1[0])
            h = abs(p2[1] - p1[1])
            a0 = arrow0 if idx == 0 else None
            a1 = arrow if idx == n - 1 else None
            out.append(self._wsp((x, y, w, h), "line", None, color, lw, dash,
                                 None, "", a1, a0, fh, fv, name="lnk"))
        return "".join(out)

    def _text(self, op):
        box = op.get("box")
        if box is None:
            return ""
        pad = op.get("pad", 0.0)
        # Koordinat box ikut diskalakan (self.k); font juga harus ikut, kalau tidak
        # teks meluap dari kotak yang sudah mengecil saat dibuat versi A4.
        pt = op["pt"] * self.k
        bold = op.get("bold", False)
        color = op.get("color", "000000")
        align = op.get("align", "center")
        valign = op.get("valign", "center")
        anchor = {"top": "t", "bottom": "b"}.get(valign, "ctr")
        jc = {"left": "left", "right": "right"}.get(align, "center")
        sz = max(int(round(pt * 2)), 4)
        line_tw = max(int(round(pt * 1.22 * 20)), 40)
        nlines = max(len(op["lines"]), 1)
        # Word memotong teks pada batas box -> tinggi konten wajib muat semua
        # baris (line_rule exact = pt*1.22 TIP per baris = *2.54/72 cm).
        need = nlines * pt * 1.22 * 2.54 / 72.0 + 0.06 * self.k
        if box.h - 2 * pad < need - 1e-9:
            CLAMPED.append((round(box.h, 3), round(pad, 3), nlines, pt))
        bw = max(box.w - 2 * pad, 0.05)
        bh = max(box.h - 2 * pad, need)
        # Word mengukur teks ~8% lebih lebar dari PIL; beri ruang ekstra
        # agar tidak wrap (baris ekstra ter-cllip). Glif tetap di tempat
        # karena perataan kiri/tengah/kanan mengunci tepi yang sesuai.
        bw2 = bw * 1.14
        if jc == "left":
            bx = box.x + (box.w - bw) / 2.0
        elif jc == "right":
            bx = box.x + (box.w - bw) / 2.0 - (bw2 - bw)
        else:
            bx = box.x + (box.w - bw2) / 2.0
        bw = bw2
        by = box.y + (box.h - bh) / 2.0
        ps = []
        for ln in op["lines"]:
            body = (_esc(ln) if ln else "")
            if not body:
                ps.append(f'<w:p><w:pPr><w:spacing w:before="0" w:after="0" '
                          f'w:line="{line_tw}" w:lineRule="exact"/>'
                          f'<w:jc w:val="{jc}"/></w:pPr></w:p>')
            else:
                ps.append(
                    f'<w:p><w:pPr><w:spacing w:before="0" w:after="0" '
                    f'w:line="{line_tw}" w:lineRule="exact"/>'
                    f'<w:jc w:val="{jc}"/></w:pPr>'
                    f'<w:r><w:rPr><w:rFonts w:ascii="Segoe UI" w:hAnsi="Segoe UI" '
                    f'w:cs="Segoe UI"/>{"<w:b/>" if bold else ""}'
                    f'<w:color w:val="{color}"/>'
                    f'<w:sz w:val="{sz}"/></w:rPr>'
                    f'<w:t xml:space="preserve">{body}</w:t></w:r></w:p>')
        i = self._nid()
        return (f'<wps:wsp><wps:cNvSpPr><a:cNvPr id="{i}" name="txt {i}"/>'
                f'<a:cNvSpPr txBox="1"/></wps:cNvSpPr><wps:spPr>'
                f'{self._xfrm(bx, by, bw, bh)}'
                f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
                f'<a:noFill/><a:ln><a:noFill/></a:ln></wps:spPr>'
                f'<wps:txbx><w:txbxContent>{"".join(ps)}</w:txbxContent></wps:txbx>'
                f'<wps:bodyPr lIns="0" tIns="0" rIns="0" bIns="0" wrap="square" '
                f'anchor="{anchor}"><a:noAutofit/></wps:bodyPr></wps:wsp>')


def to_drawingml(dg, doc_id=101, name="UML", max_w=None, max_h=None):
    """Return a complete <w:drawing> string sized to fit max_w/max_h (cm)."""
    w, h = dg.w, dg.h
    s = 1.0
    if max_w:
        s = min(s, max_w / w)
    if max_h:
        s = min(s, max_h / h)
    w2, h2 = w * s, h * s
    cx = int(round(w2 * EMU_PER_CM))
    cy = int(round(h2 * EMU_PER_CM))
    em = Emitter(dg, scale=s)
    em.n = doc_id * 1000          # id unik lintas drawing (101000..108000)
    body = em.emit_all(dg)
    if CLAMPED:
        print("  [drawml] %d box teks dipaksa membesar: %s"
              % (len(CLAMPED), CLAMPED[:3]))
        del CLAMPED[:]
    return (
        f'<w:drawing {NS}>'
        f'<wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{cx}" cy="{cy}"/>'
        f'<wp:effectExtent l="0" t="0" r="0" b="0"/>'
        f'<wp:docPr id="{doc_id}" name="{_esc(name)}"/>'
        f'<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/>'
        f'</wp:cNvGraphicFramePr>'
        f'<a:graphic><a:graphicData '
        f'uri="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup">'
        f'<wpg:wgp><wpg:cNvGrpSpPr/><wpg:grpSpPr>'
        f'<a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/>'
        f'<a:chOff x="0" y="0"/><a:chExt cx="{cx}" cy="{cy}"/></a:xfrm>'
        f'</wpg:grpSpPr>{body}</wpg:wgp>'
        f'</a:graphicData></a:graphic></wp:inline></w:drawing>')
